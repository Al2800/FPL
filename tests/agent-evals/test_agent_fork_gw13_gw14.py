"""Contracts for the sequential GW13/GW14 evidence experiment."""

from __future__ import annotations

import json
from pathlib import Path

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_fork_adapter import (
    build_agent_host_bundle,
    build_fork_solver_input,
    derive_gw13_state_from_gw12_agent_fork,
)


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
AGENT = ROOT / "reports/benchmarks/2025-26-agent-forks"


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    elif isinstance(value, str):
        yield value.lower()


def test_gw13_starts_from_sealed_gw12_agent_state() -> None:
    state, transition = derive_gw13_state_from_gw12_agent_fork(
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        gw12_fork_root=AGENT / "gw-12/sol-v1",
    )
    ids = {row["player_id"] for row in state["squad"]}

    assert state["gameweek"] == 13
    assert state["content_sha256"] == transition["next_state_sha256"]
    assert "player:2025-26:256" in ids
    assert "player:2025-26:5" not in ids


def test_research_is_predeadline_and_host_bundle_is_observed_only() -> None:
    state, _ = derive_gw13_state_from_gw12_agent_fork(
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        gw12_fork_root=AGENT / "gw-12/sol-v1",
    )
    solver_input = build_fork_solver_input(
        gameweek=13, state=state, canonical_root=CANONICAL
    )
    evidence = json.loads(
        (
            ROOT / "evals/evidence-forks/2025-26/gw-13/evidence-bundle.json"
        ).read_text(encoding="utf-8")
    )
    assert all(
        row["published_at"] < evidence["decision_cutoff"]
        for row in evidence["sources"]
    )
    candidate = {"schema_version": "1.0", "transfers": []}
    bundle = build_agent_host_bundle(
        gameweek=13,
        evidence_bundle_path=(
            ROOT / "evals/evidence-forks/2025-26/gw-13/evidence-bundle.json"
        ),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        solver_input=solver_input,
        deterministic_candidate=candidate,
        code_commit="a" * 40,
    )

    assert bundle["content_sha256"] == artifact_hash(bundle)
    flattened = list(_walk(bundle))
    assert "hidden_outcome" not in flattened
    assert not any("hidden-outcome:" in item for item in flattened)
    assert not any("realised" in item for item in flattened)
    assert bundle["player_baselines"]["player:2025-26:82"] == {
        "expected_minutes": 70.0,
        "start_probability": 0.912,
    }


def test_gw14_research_has_precise_senesi_suspension_before_cutoff() -> None:
    evidence = json.loads(
        (
            ROOT / "evals/evidence-forks/2025-26/gw-14/evidence-bundle.json"
        ).read_text(encoding="utf-8")
    )
    senesi = next(
        row for row in evidence["sources"] if "senesi-suspended" in row["claim_id"]
    )
    assert senesi["published_at"] == "2025-12-02T16:32:00Z"
    assert senesi["published_at"] < evidence["decision_cutoff"]
    assert senesi["confidence"] == 0.99


def test_committed_two_week_chain_is_state_bound_and_stops_before_gw15() -> None:
    gw13 = json.loads(
        (AGENT / "gw-13/sol-v1/comparison.json").read_text(encoding="utf-8")
    )
    gw14 = json.loads(
        (AGENT / "gw-14/sol-v1/comparison.json").read_text(encoding="utf-8")
    )
    adjusted = json.loads(
        (AGENT / "gw-14/sol-v1/adjusted-solver-input.json").read_text(
            encoding="utf-8"
        )
    )
    players = {row["player_id"]: row for row in adjusted["players"]}
    attribution = json.loads(
        (AGENT / "gw-14/sol-v1/same-state-attribution.json").read_text(
            encoding="utf-8"
        )
    )

    assert gw13["agent_decision"] == "degraded_fallback"
    assert gw13["agent_fork_gross_points"] == 37
    assert gw13["next_state_sha256"] == gw14["starting_state_sha256"]
    assert gw14["agent_decision"] == "applied"
    assert gw14["agent_fork_gross_points"] == 60
    assert players["player:2025-26:72"]["expected_minutes"] == 0
    assert players["player:2025-26:72"]["start_probability"] == 0
    assert players["player:2025-26:249"]["expected_minutes"] == 73.5
    assert attribution["control_gross_points"] == 61
    assert attribution["agent_gross_points"] == 60
    assert attribution["agent_evidence_delta"] == -1
    assert gw14["next_state_sha256"] is None
    assert not (AGENT / "gw-15").exists()
