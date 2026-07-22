"""Rolling points / per-90 event baselines and simple fixture adjustment."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.forecasting.data import add_lagged_features, load_merged_gw
from src.forecasting.minutes import expected_minutes_from_start_prob, rolling_minutes_start_prob


def per90_rate(prior_events: pd.Series, prior_minutes: pd.Series) -> pd.Series:
    denominator = pd.to_numeric(prior_minutes, errors="coerce").astype(float)
    numerator = pd.to_numeric(prior_events, errors="coerce").astype(float)
    return (numerator / denominator.where(denominator != 0) * 90).fillna(0.0)


def walk_forward_fixture_multiplier(
    df: pd.DataFrame,
    *,
    lower: float = 0.75,
    upper: float = 1.25,
) -> pd.Series:
    """Estimate home/away point multipliers using completed prior rounds only."""
    if "was_home" not in df.columns:
        return pd.Series(1.0, index=df.index)

    result = pd.Series(1.0, index=df.index, dtype=float)
    for _, season_rows in df.groupby("season", sort=False):
        total_sum = 0.0
        total_n = 0
        side_sum = {True: 0.0, False: 0.0}
        side_n = {True: 0, False: 0}
        for gameweek in sorted(season_rows["round"].unique()):
            round_rows = season_rows[season_rows["round"] == gameweek]
            if total_n:
                overall_mean = total_sum / total_n
                for side in (True, False):
                    if side_n[side] and overall_mean > 0:
                        multiplier = (side_sum[side] / side_n[side]) / overall_mean
                        result.loc[round_rows.index[round_rows["was_home"].astype(bool) == side]] = float(
                            np.clip(multiplier, lower, upper)
                        )
            points = pd.to_numeric(round_rows["total_points"], errors="coerce")
            for side in (True, False):
                mask = round_rows["was_home"].astype(bool) == side
                values = points[mask].dropna()
                side_sum[side] += float(values.sum())
                side_n[side] += int(values.count())
                total_sum += float(values.sum())
                total_n += int(values.count())
    return result


def _at_least_one_probability(expected_count: pd.Series) -> pd.Series:
    return pd.Series(1.0 - np.exp(-expected_count.clip(lower=0)), index=expected_count.index).clip(
        0.0, 1.0
    )


def build_player_event_baseline(season: str, *, root: Path | None = None) -> pd.DataFrame:
    df = add_lagged_features(load_merged_gw(season, root=root))
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
        df[f"prob_{event.removesuffix('_scored')}"] = _at_least_one_probability(
            df[f"expected_{event}"]
        )

    if "clean_sheets_prior_sum" in df.columns:
        clean_sheet_rate = per90_rate(df["clean_sheets_prior_sum"], df["minutes_prior_sum"])
        df["expected_clean_sheets"] = (clean_sheet_rate * exp_min / 90.0).clip(lower=0)
    else:
        df["expected_clean_sheets"] = 0.0
    df["prob_clean_sheet"] = _at_least_one_probability(df["expected_clean_sheets"])

    # Rolling points as crude expected points (not for cross-regime training target)
    df["expected_points_rolling"] = df["points_roll3"].fillna(df["points_lag1"]).fillna(2.0)

    df["fixture_multiplier"] = walk_forward_fixture_multiplier(df)
    df["expected_points_fixture_adj"] = df["expected_points_rolling"] * df["fixture_multiplier"]

    df["y_points"] = df["total_points"]
    df["y_goals"] = df.get("goals_scored", 0)
    df["y_assists"] = df.get("assists", 0)
    df["y_goal_event"] = (pd.to_numeric(df["y_goals"], errors="coerce") > 0).astype(int)
    df["y_assist_event"] = (pd.to_numeric(df["y_assists"], errors="coerce") > 0).astype(int)
    clean_sheets = df.get("clean_sheets", pd.Series(0, index=df.index))
    df["y_clean_sheet_event"] = (pd.to_numeric(clean_sheets, errors="coerce") > 0).astype(int)
    return df
