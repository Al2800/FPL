"""Deadline-safe, separately modelled team attack and defence context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import math
from typing import Any, Iterable, Mapping

from src.forecasting.live_faithful import artifact_hash


class TeamContextError(ValueError):
    """Raised when team context is temporally unsafe or structurally ambiguous."""


@dataclass(frozen=True)
class AttackDefenceParameters:
    league_xg_per_team: float = 1.35
    prior_matches: float = 6.0
    home_xg_multiplier: float = 1.08
    promoted_attack_multiplier: float = 0.85
    promoted_defence_vulnerability: float = 1.15
    elo_weight: float = 0.15
    odds_weight: float = 0.10
    multiplier_min: float = 0.65
    multiplier_max: float = 1.45


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise TeamContextError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise TeamContextError(f"{field} must include a timezone")
    return parsed


def _finite(value: Any, field: str, *, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TeamContextError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < minimum:
        raise TeamContextError(f"{field} must be finite and at least {minimum}")
    return number


def _clip(value: float, params: AttackDefenceParameters) -> float:
    return min(params.multiplier_max, max(params.multiplier_min, value))


def eligible_odds_snapshot(
    snapshot: Mapping[str, Any] | None,
    *,
    cutoff: str,
) -> tuple[dict[str, float] | None, str]:
    """Accept only explicitly registered pre-deadline 1X2 odds."""
    if snapshot is None:
        return None, "odds_absent"
    if snapshot.get("timing_label") != "registered_predeadline":
        return None, "odds_rejected_unregistered_timing"
    if _timestamp(snapshot.get("captured_at"), "odds.captured_at") >= _timestamp(
        cutoff, "cutoff"
    ):
        return None, "odds_rejected_at_or_after_cutoff"
    values = {
        name: _finite(snapshot.get(name), f"odds.{name}")
        for name in ("p_home", "p_draw", "p_away")
    }
    if abs(sum(values.values()) - 1.0) > 1e-6:
        return None, "odds_rejected_probabilities_not_normalised"
    return values, "odds_accepted"


def estimate_team_strengths(
    *,
    teams: Iterable[str],
    observations: Iterable[Mapping[str, Any]],
    cutoff: str,
    promoted_teams: Iterable[str] = (),
    params: AttackDefenceParameters = AttackDefenceParameters(),
) -> dict[str, dict[str, float | int | bool]]:
    """Estimate attack xG and defensive xGA using only prior observations."""
    cutoff_time = _timestamp(cutoff, "cutoff")
    promoted = {str(team) for team in promoted_teams}
    observations_by_team: dict[str, list[tuple[float, float]]] = {
        str(team): [] for team in teams
    }
    for row in sorted(observations, key=lambda value: str(value["kickoff_time"])):
        if _timestamp(row["kickoff_time"], "observation.kickoff_time") >= cutoff_time:
            raise TeamContextError("Team observation is not strictly before cutoff")
        home = str(row["home_team"])
        away = str(row["away_team"])
        if home not in observations_by_team or away not in observations_by_team:
            raise TeamContextError(f"Unknown observed team: {home} vs {away}")
        home_xg = _finite(row["home_xg"], "home_xg")
        away_xg = _finite(row["away_xg"], "away_xg")
        observations_by_team[home].append((home_xg, away_xg))
        observations_by_team[away].append((away_xg, home_xg))

    result: dict[str, dict[str, float | int | bool]] = {}
    base = params.league_xg_per_team
    for team, rows in observations_by_team.items():
        is_promoted = team in promoted
        prior_attack = base * (params.promoted_attack_multiplier if is_promoted else 1.0)
        prior_xga = base * (params.promoted_defence_vulnerability if is_promoted else 1.0)
        denominator = params.prior_matches + len(rows)
        result[team] = {
            "attack_xg": (params.prior_matches * prior_attack + sum(row[0] for row in rows)) / denominator,
            "defence_xga": (params.prior_matches * prior_xga + sum(row[1] for row in rows)) / denominator,
            "matches": len(rows),
            "promoted_cold_start": is_promoted and not rows,
        }
    return result


def build_attack_defence_prior(
    *,
    season: str,
    cutoff: str,
    team_identities: Iterable[Mapping[str, Any]],
    fixtures: Iterable[Mapping[str, Any]],
    observations: Iterable[Mapping[str, Any]],
    promoted_teams: Iterable[str] = (),
    elo_expected_scores: Mapping[tuple[int, str], float] | None = None,
    odds_snapshots: Mapping[int, Mapping[str, Any]] | None = None,
    params: AttackDefenceParameters = AttackDefenceParameters(),
    lineage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create independent attack and defence multipliers for future fixtures."""
    identity_rows = list(team_identities)
    identities = {str(row["team_name"]): str(row["club_id"]) for row in identity_rows}
    if len(identities) != len(identity_rows):
        raise TeamContextError("Duplicate team identity")
    by_club = {club_id: team for team, club_id in identities.items()}
    strengths = estimate_team_strengths(
        teams=identities,
        observations=observations,
        cutoff=cutoff,
        promoted_teams=promoted_teams,
        params=params,
    )
    degraded_reasons: set[str] = set()
    adjustments: list[dict[str, Any]] = []
    for fixture in fixtures:
        fixture_id = int(fixture["fixture_id"])
        home_club = str(fixture["home_club_id"])
        away_club = str(fixture["away_club_id"])
        if home_club not in by_club or away_club not in by_club:
            raise TeamContextError(f"Unknown fixture club in {fixture_id}")
        home = by_club[home_club]
        away = by_club[away_club]
        home_strength = strengths[home]
        away_strength = strengths[away]
        base = params.league_xg_per_team
        expected_home_xg = (
            base * params.home_xg_multiplier
            * float(home_strength["attack_xg"]) / base
            * float(away_strength["defence_xga"]) / base
        )
        expected_away_xg = (
            base * float(away_strength["attack_xg"]) / base
            * float(home_strength["defence_xga"]) / base
        )
        for club_id, own_xg, opponent_xg in (
            (home_club, expected_home_xg, expected_away_xg),
            (away_club, expected_away_xg, expected_home_xg),
        ):
            elo_score = (
                float(elo_expected_scores[(fixture_id, club_id)])
                if elo_expected_scores and (fixture_id, club_id) in elo_expected_scores
                else 0.5
            )
            if not elo_expected_scores:
                degraded_reasons.add("elo_absent")
            elo_factor = (elo_score / 0.5) ** params.elo_weight
            adjustments.append(
                {
                    "fixture_id": fixture_id,
                    "club_id": club_id,
                    "attack_multiplier": round(_clip(own_xg / base * elo_factor, params), 6),
                    "defence_multiplier": round(_clip(math.exp(base - opponent_xg) * elo_factor, params), 6),
                    "expected_team_xg": round(own_xg, 6),
                    "expected_opponent_xg": round(opponent_xg, 6),
                    "elo_expected_score": round(elo_score, 6),
                }
            )
        odds, odds_status = eligible_odds_snapshot(
            (odds_snapshots or {}).get(fixture_id), cutoff=cutoff
        )
        if odds is None:
            degraded_reasons.add(odds_status)
        else:
            for row in adjustments[-2:]:
                side_score = (
                    odds["p_home"] + 0.5 * odds["p_draw"]
                    if row["club_id"] == home_club
                    else odds["p_away"] + 0.5 * odds["p_draw"]
                )
                odds_factor = (side_score / 0.5) ** params.odds_weight
                row["attack_multiplier"] = round(_clip(row["attack_multiplier"] * odds_factor, params), 6)
                row["defence_multiplier"] = round(_clip(row["defence_multiplier"] * odds_factor, params), 6)
                row["odds_expected_score"] = round(side_score, 6)

    result = {
        "schema_version": "1.0",
        "season": season,
        "as_of": cutoff,
        "model": {"type": "separate_attack_defence_xg", **asdict(params)},
        "status": "degraded" if degraded_reasons else "complete",
        "degraded_reasons": sorted(degraded_reasons),
        "fallback_teams": sorted(
            identities[team] for team, row in strengths.items() if bool(row["promoted_cold_start"])
        ),
        "team_strengths": {
            identities[team]: {
                key: round(value, 6) if isinstance(value, float) else value
                for key, value in row.items()
            }
            for team, row in sorted(strengths.items())
        },
        "fixture_adjustments": sorted(adjustments, key=lambda row: (row["fixture_id"], row["club_id"])),
        "lineage": dict(lineage or {}),
    }
    result["content_sha256"] = artifact_hash(result)
    return result
