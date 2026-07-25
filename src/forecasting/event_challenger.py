"""Additive evaluation of the pre-season player-event blend challenger."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.evaluation.calibration import calibration_by_cohort
from src.forecasting.live_faithful import artifact_hash


def select_preseason_event_candidate(
    base_config: Mapping[str, Any],
    locked_calibration: Mapping[str, Any],
) -> dict[str, Any]:
    """Select the best non-zero weight from the already locked pre-2025/26 grid."""
    split = locked_calibration["split"]
    fitted = set(split["training_target_seasons"]) | {split["locked_validation_season"]}
    if "2025-26" in fitted or "2025-26" not in set(split["forbidden_fit_seasons"]):
        raise ValueError("event candidate selection is not sealed from 2025-26")
    candidates = [
        row
        for row in locked_calibration["selection"]["top_10"]
        if float(row["parameters"]["event_model_weight"]) > 0
    ]
    if not candidates:
        raise ValueError("locked calibration contains no non-zero event candidate")
    chosen = min(candidates, key=lambda row: (float(row["objective"]), int(row["rank"])))
    config = deepcopy(dict(base_config))
    config.pop("content_sha256", None)
    config["model_version"] = "live-faithful-v2-events"
    config["status"] = "experimental_preseason_event_challenger"
    config["event_model_weight"] = float(chosen["parameters"]["event_model_weight"])
    config["calibration"] = {
        **deepcopy(dict(config["calibration"])),
        "event_candidate_rank": int(chosen["rank"]),
        "event_candidate_objective": float(chosen["objective"]),
        "event_candidate_selection": "best_nonzero_from_locked_pre_2025_26_grid",
        "control_event_weight": float(base_config["event_model_weight"]),
    }
    config["content_sha256"] = artifact_hash(config)
    return config


def reblend_locked_forecast(
    forecast: Mapping[str, Any],
    *,
    event_model_weight: float,
) -> dict[str, Any]:
    """Reblend already frozen rate/event components without observing outcomes."""
    weight = float(event_model_weight)
    if not 0 < weight <= 1:
        raise ValueError("event challenger weight must be in (0, 1]")
    result = deepcopy(dict(forecast))
    result.pop("content_sha256", None)
    result["model_version"] = "live-faithful-v2-events"
    result["model_status"] = "experimental_preseason_event_challenger"
    result["lineage"] = {
        **deepcopy(dict(result["lineage"])),
        "base_forecast_sha256": str(forecast["content_sha256"]),
    }
    for player in result["players"]:
        total = 0.0
        for component in player["fixture_components"]:
            expected = (
                (1.0 - weight) * float(component["rate_expected_points"])
                + weight * float(component["event_expected_points"])
            )
            component["event_model_weight"] = round(weight, 4)
            component["expected_points"] = round(expected, 2)
            total += component["expected_points"]
        player["expected_points"] = round(total, 2)
    result["content_sha256"] = artifact_hash(result)
    return result


def evaluate_event_challenger(
    reports_root: Path,
    outcomes_csv: Path,
    *,
    event_model_weight: float,
) -> dict[str, Any]:
    """Evaluate the sealed challenger on 2025/26 as an out-of-sample diagnostic."""
    frame = pd.read_csv(
        outcomes_csv,
        encoding="latin-1",
        low_memory=False,
        usecols=["element", "round", "total_points"],
    )
    actuals = (
        frame.groupby(["round", "element"], as_index=False)["total_points"]
        .sum()
        .set_index(["round", "element"])["total_points"]
        .to_dict()
    )
    control_rows: list[dict[str, Any]] = []
    challenger_rows: list[dict[str, Any]] = []
    for gameweek in range(2, 39):
        root = reports_root / f"gw-{gameweek:02d}"
        forecast = json.loads(
            (root / "setup/shared-locked-forecast.json").read_text(encoding="utf-8")
        )
        challenger = reblend_locked_forecast(
            forecast,
            event_model_weight=event_model_weight,
        )
        plan = json.loads(
            (root / "forecast_optimizer/validated-plan.json").read_text(encoding="utf-8")
        )
        owned = {row["player_id"] for row in plan["squad_after"]}
        selected = set(plan["lineup"]["starting_xi_ids"])
        challenger_by_id = {row["player_id"]: row for row in challenger["players"]}
        for row in forecast["players"]:
            element = int(str(row["player_id"]).rsplit(":", 1)[-1])
            actual = actuals.get((gameweek, element))
            if actual is None or int(row.get("fixture_count", 0)) == 0:
                continue
            cohorts = []
            if row["player_id"] in owned:
                cohorts.append("owned")
            if row["player_id"] in selected:
                cohorts.append("selected_xi")
            base = {"actual": float(actual), "cohorts": cohorts}
            control_rows.append({**base, "predicted": float(row["expected_points"])})
            challenger_rows.append(
                {
                    **base,
                    "predicted": float(challenger_by_id[row["player_id"]]["expected_points"]),
                }
            )
    control = calibration_by_cohort(control_rows)
    challenger = calibration_by_cohort(challenger_rows)
    deltas = {
        cohort: {
            "mae": challenger[cohort]["mean_absolute_error"]
            - control[cohort]["mean_absolute_error"],
            "bias_absolute": abs(challenger[cohort]["bias_actual_minus_predicted"])
            - abs(control[cohort]["bias_actual_minus_predicted"]),
            "correlation": (challenger[cohort]["correlation"] or 0)
            - (control[cohort]["correlation"] or 0),
        }
        for cohort in ("all", "owned", "selected_xi")
    }
    checks = {
        "all_mae_not_worse": deltas["all"]["mae"] <= 0,
        "owned_mae_improves": deltas["owned"]["mae"] < 0,
        "selected_xi_mae_improves": deltas["selected_xi"]["mae"] < 0,
        "selected_xi_absolute_bias_improves": deltas["selected_xi"]["bias_absolute"] < 0,
    }
    return {
        "event_model_weight": float(event_model_weight),
        "control": control,
        "challenger": challenger,
        "deltas_challenger_minus_control": deltas,
        "promotion_rule": checks,
        "promotion_eligible": all(checks.values()),
        "evaluation_season": "2025-26",
        "fit_seasons": ["2022-23", "2023-24"],
        "locked_validation_season": "2024-25",
    }
