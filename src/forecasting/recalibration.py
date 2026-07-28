"""Deterministic post-composition forecast recalibration."""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Mapping
from copy import deepcopy
import math
from typing import Any

import numpy as np
import pandas as pd

from src.forecasting.live_faithful import artifact_hash


POSITIONS = ("GKP", "DEF", "MID", "FWD")


def _finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be finite")
    return parsed


def _pooled_means(counts: list[int], sums: list[float]) -> list[float]:
    blocks = [
        {"start": index, "end": index, "count": count, "sum": total}
        for index, (count, total) in enumerate(zip(counts, sums, strict=True))
    ]
    offset = 0
    while offset < len(blocks) - 1:
        left = blocks[offset]
        right = blocks[offset + 1]
        if left["sum"] / left["count"] <= right["sum"] / right["count"]:
            offset += 1
            continue
        merged = {
            "start": left["start"],
            "end": right["end"],
            "count": left["count"] + right["count"],
            "sum": left["sum"] + right["sum"],
        }
        blocks[offset : offset + 2] = [merged]
        offset = max(0, offset - 1)
    fitted = [0.0] * len(counts)
    for block in blocks:
        mean = block["sum"] / block["count"]
        for index in range(block["start"], block["end"] + 1):
            fitted[index] = float(mean)
    return fitted


def fit_position_recalibration(
    frame: pd.DataFrame,
    *,
    prediction_column: str = "live_faithful_expected_points",
    actual_column: str = "actual_points",
    bin_count: int = 10,
) -> dict[str, Any]:
    """Fit monotone binned means separately by FPL position."""
    if isinstance(bin_count, bool) or not isinstance(bin_count, int) or bin_count < 2:
        raise ValueError("bin_count must be an integer of at least two")
    required = {"position", prediction_column, actual_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"recalibration frame missing columns: {missing}")
    unknown = sorted(set(frame["position"].astype(str)) - set(POSITIONS))
    if unknown:
        raise ValueError(f"unsupported positions: {unknown}")

    positions: dict[str, Any] = {}
    for position in POSITIONS:
        selected = frame.loc[frame["position"] == position].copy()
        if selected.empty:
            raise ValueError(f"no fit rows for position {position}")
        predicted = selected[prediction_column].map(
            lambda value: _finite(value, field=prediction_column)
        )
        actual = selected[actual_column].map(
            lambda value: _finite(value, field=actual_column)
        )
        quantiles = np.linspace(0.0, 1.0, bin_count + 1)[1:-1]
        upper_bounds = sorted(
            {
                float(value)
                for value in np.quantile(
                    predicted.to_numpy(dtype=float),
                    quantiles,
                    method="linear",
                )
            }
        )
        assignments = predicted.map(
            lambda value: bisect_left(upper_bounds, float(value))
        )
        counts: list[int] = []
        sums: list[float] = []
        raw_bins: list[dict[str, Any]] = []
        for index in range(len(upper_bounds) + 1):
            mask = assignments == index
            count = int(mask.sum())
            if count == 0:
                continue
            counts.append(count)
            sums.append(float(actual.loc[mask].sum()))
            raw_bins.append(
                {
                    "source_bin": index,
                    "n": count,
                    "mean_prediction": float(predicted.loc[mask].mean()),
                    "mean_actual": float(actual.loc[mask].mean()),
                }
            )
        if len(raw_bins) != len(upper_bounds) + 1:
            raise ValueError(f"empty quantile bin for position {position}")
        fitted = _pooled_means(counts, sums)
        positions[position] = {
            "n": int(len(selected)),
            "upper_bounds": upper_bounds,
            "calibrated_values": fitted,
            "fit_bins": [
                {**row, "calibrated_value": fitted[index]}
                for index, row in enumerate(raw_bins)
            ],
        }
    return {
        "method": "per_position_quantile_bins_weighted_isotonic",
        "bin_count_requested": bin_count,
        "prediction_column": prediction_column,
        "actual_column": actual_column,
        "positions": positions,
    }


