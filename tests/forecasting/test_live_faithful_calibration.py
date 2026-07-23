"""Leakage and selection tests for early-season prior calibration."""

from __future__ import annotations

import pandas as pd

from src.forecasting.calibrate_live_faithful import (
    ForecastParameters,
    build_calibration_cases,
    evaluate_cases,
    predictions,
    select_parameters,
)


def _rows(points: list[int], *, code: int = 101) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "code": code,
                "element": 1,
                "fixture": gameweek,
                "position": "MID",
                "minutes": 90,
                "starts": 1,
                "total_points": value,
                "value": 75,
                "GW": gameweek,
            }
            for gameweek, value in enumerate(points, start=1)
        ]
    )


def test_cases_use_only_strictly_earlier_target_gameweeks() -> None:
    prior = _rows([5, 5, 5])
    original = _rows([17, 2, 2])
    changed = _rows([17, 2, 99])
    first = build_calibration_cases(
        prior_rows=prior,
        target_rows=original,
        prior_season="2023-24",
        target_season="2024-25",
    )
    second = build_calibration_cases(
        prior_rows=prior,
        target_rows=changed,
        prior_season="2023-24",
        target_season="2024-25",
    )
    assert first.loc[first["GW"] <= 3, "current_points"].tolist() == [0, 17, 19]
    assert first.loc[first["GW"] <= 3, "current_points"].tolist() == second.loc[
        second["GW"] <= 3, "current_points"
    ].tolist()


def test_shrinkage_beats_raw_one_week_chasing_in_constructed_early_case() -> None:
    cases = build_calibration_cases(
        prior_rows=_rows([5] * 10),
        target_rows=_rows([17, 2, 2, 2, 2]),
        prior_season="2023-24",
        target_season="2024-25",
    )
    result = evaluate_cases(cases, ForecastParameters(900, 8, 18))
    assert (
        result["early_gw2_5"]["live_faithful_expected_points"]["mae"]
        < result["early_gw2_5"]["raw_rolling_expected_points"]["mae"]
    )


def test_parameter_selection_is_deterministic() -> None:
    cases = build_calibration_cases(
        prior_rows=_rows([5] * 10),
        target_rows=_rows([17, 2, 2, 2, 2]),
        prior_season="2023-24",
        target_season="2024-25",
    )
    kwargs = {
        "prior_equivalent_minutes": [450, 900],
        "start_prior_equivalent_matches": [4, 8],
        "cameo_minutes": [10, 18],
    }
    assert select_parameters(cases, **kwargs) == select_parameters(cases, **kwargs)


def test_future_event_change_cannot_change_earlier_event_history() -> None:
    prior = _rows([5, 5, 5])
    prior["expected_goals"] = [0.2, 0.2, 0.2]
    original = _rows([2, 2, 2])
    original["expected_goals"] = [0.1, 0.2, 0.3]
    changed = original.copy()
    changed.loc[changed["GW"] == 3, "expected_goals"] = 99
    first = build_calibration_cases(
        prior_rows=prior,
        target_rows=original,
        prior_season="2023-24",
        target_season="2024-25",
    )
    second = build_calibration_cases(
        prior_rows=prior,
        target_rows=changed,
        prior_season="2023-24",
        target_season="2024-25",
    )
    assert first.loc[first["GW"] <= 3, "current_expected_goals"].tolist() == second.loc[
        second["GW"] <= 3, "current_expected_goals"
    ].tolist()


def test_zero_component_weights_reproduce_component_free_ablation() -> None:
    cases = build_calibration_cases(
        prior_rows=_rows([5] * 5),
        target_rows=_rows([6, 4, 2, 3, 5]),
        prior_season="2023-24",
        target_season="2024-25",
    )
    baseline = predictions(cases, ForecastParameters(900, 2, 10))
    changed = cases.copy()
    changed["base_expected_goals_per_90"] = 100
    changed["group_expected_goals_per_90"] = 100
    changed["recent_minutes_per_fixture"] = 1
    ablation = predictions(changed, ForecastParameters(900, 2, 10))
    assert baseline["live_faithful_expected_points"].tolist() == ablation[
        "live_faithful_expected_points"
    ].tolist()
