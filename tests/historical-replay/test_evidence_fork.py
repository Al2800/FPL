from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.canonical_tree_hash import canonical_tree_hash
from src.orchestration.evidence_fork import (
    EvidenceForkError,
    _canonical_span_hash,
    run_isolated_evidence_fork,
    validate_reconstructed_bundle,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "evals/evidence-forks/2025-26/gw-12/evidence-bundle.json"
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
FORK = (
    ROOT
    / "reports/benchmarks/2025-26-forks/gw-12"
    / "retrospective-availability-v1"
)


def _tree_hash(path: Path) -> str:
    digest, _count = canonical_tree_hash(path)
    return digest


def test_reconstructed_bundle_rejects_post_deadline_publication() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    invalid = deepcopy(bundle)
    invalid["sources"][0]["published_at"] = "2025-11-22T11:00:01Z"

    with pytest.raises(EvidenceForkError, match="published after decision cutoff"):
        validate_reconstructed_bundle(invalid)


@pytest.mark.artifact_backed
def test_isolated_gw12_fork_is_deterministic_and_preserves_control(tmp_path: Path) -> None:
    canonical_before = _tree_hash(CANONICAL / "gw-12")
    output = tmp_path / "fork"

    first = run_isolated_evidence_fork(
        season="2025-26",
        gameweek=12,
        evidence_bundle_path=BUNDLE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=output,
    )
    first_hash = _tree_hash(output)
    second = run_isolated_evidence_fork(
        season="2025-26",
        gameweek=12,
        evidence_bundle_path=BUNDLE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=output,
    )

    assert first == second
    assert _tree_hash(output) == first_hash
    assert _tree_hash(CANONICAL / "gw-12") == canonical_before
    assert first["canonical_gross_points"] == 29
    assert first["fork_gross_points"] == 43
    assert first["gross_points_delta"] == 14
    assert first["selected_transfer_names"] == [
        {
            "player_out": "Gabriel dos Santos Magalhães",
            "player_in": "Daniel Muñoz Mejía",
        }
    ]
    assert first["active_chip"] is None
    assert first["hit_cost"] == 0
    assert first["exploratory_only"] is True
    assert not (output / "gw-13").exists()

    plan = json.loads((output / "validated-plan.json").read_text(encoding="utf-8"))
    outcome = json.loads((output / "realised-outcome.json").read_text(encoding="utf-8"))
    assessment = json.loads(
        (output / "evidence-assessment.json").read_text(encoding="utf-8")
    )
    assert plan["frozen_at"] == "2025-11-22T11:00:00Z"
    assert outcome["plan_sha256"] == plan["content_sha256"]
    assert assessment["production_eligible"] is False
    assert assessment["exploratory_admissible"] is True


def test_committed_ceiling_review_separates_feasible_opportunity() -> None:
    review = json.loads(
        (FORK / "score-ceilings.json").read_text(encoding="utf-8")
    )
    assert review["content_sha256"] == artifact_hash(review)
    assert review["diagnostic_only"] is True
    assert review["outcome_information_used"] is True
    assert review["actual_selected_plan"] == {
        "canonical_gross_points": 29,
        "fork_gross_points": 43,
    }
    assert review["fixed_effective_lineup_captain_ceiling"][
        "canonical_gross_points"
    ] == 33
    assert review["fixed_effective_lineup_captain_ceiling"][
        "fork_gross_points"
    ] == 55
    assert review["current_squad_xi_and_captain_ceiling"]["gross_points"] == 37
    assert review["post_decision_squad_xi_and_captain_ceiling"][
        "fork_gross_points"
    ] == 58
    assert review["bounded_legal_market_opportunity"]["gross_points"] == 99
    assert "legal under budget" in review["bounded_legal_market_opportunity"][
        "feasibility"
    ]
    assert review["whole_market_position_only_upper_bound"]["gross_points"] == 173
    assert "not a selectable FPL squad" in review[
        "whole_market_position_only_upper_bound"
    ]["feasibility"]


def test_committed_longitudinal_fork_is_independent_and_preserves_control() -> None:
    report = json.loads(
        (FORK / "longitudinal.json").read_text(encoding="utf-8")
    )
    assert report["content_sha256"] == artifact_hash(report)
    assert report["comparison_type"] == (
        "retrospective_longitudinal_independent_state"
    )
    assert report["exploratory_only"] is True
    assert report["promotion_eligible"] is False
    assert report["canonical_net_points"] == 1457
    assert report["fork_net_points"] == 1461
    assert report["net_points_delta"] == 4
    assert report["terminal_cumulative_points"] == 2014
    assert [row["gameweek"] for row in report["fork_weeks"]] == list(
        range(12, 39)
    )
    assert [
        row["gameweek"]
        for row in report["fork_weeks"]
        if row["evidence_applied"]
    ] == [12]
    assert report["fork_weeks"][0]["plan_sha256"] == json.loads(
        (FORK / "validated-plan.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert report["canonical_artifacts"]["unchanged"] is True
    tree_hash, file_count = _canonical_span_hash(
        CANONICAL, start_gameweek=12, end_gameweek=38
    )
    assert tree_hash == report["canonical_artifacts"]["tree_sha256_before"]
    assert tree_hash == report["canonical_artifacts"]["tree_sha256_after"]
    assert file_count == report["canonical_artifacts"]["file_count"]
