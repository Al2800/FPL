"""Contracts for the sequential GW15-GW17 evidence experiment."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.orchestration.agent_fork_adapter import derive_next_state_from_agent_fork


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gw15_starts_from_actual_gw14_fork() -> None:
    state, transition = derive_next_state_from_agent_fork(
        gameweek=14,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        fork_root=AGENT / "gw-14/sol-v1",
    )
    ids = {row["player_id"] for row in state["squad"]}

    assert state["gameweek"] == 15
    assert state["bank"] == 0.8
    assert state["free_transfers"] == 3
    assert state["content_sha256"] == transition["next_state_sha256"]
    assert "player:2025-26:430" in ids
    assert "player:2025-26:381" not in ids


def test_all_research_is_strictly_predeadline() -> None:
    for gameweek in (15, 16, 17):
        evidence = _read(
            ROOT
            / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/evidence-bundle.json"
        )
        assert evidence["sources"]
        assert all(
            row["published_at"] < evidence["decision_cutoff"]
            for row in evidence["sources"]
        )


def test_gw16_evidence_is_precise_and_gw17_excludes_late_news() -> None:
    gw16 = _read(
        ROOT / "evals/evidence-forks/2025-26/gw-16/evidence-bundle.json"
    )
    munoz = gw16["sources"][0]
    gw17 = _read(
        ROOT / "evals/evidence-forks/2025-26/gw-17/evidence-bundle.json"
    )

    assert munoz["published_at"] == "2025-12-12T09:16:20Z"
    assert munoz["confidence"] == 0.99
    assert gw17["sources"][0]["player_id"] == "player:2025-26:119"
    assert any("post_cutoff" in item for item in gw17["limitations"])


def test_committed_chain_uses_topup_and_stops_before_gw18() -> None:
    gw15 = _read(AGENT / "gw-15/sol-v1/comparison.json")
    gw16 = _read(AGENT / "gw-16/sol-v1/comparison.json")
    gw17 = _read(AGENT / "gw-17/sol-v1/comparison.json")
    state16 = _read(AGENT / "gw-15/sol-v1/next-policy-state.json")
    transition16 = _read(AGENT / "gw-15/sol-v1/state-transition.json")
    rules15 = yaml.safe_load(
        (EPISODES / "gw-15/ruleset.yaml").read_text(encoding="utf-8")
    )
    topup = next(
        row
        for row in rules15["transfers"]
        if row["rule_id"] == "transfers.afcon_exceptional_topup"
    )

    assert gw15["next_state_sha256"] == gw16["starting_state_sha256"]
    assert gw16["next_state_sha256"] == gw17["starting_state_sha256"]
    assert state16["free_transfers"] == 5
    assert topup["value"] == {"gameweek": 16, "top_up_to": 5}
    assert transition16["next_state_sha256"] == state16["content_sha256"]
    assert gw17["next_state_sha256"] is None
    assert not (AGENT / "gw-17/sol-v1/next-policy-state.json").exists()
    assert not (AGENT / "gw-18").exists()


def test_same_state_attribution_exists_for_each_week() -> None:
    for gameweek in (15, 16, 17):
        attribution = _read(
            AGENT
            / f"gw-{gameweek:02d}/sol-v1/same-state-attribution.json"
        )
        comparison = _read(
            AGENT / f"gw-{gameweek:02d}/sol-v1/comparison.json"
        )
        assert attribution["agent_gross_points"] == comparison[
            "agent_fork_gross_points"
        ]
