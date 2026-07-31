from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.artifact_backed

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_arm import render_hosted_input
from src.orchestration.early_season_actionability import (
    build_actionability_assessment,
    enforce_actionability,
)
from src.orchestration.early_season_evidence_replay import (
    assert_reusable_baselines,
    build_early_host_bundle,
)
from src.orchestration.evidence_fork import EvidenceForkError, _read


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"
EVIDENCE = ROOT / "evals/evidence-forks/2025-26"


def _manifest() -> dict:
    return _read(EVIDENCE / "early-season-manifest.json")


def _state(gameweek: int) -> dict:
    return _read(
        CANONICAL
        / f"gw-{gameweek:02d}/setup/arms/evidence_agent/starting-policy-state.json"
    )


def _bundle(gameweek: int) -> dict:
    return build_early_host_bundle(
        gameweek=gameweek,
        early_manifest=_manifest(),
        state=_state(gameweek),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        code_commit="test-commit",
    )


def _walk_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            child
            for item in value.values()
            for child in _walk_keys(item)
        }
    if isinstance(value, list):
        return {child for item in value for child in _walk_keys(item)}
    return set()


def test_host_bundle_is_hash_bound_observed_only_and_reusable() -> None:
    bundle = _bundle(3)
    request = bundle["evidence_request"]
    assert bundle["content_sha256"] == artifact_hash(bundle)
    assert request["content_sha256"] == artifact_hash(request)
    assert request["rendered_input_sha256"] == hashlib.sha256(
        render_hosted_input(request).encode("utf-8")
    ).hexdigest()
    assert "hidden_outcome" not in _walk_keys(bundle)
    assert "realised_outcome" not in _walk_keys(bundle)
    assert bundle["actionability_assessment"]["allowed_adjustment_player_ids"] == [
        "player:2025-26:235"
    ]
    assert_reusable_baselines(
        gameweek=3,
        state=_state(3),
        host_bundle=bundle,
        canonical_root=CANONICAL,
    )


def test_actionability_gate_suppresses_context_and_ungrounded_porro() -> None:
    manifest = _manifest()
    entries = {int(row["gameweek"]): row for row in manifest["entries"]}
    gw2 = dict(entries[2])
    gw2["admitted_candidates"] = gw2["candidates"]
    gw6 = dict(entries[6])
    gw6["admitted_candidates"] = gw6["candidates"]
    assessment2 = build_actionability_assessment(gameweek=2, entry=gw2)
    assessment6 = build_actionability_assessment(gameweek=6, entry=gw6)
    assert assessment2["allowed_adjustment_player_ids"] == []
    uses = {
        row["player_id"]: row
        for row in assessment6["candidate_player_uses"]
    }
    assert uses["player:2025-26:235"]["allowed_use"] == "availability_adjustment"
    assert uses["player:2025-26:568"]["allowed_use"] == "context_only"
    assert uses["player:2025-26:568"]["grounding_passed"] is False
    assert uses["player:2025-26:568"]["reason_codes"] == [
        "insufficient_passage_grounding"
    ]


def test_context_only_or_upward_proposals_fail_completion_gate() -> None:
    context_assessment = _bundle(2)["actionability_assessment"]
    context_run = {
        "status": "completed",
        "validated_output": {
            "proposed_adjustments": [
                {
                    "player_uid": "player:2025-26:235",
                    "target": "expected_minutes",
                    "before_value": 80.0,
                    "after_value": 60.0,
                }
            ]
        },
    }
    with pytest.raises(EvidenceForkError, match="Context-only"):
        enforce_actionability(
            evidence_run=context_run,
            assessment=context_assessment,
        )

    actionable = _bundle(3)["actionability_assessment"]
    upward = {
        "status": "completed",
        "validated_output": {
            "proposed_adjustments": [
                {
                    "player_uid": "player:2025-26:235",
                    "target": "start_probability",
                    "before_value": 0.5,
                    "after_value": 0.7,
                }
            ]
        },
    }
    with pytest.raises(EvidenceForkError, match="may not increase"):
        enforce_actionability(evidence_run=upward, assessment=actionable)


def test_all_versioned_host_bundles_cover_gw2_to_gw11() -> None:
    for gameweek in range(2, 12):
        path = (
            EVIDENCE
            / f"gw-{gameweek:02d}"
            / "agent-host-bundle-v2.json"
        )
        bundle = _read(path)
        assert bundle["gameweek"] == gameweek
        assert bundle["content_sha256"] == artifact_hash(bundle)
        assert bundle["episode"]["decision_cutoff"] == bundle[
            "evidence_request"
        ]["episode"]["decision_at"]
