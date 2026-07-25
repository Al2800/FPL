"""Sealed event-challenger selection and evaluation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.calibrate_event_challenger import run_event_challenger
from src.forecasting.event_challenger import (
    reblend_locked_forecast,
    select_preseason_event_candidate,
)
from src.forecasting.live_faithful import artifact_hash

ROOT = Path(__file__).resolve().parents[2]


def _locked_inputs() -> tuple[dict, dict]:
    base = json.loads(
        (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
            encoding="utf-8"
        )
    )
    calibration = json.loads(
        (ROOT / "reports/forecasting/live-faithful-v1-feature-complete-calibration.json").read_text(
            encoding="utf-8"
        )
    )
    return base, calibration


def test_candidate_is_selected_only_from_preseason_locked_grid() -> None:
    base, calibration = _locked_inputs()
    config = select_preseason_event_candidate(base, calibration)
    assert config["model_version"] == "live-faithful-v2-events"
    assert config["event_model_weight"] == 0.25
    assert config["calibration"]["event_candidate_rank"] == 5
    assert config["content_sha256"] == artifact_hash(config)
    assert base["event_model_weight"] == 0.0

    leaked = deepcopy(calibration)
    leaked["split"]["training_target_seasons"].append("2025-26")
    with pytest.raises(ValueError, match="not sealed"):
        select_preseason_event_candidate(base, leaked)


def test_reblend_uses_only_frozen_component_values() -> None:
    forecast = {
        "content_sha256": "a" * 64,
        "model_version": "live-faithful-v1",
        "model_status": "locked",
        "lineage": {"model_sha256": "b" * 64},
        "players": [
            {
                "player_id": "player:1",
                "expected_points": 4.0,
                "fixture_components": [
                    {
                        "rate_expected_points": 4.0,
                        "event_expected_points": 8.0,
                        "event_model_weight": 0.0,
                        "expected_points": 4.0,
                    }
                ],
            }
        ],
    }
    result = reblend_locked_forecast(forecast, event_model_weight=0.25)
    assert result["players"][0]["expected_points"] == 5.0
    assert result["players"][0]["fixture_components"][0]["event_model_weight"] == 0.25
    assert result["lineage"]["base_forecast_sha256"] == "a" * 64
    assert forecast["players"][0]["expected_points"] == 4.0


def test_2025_26_out_of_sample_decision_when_private_data_available() -> None:
    outcomes = ROOT / "data/raw/vaastav/Fantasy-Premier-League/data/2025-26/gws/merged_gw.csv"
    if not outcomes.exists():
        pytest.skip("private historical outcomes are not installed")
    config, report = run_event_challenger(
        base_config_path=ROOT / "control/models/live-faithful-v1.feature-complete.json",
        locked_calibration_path=ROOT / "reports/forecasting/live-faithful-v1-feature-complete-calibration.json",
        reports_root=ROOT / "reports/benchmarks/2025-26",
        outcomes_csv=outcomes,
    )
    assert report["event_model_weight"] == config["event_model_weight"]
    assert report["evaluation_season"] == "2025-26"
    assert report["decision"] in {"promote", "reject"}
    assert set(report["promotion_rule"]) == {
        "all_mae_not_worse",
        "owned_mae_improves",
        "selected_xi_mae_improves",
        "selected_xi_absolute_bias_improves",
    }
