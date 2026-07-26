"""Contracts for the sequential GW18-GW22 evidence experiment."""

from __future__ import annotations

import json
from pathlib import Path

from src.orchestration.agent_fork_adapter import (
    _tree_hash,
    derive_next_state_from_agent_fork,
)


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"
SOL_V1_TREE_HASHES = {
    20: "9695b3d0db4943b1283fc42700986c6c23e22f0072ac4de98ae21560584f9551",
    21: "f21d8c6ecba010741ebb1819adbe2cdcb92691d649b4bce42204d32e634d44e6",
    22: "5d1215207ac4c66c3a2265ca4d80fe54db4af1b26cc5e99546081c70d2202d8e",
}
SOL_V2_PARTIAL_TREE_HASHES = {
    20: "479b5abfa2edbbdf7c1fbdea8fd0af390744c58427e31c58917d52f722448600",
    21: "6ad50af80ffe3a5fea522b6bdd356539d7345c19a39558ec1dccd24553078a4f",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gw18_starts_from_actual_gw17_fork() -> None:
    state, transition = derive_next_state_from_agent_fork(
        gameweek=17, canonical_root=CANONICAL, episode_root=EPISODES,
        fork_root=AGENT / "gw-17/sol-v1",
    )
    ids = {row["player_id"] for row in state["squad"]}
    assert state["gameweek"] == 18
    assert state["bank"] == 1.4
    assert state["free_transfers"] == 4
    assert state["content_sha256"] == transition["next_state_sha256"]
    assert "player:2025-26:414" in ids
    assert "player:2025-26:119" not in ids


def test_all_research_is_strictly_predeadline() -> None:
    for gameweek in range(18, 23):
        evidence = _read(ROOT / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/evidence-bundle.json")
        assert evidence["sources"]
        assert all(row["published_at"] < evidence["decision_cutoff"] for row in evidence["sources"])


def test_committed_sol_v1_chain_is_bound_and_stops_before_gw23() -> None:
    comparisons = {
        gw: _read(AGENT / f"gw-{gw:02d}/sol-v1/comparison.json")
        for gw in range(18, 23)
    }
    for gw in range(18, 22):
        assert comparisons[gw]["next_state_sha256"] == comparisons[gw + 1]["starting_state_sha256"]
    assert comparisons[22]["next_state_sha256"] is None
    assert not (AGENT / "gw-22/sol-v1/next-policy-state.json").exists()
    assert not (AGENT / "gw-23/sol-v1").exists()


def test_same_state_attribution_exists_for_all_five_weeks() -> None:
    for gameweek in range(18, 23):
        attribution = _read(AGENT / f"gw-{gameweek:02d}/sol-v1/same-state-attribution.json")
        comparison = _read(AGENT / f"gw-{gameweek:02d}/sol-v1/comparison.json")
        assert attribution["agent_gross_points"] == comparison["agent_fork_gross_points"]


def test_degraded_sol_v1_archive_remains_byte_identical() -> None:
    for gameweek, expected_hash in SOL_V1_TREE_HASHES.items():
        assert (
            _tree_hash(AGENT / f"gw-{gameweek:02d}/sol-v1")
            == expected_hash
        )


def test_partial_sol_v2_diagnostic_archive_remains_byte_identical() -> None:
    for gameweek, expected_hash in SOL_V2_PARTIAL_TREE_HASHES.items():
        assert (
            _tree_hash(AGENT / f"gw-{gameweek:02d}/sol-v2")
            == expected_hash
        )


def test_sol_v3_repair_completes_every_agent_gate() -> None:
    for gameweek in range(20, 23):
        root = AGENT / f"gw-{gameweek:02d}/sol-v3"
        evidence = _read(root / "evidence-run.json")
        challenger = _read(root / "challenger-run.json")
        audit = _read(root / "adapter-audit.json")
        proposed = {
            row["adjustment_id"]
            for row in evidence["validated_output"]["proposed_adjustments"]
        }
        applied = {row["adjustment_id"] for row in audit["adjustments"]}

        assert evidence["status"] == "completed"
        assert challenger["status"] == "completed"
        assert audit["applied"] is True
        assert audit["fallback_reason"] is None
        assert proposed == applied


def test_sol_v3_uses_the_same_gw20_start_and_chains_to_gw22() -> None:
    v1_start = _read(AGENT / "gw-20/sol-v1/starting-policy-state.json")
    v3_start = _read(AGENT / "gw-20/sol-v3/starting-policy-state.json")
    comparisons = {
        gw: _read(AGENT / f"gw-{gw:02d}/sol-v3/comparison.json")
        for gw in range(20, 23)
    }

    assert v3_start["content_sha256"] == v1_start["content_sha256"]
    assert (
        comparisons[20]["next_state_sha256"]
        == comparisons[21]["starting_state_sha256"]
    )
    assert (
        comparisons[21]["next_state_sha256"]
        == comparisons[22]["starting_state_sha256"]
    )
    assert comparisons[22]["next_state_sha256"] is None
    assert not (AGENT / "gw-22/sol-v3/next-policy-state.json").exists()
