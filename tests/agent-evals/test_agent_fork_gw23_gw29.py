"""Contracts for the sequential GW23-GW29 evidence trajectory."""

from __future__ import annotations

import json
from pathlib import Path

from src.orchestration.agent_fork_adapter import (
    derive_next_state_from_agent_fork,
)


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"
ACCEPTED_VERSION = {
    23: "sol-v2",
    24: "sol-v1",
    25: "sol-v3",
    26: "sol-v3",
    27: "sol-v1",
    28: "sol-v1",
    29: "sol-v1",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gw23_starts_from_repaired_gw22_fork() -> None:
    expected, transition = derive_next_state_from_agent_fork(
        gameweek=22,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        fork_root=AGENT / "gw-22/sol-v3",
    )
    actual = _read(
        AGENT / "gw-23/sol-v2/starting-policy-state.json"
    )
    assert actual == expected
    assert actual["gameweek"] == 23
    assert actual["bank"] == 0.6
    assert actual["free_transfers"] == 4
    assert actual["content_sha256"] == transition["next_state_sha256"]


def test_all_research_is_strictly_predeadline() -> None:
    for gameweek in range(23, 30):
        evidence = _read(
            ROOT
            / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}"
            / "evidence-bundle.json"
        )
        assert evidence["sources"]
        assert all(
            row["published_at"] < evidence["decision_cutoff"]
            for row in evidence["sources"]
        )
        assert (
            "not_eligible_for_headline_agent_performance"
            in evidence["limitations"]
        )


def test_every_week_completes_both_agent_gates() -> None:
    for gameweek in range(23, 30):
        root = (
            AGENT
            / f"gw-{gameweek:02d}/{ACCEPTED_VERSION[gameweek]}"
        )
        evidence = _read(root / "evidence-run.json")
        challenger = _read(root / "challenger-run.json")
        audit = _read(root / "adapter-audit.json")
        proposed = {
            row["adjustment_id"]
            for row in evidence["validated_output"][
                "proposed_adjustments"
            ]
        }
        applied = {
            row["adjustment_id"] for row in audit["adjustments"]
        }
        assert evidence["status"] == "completed"
        assert challenger["status"] == "completed"
        assert proposed == applied
        if proposed:
            assert audit["applied"] is True
            assert audit["fallback_reason"] is None
        else:
            assert audit["applied"] is False
            assert audit["fallback_reason"] == "no_agent_adjustments"


def test_state_chain_is_bound_and_stops_before_gw30() -> None:
    comparisons = {
        gameweek: _read(
            AGENT
            / (
                f"gw-{gameweek:02d}/"
                f"{ACCEPTED_VERSION[gameweek]}/comparison.json"
            )
        )
        for gameweek in range(23, 30)
    }
    for gameweek in range(23, 29):
        assert (
            comparisons[gameweek]["next_state_sha256"]
            == comparisons[gameweek + 1]["starting_state_sha256"]
        )
    assert comparisons[29]["next_state_sha256"] is None
    assert not (
        AGENT
        / (
            "gw-29/"
            f"{ACCEPTED_VERSION[29]}/next-policy-state.json"
        )
    ).exists()
    assert not (AGENT / "gw-30").exists()


def test_same_state_attribution_exists_for_all_seven_weeks() -> None:
    for gameweek in range(23, 30):
        root = (
            AGENT
            / f"gw-{gameweek:02d}/{ACCEPTED_VERSION[gameweek]}"
        )
        attribution = _read(root / "same-state-attribution.json")
        comparison = _read(root / "comparison.json")
        assert (
            attribution["agent_gross_points"]
            == comparison["agent_fork_gross_points"]
        )


def test_canonical_comparison_scores_remain_expected() -> None:
    expected = {23: 41, 24: 60, 25: 58, 26: 68, 27: 43, 28: 67, 29: 53}
    for gameweek, score in expected.items():
        comparison = _read(
            AGENT
            / (
                f"gw-{gameweek:02d}/"
                f"{ACCEPTED_VERSION[gameweek]}/comparison.json"
            )
        )
        assert comparison["canonical_gross_points"] == score


def test_failed_versions_are_preserved_and_never_scored() -> None:
    gw23_v1 = ROOT / "evals/evidence-forks/2025-26/gw-23/agent-host-bundle.json"
    assert gw23_v1.exists()
    assert not (AGENT / "gw-23/sol-v1/comparison.json").exists()

    gw25_v1 = _read(AGENT / "gw-25/sol-v1/challenger-run.json")
    gw25_v2 = _read(AGENT / "gw-25/sol-v2/evidence-run.json")
    gw26_v1 = _read(AGENT / "gw-26/sol-v1/evidence-run.json")
    gw26_v2 = _read(AGENT / "gw-26/sol-v2/challenger-run.json")
    assert gw25_v1["status"] == "degraded"
    assert gw25_v2["status"] == "degraded"
    assert gw26_v1["status"] == "degraded"
    assert gw26_v2["status"] == "degraded"
    for root in (
        AGENT / "gw-25/sol-v1",
        AGENT / "gw-25/sol-v2",
        AGENT / "gw-26/sol-v1",
        AGENT / "gw-26/sol-v2",
    ):
        assert not (root / "comparison.json").exists()


def test_seven_week_score_summary_and_same_state_effect() -> None:
    comparisons = [
        _read(
            AGENT
            / (
                f"gw-{gameweek:02d}/"
                f"{ACCEPTED_VERSION[gameweek]}/comparison.json"
            )
        )
        for gameweek in range(23, 30)
    ]
    attributions = [
        _read(
            AGENT
            / (
                f"gw-{gameweek:02d}/"
                f"{ACCEPTED_VERSION[gameweek]}/"
                "same-state-attribution.json"
            )
        )
        for gameweek in range(23, 30)
    ]
    assert sum(row["agent_fork_gross_points"] for row in comparisons) == 410
    assert sum(row["canonical_gross_points"] for row in comparisons) == 390
    assert all(row["agent_evidence_delta"] == 0 for row in attributions)