def apply_position_recalibration(
    frame: pd.DataFrame,
    calibrator: Mapping[str, Any],
    *,
    output_column: str = "recalibrated_expected_points",
) -> pd.DataFrame:
    """Apply a fitted calibrator without changing row order or source columns."""
    prediction_column = str(calibrator["prediction_column"])
    required = {"position", prediction_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"recalibration frame missing columns: {missing}")
    result = frame.copy()
    values: list[float] = []
    for row in result.itertuples(index=False):
        position = str(getattr(row, "position"))
        spec = calibrator["positions"].get(position)
        if not isinstance(spec, Mapping):
            raise ValueError(f"missing calibrator for position {position}")
        predicted = _finite(
            getattr(row, prediction_column),
            field=prediction_column,
        )
        index = bisect_left(
            [float(value) for value in spec["upper_bounds"]],
            predicted,
        )
        values.append(float(spec["calibrated_values"][index]))
    result[output_column] = values
    return result


def _premium_mask(frame: pd.DataFrame, *, minimum_price: float) -> pd.Series:
    if "price" in frame.columns:
        return frame["price"].map(
            lambda value: _finite(value, field="price") >= minimum_price
        )
    if "price_band" not in frame.columns:
        raise ValueError("premium ranking requires price or price_band")

    def lower_bound(value: Any) -> float:
        label = str(value)
        lower, separator, _ = label.partition("-")
        if not separator:
            raise ValueError(f"invalid price_band: {label}")
        try:
            return _finite(float(lower), field="price_band lower bound")
        except ValueError as error:
            raise ValueError(f"invalid price_band: {label}") from error

    return frame["price_band"].map(lower_bound) >= minimum_price


def _rank_correlation(
    frame: pd.DataFrame,
    prediction_column: str,
    *,
    minimum_price: float,
) -> float | None:
    correlations: list[float] = []
    for _, gameweek in frame.groupby("GW", sort=True):
        cohort = gameweek.loc[
            _premium_mask(gameweek, minimum_price=minimum_price)
        ]
        if len(cohort) < 2:
            continue
        predicted = cohort[prediction_column].rank(
            method="average", ascending=False
        )
        actual = cohort["actual_points"].rank(method="average", ascending=False)
        correlation = predicted.corr(actual)
        if pd.notna(correlation):
            correlations.append(float(correlation))
    return float(np.mean(correlations)) if correlations else None


def decision_proxy_metrics(
    frame: pd.DataFrame,
    *,
    prediction_column: str,
    calibrator: Mapping[str, Any],
    minimum_price: float = 7.5,
) -> dict[str, Any]:
    """Report ranking proxies without relabelling them as legal XI regret."""
    selected_errors: list[float] = []
    regrets: list[float] = []
    precisions: list[float] = []
    top_bin_actual: list[float] = []
    top_bin_predicted: list[float] = []
    for _, gameweek in frame.groupby("GW", sort=True):
        count = min(15, len(gameweek))
        selected = gameweek.sort_values(
            [prediction_column, "code"],
            ascending=[False, True],
            kind="mergesort",
        ).head(count)
        hindsight = gameweek.sort_values(
            ["actual_points", "code"],
            ascending=[False, True],
            kind="mergesort",
        ).head(count)
        selected_errors.extend(
            (selected["actual_points"] - selected[prediction_column]).tolist()
        )
        regrets.append(
            float(hindsight["actual_points"].sum() - selected["actual_points"].sum())
        )
        precisions.append(
            len(set(selected["code"]) & set(hindsight["code"])) / count
        )
    for position in POSITIONS:
        spec = calibrator["positions"][position]
        upper = [float(value) for value in spec["upper_bounds"]]
        selected = frame.loc[
            (frame["position"] == position)
            & frame[calibrator["prediction_column"]].map(
                lambda value: bisect_left(upper, float(value)) == len(upper)
            )
        ]
        top_bin_actual.extend(selected["actual_points"].astype(float).tolist())
        top_bin_predicted.extend(selected[prediction_column].astype(float).tolist())
    all_error = frame["actual_points"] - frame[prediction_column]
    return {
        "player_gameweeks": int(len(frame)),
        "gameweeks": int(frame["GW"].nunique()),
        "all_player_mae": float(all_error.abs().mean()),
        "all_player_rmse": float(np.sqrt((all_error**2).mean())),
        "selected_top15_mae": float(pd.Series(selected_errors).abs().mean()),
        "selected_top15_bias_actual_minus_predicted": float(
            pd.Series(selected_errors).mean()
        ),
        "mean_top15_ranking_regret": float(np.mean(regrets)),
        "top15_precision": float(np.mean(precisions)),
        "top_bin_n": len(top_bin_actual),
        "top_bin_bias_actual_minus_predicted": float(
            np.mean(top_bin_actual) - np.mean(top_bin_predicted)
        ),
        "mean_gameweek_premium_rank_correlation": _rank_correlation(
            frame,
            prediction_column,
            minimum_price=minimum_price,
        ),
        "xi_regret_status": "requires_optimizer_supplied_legal_candidates",
    }


