"""Companion context for initial-squad packets: fixtures, availability, roles, gaps."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.evidence.availability_ledger import project_availability
from src.forecasting.live_faithful import artifact_hash


class InitialSquadContextError(ValueError):
    """Raised when packet companion context cannot be built safely."""


_DOUBTFUL_START_DELTA = 0.25


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise InitialSquadContextError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise InitialSquadContextError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _as_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _player_uid(season: str, player_id: str) -> str:
    return f"player:{season}:{player_id}"


def _player_id_from_uid(player_uid: str, *, season: str) -> str | None:
    prefix = f"player:{season}:"
    text = str(player_uid)
    if not text.startswith(prefix):
        return None
    identity = text[len(prefix) :].strip()
    return identity or None


def build_fixture_audit(
    *,
    season: str,
    decision_cutoff: str,
    captured_at: str,
    horizon_gameweeks: Sequence[int],
    bootstrap: Mapping[str, Any],
    fixtures: Sequence[Mapping[str, Any]],
    players: Sequence[Mapping[str, Any]],
    forecasts: Sequence[Mapping[str, Any]],
    team_prior: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build a hash-bound per-player-week fixture audit companion."""

    clubs = {
        str(int(team["id"])): str(team["name"])
        for team in bootstrap.get("teams", [])
        if isinstance(team, Mapping)
    }
    fixture_by_id: dict[int, dict[str, Any]] = {}
    for raw in fixtures:
        if not isinstance(raw, Mapping) or raw.get("id") is None:
            continue
        fixture_by_id[int(raw["id"])] = dict(raw)

    adjustments: dict[tuple[int, str], dict[str, Any]] = {}
    if isinstance(team_prior, Mapping):
        for row in team_prior.get("fixture_adjustments", []):
            if not isinstance(row, Mapping):
                continue
            adjustments[(int(row["fixture_id"]), str(row["club_id"]))] = dict(row)

    forecast_by_gw = {
        int(item["gameweek"]): item.get("forecast", {})
        for item in forecasts
        if isinstance(item, Mapping)
    }
    components_by_player_gw: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for gameweek, forecast in forecast_by_gw.items():
        if not isinstance(forecast, Mapping):
            continue
        for row in forecast.get("players", []):
            if not isinstance(row, Mapping):
                continue
            player_id = str(row["player_id"])
            components_by_player_gw.setdefault(player_id, {})[gameweek] = [
                dict(component)
                for component in row.get("fixture_components", [])
                if isinstance(component, Mapping)
            ]

    audit_players: dict[str, Any] = {}
    for player in players:
        if not isinstance(player, Mapping):
            continue
        player_id = str(player["player_id"])
        club_id = str(player["club_id"])
        weeks: list[dict[str, Any]] = []
        for index, gameweek in enumerate(horizon_gameweeks):
            components = components_by_player_gw.get(player_id, {}).get(int(gameweek), [])
            fixture_rows: list[dict[str, Any]] = []
            for component in components:
                fixture_id = int(component["fixture_id"])
                official = fixture_by_id.get(fixture_id, {})
                was_home = bool(component.get("was_home"))
                opponent = str(component.get("opponent_club_id"))
                fdr = (
                    official.get("team_h_difficulty")
                    if was_home
                    else official.get("team_a_difficulty")
                )
                adj = adjustments.get((fixture_id, club_id), {})
                fixture_rows.append(
                    {
                        "fixture_id": fixture_id,
                        "opponent_club_id": opponent,
                        "opponent_name": clubs.get(opponent),
                        "was_home": was_home,
                        "kickoff_time": official.get("kickoff_time"),
                        "fdr": fdr,
                        "attack_multiplier": adj.get(
                            "attack_multiplier", component.get("team_multiplier")
                        ),
                        "defence_multiplier": adj.get("defence_multiplier"),
                        "team_multiplier": component.get("team_multiplier"),
                        "expected_team_xg": adj.get("expected_team_xg"),
                        "expected_opponent_xg": adj.get("expected_opponent_xg"),
                        "elo_expected_score": adj.get("elo_expected_score"),
                        "odds_expected_score": adj.get("odds_expected_score"),
                        "expected_minutes": component.get("expected_minutes"),
                        "rate_expected_points": component.get("rate_expected_points"),
                        "event_expected_points": component.get("event_expected_points"),
                        "expected_points": component.get("expected_points"),
                    }
                )
            count = len(fixture_rows)
            weeks.append(
                {
                    "gameweek": int(gameweek),
                    "fixture_count": count,
                    "blank": count == 0,
                    "double": count > 1,
                    "fixtures": fixture_rows,
                    "expected_points": (
                        float(player["expected_points"][index])
                        if index < len(player.get("expected_points", []))
                        else None
                    ),
                    "start_probability": (
                        float(player["start_probability"][index])
                        if index < len(player.get("start_probability", []))
                        else None
                    ),
                }
            )
        audit_players[player_id] = {
            "player_id": player_id,
            "web_name": str(player.get("web_name", "")),
            "club_id": club_id,
            "club_name": clubs.get(club_id),
            "position": str(player.get("position", "")),
            "gameweeks": weeks,
        }

    result = {
        "schema_version": "initial-squad-fixture-audit-v1",
        "season": season,
        "decision_cutoff": decision_cutoff,
        "captured_at": captured_at,
        "horizon_gameweeks": [int(value) for value in horizon_gameweeks],
        "club_names": clubs,
        "players": audit_players,
        "team_prior_source": (
            (team_prior or {}).get("lineage", {}).get("source_id")
            if isinstance(team_prior, Mapping)
            else None
        ),
        "team_prior_sha256": (
            team_prior.get("content_sha256") if isinstance(team_prior, Mapping) else None
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def bounded_fixture_audit_view(
    audit: Mapping[str, Any],
    *,
    player_ids: Sequence[str],
) -> dict[str, Any]:
    """Return a shortlist-sized fixture audit view for strategy prompts."""

    selected = {
        str(player_id): deepcopy(audit["players"][str(player_id)])
        for player_id in player_ids
        if str(player_id) in audit.get("players", {})
    }
    view = {
        "schema_version": "initial-squad-fixture-audit-view-v1",
        "source_audit_sha256": audit.get("content_sha256"),
        "season": audit.get("season"),
        "decision_cutoff": audit.get("decision_cutoff"),
        "player_ids": [str(value) for value in player_ids],
        "players": selected,
    }
    view["content_sha256"] = artifact_hash(view)
    return view


def blend_availability_into_horizon_players(
    players: Sequence[Mapping[str, Any]],
    *,
    ledger: Mapping[str, Any] | None,
    season: str,
    as_of: str,
    fixtures: Sequence[Mapping[str, Any]],
    horizon_gameweeks: Sequence[int],
    doubtful_start_delta: float = _DOUBTFUL_START_DELTA,
    trust_admitted_ledger: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deterministically adjust GW start_p / EP from an availability ledger."""

    result_players = [deepcopy(dict(row)) for row in players]
    audit: dict[str, Any] = {
        "schema_version": "initial-squad-availability-blend-v1",
        "status": "absent",
        "as_of": as_of,
        "applied": [],
        "skipped": [],
        "ledger_sha256": None,
        "view_sha256": None,
    }
    if ledger is None:
        return result_players, _seal(audit)

    by_id = {str(row["player_id"]): row for row in result_players}
    view = project_availability(
        ledger,
        decision_at=as_of,
        player_uids=[_player_uid(season, player_id) for player_id in by_id],
    )
    audit["ledger_sha256"] = ledger.get("content_sha256")
    audit["view_sha256"] = view.get("content_sha256")

    kickoffs: dict[tuple[str, int], datetime] = {}
    for raw in fixtures:
        if not isinstance(raw, Mapping) or raw.get("event") is None:
            continue
        gameweek = int(raw["event"])
        if gameweek not in set(int(value) for value in horizon_gameweeks):
            continue
        try:
            ko = _timestamp(raw.get("kickoff_time"), "fixture.kickoff_time")
        except InitialSquadContextError:
            continue
        for club_key in ("team_h", "team_a"):
            club_id = str(int(raw[club_key]))
            key = (club_id, gameweek)
            prior = kickoffs.get(key)
            if prior is None or ko < prior:
                kickoffs[key] = ko

    as_of_dt = _timestamp(as_of, "as_of")
    for claim in view.get("accepted", []):
        player_id = _player_id_from_uid(str(claim["player_uid"]), season=season)
        if player_id is None or player_id not in by_id:
            audit["skipped"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "reason": "player_not_in_packet",
                    "player_uid": str(claim["player_uid"]),
                }
            )
            continue
        provenance = claim.get("provenance", {})
        if not trust_admitted_ledger:
            if provenance.get("identity_resolution") != "exact":
                audit["skipped"].append(
                    {
                        "claim_id": str(claim["claim_id"]),
                        "reason": "identity_not_exact",
                        "player_id": player_id,
                    }
                )
                continue
            hashes = provenance.get("source_hashes")
            if not isinstance(hashes, Mapping) or not hashes:
                audit["skipped"].append(
                    {
                        "claim_id": str(claim["claim_id"]),
                        "reason": "source_hashes_missing",
                        "player_id": player_id,
                    }
                )
                continue

        row = by_id[player_id]
        status = str(claim["status"])
        expires = (
            _timestamp(claim["expires_at"], "expires_at")
            if claim.get("expires_at")
            else None
        )
        # Default information-time mode: claims accepted at as_of apply across
        # the horizon. If expires_at falls between Gameweek kickoffs, later
        # Gameweeks stop receiving the adjustment (kickoff-aware tail cut).
        gw_effects: list[dict[str, Any]] = []
        start = list(row["start_probability"])
        points = list(row["expected_points"])
        uncertainty = list(row["uncertainty"])
        for index, gameweek in enumerate(horizon_gameweeks):
            ko = kickoffs.get((str(row["club_id"]), int(gameweek)))
            if expires is not None and expires <= as_of_dt:
                gw_effects.append(
                    {
                        "gameweek": int(gameweek),
                        "applied": False,
                        "reason": "expired_at_information_time",
                    }
                )
                continue
            # Tail cut only when expiry sits inside the fixture horizon, i.e.
            # after as_of but before this GW kickoff while a prior GW was still
            # covered. Preseason claims that expire before every kickoff still
            # apply (they remain live in the information set).
            prior_gw_kickoffs = [
                kickoffs.get((str(row["club_id"]), int(prior)))
                for prior in horizon_gameweeks
                if int(prior) < int(gameweek)
            ]
            prior_covered = any(
                value is not None and expires is not None and expires > value
                for value in prior_gw_kickoffs
            )
            if (
                expires is not None
                and ko is not None
                and expires <= ko
                and prior_covered
            ):
                gw_effects.append(
                    {
                        "gameweek": int(gameweek),
                        "applied": False,
                        "reason": "expired_before_gameweek_kickoff",
                    }
                )
                continue
            before_p = float(start[index])
            before_ep = float(points[index])
            if status == "unavailable":
                after_p = 0.0
                after_ep = 0.0
                effect = "zero_projection"
            elif status == "doubtful":
                after_p = max(0.0, before_p - float(doubtful_start_delta))
                ratio = after_p / before_p if before_p else 0.0
                after_ep = round(before_ep * ratio, 6)
                effect = "bounded_reduction"
            else:
                gw_effects.append(
                    {
                        "gameweek": int(gameweek),
                        "applied": False,
                        "reason": f"status_{status}_no_reduction",
                    }
                )
                continue
            start[index] = round(after_p, 6)
            points[index] = round(after_ep, 6)
            uncertainty[index] = round(1.0 - after_p, 6)
            gw_effects.append(
                {
                    "gameweek": int(gameweek),
                    "applied": True,
                    "effect": effect,
                    "before_start_probability": before_p,
                    "after_start_probability": start[index],
                    "before_expected_points": before_ep,
                    "after_expected_points": points[index],
                    "expires_before_kickoff": bool(
                        expires is not None and ko is not None and expires <= ko
                    ),
                }
            )
        if any(item.get("applied") for item in gw_effects):
            row["start_probability"] = start
            row["expected_points"] = points
            row["uncertainty"] = uncertainty
            row["availability_blend"] = {
                "claim_id": str(claim["claim_id"]),
                "status": status,
                "confidence": float(claim.get("confidence", 0.0) or 0.0),
            }
            audit["applied"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_id": player_id,
                    "status": status,
                    "gameweeks": gw_effects,
                }
            )
        else:
            audit["skipped"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_id": player_id,
                    "reason": "no_gameweek_in_horizon_before_expiry",
                    "gameweeks": gw_effects,
                }
            )

    audit["status"] = "applied" if audit["applied"] else "absent"
    return result_players, _seal(audit)


def attach_set_piece_roles(
    players: Sequence[Mapping[str, Any]],
    *,
    set_pieces_artifact: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach shadow-only set-piece role flags; never change EP."""

    result = [deepcopy(dict(row)) for row in players]
    summary: dict[str, Any] = {
        "schema_version": "initial-squad-set-piece-surface-v1",
        "status": "absent",
        "players_tagged": 0,
        "effect_weights": None,
        "promotion_status": None,
        "ledger_sha256": None,
    }
    if not isinstance(set_pieces_artifact, Mapping):
        return result, _seal(summary)

    ledger = set_pieces_artifact.get("ledger")
    active = []
    if isinstance(ledger, Mapping):
        active = list(ledger.get("active_roles") or [])
    summary["effect_weights"] = set_pieces_artifact.get("effect_weights")
    summary["promotion_status"] = set_pieces_artifact.get("promotion_status")
    summary["ledger_sha256"] = (
        ledger.get("content_sha256") if isinstance(ledger, Mapping) else None
    )
    by_player: dict[str, list[dict[str, Any]]] = {}
    for role in active:
        if not isinstance(role, Mapping):
            continue
        player_id = str(role.get("official_player_id"))
        by_player.setdefault(player_id, []).append(
            {
                "role": str(role.get("role")),
                "rank": role.get("rank"),
                "confidence": role.get("confidence"),
                "expires_at": role.get("expires_at"),
                "observation_id": role.get("observation_id"),
            }
        )
    tagged = 0
    for row in result:
        roles = by_player.get(str(row["player_id"]))
        if not roles:
            continue
        row["set_piece_roles"] = {
            "effect_weights": summary["effect_weights"],
            "promotion_status": summary["promotion_status"],
            "roles": sorted(
                roles, key=lambda item: (str(item["role"]), int(item.get("rank") or 99))
            ),
        }
        tagged += 1
    summary["players_tagged"] = tagged
    summary["status"] = "applied" if tagged else "absent"
    return result, _seal(summary)


def build_gap_panel(
    *,
    source_families: Mapping[str, Mapping[str, Any]],
    forecast_limitations: Sequence[str],
    availability_blend: Mapping[str, Any] | None,
    odds_summary: Mapping[str, Any] | None,
    set_piece_summary: Mapping[str, Any] | None,
    fixture_audit_sha256: str | None,
) -> dict[str, Any]:
    """Single panel of optional-family presence/gaps for strategy agents."""

    def family_row(family_id: str) -> dict[str, Any]:
        state = source_families.get(family_id, {})
        return {
            "family_id": family_id,
            "state": state.get("state"),
            "manifest_status": state.get("manifest_status"),
            "reasons": list(state.get("reasons") or []),
            "artifact_sha256": state.get("artifact_sha256"),
        }

    availability_status = "absent"
    if availability_blend and availability_blend.get("status") == "applied":
        availability_status = "blended_into_start_probability"
    elif family_row("availability_role_evidence").get("state") == "admitted":
        availability_status = "admitted_not_blended_or_expired"

    odds_status = "absent"
    if odds_summary and odds_summary.get("status") == "applied":
        odds_status = "applied_to_team_prior"
    elif odds_summary and odds_summary.get("reason"):
        odds_status = str(odds_summary["reason"])

    panel = {
        "schema_version": "initial-squad-gap-panel-v1",
        "families": {
            "official_bootstrap": family_row("official_bootstrap"),
            "official_fixtures": family_row("official_fixtures"),
            "licensed_odds": {
                **family_row("licensed_odds"),
                "integration": odds_status,
                "runbook": (
                    ".scratch/evidence-gap-fill/issues/04-odds-slot-capture-runbook.md"
                ),
            },
            "player_ratings": {
                **family_row("player_ratings"),
                "integration": "degraded_shadow_only_no_scrape",
            },
            "transfers_and_signings": {
                **family_row("transfers_and_signings"),
                "integration": "launch_context_partial_or_absent",
            },
            "promoted_team_priors": {
                **family_row("promoted_team_priors"),
                "integration": "launch_context_and_understat_fallback",
            },
            "availability_role_evidence": {
                **family_row("availability_role_evidence"),
                "integration": availability_status,
            },
            "set_pieces": {
                **family_row("set_pieces"),
                "integration": (
                    set_piece_summary.get("status")
                    if set_piece_summary
                    else "absent"
                ),
                "effect_weights": (
                    set_piece_summary.get("effect_weights")
                    if set_piece_summary
                    else None
                ),
                "promotion_status": (
                    set_piece_summary.get("promotion_status")
                    if set_piece_summary
                    else None
                ),
            },
            "launch_context": family_row("launch_context"),
            "world_cup_return_fatigue": family_row("world_cup_return_fatigue"),
        },
        "forecast_limitations": sorted(str(value) for value in forecast_limitations),
        "fixture_audit_sha256": fixture_audit_sha256,
        "notes": [
            "Agents must read this panel before recommending; degraded families "
            "are explicit gaps, not neutral evidence.",
            "Player ratings remain rights-gated; do not scrape FotMob/Sofascore/FBref.",
            "Set-piece roles may be visible while effect_weights stay null.",
        ],
    }
    panel["content_sha256"] = artifact_hash(panel)
    return panel


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    sealed = deepcopy(dict(value))
    sealed.pop("content_sha256", None)
    sealed["content_sha256"] = artifact_hash(sealed)
    return sealed
