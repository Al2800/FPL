"""Contracts for the W9 position-specific recalibration challenger."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.recalibration import (
    POSITIONS,
    apply_position_recalibration,
    build_recalibration_report,
    fit_position_recalibration,
)


def _frame(*, offset: float = 0.0) -> pd.DataFrame:
    rows = []
    code = 1
    for gameweek in (2, 3, 4):
        for position_index, position in enumerate(POSITIONS):
            for index in range(12):
                predicted = 0.5 + index * 0.7 + position_index * 0.1
                actual = min(predicted, 4.0 + position_index * 0.2) + offset
                rows.append(
                    {
                        "GW": gameweek,
                        "code": code,
                        "position": position,
                        "price_band": (
                            "7.5-10" if 4.0 + index * 0.6 >= 7.5 else "0-7.5"
                        ),
                        "actual_points": actual,
                        "live_faithful_expected_points": predicted,
                    }
                )
                code += 1
    return pd.DataFrame(rows)


def test_fit_is_position_specific_monotone_and_deterministic() -> None:
    frame = _frame()
    first = fit_position_recalibration(frame, bin_count=4)
    second = fit_position_recalibration(frame, bin_count=4)

    assert first == second
    assert set(first["positions"]) == set(POSITIONS)
    for spec in first["positions"].values():
        assert spec["n"] == 36
        assert spec["calibrated_values"] == sorted(spec["calibrated_values"])
        assert sum(row["n"] for row in spec["fit_bins"]) == spec["n"]


def test_apply_preserves_input_and_clamps_to_terminal_bins() -> None:
    training = _frame()
    calibrator = fit_position_recalibration(training, bin_count=4)
    candidate = training.head(4).copy()
    candidate.loc[candidate.index[0], "live_faithful_expected_points"] = -5.0
    candidate.loc[candidate.index[1], "live_faithful_expected_points"] = 50.0
    before = candidate.copy(deep=True)

    result = apply_position_recalibration(candidate, calibrator)

    pd.testing.assert_frame_equal(candidate, before)
    low_spec = calibrator["positions"][candidate.iloc[0]["position"]]
    high_spec = calibrator["positions"][candidate.iloc[1]["position"]]
    assert result.iloc[0]["recalibrated_expected_points"] == (
        low_spec["calibrated_values"][0]
    )
    assert result.iloc[1]["recalibrated_expected_points"] == (
        high_spec["calibrated_values"][-1]
    )


def test_report_locks_split_hashes_outputs_and_keeps_promotion_owner_gated() -> None:
    training = _frame()
    validation = _frame(offset=0.1)
    final = _frame(offset=-0.1)
    lineage = [
        {
            "season": season,
            "merged_gw_sha256": character * 64,
            "players_raw_sha256": character.upper() * 64,
            "row_count": 100,
            "start_source": "recorded",
            "excluded_assistant_manager_rows": 0,
        }
        for season, character in (
            ("2021-22", "a"),
            ("2022-23", "b"),
            ("2023-24", "c"),
            ("2024-25", "d"),
            ("2025-26", "e"),
        )
    ]
    lineage_before = deepcopy(lineage)

    config, report = build_recalibration_report(
        training=training,
        validation=validation,
        final=final,
        source_lineage=lineage,
        bin_count=4,
    )

    assert lineage == lineage_before
    assert config["content_sha256"] == artifact_hash(config)
    assert report["content_sha256"] == artifact_hash(report)
    assert config["calibration"]["fit_seasons"] == ["2022-23", "2023-24"]
    assert config["calibration"]["forbidden_fit_seasons"] == [
        "2024-25",
        "2025-26",
    ]
    assert config["promotion"]["production_default_changed"] is False
    assert report["promotion_gates"]["legal_replay_completed"] is False
    assert report["promotion_gates"]["production_owner_approval"] is False
    assert report["promotion_eligible"] is False
    assert report["metric_scope"]["top15"].startswith("unconstrained")
    assert (
        report["locked_validation"]["control"]
        ["mean_gameweek_premium_rank_correlation"]
        is not None
    )
