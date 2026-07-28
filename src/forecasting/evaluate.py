"""Time-based evaluation for WP-05 baselines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from src.evaluation.calibration import decision_aligned_comparison_table

from src.forecasting.data import DEFAULT_VAASTAV, list_seasons, load_merged_gw
from src.forecasting.minutes import build_minutes_frame
from src.forecasting.odds_implied import build_odds_implied, odds_multiclass_log_loss
from src.forecasting.player_events import build_player_event_baseline
from src.forecasting.team_strength import (
    elo_multiclass_brier,
    elo_multiclass_log_loss,
    fit_elo,
    load_results,
)


def _mae(y: pd.Series, p: pd.Series) -> float:
    mask = y.notna() & p.notna()
    if not mask.any():
        return float("nan")
    return float((y[mask] - p[mask]).abs().mean())


def _rmse(y: pd.Series, p: pd.Series) -> float:
    mask = y.notna() & p.notna()
    if not mask.any():
        return float("nan")
    return float(np.sqrt(((y[mask] - p[mask]) ** 2).mean()))


def _brier(y: pd.Series, p: pd.Series) -> float:
    mask = y.notna() & p.notna()
    if not mask.any():
        return float("nan")
    return float(((p[mask].astype(float) - y[mask].astype(float)) ** 2).mean())


def binary_log_loss(y: pd.Series, p: pd.Series) -> float:
    mask = y.notna() & p.notna()
    if not mask.any():
        return float("nan")
    observed = y[mask].astype(float)
    predicted = p[mask].astype(float).clip(1e-6, 1 - 1e-6)
    return float(-(observed * np.log(predicted) + (1 - observed) * np.log(1 - predicted)).mean())


def calibration_table(y: pd.Series, p: pd.Series, *, bins: int = 10) -> list[dict[str, float | int]]:
    mask = y.notna() & p.notna()
    if not mask.any():
        return []
    frame = pd.DataFrame({"observed": y[mask].astype(float), "predicted": p[mask].astype(float)})
    frame["bin"] = pd.cut(
        frame["predicted"],
        bins=np.linspace(0, 1, bins + 1),
        labels=False,
        include_lowest=True,
    )
    rows = []
    for bin_id, group in frame.groupby("bin", observed=True):
        rows.append(
            {
                "bin": int(bin_id),
                "n": int(len(group)),
                "mean_predicted": float(group["predicted"].mean()),
                "observed_rate": float(group["observed"].mean()),
            }
        )
    return rows


def expected_calibration_error(y: pd.Series, p: pd.Series, *, bins: int = 10) -> float:
    table = calibration_table(y, p, bins=bins)
    total = sum(row["n"] for row in table)
    if not total:
        return float("nan")
    return float(
        sum(
            row["n"] / total * abs(row["mean_predicted"] - row["observed_rate"])
            for row in table
        )
    )


def decision_aligned_frame_comparison(
    frame: pd.DataFrame,
    *,
    prediction_columns: dict[str, str],
    boundary_type: str,
    top_price_band_min: float,
    legal_lineups: list[list[str]] | None = None,
    selected_xi_ids_by_model: dict[str, list[str]] | None = None,
    captain_id_by_model: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Map a shared forecast frame into the evaluation-only comparison table."""

    required = {"player_id", "actual", "position", "price"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            "decision-aligned frame missing columns: " + ", ".join(missing)
        )
    if not prediction_columns:
        raise ValueError("prediction_columns must not be empty")
    missing_predictions = sorted(
        set(prediction_columns.values()) - set(frame.columns)
    )
    if missing_predictions:
        raise ValueError(
            "decision-aligned frame missing prediction columns: "
            + ", ".join(missing_predictions)
        )
    records = frame.to_dict(orient="records")
    model_rows = {
        str(model): [
            {
                "player_id": row["player_id"],
                "predicted": row[column],
                "actual": row["actual"],
                "position": row["position"],
                "price": row["price"],
            }
            for row in records
        ]
        for model, column in prediction_columns.items()
    }
    return decision_aligned_comparison_table(
        model_rows,
        boundary_type=boundary_type,
        top_price_band_min=top_price_band_min,
        legal_lineups=legal_lineups,
        selected_xi_ids_by_model=selected_xi_ids_by_model,
        captain_id_by_model=captain_id_by_model,
    )


def evaluate_minutes(season: str, *, vaastav_root: Path | None = None) -> dict[str, Any]:
    """Start-prob and expected-minutes under leakage-safe lags (features already shifted)."""
    df = build_minutes_frame(season, root=vaastav_root)
    # Drop GW1 where lag is undefined for a fairer minutes MAE
    eval_df = df[df["round"] >= 2].copy()
    return {
        "season": season,
        "n": int(len(eval_df)),
        "start_prob_naive_brier": _brier(eval_df["y_started"], eval_df["start_prob_naive"]),
        "start_prob_rolling_brier": _brier(eval_df["y_started"], eval_df["start_prob_rolling"]),
        "start_prob_rolling_log_loss": binary_log_loss(
            eval_df["y_started"], eval_df["start_prob_rolling"]
        ),
        "start_prob_rolling_ece": expected_calibration_error(
            eval_df["y_started"], eval_df["start_prob_rolling"]
        ),
        "start_prob_rolling_calibration": calibration_table(
            eval_df["y_started"], eval_df["start_prob_rolling"]
        ),
        "expected_minutes_mae": _mae(
            eval_df["y_minutes"],
            eval_df["start_prob_rolling"] * 75.0,
        ),
        "naive_beats_rolling": bool(
            _brier(eval_df["y_started"], eval_df["start_prob_naive"])
            <= _brier(eval_df["y_started"], eval_df["start_prob_rolling"])
        ),
    }


