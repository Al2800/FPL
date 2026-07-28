"""Deterministic bounded receding-horizon transfer planning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from time import perf_counter
from typing import Any

from src.optimisation.solver import solve
from src.optimisation.trajectory import (
    TrajectoryError,
    advance_trajectory_state,
    initial_trajectory_state,
    market_for_state,
    trajectory_state_hash,
)
from src.optimisation.types import SolverInput


class MultiweekPlanningError(ValueError):
    """Raised when a horizon is unsafe, incomplete, or internally inconsistent."""


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def multiweek_plan_hash(value: Mapping[str, Any]) -> str:
    """Hash decision semantics while excluding observational wall-clock latency."""
    projection = deepcopy(dict(value))
    projection.pop("content_sha256", None)
    projection.get("search", {}).pop("elapsed_seconds", None)
    return _fingerprint(projection)


def validate_horizon(
    horizon: Sequence[Mapping[str, Any]],
    *,
    base_input: SolverInput,
) -> None:
    if not 3 <= len(horizon) <= 6:
        raise MultiweekPlanningError("horizon must contain three to six Gameweeks")
    expected = list(range(base_input.gameweek, base_input.gameweek + len(horizon)))
    actual = [int(week["gameweek"]) for week in horizon]
    if actual != expected:
        raise MultiweekPlanningError("horizon Gameweeks must be consecutive")
    cutoffs = {str(week.get("cutoff")) for week in horizon}
    if len(cutoffs) != 1 or None in cutoffs or "None" in cutoffs:
        raise MultiweekPlanningError("every horizon week must share one cutoff")
    source_hashes = {str(week.get("feature_state_sha256")) for week in horizon}
    if len(source_hashes) != 1 or any(len(value) != 64 for value in source_hashes):
        raise MultiweekPlanningError(
            "every horizon week must bind one feature-state hash"
        )
    fixture_hashes = {
        str(week["fixture_state_sha256"])
        for week in horizon
        if week.get("fixture_state_sha256") is not None
    }
    count_table_hashes = {
        str(week["fixture_count_table_sha256"])
        for week in horizon
        if week.get("fixture_count_table_sha256") is not None
    }
    if fixture_hashes:
        if (
            len(fixture_hashes) != 1
            or len(fixture_hashes) != len(
                {str(week.get("fixture_state_sha256")) for week in horizon}
            )
            or any(len(value) != 64 for value in fixture_hashes)
            or len(count_table_hashes) != 1
            or len(count_table_hashes) != len(
                {str(week.get("fixture_count_table_sha256")) for week in horizon}
            )
            or any(len(value) != 64 for value in count_table_hashes)
        ):
            raise MultiweekPlanningError(
                "fixture-state-bound weeks must share state and count SHA-256s"
            )
        for week in horizon:
            counts = week.get("team_fixture_counts")
            if not isinstance(counts, Mapping):
                raise MultiweekPlanningError(
                    "fixture-state-bound horizon lacks team fixture counts"
                )
            for player in week.get("players", []):
                club_id = str(player["club_id"])
                components = player.get("horizon_fixture_components")
                if club_id not in counts or not isinstance(components, list):
                    raise MultiweekPlanningError(
                        "fixture-state-bound player lacks count/component lineage"
                    )
                fixture_count = int(player.get("fixture_count", -1))
                if fixture_count != int(counts[club_id]) or fixture_count != len(
                    components
                ):
                    raise MultiweekPlanningError(
                        "fixture-state count differs from projected components"
                    )
    base_ids = {str(row["player_id"]) for row in base_input.players}
    for week in horizon:
        ids = [str(row["player_id"]) for row in week.get("players", [])]
        if len(ids) != len(set(ids)) or set(ids) != base_ids:
            raise MultiweekPlanningError(
                f"Gameweek {week['gameweek']} market differs from base market"
            )


def _week_input(
    base: SolverInput,
    state: Mapping[str, Any],
    week: Mapping[str, Any],
    config: Mapping[str, Any],
) -> SolverInput:
    return SolverInput(
        season=base.season,
        gameweek=int(week["gameweek"]),
        ruleset_id=base.ruleset_id,
        bank=float(state["bank"]),
        free_transfers=int(state["free_transfers"]),
        squad_player_ids=[str(row["player_id"]) for row in state["squad"]],
        players=market_for_state(state, week["players"]),
        active_chip=None,
        chips_available=[],
        max_transfers=int(config["max_transfers_per_week"]),
        sell_pool_per_pos=int(config["sell_pool_per_pos"]),
        buy_pool_per_pos=int(config["buy_pool_per_pos"]),
        allow_hits=bool(config["allow_hits"]),
        transfer_value_policy="none",
        squad_contingency_policy=base.squad_contingency_policy,
        appearance_calibration=deepcopy(base.appearance_calibration),
        ruleset_mismatch_policy=base.ruleset_mismatch_policy,
        availability_policy=base.availability_policy,
    )


def _candidate_key(candidate: Mapping[str, Any]) -> str:
    return _fingerprint(
        {
            "transfers": candidate["transfers"],
            "lineup": candidate["lineup"],
            "hit_cost": candidate["hit_cost"],
        }
    )


def _branch_candidates(output: Mapping[str, Any], limit: int) -> list[dict[str, Any]]:
    candidates = [deepcopy(dict(row)) for row in output["all_candidates"]]
    for name in ("no_transfer", "bank_transfer"):
        row = output["plans"].get(name)
        if row is not None:
            candidates.append(deepcopy(dict(row)))
    unique: dict[str, dict[str, Any]] = {}
    for row in candidates:
        key = _candidate_key(row)
        current = unique.get(key)
        if current is None or float(row["objective"]) > float(current["objective"]):
            unique[key] = row
    ordered = sorted(
        unique.values(),
        key=lambda row: (
            -float(row["objective"]),
            len(row["transfers"]),
            _candidate_key(row),
        ),
    )
    return ordered[:limit]


def _fallback(
    base_input: SolverInput,
    *,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    reason: str,
    elapsed: float,
    fixture_state_sha256: str | None = None,
    fixture_count_table_sha256: str | None = None,
) -> dict[str, Any]:
    safe = deepcopy(base_input)
    safe.transfer_value_policy = "none"
    safe.horizon_gameweeks = 1
    safe.discount_factors = [1.0]
    output = solve(safe, rules=rules, ruleset_sha256=ruleset_sha256)
    selected = deepcopy(output["selected"])
    result = {
        "schema_version": "1.0",
        "status": "deterministic_fallback",
        "fallback_reason": reason,
        "selected": selected,
        "executable_action": selected,
        "advisory_trajectory": [],
        "value": {
            "immediate": float(selected["objective"]),
            "future": 0.0,
            "total": float(selected["objective"]),
        },
        "search": {"elapsed_seconds": round(elapsed, 6)},
    }
    if fixture_state_sha256 is not None:
        result["lineage"] = {
            "fixture_state_sha256": fixture_state_sha256,
            "fixture_count_table_sha256": fixture_count_table_sha256,
        }
    result["content_sha256"] = multiweek_plan_hash(result)
    return result


def plan_multiweek(
    base_input: SolverInput,
    horizon: Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Plan a bounded trajectory and expose only its first action for execution."""
    validate_horizon(horizon, base_input=base_input)
    fixture_state_sha256 = horizon[0].get("fixture_state_sha256")
    fixture_count_table_sha256 = horizon[0].get("fixture_count_table_sha256")
    if int(config["horizon_gameweeks"]) != len(horizon):
        raise MultiweekPlanningError("config horizon differs from supplied horizon")
    discount = float(config["discount_factor"])
    if not 0 < discount <= 1:
        raise MultiweekPlanningError("discount_factor must be in (0, 1]")
    beam_width = int(config["beam_width"])
    branch_width = int(config["branch_width"])
    max_nodes = int(config["max_expanded_nodes"])
    if min(beam_width, branch_width, max_nodes) < 1:
        raise MultiweekPlanningError("search budgets must be positive")

    started = perf_counter()
    initial = initial_trajectory_state(base_input, rules=rules)
    frontier = [{"state": initial, "actions": [], "total": 0.0}]
    expanded = generated = deduplicated = 0
    root_output: dict[str, Any] | None = None

    for depth, week in enumerate(horizon):
        next_paths: list[dict[str, Any]] = []
        for path in frontier:
            if expanded >= max_nodes:
                return _fallback(
                    base_input,
                    rules=rules,
                    ruleset_sha256=ruleset_sha256,
                    reason="expanded_node_budget_exhausted",
                    elapsed=perf_counter() - started,
                    fixture_state_sha256=fixture_state_sha256,
                    fixture_count_table_sha256=fixture_count_table_sha256,
                )
            solver_input = _week_input(base_input, path["state"], week, config)
            output = solve(
                solver_input,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
            if root_output is None:
                root_output = output
            expanded += 1
            for candidate in _branch_candidates(output, branch_width):
                generated += 1
                action = {
                    "gameweek": int(week["gameweek"]),
                    "candidate": candidate,
                    "discount": round(discount**depth, 8),
                    "discounted_value": round(
                        float(candidate["objective"]) * discount**depth, 6
                    ),
                    "executable": depth == 0,
                }
                total = float(path["total"]) + float(action["discounted_value"])
                if depth == len(horizon) - 1:
                    state = path["state"]
                else:
                    try:
                        state = advance_trajectory_state(
                            path["state"],
                            candidate,
                            current_players=week["players"],
                            next_players=horizon[depth + 1]["players"],
                            rules=rules,
                        )
                    except TrajectoryError:
                        continue
                next_paths.append(
                    {
                        "state": state,
                        "actions": [*path["actions"], action],
                        "total": round(total, 6),
                    }
                )
        if not next_paths:
            return _fallback(
                base_input,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
                reason="no_complete_legal_trajectory",
                elapsed=perf_counter() - started,
                fixture_state_sha256=fixture_state_sha256,
                fixture_count_table_sha256=fixture_count_table_sha256,
            )
        by_state: dict[str, dict[str, Any]] = {}
        for path in next_paths:
            state_key = trajectory_state_hash(path["state"])
            existing = by_state.get(state_key)
            rank = (-float(path["total"]), _fingerprint(path["actions"]))
            if existing is None or rank < (
                -float(existing["total"]),
                _fingerprint(existing["actions"]),
            ):
                if existing is not None:
                    deduplicated += 1
                by_state[state_key] = path
            else:
                deduplicated += 1
        frontier = sorted(
            by_state.values(),
            key=lambda path: (-float(path["total"]), _fingerprint(path["actions"])),
        )[:beam_width]

    best = frontier[0]
    actions = best["actions"]
    first = deepcopy(actions[0]["candidate"])
    immediate = float(actions[0]["discounted_value"])
    total = float(best["total"])
    result = {
        "schema_version": "1.0",
        "status": "complete",
        "horizon_gameweeks": len(horizon),
        "selected": first,
        "executable_action": first,
        "advisory_trajectory": actions[1:],
        "value": {
            "immediate": round(immediate, 6),
            "future": round(total - immediate, 6),
            "total": round(total, 6),
        },
        "search": {
            "algorithm": "deterministic_beam_search",
            "beam_width": beam_width,
            "branch_width": branch_width,
            "max_expanded_nodes": max_nodes,
            "expanded_nodes": expanded,
            "generated_paths": generated,
            "deduplicated_paths": deduplicated,
            "elapsed_seconds": round(perf_counter() - started, 6),
            "global_optimality_guaranteed": False,
        },
        "lineage": {
            "base_input_fingerprint": _fingerprint(base_input.as_dict()),
            "horizon_fingerprint": _fingerprint(list(horizon)),
            "config_sha256": str(config["content_sha256"]),
        },
    }
    if horizon[0].get("fixture_state_sha256") is not None:
        result["lineage"]["fixture_state_sha256"] = str(
            horizon[0]["fixture_state_sha256"]
        )
        result["lineage"]["fixture_count_table_sha256"] = str(
            fixture_count_table_sha256
        )
    result["content_sha256"] = multiweek_plan_hash(result)
    return result
