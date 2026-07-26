"""Captain-only policy and frozen counterfactual evaluation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.captaincy import CaptaincyError, choose_captain_pair

ROOT = Path(__file__).resolve().parents[2]


def _config() -> dict:
    return json.loads(
        (ROOT / "control/policies/captain-v1.json").read_text(encoding="utf-8")
    )


def _appearance() -> dict:
    return json.loads(
        (
            ROOT / "control/models/appearance-distribution-v1.json"
        ).read_text(encoding="utf-8")
    )


def _xi() -> list[dict]:
    positions = ["GKP", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "MID", "FWD", "FWD"]
    return [
        {
            "player_id": str(index),
            "position": position,
            "expected_points": 10.0 if index == 1 else 9.0 if index == 2 else 4.0,
            "start_probability": 0.5 if index == 1 else 0.95,
            "fixture_count": 1,
        }
        for index, position in enumerate(positions, start=1)
    ]


def test_pair_is_legal_deterministic_and_values_zero_minute_fallback() -> None:
    first = choose_captain_pair(
        _xi(), config=_config(), appearance_calibration=_appearance()
    )
    again = choose_captain_pair(
        _xi(), config=_config(), appearance_calibration=_appearance()
    )
    assert first == again
    selected = first["selected"]
    assert selected["captain_id"] != selected["vice_captain_id"]
    assert selected["captain_id"] in first["fixed_starting_xi_ids"]
    assert selected["vice_fallback_value"] > 0
    assert selected["expected_captain_extra"] == pytest.approx(
        selected["captain_expected_points"] + selected["vice_fallback_value"]
    )


def test_tampered_config_and_non_xi_fail_closed() -> None:
    config = _config()
    config["ceiling_weight"] = 99
    with pytest.raises(CaptaincyError, match="hash mismatch"):
        choose_captain_pair(
            _xi(), config=config, appearance_calibration=_appearance()
        )
    with pytest.raises(CaptaincyError, match="eleven"):
        choose_captain_pair(
            _xi()[:10], config=_config(), appearance_calibration=_appearance()
        )


def test_sealed_report_rejects_policy_and_is_captain_only() -> None:
    path = ROOT / "reports/benchmarks/2025-26-captain/evaluation.json"
    if not path.exists():
        pytest.skip("sealed captain report is not installed")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["content_sha256"] == artifact_hash(report)
    assert report["decision"] == "reject"
    assert report["promotion_eligible"] is False
    for row in report["episodes"]:
        assert row["realised_points_delta"] == (
            row["challenger_captain_extra"] - row["canonical_captain_extra"]
        )
