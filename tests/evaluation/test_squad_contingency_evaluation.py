"""Contracts for W10's paired squad-contingency evaluation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.artifact_backed

from src.evaluation.squad_contingency import (
    build_contingency_report,
    evaluate_sealed_forks,
    paired_decision_hash,
    paired_decision_row,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]


def _plan(*, bench: list[str], plan_hash: str) -> dict:
    return {
        "content_sha256": plan_hash,
        "transfers": [],
        "finance": {"hit_cost": 0, "transfer_count": 0},
        "lineup": {
            "starting_xi_ids": [f"p{index}" for index in range(1, 12)],
            "bench_ids": bench,
            "captain_id": "p1",
            "vice_captain_id": "p2",
        },
        "validation": {"status": "passed"},
    }


def _outcome(*, outcome_hash: str, gross: int, sub_points: int) -> dict:
    return {
        "content_sha256": outcome_hash,
        "gross_points": gross,
        "substitutions": [
            {"player_out_id": "p3", "player_in_id": "b1"}
        ],
        "aggregated_players": [
            {"player_id": "b1", "total_points": sub_points}
        ],
        "captain": {"source": "captain"},
    }


def test_paired_row_reports_bench_and_realised_value_without_relabelling() -> None:
    control = _plan(bench=["g2", "b1", "b2", "b3"], plan_hash="a" * 64)
    challenger = _plan(
        bench=["g2", "b2", "b1", "b3"],
        plan_hash="b" * 64,
    )
    row = paired_decision_row(
        scope="test",
        gameweek=2,
        episode_id="episode",
        control_plan=control,
        control_outcome=_outcome(
            outcome_hash="c" * 64, gross=50, sub_points=2
        ),
        challenger_plan=challenger,
        challenger_outcome=_outcome(
            outcome_hash="d" * 64, gross=53, sub_points=5
        ),
        observed_sha256="e" * 64,
        hidden_outcome_sha256="f" * 64,
        ruleset_sha256_value="1" * 64,
        challenger_wall_ms=12.5,
    )

    assert row["decision_changes"]["bench_order"] is True
    assert row["delta_challenger_minus_control"]["net_points"] == 3
    assert (
        row["delta_challenger_minus_control"][
            "automatic_substitution_points"
        ]
        == 3
    )
    assert row["validation"]["challenger"] == "passed"

    changed_latency = deepcopy(row)
    changed_latency["challenger"]["wall_ms"] = 999.0
    assert paired_decision_hash([row]) == paired_decision_hash([changed_latency])


def test_single_sealed_fork_is_same_state_valid_and_non_mutating() -> None:
    reports = ROOT / "reports/benchmarks/2025-26"
    episodes = ROOT / "data/benchmark-v0/episodes/v1/2025-26"
    protected = [
        reports
        / "gw-02/setup/arms/forecast_optimizer/reviewed-engine-input.json",
        reports / "gw-02/forecast_optimizer/validated-plan.json",
        episodes / "gw-02/hidden-outcome.json",
    ]
    if not all(path.exists() for path in protected):
        pytest.skip("sealed benchmark episodes absent")
    before = {path: path.read_bytes() for path in protected}
    calibration = json.loads(
        (
            ROOT / "control/models/appearance-distribution-v1.json"
        ).read_text(encoding="utf-8")
    )

    result = evaluate_sealed_forks(
        reports_root=reports,
        episodes_root=episodes,
        calibration=calibration,
        rules_path=ROOT / "control/rules/2025-26.yaml",
        gameweeks=(2,),
    )

    assert result["summary"]["all_plans_valid"] is True
    assert len(result["decision_sha256"]) == 64
    assert result["rows"][0]["transfer_search"] == (
        "held_constant_at_zero_for_both_arms"
    )
    assert result["rows"][0]["control"]["transfers"] == 0
    assert result["rows"][0]["challenger"]["transfers"] == 0
    assert {path: path.read_bytes() for path in protected} == before


def test_report_keeps_owner_gate_and_production_default_unchanged() -> None:
    calibration = json.loads(
        (
            ROOT / "control/models/appearance-distribution-v1.json"
        ).read_text(encoding="utf-8")
    )
    summary = {
        "pairs": 1,
        "decision_change_weeks": 1,
        "net_points_delta": 2,
        "all_plans_valid": True,
    }
    locked = {"scope": "locked", "summary": deepcopy(summary), "rows": []}
    descriptive = {
        "scope": "descriptive",
        "summary": deepcopy(summary),
        "rows": [],
    }

    report = build_contingency_report(
        calibration=calibration,
        locked=locked,
        descriptive=descriptive,
    )

    assert report["evidence_gate_passed"] is True
    assert report["promotion_gates"]["production_owner_approval"] is False
    assert report["promotion_eligible"] is False
    assert report["policy"]["production_default_changed"] is False
    assert report["decision"] == "eligible_for_owner_review"
    assert report["content_sha256"] == artifact_hash(report)

def test_committed_report_rejects_v1_and_preserves_production() -> None:
    report = json.loads(
        (ROOT / "reports/evaluation/squad-contingency-v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["decision"] == "reject_or_defer"
    assert report["evidence_gate_passed"] is False
    assert report["locked_2024_25"]["summary"]["net_points_delta"] == -10
    assert report["descriptive_2025_26"]["summary"]["net_points_delta"] == 22
    assert report["locked_2024_25"]["summary"]["all_plans_valid"] is True
    assert report["descriptive_2025_26"]["summary"]["all_plans_valid"] is True
    assert len(report["locked_2024_25"]["decision_sha256"]) == 64
    assert len(report["descriptive_2025_26"]["decision_sha256"]) == 64
    assert report["policy"]["production_default_before"] == "none"
    assert report["policy"]["production_default_changed"] is False
    assert report["promotion_eligible"] is False