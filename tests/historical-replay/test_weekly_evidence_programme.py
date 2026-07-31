from copy import deepcopy
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.artifact_backed

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.weekly_evidence_programme import (
    WeeklyEvidenceProgrammeError,
    run_weekly_evidence_programme,
    write_weekly_evidence_report,
)


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
BUNDLE = ROOT / "evals/evidence-forks/2025-26/gw-12/evidence-bundle.json"
REPORT = (
    ROOT
    / "reports/benchmarks/2025-26-evidence-programme/evaluation.json"
)
ONE_OFF = (
    ROOT
    / "reports/benchmarks/2025-26-forks/gw-12"
    / "retrospective-availability-v1"
)


def test_programme_rejects_post_deadline_bundle_before_replay(
    tmp_path: Path,
) -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    bundle["sources"][0]["published_at"] = "2025-11-22T11:00:01Z"
    invalid = tmp_path / "post-deadline.json"
    invalid.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(
        WeeklyEvidenceProgrammeError,
        match="published after decision cutoff",
    ):
        run_weekly_evidence_programme(
            season="2025-26",
            bundle_paths={12: invalid},
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            terminal_gameweek=12,
        )


def test_short_programme_separates_isolated_and_compounded_state(
    tmp_path: Path,
) -> None:
    report = run_weekly_evidence_programme(
        season="2025-26",
        bundle_paths={12: BUNDLE},
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        terminal_gameweek=13,
    )
    assert report["content_sha256"] == artifact_hash(report)
    assert report["selected_evidence_gameweeks"] == [12]
    assert report["production_eligible"] is False
    assert report["promotion_eligible"] is False
    assert len(report["isolated_results"]) == 1
    isolated = report["isolated_results"][0]
    assert isolated["comparison_type"] == "isolated_same_starting_state"
    assert isolated["state_advanced"] is False
    assert isolated["net_points_delta"] == 14
    assert isolated["evidence"]["claims"][0]["expires_at"]
    assert isolated["evidence"]["claims"][0]["claim_confidence"] > 0
    assert isolated["evidence"]["claims"][0]["citation_excerpt_sha256"]

    weeks = report["longitudinal"]["weeks"]
    assert [row["gameweek"] for row in weeks] == [12, 13]
    assert [row["evidence_applied"] for row in weeks] == [True, False]
    assert weeks[1]["starting_state_sha256"] == weeks[0]["next_state_sha256"]
    assert report["attribution"]["isolated_direct_net_points_delta"] == 14
    assert report["attribution"]["state_compounding_net_points_delta"] == (
        report["attribution"]["longitudinal_net_points_delta"] - 14
    )
    assert report["canonical_artifacts"]["unchanged"] is True

    output = tmp_path / "evaluation.json"
    write_weekly_evidence_report(output, report)
    write_weekly_evidence_report(output, report)
    tampered = deepcopy(report)
    tampered["attribution"]["longitudinal_net_points_delta"] += 1
    tampered["content_sha256"] = artifact_hash(tampered)
    with pytest.raises(
        WeeklyEvidenceProgrammeError,
        match="refusing to overwrite",
    ):
        write_weekly_evidence_report(output, tampered)


def test_committed_full_programme_reports_direct_and_compounded_value() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["content_sha256"] == artifact_hash(report)
    assert report["selected_evidence_gameweeks"] == [12]
    assert report["attribution"] == {
        "isolated_direct_net_points_delta": 14,
        "longitudinal_net_points_delta": 4,
        "state_compounding_net_points_delta": -10,
        "interpretation": report["attribution"]["interpretation"],
    }
    assert report["longitudinal"]["terminal_cumulative_points"] == 2014
    assert len(report["longitudinal"]["weeks"]) == 27
    assert report["canonical_artifacts"]["unchanged"] is True
    assert report["isolated_results"][0]["fork_plan_sha256"] == json.loads(
        (ONE_OFF / "validated-plan.json").read_text(encoding="utf-8")
    )["content_sha256"]
    one_off = json.loads(
        (ONE_OFF / "longitudinal.json").read_text(encoding="utf-8")
    )
    assert [
        row["plan_sha256"] for row in report["longitudinal"]["weeks"]
    ] == [row["plan_sha256"] for row in one_off["fork_weeks"]]
