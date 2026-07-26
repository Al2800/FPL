"""Fit provenance and held-out evaluation for robust player selection."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.forecasting.calibrate_live_faithful import (
    ForecastParameters,
    build_calibration_cases,
    load_season_rows,
    predictions,
)
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.reliability_shrinkage import (
    RobustSelectionParameters,
    deterministic_quantile,
)


def _season_cases(
    prior_season: str,
    target_season: str,
    *,
    vaastav_root: Path,
) -> pd.DataFrame:
    prior, _ = load_season_rows(prior_season, vaastav_root=vaastav_root)
    target, _ = load_season_rows(target_season, vaastav_root=vaastav_root)
    return predictions(
        build_calibration_cases(
            prior_rows=prior,
            target_rows=target,
            prior_season=prior_season,
            target_season=target_season,
        ),
        ForecastParameters(
            prior_equivalent_minutes=1350.0,
            start_prior_equivalent_matches=2.0,
            cameo_minutes=10.0,
            team_fixture_scale=0.25,
            player_prior_reliability_minutes=900.0,
            event_model_weight=0.0,
            recent_minutes_weight=0.5,
        ),
    )


def _enrich(
    frame: pd.DataFrame,
    parameters: RobustSelectionParameters,
) -> pd.DataFrame:
    result = frame.copy()
    result["raw"] = result["live_faithful_expected_points"].astype(float)
    minutes = result["prior_minutes"].fillna(0.0).clip(lower=0.0)
    result["reliability"] = minutes / (minutes + parameters.reliability_minutes)
    result["anchor"] = result.groupby(["GW", "position"])["raw"].transform(
        lambda values: deterministic_quantile(values, parameters.anchor_quantile)
    )
    result["central"] = (
        result["raw"]
        - parameters.shrinkage_strength
        * (1.0 - result["reliability"])
        * (result["raw"] - result["anchor"]).clip(lower=0.0)
    ).clip(lower=parameters.scenario_floor, upper=parameters.scenario_ceiling)

    def width(reliability: float) -> float:
        for index, upper in enumerate(parameters.reliability_bucket_edges[1:]):
            if reliability <= upper or index == len(parameters.absolute_error_q80) - 1:
                return parameters.absolute_error_q80[index]
        raise AssertionError("validated buckets cover every reliability")

    result["uncertainty"] = result["reliability"].map(width)
    result["robust"] = (
        result["central"] - parameters.risk_aversion * result["uncertainty"]
    ).clip(lower=parameters.scenario_floor)
    return result


def _metrics(frame: pd.DataFrame, *, robust: bool) -> dict[str, Any]:
    selection_field = "robust" if robust else "raw"
    prediction_field = "central" if robust else "raw"
    selected_absolute_errors: list[float] = []
    selected_biases: list[float] = []
    regrets: list[float] = []
    selected_actual: list[float] = []
    selected_predicted: list[float] = []
    for _, gameweek in frame.groupby("GW", sort=True):
        selected = gameweek.sort_values(
            [selection_field, "code"], ascending=[False, True], kind="mergesort"
        ).head(15)
        hindsight = gameweek.sort_values(
            ["actual_points", "code"], ascending=[False, True], kind="mergesort"
        ).head(15)
        errors = selected["actual_points"] - selected[prediction_field]
        selected_absolute_errors.extend(errors.abs().tolist())
        selected_biases.extend(errors.tolist())
        selected_actual.extend(selected["actual_points"].tolist())
        selected_predicted.extend(selected[prediction_field].tolist())
        regrets.append(
            float(hindsight["actual_points"].sum() - selected["actual_points"].sum())
        )
    all_error = frame["actual_points"] - frame[prediction_field]
    return {
        "all_player_mae": float(all_error.abs().mean()),
        "selected_top15_mae": float(pd.Series(selected_absolute_errors).mean()),
        "selected_top15_bias_actual_minus_predicted": float(
            pd.Series(selected_biases).mean()
        ),
        "mean_top15_decision_regret": float(pd.Series(regrets).mean()),
        "mean_selected_actual_points": float(pd.Series(selected_actual).mean()),
        "mean_selected_predicted_points": float(
            pd.Series(selected_predicted).mean()
        ),
        "gameweeks": int(frame["GW"].nunique()),
        "player_gameweeks": int(len(frame)),
    }


def _comparison(frame: pd.DataFrame) -> dict[str, Any]:
    raw = _metrics(frame, robust=False)
    robust = _metrics(frame, robust=True)
    return {
        "raw_unshrunk": raw,
        "robust": robust,
        "delta_robust_minus_raw": {
            key: robust[key] - raw[key]
            for key in (
                "all_player_mae",
                "selected_top15_mae",
                "selected_top15_bias_actual_minus_predicted",
                "mean_top15_decision_regret",
                "mean_selected_actual_points",
                "mean_selected_predicted_points",
            )
        },
    }


def evaluate_robust_selection(
    *,
    config: Mapping[str, Any],
    vaastav_root: Path,
) -> dict[str, Any]:
    """Evaluate fixed controls without fitting on 2024/25 or 2025/26."""
    if config.get("content_sha256") != artifact_hash(config):
        raise ValueError("robust-selection config hash mismatch")
    calibration = config["calibration"]
    if set(calibration["forbidden_fit_seasons"]) != {"2024-25", "2025-26"}:
        raise ValueError("held-out season gate changed")
    parameters = RobustSelectionParameters.from_config(config)
    training = pd.concat(
        [
            _season_cases("2021-22", "2022-23", vaastav_root=vaastav_root),
            _season_cases("2022-23", "2023-24", vaastav_root=vaastav_root),
        ],
        ignore_index=True,
    )
    validation = _season_cases(
        "2023-24", "2024-25", vaastav_root=vaastav_root
    )
    final = _season_cases("2024-25", "2025-26", vaastav_root=vaastav_root)
    report = {
        "schema_version": "1.0",
        "report_id": "live-faithful-v2-robust-selection-evaluation",
        "model_config_sha256": config["content_sha256"],
        "split": {
            "training_target_seasons": ["2022-23", "2023-24"],
            "locked_validation_season": "2024-25",
            "final_out_of_sample_season": "2025-26",
            "forbidden_fit_seasons": ["2024-25", "2025-26"],
        },
        "metric_scope": (
            "Top-15 ranking proxy per Gameweek; legal squad/price/club constraints "
            "are evaluated separately through the optimiser adapter."
        ),
        "training": _comparison(_enrich(training, parameters)),
        "locked_validation": _comparison(_enrich(validation, parameters)),
        "final_out_of_sample": _comparison(_enrich(final, parameters)),
    }
    locked_delta = report["locked_validation"]["delta_robust_minus_raw"]
    checks = {
        "locked_selected_mae_improves": locked_delta["selected_top15_mae"] < 0,
        "locked_decision_regret_improves": (
            locked_delta["mean_top15_decision_regret"] < 0
        ),
        "deterministic_fixed_controls": True,
        "raw_and_robust_reported": True,
    }
    report["promotion_rule"] = checks
    report["promotion_eligible"] = all(checks.values())
    report["decision"] = "promote_to_challenger" if all(checks.values()) else "reject"
    report["content_sha256"] = artifact_hash(report)
    return report


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    config_path = root / "control/models/live-faithful-v2.robust.json"
    output_path = (
        root / "reports/forecasting/live-faithful-v2-robust-evaluation.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    report = evaluate_robust_selection(
        config=config,
        vaastav_root=root / "data/raw/vaastav/Fantasy-Premier-League/data",
    )
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
