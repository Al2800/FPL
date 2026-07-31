"""Counterfactual, calibration, paired-evaluation and power guardrails."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.artifact_backed
from jsonschema import Draft202012Validator

from src.evaluation.calibration import calibration_by_cohort, calibration_summary
from src.evaluation.paired_metrics import paired_summary, resource_summary
from src.evaluation.power import minimum_detectable_paired_effect
from src.evaluation.replay_review import review_replay_season
from src.reporting.baseline_comparison import (
    compare_realised_outcomes,
    compare_to_do_nothing,
)

ROOT = Path(__file__).resolve().parents[1]
SHA_A = "a" * 64
SHA_B = "b" * 64


def _outcome(*, plan: str, points: int, source: str = SHA_A) -> dict:
    return {
        "episode_id": "benchmark-v0:2025-26:gw12:manager-neutral",
        "season": "2025-26",
        "gameweek": 12,
        "plan_id": plan,
        "plan_sha256": SHA_A if plan == "challenger" else SHA_B,
        "source_outcome_sha256": source,
        "ruleset": {"content_sha256": SHA_A},
        "gross_points": points,
    }


def test_expected_proxy_is_explicitly_not_realised() -> None:
    result = compare_to_do_nothing(
        recommended_objective=60.0,
        do_nothing_objective=55.0,
    )
    assert result["comparison_basis"] == "expected_proxy"
    assert result["is_realised"] is False
    assert result["expected_advantage"] == 5.0


@pytest.mark.parametrize(
    "counterfactual_type",
    ["do_nothing", "captain", "transfer", "bench", "chip", "policy_arm"],
)
def test_realised_feasible_counterfactuals_retain_provenance(
    counterfactual_type: str,
) -> None:
    result = compare_realised_outcomes(
        evaluated_outcome=_outcome(plan="challenger", points=64),
        baseline_outcome=_outcome(plan="baseline", points=58),
        counterfactual_type=counterfactual_type,
    )
    assert result["realised_gain"] == 6.0
    assert result["evaluated"]["plan_sha256"] == SHA_A
    assert result["baseline"]["plan_sha256"] == SHA_B
    assert result["scoring_provenance"]["source_outcome_sha256"] == SHA_A


def test_realised_counterfactual_rejects_different_revealed_source() -> None:
    with pytest.raises(ValueError, match="source_outcome_sha256"):
        compare_realised_outcomes(
            evaluated_outcome=_outcome(plan="challenger", points=64),
            baseline_outcome=_outcome(plan="baseline", points=58, source=SHA_B),
            counterfactual_type="transfer",
        )


def test_paired_summary_uses_cluster_means_for_inference() -> None:
    rows = [
        {"episode_id": "gw1-a", "cluster_id": "gw1", "evaluated_value": 3, "baseline_value": 2},
        {"episode_id": "gw1-b", "cluster_id": "gw1", "evaluated_value": 6, "baseline_value": 3},
        {"episode_id": "gw2-a", "cluster_id": "gw2", "evaluated_value": 10, "baseline_value": 5},
        {"episode_id": "gw2-b", "cluster_id": "gw2", "evaluated_value": 9, "baseline_value": 2},
    ]
    result = paired_summary(rows)
    assert result["n_pairs"] == 4
    assert result["n_clusters"] == 2
    assert result["total_difference"] == 16
    assert result["mean_difference"] == 4
    assert result["sample_standard_deviation"] == pytest.approx(math.sqrt(8))
    assert result["wins"] == 4
    assert result["confidence_interval"][0] < 4 < result["confidence_interval"][1]


def test_calibration_reports_selection_cohorts() -> None:
    summary = calibration_summary([1, 2, 3], [0, 2, 4], bins=2)
    assert summary["bias_actual_minus_predicted"] == 0
    assert summary["mean_absolute_error"] == pytest.approx(2 / 3)
    assert summary["root_mean_square_error"] == pytest.approx(math.sqrt(2 / 3))
    assert summary["correlation"] == pytest.approx(1)

    cohorts = calibration_by_cohort(
        [
            {"predicted": 1, "actual": 0, "cohorts": []},
            {"predicted": 2, "actual": 2, "cohorts": ["owned"]},
            {"predicted": 3, "actual": 4, "cohorts": ["owned", "selected_xi"]},
        ],
        bins=2,
    )
    assert cohorts["all"]["n"] == 3
    assert cohorts["owned"]["n"] == 2
    assert cohorts["selected_xi"]["n"] == 1


def test_detectable_effect_and_resource_use_are_reported() -> None:
    result = minimum_detectable_paired_effect(
        n_clusters=38,
        sample_standard_deviation=10,
    )
    assert result["absolute_effect"] == pytest.approx(4.544, abs=0.01)
    resources = resource_summary(
        [
            {
                "evaluated_latency_ms": 20,
                "baseline_latency_ms": 10,
                "evaluated_cost": 0.1,
                "baseline_cost": 0,
            },
            {
                "evaluated_latency_ms": 30,
                "baseline_latency_ms": 10,
                "evaluated_cost": 0.2,
                "baseline_cost": 0,
            },
        ]
    )
    assert resources["evaluated_latency_ms"]["mean"] == 25
    assert resources["evaluated_cost"]["total"] == pytest.approx(0.3)


def test_decision_outcome_comparison_schema_requires_both_frozen_plans() -> None:
    schema = json.loads(
        (ROOT / "control/schemas/decisions/decision_outcomes.json").read_text(
            encoding="utf-8"
        )
    )
    comparison_schema = schema["properties"]["comparison"]
    valid = {
        "basis": "realised_feasible_counterfactual",
        "counterfactual_type": "transfer",
        "episode_id": "episode-1",
        "evaluated_plan": {"plan_id": "plan-a", "plan_sha256": SHA_A},
        "baseline_plan": {"plan_id": "plan-b", "plan_sha256": SHA_B},
        "scoring_provenance": {
            "source_outcome_sha256": SHA_A,
            "ruleset_sha256": SHA_B,
        },
    }
    validator = Draft202012Validator(comparison_schema)
    validator.validate(valid)
    del valid["baseline_plan"]
    assert list(validator.iter_errors(valid))

def test_frozen_2025_26_review_when_private_outcomes_are_available() -> None:
    reports = ROOT / "reports/benchmarks/2025-26"
    outcomes = (
        ROOT
        / "data/raw/vaastav/Fantasy-Premier-League/data/2025-26/gws/merged_gw.csv"
    )
    if not outcomes.exists():
        pytest.skip("private local historical outcomes are not installed")
    result = review_replay_season(reports, outcomes)
    assert result["paired_metrics"]["n_pairs"] == 38
    assert result["paired_metrics"]["total_difference"] == 20
    assert result["calibration"]["all"]["n"] == 28497
    assert result["calibration"]["selected_xi"]["n"] == 403
    assert result["decision_activity"]["transfers"] == 39
    assert result["decision_activity"]["automatic_substitutions"] == 27
