"""Tests for WP-05 forecasting baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.forecasting.data import add_lagged_features
from src.forecasting.minutes import (
    expected_minutes_from_start_prob,
    naive_started_last,
    rolling_minutes_start_prob,
)
from src.forecasting.odds_implied import clean_sheet_proxy_from_odds
from src.forecasting.player_events import per90_rate
from src.forecasting.team_strength import fit_elo


def test_lagged_features_no_same_gw_leakage() -> None:
    df = pd.DataFrame(
        {
            "season": ["2023-24"] * 3,
            "element": [1, 1, 1],
            "round": [1, 2, 3],
            "minutes": [90, 0, 90],
            "total_points": [6, 0, 8],
            "goals_scored": [1, 0, 1],
            "assists": [0, 0, 0],
            "clean_sheets": [1, 0, 0],
        }
    )
    out = add_lagged_features(df)
    assert pd.isna(out.loc[0, "minutes_lag1"])
    assert out.loc[1, "minutes_lag1"] == 90
    assert out.loc[2, "points_lag1"] == 0
    assert out.loc[2, "goals_scored_prior_sum"] == 1  # only GW1 counted before GW3


def test_naive_started_last() -> None:
    df = pd.DataFrame(
        {
            "minutes_lag1": [np.nan, 90.0, 0.0],
            "minutes_roll3": [np.nan, 90.0, 45.0],
        }
    )
    naive = naive_started_last(df)
    assert naive.iloc[0] == 0.5
    assert naive.iloc[1] == 1.0
    assert naive.iloc[2] == 0.0
    rolling = rolling_minutes_start_prob(df)
    assert 0.05 <= rolling.iloc[1] <= 0.95
    mins = expected_minutes_from_start_prob(rolling)
    assert mins.iloc[1] == round(rolling.iloc[1] * 75.0, 1)


def test_per90_rate() -> None:
    rate = per90_rate(pd.Series([2.0, 0.0]), pd.Series([180.0, 0.0]))
    assert float(rate.iloc[0]) == 1.0
    assert float(rate.iloc[1]) == 0.0


def test_elo_walk_forward() -> None:
    results = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-08-01", "2024-08-08"]),
            "HomeTeam": ["A", "B"],
            "AwayTeam": ["B", "A"],
            "FTHG": [2, 0],
            "FTAG": [0, 1],
        }
    )
    ratings, frame = fit_elo(results)
    assert "A" in ratings and "B" in ratings
    assert len(frame) == 2
    # Second match must use updated ratings from first
    assert frame.iloc[1]["rating_home_pre"] != 1500.0 or frame.iloc[1]["rating_away_pre"] != 1500.0


def test_clean_sheet_proxy() -> None:
    cs = clean_sheet_proxy_from_odds(0.5, 0.25, 0.25, "home")
    assert 0.02 <= cs <= 0.85
