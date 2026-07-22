"""Contract tests for benchmark information parity and outcome isolation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "control" / "schemas" / "benchmark"
SHA = "a" * 64
ARMS = [
    "naive_baseline",
    "forecast_optimizer",
    "evidence_agent",
    "evidence_challenger",
    "human_decision",
]


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _validate(name: str, record: dict) -> None:
    Draft202012Validator(
        _schema(name), format_checker=FormatChecker()
    ).validate(record)


def _episode() -> dict:
    ref = {"artifact_id": "artifact-1", "content_sha256": SHA}
    return {
        "schema_version": "1.0",
        "episode_id": "2026-27:gw01:manager-1",
        "season": "2026-27",
        "gameweek": 1,
        "mode": "live_shadow",
        "cutoff": "2026-08-14T12:00:00Z",
        "deadline": "2026-08-15T12:30:00Z",
        "created_at": "2026-08-14T12:01:00Z",
        "code_commit": SHA,
        "ruleset": {"ruleset_id": "2026-27-v1", "content_sha256": SHA},
        "observed": {
            "snapshot_ids": ["bootstrap-1", "fixtures-1"],
            "source_artifacts": [
                {
                    "source_id": "fpl-bootstrap",
                    "artifact_id": "bootstrap-1",
                    "content_sha256": SHA,
                    "available_at": "2026-08-14T11:59:00Z",
                }
            ],
            "manager_state_ref": ref,
            "feature_snapshot_ref": ref,
            "forecast_uncertainty_ref": ref,
        },
        "allowed_tools": [
            {"tool_id": "projection-query", "version": "1.0", "access": "read_only"}
        ],
        "resource_budget": {
            "wall_clock_seconds": 120,
            "tool_calls": 20,
            "tokens": 10000,
            "cost_currency": "GBP",
            "cost_cap": 1.0,
        },
        "policy_arms": list(ARMS),
        "hidden_outcome_ref": {
            "outcome_id": "outcome-gw01",
            "content_sha256": SHA,
            "reveal_after": "proposal_frozen",
        },
    }


def _result() -> dict:
    ref = {"artifact_id": "artifact-1", "content_sha256": SHA}
    usage = {
        "wall_clock_seconds": 10,
        "tool_calls": 3,
        "tokens": 0,
        "cost_currency": "GBP",
        "cost": 0,
    }
    return {
        "schema_version": "1.0",
        "episode_id": "2026-27:gw01:manager-1",
        "run_id": "run-naive-1",
        "policy_arm": "naive_baseline",
        "execution_status": "completed",
        "observed_episode_sha256": SHA,
        "started_at": "2026-08-14T12:02:00Z",
        "completed_at": "2026-08-14T12:02:10Z",
        "versions": {
            "code_commit": SHA,
            "ruleset_id": "2026-27-v1",
            "policy_version": "1.0",
            "tool_versions": {},
        },
        "budget": {"limit": usage, "used": usage},
        "trace_ref": ref,
        "proposal": {
            "proposal_id": "proposal-1",
            "gdr_ref": ref,
            "content_sha256": SHA,
            "validation": {"status": "passed", "rule_validation_ref": ref},
            "frozen_at": "2026-08-14T12:02:10Z",
        },
        "outcome_access": "sealed_until_proposal_frozen",
    }


def _assert_temporal_semantics(episode: dict) -> None:
    cutoff = datetime.fromisoformat(episode["cutoff"].replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(episode["deadline"].replace("Z", "+00:00"))
    assert cutoff <= deadline
    for artifact in episode["observed"]["source_artifacts"]:
        available = datetime.fromisoformat(artifact["available_at"].replace("Z", "+00:00"))
        assert available <= cutoff


def test_valid_episode_and_policy_result_contracts() -> None:
    episode = _episode()
    _validate("episode-manifest.json", episode)
    _assert_temporal_semantics(episode)
    _validate("policy-result.json", _result())


def test_episode_requires_exact_fixed_arm_set() -> None:
    episode = _episode()
    episode["policy_arms"].remove("human_decision")
    with pytest.raises(ValidationError):
        _validate("episode-manifest.json", episode)


def test_hidden_outcome_is_reference_only() -> None:
    episode = _episode()
    episode["hidden_outcome_ref"]["realised_points"] = 72
    with pytest.raises(ValidationError):
        _validate("episode-manifest.json", episode)


def test_observed_artifact_after_cutoff_is_rejected_semantically() -> None:
    episode = _episode()
    episode["observed"]["source_artifacts"][0]["available_at"] = "2026-08-14T12:00:01Z"
    _validate("episode-manifest.json", episode)
    with pytest.raises(AssertionError):
        _assert_temporal_semantics(episode)


def test_policy_result_requires_passed_validation_and_freeze() -> None:
    result = _result()
    del result["proposal"]["frozen_at"]
    with pytest.raises(ValidationError):
        _validate("policy-result.json", result)

    result = _result()
    result["proposal"]["validation"]["status"] = "failed"
    with pytest.raises(ValidationError):
        _validate("policy-result.json", result)


def test_policy_result_forbids_outcome_payload_and_early_access() -> None:
    result = _result()
    result["outcome"] = {"realised_points": 72}
    with pytest.raises(ValidationError):
        _validate("policy-result.json", result)

    result = _result()
    result["outcome_access"] = "revealed"
    with pytest.raises(ValidationError):
        _validate("policy-result.json", result)


def test_degraded_result_requires_reason() -> None:
    result = _result()
    result["execution_status"] = "degraded"
    with pytest.raises(ValidationError):
        _validate("policy-result.json", result)
    result["degraded_reason"] = "evidence timeout; deterministic fallback used"
    _validate("policy-result.json", result)


def test_protocol_and_adr_name_all_human_gates() -> None:
    protocol = (ROOT / "docs" / "evaluation" / "benchmark-protocol.md").read_text(
        encoding="utf-8"
    )
    for arm in ARMS:
        assert arm in protocol
    assert "available_at <= cutoff <= deadline" in protocol
    assert "Open Decision 8" in protocol

    adr = (ROOT / "docs" / "decisions" / "0017-benchmark-kernel.md").read_text(
        encoding="utf-8"
    )
    assert "**Status:** Proposed" in adr
    assert "must not merge until this ADR is marked `Accepted`" in adr
