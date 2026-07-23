"""Reveal-gated scoring of official FPL outcomes against a frozen plan."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from src.optimisation.io import fingerprint
from src.orchestration.validated_plan import (
    ValidatedPlanError,
    validate_plan_integrity,
)
from src.scoring.rules_loader import get_rule


class OutcomeScoringError(ValueError):
    """Raised when revealed data cannot be safely scored."""


def realised_outcome_hash(outcome: Mapping[str, Any]) -> str:
    body = deepcopy(dict(outcome))
    body.pop("content_sha256", None)
    return fingerprint(body)


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise OutcomeScoringError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise OutcomeScoringError(f"{field} must include a timezone")
    return parsed


def _position(value: Any) -> str:
    position = str(value)
    return "GKP" if position == "GK" else position


def _automatic_substitutions(
    starting_ids: list[str],
    bench_ids: list[str],
    players: Mapping[str, Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> tuple[list[str], list[dict[str, str]]]:
    """Apply the ordered bench once, selecting an eligible absent starter."""
    effective = list(starting_ids)
    substitutions: list[dict[str, str]] = []
    constraints = get_rule(dict(rules), "lineup.formation_constraints")["value"]

    def legal(ids: list[str]) -> bool:
        counts = Counter(players[player_id]["position"] for player_id in ids)
        return len(ids) == 11 and all(
            bounds["min"] <= counts.get(position, 0) <= bounds["max"]
            for position, bounds in constraints.items()
        )

    for bench_id in bench_ids:
        if players[bench_id]["minutes"] <= 0:
            continue
        bench_position = players[bench_id]["position"]
        candidates = [
            (index, starter_id)
            for index, starter_id in enumerate(effective)
            if players[starter_id]["minutes"] <= 0
            and (
                (bench_position == "GKP" and players[starter_id]["position"] == "GKP")
                or (bench_position != "GKP" and players[starter_id]["position"] != "GKP")
            )
        ]
        for index, starter_id in candidates:
            trial = list(effective)
            trial[index] = bench_id
            if legal(trial):
                effective = trial
                substitutions.append(
                    {"player_out_id": starter_id, "player_in_id": bench_id}
                )
                break
    return effective, substitutions


def score_revealed_outcome(
    plan: Mapping[str, Any],
    hidden_outcome: Mapping[str, Any],
    *,
    revealed_at: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Aggregate official rows and score one immutable frozen plan."""
    try:
        validate_plan_integrity(
            plan, rules=rules, ruleset_sha256=ruleset_sha256
        )
    except ValidatedPlanError as exc:
        raise OutcomeScoringError(f"Validated plan hash/integrity failed: {exc}") from exc
    if hidden_outcome.get("episode_id") != plan["episode_id"]:
        raise OutcomeScoringError("Hidden outcome episode does not match plan")
    if hidden_outcome.get("season") != plan["season"] or int(hidden_outcome.get("gameweek", -1)) != plan["gameweek"]:
        raise OutcomeScoringError("Hidden outcome season or gameweek does not match plan")
    if hidden_outcome.get("reveal_after") != "proposal_frozen":
        raise OutcomeScoringError("Hidden outcome lacks proposal_frozen reveal gate")
    if _timestamp(revealed_at, "revealed_at") <= _timestamp(plan["frozen_at"], "frozen_at"):
        raise OutcomeScoringError("Outcome must be revealed after plan freeze")

    squad = {row["player_id"]: dict(row) for row in plan["squad_after"]}
    aggregate = {
        player_id: {
            "player_id": player_id,
            "position": row["position"],
            "minutes": 0,
            "total_points": 0,
        }
        for player_id, row in squad.items()
    }
    seen: set[tuple[str, str]] = set()
    for row in hidden_outcome.get("player_outcomes", []):
        player_id = str(row.get("element", row.get("player_id")))
        fixture_id = str(row.get("fixture"))
        key = (player_id, fixture_id)
        if key in seen:
            raise OutcomeScoringError(
                f"Duplicate player/fixture outcome row: {player_id}/{fixture_id}"
            )
        seen.add(key)
        if player_id not in squad:
            continue
        position = _position(row.get("position"))
        if position != squad[player_id]["position"]:
            raise OutcomeScoringError(f"Outcome position mismatch for player {player_id}")
        minutes = row.get("minutes", 0)
        points = row.get("total_points", 0)
        if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0:
            raise OutcomeScoringError("Outcome minutes must be a non-negative integer")
        if isinstance(points, bool) or not isinstance(points, int):
            raise OutcomeScoringError("Outcome total_points must be an integer")
        aggregate[player_id]["minutes"] += minutes
        aggregate[player_id]["total_points"] += points

    lineup = plan["lineup"]
    starting_ids = list(lineup["starting_xi_ids"])
    bench_ids = list(lineup["bench_ids"])
    bench_boost = plan["active_chip"] in {"bench_boost_fh", "bench_boost_sh"}
    if bench_boost:
        effective_ids = starting_ids + bench_ids
        substitutions: list[dict[str, str]] = []
    else:
        effective_ids, substitutions = _automatic_substitutions(
            starting_ids, bench_ids, aggregate, rules
        )

    base_points = sum(aggregate[player_id]["total_points"] for player_id in effective_ids)
    captain_id = lineup["captain_id"]
    vice_id = lineup["vice_captain_id"]
    captain_source = "captain"
    selected_id: str | None = captain_id
    if aggregate[captain_id]["minutes"] == 0:
        if get_rule(dict(rules), "captain_fallback.vice_on_zero_minutes")["value"] and aggregate[vice_id]["minutes"] > 0:
            captain_source = "vice_captain"
            selected_id = vice_id
        else:
            captain_source = "none"
            selected_id = None
    multiplier = (
        int(get_rule(dict(rules), "scoring.captain_multiplier")["value"]["triple_captain"])
        if plan["active_chip"] in {"triple_captain_fh", "triple_captain_sh"}
        else int(get_rule(dict(rules), "scoring.captain_multiplier")["value"]["normal"])
    )
    if selected_id is None:
        raw_points = 0
        total_minutes = 0
        extra_points = 0
        applied_multiplier = 1
    else:
        raw_points = int(aggregate[selected_id]["total_points"])
        total_minutes = int(aggregate[selected_id]["minutes"])
        extra_points = (multiplier - 1) * raw_points
        applied_multiplier = multiplier
    bench_points = sum(aggregate[player_id]["total_points"] for player_id in bench_ids)

    source_hash = fingerprint(hidden_outcome)
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "outcome_id": f"realised-outcome:{plan['episode_id']}:{plan['policy_arm']}",
        "episode_id": plan["episode_id"],
        "season": plan["season"],
        "gameweek": plan["gameweek"],
        "plan_id": plan["plan_id"],
        "plan_sha256": plan["content_sha256"],
        "ruleset": deepcopy(plan["ruleset"]),
        "source_outcome_sha256": source_hash,
        "revealed_at": str(revealed_at),
        "aggregated_players": [
            aggregate[player_id] for player_id in sorted(aggregate)
        ],
        "effective_lineup_ids": effective_ids,
        "substitutions": substitutions,
        "captain": {
            "source": captain_source,
            "player_id": selected_id,
            "multiplier": applied_multiplier,
            "raw_points": raw_points,
            "total_minutes": total_minutes,
            "extra_points": extra_points,
        },
        "bench_points": bench_points,
        "gross_points": base_points + extra_points,
    }
    result["content_sha256"] = realised_outcome_hash(result)
    return result
