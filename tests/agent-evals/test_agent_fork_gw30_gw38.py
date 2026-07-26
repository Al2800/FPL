"""Contracts for the completed GW30-GW38 evidence trajectory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_gw30_gw38_agent_forks import _complete_week
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_fork_adapter import (
    derive_next_state_from_agent_fork,
)


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"
ACCEPTED_VERSION = {
    30: "sol-v5",
    31: "sol-v3",
    32: "sol-v1",
    33: "sol-v3",
    34: "sol-v1",
    35: "sol-v1",
    36: "sol-v1",
    37: "sol-v1",
    38: "sol-v1",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _accepted_root(gameweek: int) -> Path:
    return (
        AGENT
        / f"gw-{gameweek:02d}"
        / ACCEPTED_VERSION[gameweek]
    )


def test_gw30_starts_from_legal_gw29_successor() -> None:
    expected, transition = derive_next_state_from_agent_fork(
        gameweek=29,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        fork_root=AGENT / "gw-29/sol-v1",
    )
    actual = _read(_accepted_root(30) / "starting-policy-state.json")
    assert actual == expected
    assert actual["gameweek"] == 30
    assert actual["bank"] == 0.4
    assert actual["free_transfers"] == 5
    assert actual["content_sha256"] == transition["next_state_sha256"]


def test_all_research_is_strictly_predeadline() -> None:
    for gameweek in range(30, 39):
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


def test_every_accepted_week_completed_both_gates() -> None:
    for gameweek in range(30, 39):
        root = _accepted_root(gameweek)
        evidence = _read(root / "evidence-run.json")
        challenger = _read(root / "challenger-run.json")
        audit = _read(root / "adapter-audit.json")
        proposed = {
            row["adjustment_id"]
            for row in evidence["validated_output"][
                "proposed_adjustments"
            ]
        }
        applied = {row["adjustment_id"] for row in audit["adjustments"]}
        assert evidence["status"] == "completed"
        assert challenger["status"] == "completed"
        assert proposed == applied


def test_state_hashes_chain_to_explicit_terminal_state() -> None:
    comparisons = {
        gameweek: _read(_accepted_root(gameweek) / "comparison.json")
        for gameweek in range(30, 39)
    }
    for gameweek in range(30, 38):
        assert (
            comparisons[gameweek]["next_state_sha256"]
            == comparisons[gameweek + 1]["starting_state_sha256"]
        )
    terminal = _read(_accepted_root(38) / "terminal-season-state.json")
    assert comparisons[38]["next_state_sha256"] is None
    assert terminal["next_state_sha256"] is None
    assert terminal["next_gameweek"] is None
    assert terminal["comparison_sha256"] == comparisons[38][
        "content_sha256"
    ]
    assert terminal["content_sha256"] == artifact_hash(terminal)
    assert not (_accepted_root(38) / "next-policy-state.json").exists()
    assert not (AGENT / "gw-39").exists()


def test_final_block_scores_and_attribution() -> None:
    comparisons = [
        _read(_accepted_root(gameweek) / "comparison.json")
        for gameweek in range(30, 39)
    ]
    attributions = [
        _read(_accepted_root(gameweek) / "same-state-attribution.json")
        for gameweek in range(30, 39)
    ]
    assert sum(row["agent_fork_gross_points"] for row in comparisons) == 558
    assert sum(row["canonical_gross_points"] for row in comparisons) == 509
    assert sum(row["hit_cost"] for row in comparisons) == 8
    assert all(row["agent_evidence_delta"] == 0 for row in attributions)


def test_known_failures_are_preserved_and_completion_gate_is_hard() -> None:
    failed = {
        (30, "sol-v1", "evidence-run.json"),
        (30, "sol-v2", "evidence-run.json"),
        (30, "sol-v3", "evidence-run.json"),
        (30, "sol-v4", "evidence-run.json"),
        (31, "sol-v1", "evidence-run.json"),
        (31, "sol-v2", "challenger-run.json"),
        (33, "sol-v1", "evidence-run.json"),
        (33, "sol-v2", "challenger-run.json"),
    }
    for gameweek, version, name in failed:
        run = _read(AGENT / f"gw-{gameweek:02d}/{version}/{name}")
        assert run["status"] == "degraded"

    with pytest.raises(
        RuntimeError,
        match="Refusing to score a non-completed challenger gate",
    ):
        _complete_week(33, "sol-v2", "sol-v1")


def test_canonical_scores_and_trees_remain_expected() -> None:
    expected = {
        30: 45,
        31: 63,
        32: 53,
        33: 79,
        34: 36,
        35: 44,
        36: 89,
        37: 70,
        38: 30,
    }
    for gameweek, score in expected.items():
        comparison = _read(
            _accepted_root(gameweek) / "comparison.json"
        )
        assert comparison["canonical_gross_points"] == score
        assert (
            comparison["canonical_tree_sha256_before"]
            == comparison["canonical_tree_sha256_after"]
        )