def build_recalibration_report(
    *,
    training: pd.DataFrame,
    validation: pd.DataFrame,
    final: pd.DataFrame,
    source_lineage: list[Mapping[str, Any]],
    bin_count: int = 10,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fit on training only and evaluate the locked and descriptive seasons."""
    calibrator = fit_position_recalibration(training, bin_count=bin_count)
    config = {
        "schema_version": "1.0",
        "model_version": "live-faithful-v2.recalibrated",
        "status": "registered_challenger_owner_gated",
        "base_model_version": "live-faithful-v1",
        "calibration": {
            "fit_seasons": ["2022-23", "2023-24"],
            "locked_validation_season": "2024-25",
            "descriptive_only_season": "2025-26",
            "forbidden_fit_seasons": ["2024-25", "2025-26"],
            "source_lineage": [deepcopy(dict(row)) for row in source_lineage],
        },
        "recalibrator": calibrator,
        "promotion": {
            "owner_gated": True,
            "production_default_changed": False,
            "legal_replay_required": True,
        },
    }
    config["content_sha256"] = artifact_hash(config)

    def compare(frame: pd.DataFrame) -> dict[str, Any]:
        enriched = apply_position_recalibration(frame, calibrator)
        control = decision_proxy_metrics(
            enriched,
            prediction_column="live_faithful_expected_points",
            calibrator=calibrator,
        )
        challenger = decision_proxy_metrics(
            enriched,
            prediction_column="recalibrated_expected_points",
            calibrator=calibrator,
        )
        return {
            "control": control,
            "challenger": challenger,
            "delta_challenger_minus_control": {
                key: (
                    None
                    if control[key] is None or challenger[key] is None
                    else float(challenger[key]) - float(control[key])
                )
                for key in (
                    "all_player_mae",
                    "all_player_rmse",
                    "selected_top15_mae",
                    "selected_top15_bias_actual_minus_predicted",
                    "mean_top15_ranking_regret",
                    "top15_precision",
                    "top_bin_bias_actual_minus_predicted",
                    "mean_gameweek_premium_rank_correlation",
                )
            },
        }

    training_result = compare(training)
    validation_result = compare(validation)
    final_result = compare(final)
    control = validation_result["control"]
    challenger = validation_result["challenger"]
    gates = {
        "locked_absolute_top_bin_bias_improves": abs(
            challenger["top_bin_bias_actual_minus_predicted"]
        ) < abs(control["top_bin_bias_actual_minus_predicted"]),
        "locked_top15_precision_not_worse": (
            challenger["top15_precision"] >= control["top15_precision"]
        ),
        "locked_selected_top15_mae_not_worse": (
            challenger["selected_top15_mae"] <= control["selected_top15_mae"]
        ),
        "locked_ranking_regret_not_worse": (
            challenger["mean_top15_ranking_regret"]
            <= control["mean_top15_ranking_regret"]
        ),
        "locked_premium_rank_not_worse": (
            challenger["mean_gameweek_premium_rank_correlation"]
            >= control["mean_gameweek_premium_rank_correlation"]
        ),
        "legal_replay_completed": False,
        "production_owner_approval": False,
    }
    proxy_gates = {
        key: value
        for key, value in gates.items()
        if key not in {"legal_replay_completed", "production_owner_approval"}
    }
    report = {
        "schema_version": "1.0",
        "report_id": "live-faithful-v2-recalibrated-evaluation",
        "model_config_sha256": config["content_sha256"],
        "split": deepcopy(config["calibration"]),
        "metric_scope": {
            "top15": "unconstrained ranking proxy, not legal XI regret",
            "premium_rank": (
                "mean per-Gameweek Spearman correlation among price bands "
                "whose lower bound is at least 7.5"
            ),
            "hindsight": "evaluation only",
        },
        "training": training_result,
        "locked_validation": validation_result,
        "descriptive_2025_26": final_result,
        "promotion_gates": gates,
        "proxy_gate_passed": all(proxy_gates.values()),
        "promotion_eligible": all(gates.values()),
        "decision": (
            "eligible_for_legal_replay"
            if all(proxy_gates.values())
            else "reject_locked_validation"
        ),
    }
    report["content_sha256"] = artifact_hash(report)
    return config, report
