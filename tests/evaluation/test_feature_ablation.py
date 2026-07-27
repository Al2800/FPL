import json
from pathlib import Path

import pytest

from src.evaluation.feature_ablation import (
    FeatureAblationError,
    evaluate_feature_ablation,
    validate_preregistration,
)
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.live_shadow import shadow_hash


ROOT = Path(__file__).resolve().parents[2]
PREREGISTRATION = json.loads(
    (
        ROOT
        / "reports/forecasting/2026-27-preregistration/preregistration.json"
    ).read_text(encoding="utf-8")
)
SHA = "a" * 64


def _row(
    episode_id: str,
    *,
    family: str = "odds",
    fold_id: str = "live-gw01-06",
    season: str = "2026-27",
    gameweek: int = 1,
) -> dict:
    return {
        "episode_id": episode_id,
        "fold_id": fold_id,
        "season": season,
        "gameweek": gameweek,
        "feature_families": [family],
        "available_at": "2026-08-14T09:00:00Z",
        "decision_cutoff": "2026-08-14T10:00:00Z",
        "source_snapshot_sha256": SHA,
        "baseline_plan_sha256": SHA,
        "candidate_plan_sha256": SHA,
        "outcome_sha256": SHA,
        "plan_legal": True,
        "baseline_prediction": 0.0,
        "candidate_prediction": 1.0,
        "actual": 1.0,
        "baseline_decision_points": 5.0,
        "candidate_decision_points": 8.0,
        "hindsight_legal_points": 10.0,
        "candidate_latency_ms": 100.0,
        "degraded": False,
    }


def _passing_live_rows() -> list[dict]:
    rows = []
    for fold_id, gameweek in (
        ("live-gw01-06", 1),
        ("live-gw07-12", 7),
        ("live-gw13-19", 13),
    ):
        rows.extend(
            _row(f"{fold_id}:{index}", fold_id=fold_id, gameweek=gameweek)
            for index in range(4)
        )
    return rows


def test_preregistration_is_sealed_and_declares_every_isolated_family():
    validate_preregistration(PREREGISTRATION)
    assert PREREGISTRATION["content_sha256"] == artifact_hash(PREREGISTRATION)
    assert set(PREREGISTRATION["candidate_families"]) == {
        "odds",
        "team_strength",
        "set_piece_role",
        "player_ratings",
    }
    assert {
        config["arm_id"]
        for config in PREREGISTRATION["candidate_families"].values()
    } == {
        "forecast_optimizer_plus_odds",
        "forecast_optimizer_plus_team_strength",
        "forecast_optimizer_plus_set_piece_role",
        "forecast_optimizer_plus_player_ratings",
    }


@pytest.mark.parametrize(
    "family", ["odds", "team_strength", "set_piece_role", "player_ratings"]
)
def test_live_ablation_requires_three_locked_folds_and_all_gates(family: str):
    rows = _passing_live_rows()
    for row in rows:
        row["feature_families"] = [family]
    report = evaluate_feature_ablation(
        rows=rows,
        preregistration=PREREGISTRATION,
        family=family,
    )
    assert report["content_sha256"] == artifact_hash(report)
    assert report["promotion_eligible"] is True
    assert report["decision"] == "eligible_for_owner_review"
    assert all(report["promotion_checks"].values())
    assert report["candidate_minus_baseline"]["proper_score"] == -1.0
    assert report["candidate_minus_baseline"]["legal_decision_regret"] == -3.0
    assert report["uncertainty"]["mean_candidate_minus_baseline_points"] == 3.0
    assert report == evaluate_feature_ablation(
        rows=list(reversed(rows)),
        preregistration=PREREGISTRATION,
        family=family,
    )


def test_historical_2025_26_ablation_is_reported_but_production_ineligible():
    rows = [
        _row(
            f"historical:{index}",
            fold_id="exploratory-2025-26",
            season="2025-26",
            gameweek=index + 1,
        )
        for index in range(4)
    ]
    report = evaluate_feature_ablation(
        rows=rows,
        preregistration=PREREGISTRATION,
        family="odds",
    )
    assert report["promotion_eligible"] is False
    assert report["decision"] == "remain_shadow_only"
    assert (
        report["promotion_checks"]["not_historical_2025_26_only"] is False
    )
    assert report["promotion_checks"]["live_season_only"] is False
    assert report["promotion_checks"]["minimum_locked_folds"] is False


def test_post_cutoff_or_non_isolated_feature_rows_fail_closed():
    row = _row("late")
    row["available_at"] = row["decision_cutoff"]
    with pytest.raises(FeatureAblationError, match="strictly pre-cutoff"):
        evaluate_feature_ablation(
            rows=[row],
            preregistration=PREREGISTRATION,
            family="odds",
        )

    row = _row("mixed")
    row["feature_families"] = ["odds", "team_strength"]
    with pytest.raises(FeatureAblationError, match="exactly"):
        evaluate_feature_ablation(
            rows=[row],
            preregistration=PREREGISTRATION,
            family="odds",
        )


def test_ablation_rows_require_immutable_source_plan_and_outcome_bindings():
    row = _row("unbound")
    row["source_snapshot_sha256"] = ""
    with pytest.raises(FeatureAblationError, match="source_snapshot_sha256"):
        evaluate_feature_ablation(
            rows=[row],
            preregistration=PREREGISTRATION,
            family="odds",
        )


def test_live_policy_binds_preregistration_and_required_scorecard_metrics():
    policy = json.loads(
        (ROOT / "control/policies/live-shadow-candidate.json").read_text(
            encoding="utf-8"
        )
    )
    assert policy["content_sha256"] == shadow_hash(policy)
    assert policy["preregistration"]["content_sha256"] == PREREGISTRATION[
        "content_sha256"
    ]
    assert policy["preregistration"]["historical_2025_26"] == (
        "exploratory_production_ineligible"
    )
    assert {
        "latency_mean",
        "latency_p95",
        "degradation_rate",
        "validation_failures",
    } <= set(policy["reporting_contract"]["operational_metrics"])
    assert {
        "current_evidence",
        "inherited_state",
        "total_evidence_trajectory",
    } <= set(policy["reporting_contract"]["causal_effects"])


def test_preseason_readiness_and_appearance_diagnostic_are_sealed():
    report_root = ROOT / "reports/forecasting/2026-27-preregistration"
    readiness = json.loads(
        (report_root / "family-readiness.json").read_text(encoding="utf-8")
    )
    diagnostic = json.loads(
        (report_root / "2025-26-appearance-diagnostic.json").read_text(
            encoding="utf-8"
        )
    )
    assert readiness["content_sha256"] == artifact_hash(readiness)
    assert diagnostic["content_sha256"] == artifact_hash(diagnostic)
    assert readiness["status"] == "preseason_no_optional_family_promoted"
    assert all(
        row["promotion_eligible"] is False
        for row in readiness["families"].values()
    )
    assert diagnostic["promotion_eligible"] is False
    assert diagnostic["model_config_sha256"] == PREREGISTRATION["baseline"][
        "model_config_sha256"
    ]