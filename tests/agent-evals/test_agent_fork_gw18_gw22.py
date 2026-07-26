"""Contracts for the sequential GW18-GW22 evidence experiment."""

from __future__ import annotations

import json
from pathlib import Path

from src.orchestration.agent_fork_adapter import derive_next_state_from_agent_fork


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"


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


def test_committed_chain_is_bound_and_stops_before_gw23() -> None:
    comparisons = {
        gw: _read(AGENT / f"gw-{gw:02d}/sol-v1/comparison.json")
        for gw in range(18, 23)
    }
    for gw in range(18, 22):
        assert comparisons[gw]["next_state_sha256"] == comparisons[gw + 1]["starting_state_sha256"]
    assert comparisons[22]["next_state_sha256"] is None
    assert not (AGENT / "gw-22/sol-v1/next-policy-state.json").exists()
    assert not (AGENT / "gw-23").exists()


def test_same_state_attribution_exists_for_all_five_weeks() -> None:
    for gameweek in range(18, 23):
        attribution = _read(AGENT / f"gw-{gameweek:02d}/sol-v1/same-state-attribution.json")
        comparison = _read(AGENT / f"gw-{gameweek:02d}/sol-v1/comparison.json")
        assert attribution["agent_gross_points"] == comparison["agent_fork_gross_points"]
