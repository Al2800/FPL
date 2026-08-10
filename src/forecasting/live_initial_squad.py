"""Build a cutoff-safe live-faithful horizon for the initial-squad packet.

This adapter deliberately composes the existing ``live_faithful`` forecaster
once per Gameweek.  It does not fit weights, fetch data, or turn optional
evidence gaps into neutral observations.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

from src.forecasting.live_faithful import (
    LiveFaithfulForecastError,
    artifact_hash,
    build_live_faithful_forecast,
)
from src.forecasting.team_attack_defence import AttackDefenceParameters
from src.forecasting.team_prior import EloParameters
from src.forecasting.initial_squad_context import build_fixture_audit
from src.forecasting.understat_player_context import (
    UnderstatPlayerContextError,
    build_understat_player_join,
    enrich_player_prior_with_understat_event_rates,
)
from src.forecasting.understat_team_context import (
    UnderstatTeamContextError,
    build_understat_attack_defence_team_prior,
)
from src.orchestration.historical_feature_state import feature_state_hash


POSITIONS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
FDR_MIN = 1
FDR_MAX = 5


class LiveInitialSquadForecastError(ValueError):
    """Raised when a live-faithful initial-squad horizon cannot be built."""


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveInitialSquadForecastError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveInitialSquadForecastError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        raise LiveInitialSquadForecastError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise LiveInitialSquadForecastError(f"{field} must be numeric") from exc
    if number < minimum:
        raise LiveInitialSquadForecastError(f"{field} must be at least {minimum}")
    return number


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _fdr_multiplier(
    difficulty: Any,
    *,
    bounds: tuple[float, float],
    field: str,
) -> float:
    value = _number(difficulty, field)
    if int(value) != value or not FDR_MIN <= int(value) <= FDR_MAX:
        raise LiveInitialSquadForecastError(
            f"{field} must be an integer from {FDR_MIN} to {FDR_MAX}"
        )
    # FDR is an official ordinal field.  Map it linearly to the model's
    # declared multiplier bounds; the mapping is a baseline, not a fitted
    # claim about goals or clean sheets.
    ratio = (int(value) - FDR_MIN) / (FDR_MAX - FDR_MIN)
    return round(bounds[1] - ratio * (bounds[1] - bounds[0]), 6)


def build_official_fdr_team_prior(
    *,
    fixtures: Sequence[Mapping[str, Any]],
    observed_at: str,
    source_sha256: str,
    season: str,
    multiplier_bounds: Sequence[float] = (0.7, 1.3),
) -> dict[str, Any]:
    """Build an explicit official-FDR team prior for unrevealed fixtures."""

    if len(str(source_sha256)) != 64 or any(
        character not in "0123456789abcdef" for character in str(source_sha256)
    ):
        raise LiveInitialSquadForecastError("source_sha256 must be lowercase SHA-256")
    observed_text, _ = _timestamp(observed_at, "observed_at")
    if len(multiplier_bounds) != 2:
        raise LiveInitialSquadForecastError("multiplier_bounds must have two values")
    lower, upper = (
        _number(multiplier_bounds[0], "multiplier_bounds[0]"),
        _number(multiplier_bounds[1], "multiplier_bounds[1]"),
    )
    if lower > upper:
        raise LiveInitialSquadForecastError("multiplier bounds are reversed")

    adjustments: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for raw in fixtures:
        if not isinstance(raw, Mapping):
            raise LiveInitialSquadForecastError("fixture must be an object")
        try:
            fixture_id = int(raw["id"])
            event = int(raw["event"])
            home_team = int(raw["team_h"])
            away_team = int(raw["team_a"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveInitialSquadForecastError(
                "fixture requires id, event, team_h and team_a"
            ) from exc
        for team, difficulty, was_home in (
            (home_team, raw.get("team_h_difficulty"), True),
            (away_team, raw.get("team_a_difficulty"), False),
        ):
            club_id = str(team)
            key = (fixture_id, club_id)
            if key in seen:
                raise LiveInitialSquadForecastError(
                    f"duplicate fixture/team adjustment: {fixture_id}/{club_id}"
                )
            seen.add(key)
            multiplier = _fdr_multiplier(
                difficulty,
                bounds=(lower, upper),
                field=(
                    f"fixture[{fixture_id}]."
                    f"{'team_h_difficulty' if was_home else 'team_a_difficulty'}"
                ),
            )
            adjustments.append(
                {
                    "fixture_id": fixture_id,
                    "gameweek": event,
                    "club_id": club_id,
                    "attack_multiplier": multiplier,
                    "defence_multiplier": multiplier,
                    "official_fdr": int(difficulty),
                    "was_home": was_home,
                }
            )

    result: dict[str, Any] = {
        "schema_version": "live-initial-squad-team-prior-v1",
        "season": season,
        "as_of": observed_text,
        "model": {
            "type": "official_fdr_baseline",
            "mapping": "linear_official_fdr_to_declared_multiplier_bounds",
            "multiplier_bounds": [lower, upper],
        },
        "fallback_teams": [],
        "fixture_adjustments": sorted(
            adjustments,
            key=lambda row: (row["fixture_id"], row["club_id"]),
        ),
        "lineage": {
            "source_id": "fpl-official-endpoints",
            "source_sha256": source_sha256,
            "observed_at": observed_text,
            "outcome_data_used": False,
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _feature_player(
    raw: Mapping[str, Any],
    *,
    fixture_components: Sequence[Mapping[str, Any]],
    available_at: str,
) -> dict[str, Any]:
    try:
        player_id = str(int(raw["id"]))
        position = POSITIONS[int(raw["element_type"])]
        club_id = str(int(raw["team"]))
        fpl_code = int(raw["code"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LiveInitialSquadForecastError(
            "current player has invalid id, code, team or position"
        ) from exc
    now_cost = _number(raw.get("now_cost"), f"player[{player_id}].now_cost")
    ep_next = _number(
        raw.get("ep_next"),
        f"player[{player_id}].ep_next",
        minimum=-100,
    )
    return {
        "player_id": player_id,
        "fpl_code": fpl_code,
        "name": str(raw.get("web_name", "")),
        "position": position,
        "club_id": club_id,
        "quote": {"now_cost": now_cost / 10.0},
        "history": [],
        "projection": {
            "expected_points": ep_next,
            "fixture_components": [deepcopy(dict(row)) for row in fixture_components],
        },
        "available_at": available_at,
        "official_ep_next": ep_next,
    }


def _merge_horizon_limitations(
    limitations: Sequence[str],
    forecasts: Sequence[Mapping[str, Any]],
    odds_snapshots: Mapping[int, Mapping[str, Any]] | None,
) -> list[str]:
    merged = set(limitations)
    for item in forecasts:
        forecast = item.get("forecast")
        if isinstance(forecast, Mapping):
            merged.update(str(value) for value in forecast.get("limitations", []))
    if odds_snapshots:
        merged.discard("timestamped_odds_absent")
        merged.add("timestamped_odds_applied_to_team_prior")
    return sorted(merged)


def build_live_faithful_initial_squad_horizon(
    *,
    bootstrap: Mapping[str, Any],
    fixtures: Sequence[Mapping[str, Any]],
    official_bootstrap_sha256: str,
    official_fixtures_sha256: str,
    observed_at: str,
    decision_cutoff: str,
    horizon_gameweeks: Sequence[int],
    player_prior: Mapping[str, Any],
    model_config: Mapping[str, Any],
    launch_context_status: str = "unavailable",
    understat_capture: Mapping[str, Any] | None = None,
    clubelo_ratings_by_fpl_name: Mapping[str, float] | None = None,
    clubelo_body_sha256: str | None = None,
    odds_snapshots: Mapping[int, Mapping[str, Any]] | None = None,
    odds_summary: Mapping[str, Any] | None = None,
    promoted_team_names: Sequence[str] = (),
    attack_defence_params: AttackDefenceParameters | None = None,
    elo_params: EloParameters | None = None,
) -> dict[str, Any]:
    """Materialise one deterministic live-faithful result per Gameweek."""

    observed_text, observed = _timestamp(observed_at, "observed_at")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if observed >= cutoff:
        raise LiveInitialSquadForecastError(
            "official observations must be before the decision cutoff"
        )
    if player_prior.get("content_sha256") != artifact_hash(player_prior):
        raise LiveInitialSquadForecastError("player prior content hash mismatch")
    if model_config.get("content_sha256") != artifact_hash(model_config):
        raise LiveInitialSquadForecastError("model config content hash mismatch")

    raw_elements = bootstrap.get("elements")
    if not isinstance(raw_elements, list):
        raise LiveInitialSquadForecastError("bootstrap elements must be a list")
    raw_fixtures = [dict(row) for row in fixtures if isinstance(row, Mapping)]
    if not raw_fixtures:
        raise LiveInitialSquadForecastError("official fixtures are required")
    gameweeks = [int(value) for value in horizon_gameweeks]
    if not gameweeks or any(value < 1 for value in gameweeks):
        raise LiveInitialSquadForecastError("horizon_gameweeks must be positive")

    by_gameweek: dict[int, list[dict[str, Any]]] = {value: [] for value in gameweeks}
    for raw in raw_fixtures:
        if raw.get("event") is None:
            continue
        event = int(raw["event"])
        if event in by_gameweek:
            by_gameweek[event].append(raw)

    bounds = model_config.get("fixture_multiplier_bounds", [0.7, 1.3])
    horizon_fixtures = [row for rows in by_gameweek.values() for row in rows]
    season = str(bootstrap.get("season", "2026-27"))

    player_understat_summary: dict[str, Any] = {
        "status": "absent",
        "players_enriched": 0,
    }
    effective_player_prior = deepcopy(dict(player_prior))
    if understat_capture is not None:
        try:
            join_report = build_understat_player_join(
                bootstrap=bootstrap,
                understat_capture=understat_capture,
            )
            effective_player_prior, player_understat_summary = (
                enrich_player_prior_with_understat_event_rates(
                    effective_player_prior,
                    join_report=join_report,
                )
            )
            player_understat_summary = {
                **player_understat_summary,
                "join_counts": deepcopy(dict(join_report.get("counts", {}))),
            }
        except UnderstatPlayerContextError as exc:
            player_understat_summary = {
                "status": "absent",
                "players_enriched": 0,
                "reason": str(exc),
            }

    team_prior_source = "official_fdr"
    understat_fallback_reason: str | None = None
    team_prior: dict[str, Any] | None = None
    if understat_capture is not None:
        try:
            team_prior = build_understat_attack_defence_team_prior(
                bootstrap=bootstrap,
                fixtures=horizon_fixtures,
                understat_capture=understat_capture,
                observed_at=observed_text,
                decision_cutoff=cutoff_text,
                season=season,
                promoted_team_names=promoted_team_names,
                clubelo_ratings_by_fpl_name=clubelo_ratings_by_fpl_name,
                clubelo_body_sha256=clubelo_body_sha256,
                odds_snapshots=odds_snapshots,
                params=attack_defence_params,
                elo_params=elo_params,
            )
            team_prior_source = "understat_attack_defence"
        except UnderstatTeamContextError as exc:
            # Keep the horizon available: FDR remains the explicit baseline when
            # a private capture cannot be joined to the current bootstrap.
            understat_fallback_reason = str(exc)
            team_prior = None
    if team_prior is None:
        team_prior = build_official_fdr_team_prior(
            fixtures=horizon_fixtures,
            observed_at=observed_text,
            source_sha256=official_fixtures_sha256,
            season=season,
            multiplier_bounds=bounds,
        )
    identity_map = {
        "schema_version": "live-initial-squad-identity-v1",
        "players": [
            {"canonical_id": str(int(row["id"])), "fpl_code": int(row["code"])}
            for row in raw_elements
            if isinstance(row, Mapping)
        ],
    }
    identity_hash = _sha256(identity_map)

    forecasts: list[dict[str, Any]] = []
    vectors: dict[str, dict[str, list[float]]] = {}
    prior_season = str(effective_player_prior.get("season", "")).strip()
    prior_season_label = prior_season.replace("-", "_") or "unknown"
    team_prior_limitation = (
        "understat_attack_defence_team_prior"
        if team_prior_source == "understat_attack_defence"
        else "official_fdr_team_prior_baseline"
    )
    limitations = [
        team_prior_limitation,
        f"historical_player_prior_{prior_season_label}",
        "uncertainty_proxy_from_start_probability",
        "launch_context_not_applied_inside_forecaster"
        if launch_context_status != "applied"
        else "launch_context_flags_applied_after_forecast",
    ]
    player_rate_status = str(player_understat_summary.get("status", "absent"))
    if player_rate_status == "applied":
        limitations.append("understat_player_event_rates_applied")
    elif player_rate_status == "partial":
        limitations.append("understat_player_event_rates_partial")
    else:
        limitations.append("understat_player_event_rates_absent")
    if team_prior_source == "understat_attack_defence":
        limitations.append("prior_season_understat_xg_matches_only")
        if clubelo_ratings_by_fpl_name is None:
            limitations.append("clubelo_expected_scores_absent")
        else:
            limitations.append("clubelo_expected_scores_applied")
        if team_prior.get("fallback_teams"):
            limitations.append("promoted_team_cold_start_priors")
        for reason in team_prior.get("degraded_reasons", []):
            limitations.append(f"team_prior_{reason}")
        if odds_snapshots:
            limitations.append("timestamped_odds_applied_to_team_prior")
        elif odds_summary and odds_summary.get("reason"):
            limitations.append(f"timestamped_odds_{odds_summary['reason']}")
        else:
            limitations.append("timestamped_odds_absent")
    elif understat_fallback_reason is not None:
        limitations.append("understat_team_prior_unavailable_fallback_fdr")
        limitations.append("timestamped_odds_absent")
    else:
        limitations.append("timestamped_odds_absent")
    for gameweek in gameweeks:
        components_by_player: dict[str, list[dict[str, Any]]] = {}
        for fixture in by_gameweek[gameweek]:
            fixture_id = int(fixture["id"])
            home = str(int(fixture["team_h"]))
            away = str(int(fixture["team_a"]))
            for raw in raw_elements:
                if not isinstance(raw, Mapping):
                    continue
                team = str(int(raw.get("team", 0)))
                if team == home:
                    components_by_player.setdefault(str(int(raw["id"])), []).append(
                        {
                            "fixture_id": fixture_id,
                            "opponent_club_id": away,
                            "was_home": True,
                        }
                    )
                elif team == away:
                    components_by_player.setdefault(str(int(raw["id"])), []).append(
                        {
                            "fixture_id": fixture_id,
                            "opponent_club_id": home,
                            "was_home": False,
                        }
                    )

        feature_players = [
            _feature_player(
                raw,
                fixture_components=components_by_player.get(str(int(raw["id"])), []),
                available_at=observed_text,
            )
            for raw in raw_elements
            if isinstance(raw, Mapping) and str(raw.get("status", "")) == "a"
        ]
        feature_state: dict[str, Any] = {
            "schema_version": "live-initial-squad-feature-state-v1",
            "season": "2026-27",
            "gameweek": gameweek,
            "cutoff": cutoff_text,
            "players": feature_players,
            "fixtures": deepcopy(by_gameweek[gameweek]),
            "limitations": list(limitations),
            "lineage": {
                "official_bootstrap_sha256": official_bootstrap_sha256,
                "official_fixtures_sha256": official_fixtures_sha256,
                "identity_map_sha256": identity_hash,
                "player_prior_sha256": str(effective_player_prior["content_sha256"]),
                "base_player_prior_sha256": str(player_prior["content_sha256"]),
                "team_prior_sha256": str(team_prior["content_sha256"]),
                "model_sha256": str(model_config["content_sha256"]),
            },
        }
        feature_state["content_sha256"] = feature_state_hash(feature_state)
        try:
            forecast = build_live_faithful_forecast(
                feature_state=feature_state,
                identity_map=identity_map,
                player_prior=effective_player_prior,
                team_prior=team_prior,
                model_config=model_config,
            )
        except LiveFaithfulForecastError as exc:
            raise LiveInitialSquadForecastError(
                f"Gameweek {gameweek} live-faithful build failed: {exc}"
            ) from exc
        forecasts.append(
            {
                "gameweek": gameweek,
                "feature_state_sha256": feature_state["content_sha256"],
                "forecast": forecast,
            }
        )
        for row in forecast.get("players", []):
            player_id = str(row["player_id"])
            vectors.setdefault(
                player_id,
                {
                    "expected_points": [],
                    "start_probability": [],
                    "uncertainty": [],
                },
            )
            start_probability = float(row["start_probability"])
            vectors[player_id]["expected_points"].append(
                round(float(row["expected_points"]), 4)
            )
            vectors[player_id]["start_probability"].append(
                round(start_probability, 6)
            )
            vectors[player_id]["uncertainty"].append(
                round(1.0 - start_probability, 6)
            )

    model_name = "live-faithful-v1.feature-complete"
    audit_players = []
    for raw in raw_elements:
        if not isinstance(raw, Mapping) or str(raw.get("status", "")) != "a":
            continue
        player_id = str(int(raw["id"]))
        vector = vectors.get(player_id)
        if vector is None:
            continue
        audit_players.append(
            {
                "player_id": player_id,
                "web_name": str(raw.get("web_name", "")),
                "position": POSITIONS[int(raw["element_type"])],
                "club_id": str(int(raw["team"])),
                "expected_points": list(vector["expected_points"]),
                "start_probability": list(vector["start_probability"]),
            }
        )
    fixture_audit = build_fixture_audit(
        season=season,
        decision_cutoff=cutoff_text,
        captured_at=observed_text,
        horizon_gameweeks=gameweeks,
        bootstrap=bootstrap,
        fixtures=raw_fixtures,
        players=audit_players,
        forecasts=forecasts,
        team_prior=team_prior,
    )
    result: dict[str, Any] = {
        "schema_version": "live-initial-squad-horizon-v1",
        "season": "2026-27",
        "gameweeks": gameweeks,
        "model_config_id": model_name,
        "model_version": str(model_config["model_version"]),
        "status": "degraded",
        "limitations": sorted(_merge_horizon_limitations(limitations, forecasts, odds_snapshots)),
        "lineage": {
            "official_bootstrap_sha256": official_bootstrap_sha256,
            "official_fixtures_sha256": official_fixtures_sha256,
            "identity_map_sha256": identity_hash,
            "player_prior_sha256": str(effective_player_prior["content_sha256"]),
            "base_player_prior_sha256": str(player_prior["content_sha256"]),
            "team_prior_sha256": str(team_prior["content_sha256"]),
            "team_prior_source": team_prior_source,
            "team_prior_model": deepcopy(dict(team_prior.get("model", {}))),
            "model_sha256": str(model_config["content_sha256"]),
            "understat_player_event_rates": deepcopy(player_understat_summary),
            "odds_team_prior": deepcopy(dict(odds_summary or {"status": "absent"})),
            "event_model_weight": float(model_config.get("event_model_weight", 0) or 0),
            "fixture_audit_sha256": fixture_audit["content_sha256"],
        },
        "player_vectors": vectors,
        "fixture_audit": fixture_audit,
        "gameweek_forecast_hashes": [
            {
                "gameweek": item["gameweek"],
                "feature_state_sha256": item["feature_state_sha256"],
                "forecast_sha256": item["forecast"]["content_sha256"],
            }
            for item in forecasts
        ],
    }
    result["content_sha256"] = artifact_hash(result)
    return result
