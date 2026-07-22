"""Offline calibration tests for data-quality gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

from src.evaluation.data_quality_calibration import (
    CalibrationError,
    calibrate_quality_cases,
    validate_live_shadow_manifest,
)

REPO = Path(__file__).resolve().parents[2]


def _report(disposition="pass", coverage=1.0, staleness=1200.0):
    return {
        "recommended_disposition": disposition,
        "metrics": {
            "schema_error_rate": 0.0,
            "exact_duplicate_rate": 0.0,
            "equivalent_duplicate_rate": 0.0,
            "conflicting_duplicate_rate": 0.0,
            "coverage_rate": coverage,
            "identity_match_rate": 1.0,
            "staleness_seconds": staleness,
            "disagreement_rate": 0.0,
        },
    }


def _case(
    case_id,
    *,
    evidence_mode="historical_replay",
    gameweek=1,
    disposition="pass",
    should_exclude=False,
    unrestricted_action="hold",
    gated_action="hold",
    unrestricted_score=60.0,
    gated_score=60.0,
    unrestricted_realized=None,
    gated_realized=None,
    coverage=1.0,
):
    return {
        "case_id": case_id,
        "evidence_mode": evidence_mode,
        "gate_id": "coverage.expected_entities",
        "source_id": "fpl-official-endpoints",
        "field_name": "selected_by_percent",
        "entity_type": "player",
        "gameweek": gameweek,
        "quality_report": _report(disposition, coverage=coverage),
        "adjudication": {"should_exclude": should_exclude},
        "unrestricted_decision": {
            "action_id": unrestricted_action,
            "projected_score": unrestricted_score,
            "realized_score": unrestricted_realized,
        },
        "gated_decision": {
            "action_id": gated_action,
            "projected_score": gated_score,
            "realized_score": gated_realized,
        },
    }


def _plan(tmp_path: Path, **overrides):
    criteria = {
        "minimum_cases_total": 2,
        "minimum_cases_per_segment": 2,
        "required_evidence_modes": ["historical_replay", "live_shadow"],
        "max_false_quarantine_rate": 0.1,
        "max_false_admission_rate": 0.1,
    }
    criteria.update(overrides)
    path = tmp_path / "plan.yaml"
    path.write_text(
        yaml.safe_dump(
            {"calibration_plan_version": "test", "promotion_criteria": criteria},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_calibration_is_deterministic_and_emits_segment_distributions():
    cases = [
        _case("gw1", coverage=1.0),
        _case(
            "gw2",
            evidence_mode="live_shadow",
            gameweek=2,
            coverage=0.8,
            unrestricted_action="transfer:a",
            gated_action="transfer:b",
            gated_score=58.0,
            unrestricted_realized=55.0,
            gated_realized=52.0,
        ),
    ]
    first = calibrate_quality_cases(cases)
    second = calibrate_quality_cases(list(reversed(cases)))
    assert first["calibration_id"] == second["calibration_id"]
    segment = first["segments"][0]
    assert segment["gameweeks"] == [1, 2]
    assert segment["evidence_modes"] == ["historical_replay", "live_shadow"]
    assert segment["metrics"]["coverage_rate"]["mean"] == pytest.approx(0.9)
    assert segment["decision_change_rate"] == 0.5
    assert segment["projected_score_delta"]["mean"] == pytest.approx(-1.0)
    assert segment["realized_score_delta"]["count"] == 1
    assert segment["realized_score_delta"]["mean"] == pytest.approx(-3.0)


def test_confusion_rates_measure_false_quarantine_and_false_admission():
    report = calibrate_quality_cases(
        [
            _case("false-q", disposition="quarantine", should_exclude=False),
            _case(
                "false-a",
                evidence_mode="live_shadow",
                gameweek=2,
                disposition="pass",
                should_exclude=True,
            ),
        ]
    )
    assert report["overall_confusion"]["false_quarantine_rate"] == 0.5
    assert report["overall_confusion"]["false_admission_rate"] == 0.5


def test_default_plan_requires_more_evidence_and_never_updates_policy():
    report = calibrate_quality_cases([_case("one")])
    review = report["promotion_review"]
    assert review["status"] == "insufficient_evidence"
    assert review["automatic_policy_update"] is False
    assert "insufficient_case_count" in review["reason_codes"]
    assert "missing_required_evidence_modes" in review["reason_codes"]


def test_clean_dual_mode_evidence_is_only_eligible_for_owner_review(tmp_path: Path):
    report = calibrate_quality_cases(
        [
            _case("historical", disposition="quarantine", should_exclude=True),
            _case("live", evidence_mode="live_shadow", disposition="pass", should_exclude=False),
        ],
        plan_path=_plan(tmp_path),
    )
    assert report["promotion_review"]["status"] == "eligible_for_owner_review"
    assert report["promotion_review"]["automatic_policy_update"] is False


def test_excess_false_quarantine_retains_observe_only(tmp_path: Path):
    report = calibrate_quality_cases(
        [
            _case("historical", disposition="quarantine", should_exclude=False),
            _case("live", evidence_mode="live_shadow", disposition="pass", should_exclude=False),
        ],
        plan_path=_plan(tmp_path),
    )
    assert report["promotion_review"]["status"] == "retain_observe_only"
    assert "false_quarantine_rate_too_high" in report["promotion_review"]["reason_codes"]


def test_live_shadow_manifest_prohibits_browser_and_account_execution():
    manifest = json.loads(
        (REPO / "evals/data-quality/live-shadow-example.json").read_text(encoding="utf-8")
    )
    assert validate_live_shadow_manifest(manifest) is manifest
    unsafe = {**manifest, "browser_actions": True}
    with pytest.raises(ValidationError):
        validate_live_shadow_manifest(unsafe)


def test_duplicate_case_ids_fail_closed():
    case = _case("duplicate")
    with pytest.raises(CalibrationError, match="must be unique"):
        calibrate_quality_cases([case, case])
