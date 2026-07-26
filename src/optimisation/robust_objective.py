"""Additive robust objective adapter around the unchanged legal FPL solver."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.reliability_shrinkage import (
    ReliabilityShrinkageError,
    RobustSelectionParameters,
    shrink_player_projections,
)
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput


class RobustObjectiveError(ValueError):
    """Raised when forecast and optimiser inputs cannot be joined safely."""


def _reliability_index(
    locked_forecast: Mapping[str, Any],
    *,
    fallback_reliability: float,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in locked_forecast.get("players", []):
        player_id = str(row["player_id"])
        prior = row.get("prior", {})
        if player_id in result:
            raise RobustObjectiveError(f"duplicate forecast player {player_id}")
        result[player_id] = float(
            prior.get("reliability_weight", fallback_reliability)
        )
    return result


def robust_solver_input(
    solver_input: Mapping[str, Any],
    *,
    locked_forecast: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a new solver input while preserving raw points and input lineage."""
    if str(config.get("model_version")) != "live-faithful-v2-robust":
        raise RobustObjectiveError("unexpected robust-selection model version")
    expected_hash = config.get("content_sha256")
    if expected_hash != artifact_hash(config):
        raise RobustObjectiveError("robust-selection config hash mismatch")
    parameters = RobustSelectionParameters.from_config(config)
    result = deepcopy(dict(solver_input))
    fallback = float(config.get("fallback_reliability", 0.0))
    if not 0.0 <= fallback <= 1.0:
        raise RobustObjectiveError("fallback_reliability must be in [0, 1]")
    reliability = _reliability_index(
        locked_forecast,
        fallback_reliability=fallback,
    )
    try:
        result["players"] = shrink_player_projections(
            result["players"],
            reliability_by_player=reliability,
            parameters=parameters,
        )
    except ReliabilityShrinkageError as exc:
        raise RobustObjectiveError(str(exc)) from exc
    result["robust_selection"] = {
        "model_version": config["model_version"],
        "model_config_sha256": expected_hash,
        "base_forecast_sha256": locked_forecast["content_sha256"],
        "raw_solver_input_sha256": artifact_hash(solver_input),
        "objective": "central_minus_risk_aversion_times_calibrated_q80_error",
    }
    return result


def solve_raw_and_robust(
    solver_input: Mapping[str, Any],
    *,
    locked_forecast: Mapping[str, Any],
    config: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Solve both objectives and expose ordering sensitivity without promotion."""
    raw_input = SolverInput.from_dict(deepcopy(dict(solver_input)))
    adjusted = robust_solver_input(
        solver_input,
        locked_forecast=locked_forecast,
        config=config,
    )
    raw = solve(raw_input, rules=rules, ruleset_sha256=ruleset_sha256)
    robust = solve(
        SolverInput.from_dict(adjusted),
        rules=rules,
        ruleset_sha256=ruleset_sha256,
    )
    scenarios: dict[str, dict[str, Any]] = {}
    for scenario in ("lower", "central", "upper"):
        scenario_input = deepcopy(adjusted)
        for row in scenario_input["players"]:
            row["expected_points"] = row["robust_selection"][scenario]
        scenarios[scenario] = solve(
            SolverInput.from_dict(scenario_input),
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
    raw_selected = raw["selected"]
    robust_selected = robust["selected"]
    robust_xi = set(robust_selected["lineup"]["starting_xi_ids"])
    scenario_selected = {
        name: output["selected"] for name, output in scenarios.items()
    }
    return {
        "schema_version": "1.0",
        "model_config_sha256": config["content_sha256"],
        "raw": raw,
        "robust": robust,
        "scenarios": scenarios,
        "comparison": {
            "raw_objective": float(raw_selected["objective"]),
            "robust_objective": float(robust_selected["objective"]),
            "same_transfers": raw_selected["transfers"] == robust_selected["transfers"],
            "same_starting_xi": (
                raw_selected["lineup"]["starting_xi_ids"]
                == robust_selected["lineup"]["starting_xi_ids"]
            ),
            "same_captain": (
                raw_selected["lineup"]["captain_id"]
                == robust_selected["lineup"]["captain_id"]
            ),
            "robust_selected_xi_central_sum": round(
                sum(
                    float(row["robust_selection"]["central"])
                    for row in adjusted["players"]
                    if row["player_id"] in robust_xi
                ),
                4,
            ),
            "scenario_sensitivity": {
                name: {
                    "objective": float(selected["objective"]),
                    "same_transfers_as_robust": (
                        selected["transfers"] == robust_selected["transfers"]
                    ),
                    "same_starting_xi_as_robust": (
                        selected["lineup"]["starting_xi_ids"]
                        == robust_selected["lineup"]["starting_xi_ids"]
                    ),
                    "same_captain_as_robust": (
                        selected["lineup"]["captain_id"]
                        == robust_selected["lineup"]["captain_id"]
                    ),
                }
                for name, selected in scenario_selected.items()
            },
        },
        "robust_solver_input": adjusted,
    }
