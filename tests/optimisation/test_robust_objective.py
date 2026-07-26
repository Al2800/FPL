"""Robust-selection shrinkage and solver integration."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.reliability_shrinkage import (
    ReliabilityShrinkageError,
    RobustSelectionParameters,
    deterministic_quantile,
    shrink_player_projections,
)
from src.optimisation.robust_objective import (
    RobustObjectiveError,
    robust_solver_input,
)

ROOT = Path(__file__).resolve().parents[2]


def _config() -> dict:
    return json.loads(
        (ROOT / "control/models/live-faithful-v2.robust.json").read_text(
            encoding="utf-8"
        )
    )


def test_deterministic_quantile_has_stable_linear_interpolation() -> None:
    assert deterministic_quantile([4, 1, 3, 2], 0.5) == 2.5
    assert deterministic_quantile([1, 2, 3], 0.9) == pytest.approx(2.8)


def test_shrinkage_only_reduces_unreliable_upper_tail_and_reports_scenarios() -> None:
    parameters = RobustSelectionParameters.from_config(_config())
    players = [
        {"player_id": "a", "position": "MID", "expected_points": 10.0},
        {"player_id": "b", "position": "MID", "expected_points": 5.0},
        {"player_id": "c", "position": "MID", "expected_points": 4.0},
    ]
    first = shrink_player_projections(
        players,
        reliability_by_player={"a": 0.0, "b": 1.0, "c": 0.5},
        parameters=parameters,
    )
    again = shrink_player_projections(
        players,
        reliability_by_player={"a": 0.0, "b": 1.0, "c": 0.5},
        parameters=parameters,
    )
    assert first == again
    assert players[0] == {"player_id": "a", "position": "MID", "expected_points": 10.0}
    assert first[0]["raw_expected_points"] == 10.0
    assert first[0]["expected_points"] < first[0]["robust_selection"]["central"] < 10.0
    assert first[1]["robust_selection"]["central"] == 5.0
    assert 0 <= first[0]["robust_selection"]["lower"]
    assert first[0]["robust_selection"]["upper"] <= 20


def test_robust_input_joins_locked_reliability_and_preserves_raw_input() -> None:
    config = _config()
    assert config["content_sha256"] == artifact_hash(config)
    solver_input = {
        "players": [
            {
                "player_id": "player:1",
                "position": "FWD",
                "expected_points": 9.0,
            },
            {
                "player_id": "player:2",
                "position": "FWD",
                "expected_points": 4.0,
            },
        ]
    }
    original = deepcopy(solver_input)
    forecast = {
        "content_sha256": "a" * 64,
        "players": [
            {"player_id": "player:1", "prior": {"reliability_weight": 0.1}},
            {"player_id": "player:2", "prior": {"reliability_weight": 0.9}},
        ],
    }
    result = robust_solver_input(
        solver_input,
        locked_forecast=forecast,
        config=config,
    )
    assert solver_input == original
    assert result["players"][0]["raw_expected_points"] == 9.0
    assert result["players"][0]["expected_points"] < 9.0
    assert result["robust_selection"]["base_forecast_sha256"] == "a" * 64


def test_missing_reliability_and_invalid_config_fail_closed() -> None:
    config = _config()
    solver_input = {
        "players": [
            {"player_id": "missing", "position": "GKP", "expected_points": 4.0}
        ]
    }
    with pytest.raises(RobustObjectiveError, match="missing reliability"):
        robust_solver_input(
            solver_input,
            locked_forecast={"content_sha256": "a" * 64, "players": []},
            config=config,
        )
    fallback_forecast = {
        "content_sha256": "a" * 64,
        "players": [{"player_id": "missing", "prior": {"source": "fallback"}}],
    }
    fallback_result = robust_solver_input(
        solver_input,
        locked_forecast=fallback_forecast,
        config=config,
    )
    assert fallback_result["players"][0]["robust_selection"]["reliability"] == 0.0
    invalid = deepcopy(config)
    invalid["anchor_quantile"] = 2
    invalid["content_sha256"] = artifact_hash(invalid)
    with pytest.raises(ReliabilityShrinkageError, match="anchor_quantile"):
        RobustSelectionParameters.from_config(invalid)


def test_sealed_evaluation_records_positive_locked_gate_and_final_disagreement() -> None:
    report = json.loads(
        (
            ROOT
            / "reports/forecasting/live-faithful-v2-robust-evaluation.json"
        ).read_text(encoding="utf-8")
    )
    assert report["content_sha256"] == artifact_hash(report)
    assert report["decision"] == "promote_to_challenger"
    locked = report["locked_validation"]["delta_robust_minus_raw"]
    final = report["final_out_of_sample"]["delta_robust_minus_raw"]
    assert locked["selected_top15_mae"] < 0
    assert locked["mean_top15_decision_regret"] < 0
    assert final["selected_top15_mae"] < 0
    assert final["mean_top15_decision_regret"] > 0
