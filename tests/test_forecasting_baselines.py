"""Tests for WP-05 forecasting baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.forecasting.data import add_lagged_features
from src.forecasting.evaluate import (
    binary_log_loss,
    calibration_table,
    evaluate_seasons,
    expected_calibration_error,
)
from src.forecasting.minutes import (
    build_minutes_frame,
    expected_minutes_from_start_prob,
    naive_started_last,
    rolling_minutes_start_prob,
)
from src.forecasting.odds_implied import clean_sheet_proxy_from_odds
from src.forecasting.player_events import (
    build_player_event_baseline,
    per90_rate,
    walk_forward_fixture_multiplier,
)
from src.forecasting.team_strength import elo_multiclass_log_loss, fit_elo


def test_lagged_features_no_same_gw_leakage() -> None:
    df = pd.DataFrame(
        {
            "season": ["2023-24"] * 3,
            "element": [1, 1, 1],
            "round": [1, 2, 3],
            "minutes": [90, 0, 90],
            "starts": [1, 0, 1],
            "total_points": [6, 0, 8],
            "goals_scored": [1, 0, 1],
            "assists": [0, 0, 0],
            "clean_sheets": [1, 0, 0],
        }
    )
    out = add_lagged_features(df)
    assert pd.isna(out.loc[0, "minutes_lag1"])
    assert out.loc[1, "minutes_lag1"] == 90
    assert out.loc[1, "started_lag1"] == 1
    assert out.loc[2, "points_lag1"] == 0
    assert out.loc[2, "goals_scored_prior_sum"] == 1  # only GW1 counted before GW3


def test_naive_started_last() -> None:
    df = pd.DataFrame(
        {
            "started_lag1": [np.nan, 1.0, 0.0],
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


def test_start_target_uses_recorded_start_not_minutes_threshold(tmp_path) -> None:
    root = tmp_path / "vaastav"
    path = root / "2099-00" / "gws"
    path.mkdir(parents=True)
    pd.DataFrame(
        {
            "element": [1, 1],
            "GW": [1, 2],
            "minutes": [30, 70],
            "starts": [1, 0],
            "total_points": [2, 1],
        }
    ).to_csv(path / "merged_gw.csv", index=False)

    frame = build_minutes_frame("2099-00", root=root)
    assert frame["y_started"].tolist() == [1, 0]
    assert frame["started_lag1"].iloc[1] == 1


def test_missing_start_field_remains_unknown() -> None:
    df = pd.DataFrame(
        {
            "season": ["2023-24"],
            "element": [1],
            "round": [1],
            "minutes": [90],
            "total_points": [6],
        }
    )
    out = add_lagged_features(df)
    assert pd.isna(out.loc[0, "started"])


def test_per90_rate() -> None:
    rate = per90_rate(pd.Series([2.0, 0.0]), pd.Series([180.0, 0.0]))
    assert float(rate.iloc[0]) == 1.0
    assert float(rate.iloc[1]) == 0.0


def test_elo_walk_forward() -> None:
    results = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-08-01", "2024-08-08", "2024-08-15"]),
            "HomeTeam": ["A", "B", "A"],
            "AwayTeam": ["B", "A", "B"],
            "FTHG": [2, 1, 0],
            "FTAG": [0, 1, 1],
        }
    )
    ratings, frame = fit_elo(results)
    assert "A" in ratings and "B" in ratings
    assert len(frame) == 3
    # Second match must use updated ratings from first
    assert frame.iloc[1]["rating_home_pre"] != 1500.0 or frame.iloc[1]["rating_away_pre"] != 1500.0
    probs = frame[["exp_home_win", "exp_draw", "exp_away_win"]]
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert (probs["exp_draw"] > 0).all()
    assert np.isfinite(elo_multiclass_log_loss(frame))


def test_fixture_multiplier_is_walk_forward_and_not_fixed() -> None:
    frame = pd.DataFrame(
        {
            "season": ["2023-24"] * 8,
            "round": [1] * 4 + [2] * 4,
            "was_home": [True, True, False, False] * 2,
            "total_points": [10, 8, 2, 2, 100, 100, 0, 0],
        }
    )
    multiplier = walk_forward_fixture_multiplier(frame)
    assert multiplier.iloc[:4].tolist() == [1.0] * 4
    assert multiplier.iloc[4] > 1.0
    assert multiplier.iloc[6] < 1.0

    changed = frame.copy()
    changed.loc[changed["round"] == 2, "total_points"] = [0, 0, 100, 100]
    assert np.allclose(
        multiplier[frame["round"] == 2],
        walk_forward_fixture_multiplier(changed)[changed["round"] == 2],
    )


def test_event_probabilities_have_proper_scores_and_calibration() -> None:
    y = pd.Series([0, 0, 1, 1])
    p = pd.Series([0.1, 0.2, 0.8, 0.9])
    assert binary_log_loss(y, p) > 0
    table = calibration_table(y, p, bins=2)
    assert sum(row["n"] for row in table) == 4
    assert 0 <= expected_calibration_error(y, p, bins=2) <= 1


def test_custom_vaastav_root_propagates_through_evaluation(tmp_path) -> None:
    root = tmp_path / "custom"
    path = root / "2099-00" / "gws"
    path.mkdir(parents=True)
    rows = []
    for gameweek in range(1, 5):
        rows.append(
            {
                "element": 1,
                "GW": gameweek,
                "minutes": 90,
                "starts": 1,
                "total_points": gameweek,
                "goals_scored": int(gameweek == 4),
                "assists": 0,
                "clean_sheets": int(gameweek % 2 == 0),
                "was_home": gameweek % 2 == 0,
            }
        )
    pd.DataFrame(rows).to_csv(path / "merged_gw.csv", index=False)

    report = evaluate_seasons(["2099-00"], vaastav_root=root)
    assert report["data_root"] == str(root)
    assert report["seasons"]["2099-00"]["minutes"]["n"] == 3
    assert report["seasons"]["2099-00"]["player_events"]["n"] == 1
    assert len(build_player_event_baseline("2099-00", root=root)) == 4


def test_clean_sheet_proxy() -> None:
    cs = clean_sheet_proxy_from_odds(0.5, 0.25, 0.25, "home")
    assert 0.02 <= cs <= 0.85