def evaluate_player_events(season: str, *, vaastav_root: Path | None = None) -> dict[str, Any]:
    df = build_player_event_baseline(season, root=vaastav_root)
    eval_df = df[df["round"] >= 4].copy()  # need some history for roll3
    # Same-GW xP is available historically but leaky for live use — report separately
    xp_mae = _mae(eval_df["y_points"], eval_df["xP"]) if "xP" in eval_df.columns else None
    result = {
        "season": season,
        "n": int(len(eval_df)),
        "rolling_points_mae": _mae(eval_df["y_points"], eval_df["expected_points_rolling"]),
        "rolling_points_rmse": _rmse(eval_df["y_points"], eval_df["expected_points_rolling"]),
        "fixture_adj_mae": _mae(eval_df["y_points"], eval_df["expected_points_fixture_adj"]),
        "fixture_adjustment": "walk_forward_prior_round_home_away_multiplier",
        "vaastav_xP_same_gw_mae": xp_mae,
        "vaastav_xP_note": (
            "Same-GW xP from merged_gw — not a pre-deadline snapshot; "
            "official ep_next/FDR deferred until WP-04-style pre-deadline captures exist."
        ),
    }
    for label, target, probability in (
        ("goal", "y_goal_event", "prob_goals"),
        ("assist", "y_assist_event", "prob_assists"),
        ("clean_sheet", "y_clean_sheet_event", "prob_clean_sheet"),
    ):
        result[f"{label}_brier"] = _brier(eval_df[target], eval_df[probability])
        result[f"{label}_log_loss"] = binary_log_loss(eval_df[target], eval_df[probability])
        result[f"{label}_ece"] = expected_calibration_error(eval_df[target], eval_df[probability])
        result[f"{label}_calibration"] = calibration_table(eval_df[target], eval_df[probability])
    return result


def evaluate_elo(season: str, *, football_data_root: Path | None = None) -> dict[str, Any]:
    try:
        results = load_results(season, root=football_data_root)
    except FileNotFoundError as exc:
        return {"season": season, "error": str(exc)}
    _, frame = fit_elo(results)
    return {
        "season": season,
        "n_matches": int(len(frame)),
        "multiclass_log_loss": elo_multiclass_log_loss(frame),
        "multiclass_brier": elo_multiclass_brier(frame),
        "note": "Walk-forward Elo using only pre-match ratings with normalised home/draw/away probabilities.",
    }


def evaluate_odds(season: str) -> dict[str, Any]:
    try:
        frame = build_odds_implied(season)
    except FileNotFoundError as exc:
        return {"season": season, "error": str(exc)}
    return {
        "season": season,
        "n_matches": int(len(frame)),
        "multiclass_log_loss": odds_multiclass_log_loss(frame),
        "odds_timing_label": "closing_or_unspecified",
        "note": (
            "football-data.co.uk 1X2 odds are typically closing/unspecified — "
            "not guaranteed pre-deadline. Live capture needed for true decision-time baseline."
        ),
    }


def evaluate_season(
    season: str,
    *,
    vaastav_root: Path | None = None,
    football_data_root: Path | None = None,
) -> dict[str, Any]:
    return {
        "season": season,
        "minutes": evaluate_minutes(season, vaastav_root=vaastav_root),
        "player_events": evaluate_player_events(season, vaastav_root=vaastav_root),
        "elo": evaluate_elo(season, football_data_root=football_data_root),
        "odds_implied": evaluate_odds(season),
    }


def evaluate_seasons(
    seasons: list[str] | None = None,
    *,
    vaastav_root: Path | None = None,
) -> dict[str, Any]:
    root = vaastav_root or DEFAULT_VAASTAV
    available = set(list_seasons(root))
    if seasons is None:
        seasons = [s for s in ("2022-23", "2023-24", "2024-25") if s in available]
    out: dict[str, Any] = {"seasons": {}, "summary": {}, "data_root": str(root)}
    for season in seasons:
        if season not in available:
            out["seasons"][season] = {"season": season, "error": "missing merged_gw"}
            continue
        # Sanity: file exists
        _ = load_merged_gw(season, root=root)
        out["seasons"][season] = evaluate_season(season, vaastav_root=root)

    # Aggregate key metrics
    def collect(path: tuple[str, str]) -> list[float]:
        vals = []
        for s in out["seasons"].values():
            node: Any = s
            for key in path:
                if not isinstance(node, dict) or key not in node:
                    node = None
                    break
                node = node[key]
            if isinstance(node, (int, float)) and node == node:
                vals.append(float(node))
        return vals

    for label, path in (
        ("start_prob_naive_brier", ("minutes", "start_prob_naive_brier")),
        ("start_prob_rolling_brier", ("minutes", "start_prob_rolling_brier")),
        ("rolling_points_mae", ("player_events", "rolling_points_mae")),
        ("fixture_adj_mae", ("player_events", "fixture_adj_mae")),
        ("elo_multiclass_log_loss", ("elo", "multiclass_log_loss")),
        ("odds_multiclass_log_loss", ("odds_implied", "multiclass_log_loss")),
    ):
        vals = collect(path)
        out["summary"][label] = {
            "mean": float(sum(vals) / len(vals)) if vals else None,
            "seasons_n": len(vals),
            "values": vals,
        }
    return out
