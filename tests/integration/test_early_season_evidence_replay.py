from __future__ import annotations

from pathlib import Path

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.evidence_fork import _read


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "reports/benchmarks/2025-26-early-evidence"
EVAL_ROOT = ROOT / "evals/evidence-forks/2025-26"


def test_full_early_replay_is_sealed_complete_and_canonical_safe() -> None:
    summary = _read(REPORT_ROOT / "early-season-summary.json")
    assert summary["content_sha256"] == artifact_hash(summary)
    assert summary == _read(EVAL_ROOT / "early-season-summary.json")
    assert [row["gameweek"] for row in summary["isolated_weeks"]] == list(
        range(2, 12)
    )
    assert [row["gameweek"] for row in summary["longitudinal_weeks"]] == list(
        range(2, 12)
    )
    assert summary["protocol_metrics"] == {
        "week_count": 10,
        "evidence_completed": 10,
        "challenger_completed": 10,
        "evidence_adjustment_weeks": 5,
        "evidence_abstention_weeks": 5,
    }
    canonical = summary["canonical_artifacts"]
    assert canonical["unchanged"] is True
    assert canonical["tree_sha256_before"] == canonical["tree_sha256_after"]


def test_replay_attributes_the_negative_result_to_gw7() -> None:
    summary = _read(REPORT_ROOT / "early-season-summary.json")
    isolated = {row["gameweek"]: row for row in summary["isolated_weeks"]}
    assert summary["frozen_no_evidence_shadow"]["net_points"] == 497
    assert summary["longitudinal_net_points"] == 490
    assert isolated[7]["agent_decision"] == "applied"
    assert isolated[7]["same_state_attribution"]["agent_evidence_delta"] == -8
    assert isolated[9]["agent_decision"] == "applied"
    assert isolated[9]["same_state_attribution"]["agent_evidence_delta"] == 0
    assert {
        gameweek
        for gameweek, row in isolated.items()
        if row["agent_decision"] == "degraded_fallback"
    } == {3, 4, 6}


def test_gw12_bridge_is_comparison_only_and_html_reports_result() -> None:
    summary = _read(REPORT_ROOT / "early-season-summary.json")
    bridge = summary["gw12_bridge"]
    assert bridge["states_equal"] is False
    assert bridge["cumulative_points_delta"] == -7
    assert bridge["fork_free_transfers"] == bridge["canonical_free_transfers"]
    assert len(bridge["squad_symmetric_difference"]) == 6
    html = (
        ROOT / "reports/benchmarks/2025-26/evidence-early-season.html"
    ).read_text(encoding="utf-8")
    assert "GW7 is the causal event" in html
    assert "was not spliced into the accepted" in html
    assert summary["content_sha256"] in html
