"""Rolling points / per-90 event baselines and simple fixture adjustment."""

from __future__ import annotations

import pandas as pd

from src.forecasting.data import add_lagged_features, load_merged_gw
from src.forecasting.minutes import expected_minutes_from_start_prob, rolling_minutes_start_prob


def per90_rate(prior_events: pd.Series, prior_minutes: pd.Series) -> pd.Series:
    return (prior_events / prior_minutes.replace(0, pd.NA) * 90).fillna(0.0)


def build_player_event_baseline(season: str) -> pd.DataFrame:
    df = add_lagged_features(load_merged_gw(season))
    start_p = rolling_minutes_start_prob(df)
    exp_min = expected_minutes_from_start_prob(start_p)
    df["start_prob"] = start_p
    df["expected_minutes"] = exp_min

    for event in ("goals_scored", "assists"):
        if f"{event}_prior_sum" in df.columns:
            rate = per90_rate(df[f"{event}_prior_sum"], df["minutes_prior_sum"])
            df[f"expected_{event}"] = (rate * exp_min / 90.0).clip(lower=0)
        else:
            df[f"expected_{event}"] = 0.0

    # Rolling points as crude expected points (not for cross-regime training target)
    df["expected_points_rolling"] = df["points_roll3"].fillna(df["points_lag1"]).fillna(2.0)

    # Simple home/away adjustment if present
    if "was_home" in df.columns:
        adj = df["was_home"].map(lambda x: 1.05 if bool(x) else 0.95)
        df["expected_points_fixture_adj"] = df["expected_points_rolling"] * adj
    else:
        df["expected_points_fixture_adj"] = df["expected_points_rolling"]

    df["y_points"] = df["total_points"]
    df["y_goals"] = df.get("goals_scored", 0)
    df["y_assists"] = df.get("assists", 0)
    return df
