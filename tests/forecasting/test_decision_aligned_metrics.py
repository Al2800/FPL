from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

from src.evaluation.calibration import (
    calibration_summary,
    decision_aligned_comparison_table,
    decision_aligned_summary,
)
from src.forecasting.evaluate import decision_aligned_frame_comparison


def _squad() -> list[dict[str, object]]:
    values = [
        ("g1", "GKP", 5.0, 2.0, 5.0),
        ("g2", "GKP", 4.0, 8.0, 4.5),
        ("d1", "DEF", 10.0, 0.0, 7.0),
        ("d2", "DEF", 9.0, 1.0, 6.5),
        ("d3", "DEF", 8.0, 2.0, 6.0),
        ("d4", "DEF", 7.0, 10.0, 5.5),
        ("d5", "DEF", 6.0, 9.0, 5.0),
        ("m1", "MID", 12.0, 1.0, 12.0),
        ("m2", "MID", 11.0, 2.0, 10.0),
        ("m3", "MID", 10.0, 3.0, 8.0),
        ("m4", "MID", 9.0, 12.0, 7.5),
        ("m5", "MID", 8.0, 11.0, 7.0),
        ("f1", "FWD", 11.0, 1.0, 14.0),
        ("f2", "FWD", 10.0, 9.0, 9.0),
        ("f3", "FWD", 9.0, 8.0, 7.0),
    ]
    return [
        {
            "player_id": player_id,
            "position": position,
            "predicted": predicted,
            "actual": actual,
            "price": price,
        }
        for player_id, position, predicted, actual, price in values
    ]


def test_owned_squad_metrics_select_and_compare_legal_lineups() -> None:
    result = decision_aligned_summary(
        _squad(),
        boundary_type="owned_squad",
        top_price_band_min=9.0,
    )

    assert result["evaluation_only"] is True
    assert result["hindsight_fields_forbidden_as_proposal_inputs"] is True
    assert result["selected_xi"]["source"] == "inferred_max_predicted_legal_xi"
    assert result["selected_xi"]["formation"] == {
        "GKP": 1,
        "DEF": 3,
        "MID": 4,
        "FWD": 3,
    }
    assert len(result["selected_xi"]["player_ids"]) == 11
    assert result["xi_regret"]["realised_points"] == 34.0
    assert result["captain"]["player_id"] == "m1"
    assert result["captain"]["oracle_player_id_within_selected_xi"] == "m4"
    assert result["captain"]["regret_points"] == 11.0
    assert result["top_price_band_rank"]["status"] == "measured"
    assert result["sample_sizes"] == {
        "boundary_player_gameweeks": 15,
        "selected_xi": 11,
        "top_price_band": 4,
    }


def test_explicit_illegal_lineup_and_captain_are_refused() -> None:
    illegal = ["g1", "g2", "d1", "d2", "d3", "m1", "m2", "m3", "f1", "f2", "f3"]
    with pytest.raises(ValueError, match="illegal starting XI formation"):
        decision_aligned_summary(
            _squad(),
            boundary_type="owned_squad",
            top_price_band_min=9.0,
            selected_xi_ids=illegal,
        )

    legal = ["g1", "d1", "d2", "d3", "m1", "m2", "m3", "m4", "f1", "f2", "f3"]
    with pytest.raises(ValueError, match="captain must belong"):
        decision_aligned_summary(
            _squad(),
            boundary_type="owned_squad",
            top_price_band_min=9.0,
            selected_xi_ids=legal,
            captain_id="m5",
        )


def test_market_boundary_requires_optimizer_supplied_legal_candidates() -> None:
    rows = _squad()
    with pytest.raises(ValueError, match="optimiser-supplied"):
        decision_aligned_summary(
            rows,
            boundary_type="market",
            top_price_band_min=9.0,
        )

    candidate_a = [
        "g1",
        "d1",
        "d2",
        "d3",
        "m1",
        "m2",
        "m3",
        "m4",
        "f1",
        "f2",
        "f3",
    ]
    candidate_b = [
        "g2",
        "d3",
        "d4",
        "d5",
        "m2",
        "m3",
        "m4",
        "m5",
        "f1",
        "f2",
        "f3",
    ]
    result = decision_aligned_summary(
        rows,
        boundary_type="market",
        top_price_band_min=9.0,
        legal_lineups=[candidate_a, candidate_b],
    )

    assert result["boundary"]["legal_candidate_count"] == 2
    assert result["selected_xi"]["player_ids"] == sorted(candidate_a)
    assert result["xi_regret"]["oracle_player_ids"] == sorted(candidate_b)


def test_empty_and_tied_price_cohorts_are_explicit() -> None:
    empty = decision_aligned_summary(
        _squad(),
        boundary_type="owned_squad",
        top_price_band_min=99.0,
    )
    assert empty["top_price_band_rank"] == {
        "status": "empty",
        "n": 0,
        "minimum_price": 99.0,
        "spearman_correlation": None,
    }

    tied_rows = _squad()
    for row in tied_rows:
        if float(row["price"]) >= 9.0:
            row["predicted"] = 1.0
    tied = decision_aligned_summary(
        tied_rows,
        boundary_type="owned_squad",
        top_price_band_min=9.0,
    )
    assert tied["top_price_band_rank"]["status"] == "degenerate_tie"
    assert tied["top_price_band_rank"]["spearman_correlation"] is None


def test_comparison_table_is_stable_and_preserves_point_error_values() -> None:
    control = _squad()
    challenger = deepcopy(control)
    for row in challenger:
        row["predicted"] = float(row["predicted"]) * 0.9
    expected_control = calibration_summary(
        [float(row["predicted"]) for row in control],
        [float(row["actual"]) for row in control],
    )

    report = decision_aligned_comparison_table(
        {"z_challenger": challenger, "a_control": control},
        boundary_type="owned_squad",
        top_price_band_min=9.0,
    )

    assert [row["model"] for row in report["comparison_table"]] == [
        "a_control",
        "z_challenger",
    ]
    point_error = report["comparison_table"][0]["point_error"]
    assert point_error["mean_absolute_error"] == expected_control[
        "mean_absolute_error"
    ]
    assert point_error["root_mean_square_error"] == expected_control[
        "root_mean_square_error"
    ]
    assert report["metric_direction"]["xi_regret.realised_points"] == (
        "lower_is_better"
    )

    broken = deepcopy(challenger)
    broken[0]["actual"] = 999.0
    with pytest.raises(ValueError, match="same decision boundary"):
        decision_aligned_comparison_table(
            {"control": control, "broken": broken},
            boundary_type="owned_squad",
            top_price_band_min=9.0,
        )


def test_dataframe_adapter_produces_the_same_one_table_contract() -> None:
    frame = pd.DataFrame(
        [
            {
                **row,
                "control": row["predicted"],
                "challenger": float(row["predicted"]) * 0.9,
            }
            for row in _squad()
        ]
    ).drop(columns=["predicted"])
    report = decision_aligned_frame_comparison(
        frame,
        prediction_columns={
            "control": "control",
            "challenger": "challenger",
        },
        boundary_type="owned_squad",
        top_price_band_min=9.0,
    )

    assert len(report["comparison_table"]) == 2
    assert all(row["evaluation_only"] for row in report["comparison_table"])

    with pytest.raises(ValueError, match="missing columns: price"):
        decision_aligned_frame_comparison(
            frame.drop(columns=["price"]),
            prediction_columns={"control": "control"},
            boundary_type="owned_squad",
            top_price_band_min=9.0,
        )
