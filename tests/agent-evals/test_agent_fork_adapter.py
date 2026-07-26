"""Contracts for the deterministic GW12 agent-to-fork bridge."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.agents.evidence_agent import EvidenceAgentError
from src.agents.evidence_agent import validate_evidence_result
from src.evidence.lifecycle import load_policy
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_fork_adapter import (
    apply_agent_adjustments,
    build_gw12_agent_host_bundle,
    run_isolated_agent_fork,
    run_sequential_agent_fork_week,
)
from src.orchestration.evidence_fork import EvidenceForkError


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
EVIDENCE = ROOT / "evals/evidence-forks/2025-26/gw-12/evidence-bundle.json"
SOLVER_INPUT = (
    CANONICAL / "gw-12/setup/arms/evidence_agent/reviewed-engine-input.json"
)
AGENT_RESULT = ROOT / "reports/benchmarks/2025-26-agent-forks/gw-12/sol-v1"
MANUAL_RESULT = (
    ROOT
    / "reports/benchmarks/2025-26-forks/gw-12/retrospective-availability-v1"
)


def _seal(value: dict) -> dict:
    result = deepcopy(value)
    result["content_sha256"] = artifact_hash(result)
    return result


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


def _runs(*, blocked: bool = False) -> tuple[dict, dict]:
    proposal = _seal(
        {
            "schema_version": "1.0",
            "role": "evidence",
            "proposed_adjustments": [
                {
                    "adjustment_id": "adjust-gabriel",
                    "signal_ids": ["signal-gabriel"],
                    "target": "expected_minutes",
                    "before_value": 85.6,
                    "after_value": 0.0,
                    "confidence": 0.99,
                    "player_uid": "player:2025-26:5",
                },
                {
                    "adjustment_id": "adjust-semenyo",
                    "signal_ids": ["signal-semenyo"],
                    "target": "start_probability",
                    "before_value": 0.9821,
                    "after_value": 0.7321,
                    "confidence": 0.65,
                    "player_uid": "player:2025-26:82",
                },
            ],
        }
    )
    evidence = _seal(
        {
            "schema_version": "1.0",
            "run_id": "evidence",
            "status": "completed",
            "validated_output": proposal,
        }
    )
    review = _seal(
        {
            "schema_version": "1.0",
            "role": "challenger",
            "proposal_sha256": proposal["content_sha256"],
            "unopposed_proposed_adjustment_ids": (
                [] if blocked else ["adjust-gabriel", "adjust-semenyo"]
            ),
            "approval_gate": {
                "requires_human_review": blocked,
                "force_rerun": False,
                "confidence_downgraded": blocked,
                "unresolved_challenges": [],
            },
        }
    )
    challenger = _seal(
        {
            "schema_version": "1.0",
            "run_id": "challenger",
            "status": "completed",
            "validated_output": review,
        }
    )
    return evidence, challenger


def test_host_bundle_is_observed_only_hash_bound_and_uses_frozen_baselines() -> None:
    bundle = build_gw12_agent_host_bundle(
        evidence_bundle_path=EVIDENCE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        code_commit="a" * 40,
    )

    assert bundle["content_sha256"] == artifact_hash(bundle)
    assert bundle["player_baselines"]["player:2025-26:5"] == {
        "expected_minutes": 85.6,
        "start_probability": 0.9524,
    }
    assert bundle["player_baselines"]["player:2025-26:82"] == {
        "expected_minutes": 87.7,
        "start_probability": 0.9821,
    }
    flattened = list(_walk(bundle))
    assert "hidden_outcome" not in flattened
    assert not any("hidden-outcome:" in item for item in flattened)
    assert not any("realised" in item for item in flattened)
    assert all(
        document["content_sha256"] == artifact_hash(document)
        for document in bundle["evidence_documents"]
    )


def test_truthful_retrospective_capture_is_exploratory_not_production_eligible() -> None:
    bundle = build_gw12_agent_host_bundle(
        evidence_bundle_path=EVIDENCE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        code_commit="a" * 40,
    )
    documents = {
        row["document_id"]: row for row in bundle["evidence_documents"]
    }
    sources = json.loads(EVIDENCE.read_text(encoding="utf-8"))["sources"]
    claims = []
    adjustments = []
    targets = (
        ("expected_minutes", 85.6, 0.0),
        ("start_probability", 0.9821, 0.7321),
    )
    for source, (target, before, after) in zip(sources, targets, strict=True):
        passage = f"passage:{source['claim_id']}"
        excerpt = source["citation_excerpt"]
        claims.append(
            {
                "claim_id": source["claim_id"],
                "document_id": f"document:{source['source_id']}",
                "passage_id": passage,
                "source_id": source["source_id"],
                "claim_text": source["claim_text"],
                "citation_excerpt": excerpt,
                "citation_excerpt_sha256": hashlib.sha256(
                    excerpt.encode("utf-8")
                ).hexdigest(),
                "expires_at": source["expires_at"],
                "confidence": source["confidence"],
                "player_uid": source["player_id"],
            }
        )
        adjustments.append(
            {
                "adjustment_id": source["adjustment"]["adjustment_id"],
                "claim_ids": [source["claim_id"]],
                "target": target,
                "before_value": before,
                "after_value": after,
                "confidence": source["adjustment"]["confidence"],
                "expires_at": source["expires_at"],
                "player_uid": source["player_id"],
                "rationale": source["adjustment"]["rationale"],
            }
        )
    normalised = validate_evidence_result(
        {
            "schema_version": "1.0",
            "role": "evidence",
            "claims": claims,
            "conflicts": [],
            "proposed_adjustments": adjustments,
            "notes": [],
        },
        decision_at="2025-11-22T11:00:00Z",
        known_player_ids=set(bundle["player_baselines"]),
        policy=load_policy(),
        approved_evidence=documents,
        player_baselines=bundle["player_baselines"],
        run_observed_at="2026-07-26T12:00:00Z",
        evidence_mode="retrospective_published_before_deadline",
    )

    assert normalised["production_eligible"] is False
    assert normalised["exploratory_admissible"] is True
    assert all(
        claim["decision_eligibility"]["production_ineligibility_reasons"]
        == ["observed_at_after_decision", "available_at_after_decision"]
        for claim in normalised["claims"]
    )

    expired = deepcopy(adjustments)
    expired[0]["expires_at"] = "2025-11-22T10:59:59Z"
    with pytest.raises(EvidenceAgentError, match="adjustment is expired"):
        validate_evidence_result(
            {
                "schema_version": "1.0",
                "role": "evidence",
                "claims": claims,
                "conflicts": [],
                "proposed_adjustments": expired,
                "notes": [],
            },
            decision_at="2025-11-22T11:00:00Z",
            known_player_ids=set(bundle["player_baselines"]),
            policy=load_policy(),
            approved_evidence=documents,
            player_baselines=bundle["player_baselines"],
            run_observed_at="2026-07-26T12:00:00Z",
            evidence_mode="retrospective_published_before_deadline",
        )


def test_adapter_applies_reviewed_reductions_and_keeps_rows_coherent() -> None:
    solver_input = json.loads(SOLVER_INPUT.read_text(encoding="utf-8"))
    evidence, challenger = _runs()
    adjusted, audit = apply_agent_adjustments(
        solver_input, evidence, challenger
    )
    players = {row["player_id"]: row for row in adjusted["players"]}

    assert audit["applied"] is True
    assert players["player:2025-26:5"]["expected_minutes"] == 0
    assert players["player:2025-26:5"]["expected_points"] == 0
    assert players["player:2025-26:5"]["start_probability"] == 0
    assert players["player:2025-26:82"]["start_probability"] == 0.7321
    assert players["player:2025-26:82"]["expected_minutes"] == 65.4
    assert players["player:2025-26:82"]["expected_points"] == 4.55


def test_blocked_challenger_returns_exact_canonical_input() -> None:
    solver_input = json.loads(SOLVER_INPUT.read_text(encoding="utf-8"))
    evidence, challenger = _runs(blocked=True)
    adjusted, audit = apply_agent_adjustments(
        solver_input, evidence, challenger
    )

    assert adjusted == solver_input
    assert audit["applied"] is False
    assert audit["fallback_reason"] == "challenger_gate_blocked"


@pytest.mark.parametrize("degraded_arm", ["evidence", "challenger"])
def test_non_completed_agent_run_is_refused_before_adjustment(
    degraded_arm: str,
) -> None:
    solver_input = json.loads(SOLVER_INPUT.read_text(encoding="utf-8"))
    evidence, challenger = _runs()
    selected = evidence if degraded_arm == "evidence" else challenger
    selected["status"] = "degraded"
    selected["content_sha256"] = artifact_hash(selected)

    with pytest.raises(
        EvidenceForkError,
        match=f"{degraded_arm} run must be completed",
    ):
        apply_agent_adjustments(solver_input, evidence, challenger)


def test_tampered_completed_run_is_refused_instead_of_scored_as_fallback() -> None:
    solver_input = json.loads(SOLVER_INPUT.read_text(encoding="utf-8"))
    evidence, challenger = _runs()
    evidence["content_sha256"] = "0" * 64

    with pytest.raises(EvidenceForkError, match="evidence run hash mismatch"):
        apply_agent_adjustments(solver_input, evidence, challenger)


def test_shared_fork_runners_refuse_degraded_run_without_writing(
    tmp_path: Path,
) -> None:
    host_bundle = json.loads(
        (EVIDENCE.parent / "agent-host-bundle.json").read_text(encoding="utf-8")
    )
    evidence = json.loads(
        (AGENT_RESULT / "evidence-run.json").read_text(encoding="utf-8")
    )
    challenger = json.loads(
        (AGENT_RESULT / "challenger-run.json").read_text(encoding="utf-8")
    )
    evidence["status"] = "degraded"
    evidence["content_sha256"] = artifact_hash(evidence)
    isolated_output = tmp_path / "isolated"

    with pytest.raises(EvidenceForkError, match="evidence run must be completed"):
        run_isolated_agent_fork(
            host_bundle=host_bundle,
            evidence_run=evidence,
            challenger_run=challenger,
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            manual_fork_root=MANUAL_RESULT,
            output_root=isolated_output,
        )
    assert not isolated_output.exists()

    state = json.loads(
        (
            CANONICAL
            / "gw-12/setup/arms/evidence_agent/starting-policy-state.json"
        ).read_text(encoding="utf-8")
    )
    sequential_output = tmp_path / "sequential"
    with pytest.raises(EvidenceForkError, match="evidence run must be completed"):
        run_sequential_agent_fork_week(
            gameweek=12,
            state=state,
            host_bundle=host_bundle,
            evidence_run=evidence,
            challenger_run=challenger,
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            output_root=sequential_output,
            transition_to_next=False,
        )
    assert not sequential_output.exists()


def test_committed_sol_runs_reproduce_isolated_result_without_mutating_control(
    tmp_path: Path,
) -> None:
    comparison = run_isolated_agent_fork(
        host_bundle=json.loads(
            (EVIDENCE.parent / "agent-host-bundle.json").read_text(encoding="utf-8")
        ),
        evidence_run=json.loads(
            (AGENT_RESULT / "evidence-run.json").read_text(encoding="utf-8")
        ),
        challenger_run=json.loads(
            (AGENT_RESULT / "challenger-run.json").read_text(encoding="utf-8")
        ),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        manual_fork_root=MANUAL_RESULT,
        output_root=tmp_path / "agent-fork",
    )

    assert comparison["canonical_tree_sha256_before"] == comparison[
        "canonical_tree_sha256_after"
    ]
    assert comparison["canonical_gross_points"] == 29
    assert comparison["manual_fork_gross_points"] == 43
    assert comparison["agent_fork_gross_points"] == 43
    assert comparison["selected_transfer_names"] == [
        {
            "player_out": "Gabriel dos Santos Magalhães",
            "player_in": "Daniel Muñoz Mejía",
        }
    ]
    assert not (tmp_path / "gw-13").exists()
