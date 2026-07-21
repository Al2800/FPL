"""Time-based evaluation for WP-05 baselines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.forecasting.data import DEFAULT_VAASTAV, list_seasons, load_merged_gw
from src.forecasting.minutes import build_minutes_frame
from src.forecasting.odds_implied import build_odds_implied, odds_multiclass_log_loss
from src.forecasting.player_events import build_player_event_baseline
from src.forecasting.team_strength import elo_log_loss, fit_elo, load_results


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


def evaluate_minutes(season: str) -> dict[str, Any]:
    """Start-prob and expected-minutes under leakage-safe lags (features already shifted)."""
    df = build_minutes_frame(season)
    # Drop GW1 where lag is undefined for a fairer minutes MAE
    eval_df = df[df["round"] >= 2].copy()
    return {
        "season": season,
        "n": int(len(eval_df)),
        "start_prob_naive_brier": _brier(eval_df["y_started"], eval_df["start_prob_naive"]),
        "start_prob_rolling_brier": _brier(eval_df["y_started"], eval_df["start_prob_rolling"]),
        "expected_minutes_mae": _mae(
            eval_df["y_minutes"],
            eval_df["start_prob_rolling"] * 75.0,
        ),
        "naive_beats_rolling": bool(
            _brier(eval_df["y_started"], eval_df["start_prob_naive"])
            <= _brier(eval_df["y_started"], eval_df["start_prob_rolling"])
        ),
    }


def evaluate_player_events(season: str) -> dict[str, Any]:
    df = build_player_event_baseline(season)
    eval_df = df[df["round"] >= 4].copy()  # need some history for roll3
    # Same-GW xP is available historically but leaky for live use — report separately
    xp_mae = _mae(eval_df["y_points"], eval_df["xP"]) if "xP" in eval_df.columns else None
    return {
        "season": season,
        "n": int(len(eval_df)),
        "rolling_points_mae": _mae(eval_df["y_points"], eval_df["expected_points_rolling"]),
        "rolling_points_rmse": _rmse(eval_df["y_points"], eval_df["expected_points_rolling"]),
        "fixture_adj_mae": _mae(eval_df["y_points"], eval_df["expected_points_fixture_adj"]),
        "vaastav_xP_same_gw_mae": xp_mae,
        "vaastav_xP_note": (
            "Same-GW xP from merged_gw — not a pre-deadline snapshot; "
            "official ep_next/FDR deferred until WP-04-style pre-deadline captures exist."
        ),
    }


def evaluate_elo(season: str) -> dict[str, Any]:
    try:
        results = load_results(season)
    except FileNotFoundError as exc:
        return {"season": season, "error": str(exc)}
    _, frame = fit_elo(results)
    return {
        "season": season,
        "n_matches": int(len(frame)),
        "home_win_log_loss": elo_log_loss(frame),
        "note": "Walk-forward Elo using only pre-match ratings; draws excluded from binary log-loss.",
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


def evaluate_season(season: str) -> dict[str, Any]:
    return {
        "season": season,
        "minutes": evaluate_minutes(season),
        "player_events": evaluate_player_events(season),
        "elo": evaluate_elo(season),
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
        out["seasons"][season] = evaluate_season(season)

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
        ("elo_home_win_log_loss", ("elo", "home_win_log_loss")),
        ("odds_multiclass_log_loss", ("odds_implied", "multiclass_log_loss")),
    ):
        vals = collect(path)
        out["summary"][label] = {
            "mean": float(sum(vals) / len(vals)) if vals else None,
            "seasons_n": len(vals),
            "values": vals,
        }
    return out
