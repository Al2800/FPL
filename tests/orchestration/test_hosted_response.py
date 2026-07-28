"""Golden protocol contracts for host-owned response linting."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.hosted_response import (
    build_hosted_response,
    build_repair_request,
    hosted_response_policy,
    lint_hosted_response,
    lint_semantic_output,
)


ROOT = Path(__file__).resolve().parents[2]
GOLDEN = (
    ROOT
    / "evals"
    / "golden-cases"
    / "evidence"
    / "hosted-response-failures.json"
)


def _golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _request(*, arm: str = "evidence_agent") -> dict:
    request = {
        "arm": arm,
        "rendered_input_sha256": "a" * 64,
        "episode": {
            "observed_episode_sha256": "b" * 64,
        },
    }
    if arm == "evidence_challenger":
        request["evidence_proposal"] = {
            "validated_output": {
                "proposed_adjustments": [
                    {"adjustment_id": "adjustment:bound"}
                ]
            }
        }
    request["content_sha256"] = artifact_hash(request)
    return request


def _valid_output() -> dict:
    return {
        "schema_version": "1.0",
        "role": "evidence",
        "claims": [],
        "conflicts": [],
        "proposed_adjustments": [],
        "notes": [],
    }


def _envelope(request: dict) -> dict:
    return build_hosted_response(
        request=request,
        structured_output=_valid_output(),
        completed_at="2026-07-26T19:30:37Z",
        usage={
            "wall_clock_ms": 1_000,
            "tool_calls": 0,
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
        },
    )


def test_live_policy_is_default_on_hash_bound_and_has_explicit_rollback() -> None:
    live = hosted_response_policy()
    rollback = hosted_response_policy(enabled=False)

    assert live["policy_id"] == "hosted-response-lint-v1"
    assert live["enabled"] is True
    assert live["max_repair_attempts"] == 1
    assert live["content_sha256"] == artifact_hash(live)
    assert rollback["enabled"] is False
    assert rollback["max_repair_attempts"] == 0
    assert rollback["content_sha256"] == artifact_hash(rollback)


def test_archived_semantic_failure_patterns_have_stable_actionable_codes() -> None:
    for case in _golden()["semantic_cases"]:
        request = _request(arm=case["arm"])
        before = deepcopy(case["structured_output"])
        violations = lint_semantic_output(
            arm=case["arm"],
            structured_output=case["structured_output"],
            request=request,
        )

        assert sorted({row["code"] for row in violations}) == sorted(
            case["expected_codes"]
        )
        assert case["structured_output"] == before
        assert all(row["path"].startswith("$") for row in violations)
        assert all(row["message"] for row in violations)


def test_compliant_semantic_payload_passes_without_mutation() -> None:
    payload = _valid_output()
    before = deepcopy(payload)

    assert lint_semantic_output(
        arm="evidence_agent",
        structured_output=payload,
        request=_request(),
    ) == []
    assert payload == before


def test_archived_envelope_failures_are_detected_with_exact_codes() -> None:
    for case in _golden()["envelope_cases"]:
        request = _request()
        envelope = _envelope(request)
        envelope[case["field"]] = case["value"]
        violations = lint_hosted_response(
            request=request,
            hosted_response=envelope,
        )

        assert case["expected_code"] in {row["code"] for row in violations}


def test_valid_host_owned_envelope_passes_unchanged() -> None:
    request = _request()
    envelope = _envelope(request)
    before = deepcopy(envelope)

    assert lint_hosted_response(
        request=request,
        hosted_response=envelope,
    ) == []
    assert envelope == before


def test_non_serializable_envelope_is_reported_without_hashing_it() -> None:
    request = _request()
    envelope = _envelope(request)
    envelope["structured_output"]["notes"] = {object()}

    assert lint_hosted_response(
        request=request,
        hosted_response=envelope,
    ) == [
        {
            "code": "hosted_response_not_serializable",
            "path": "$",
            "message": (
                "The host response must contain JSON-serializable values only."
            ),
            "expected": "valid JSON object",
        }
    ]


def test_repair_request_is_deterministic_and_bound_to_original_episode() -> None:
    request = _request()
    failed = _envelope(request)
    failed["structured_output"]["role"] = "evidence_agent"
    violations = lint_hosted_response(
        request=request,
        hosted_response=failed,
    )

    first = build_repair_request(
        request=request,
        failed_payload=failed,
        violations=violations,
    )
    second = build_repair_request(
        request=request,
        failed_payload=failed,
        violations=violations,
    )

    assert first == second
    assert first["original_request_sha256"] == request["rendered_input_sha256"]
    assert first["observed_episode_sha256"] == "b" * 64
    assert first["failed_payload_sha256"] == artifact_hash(failed)
    assert first["content_sha256"] == artifact_hash(first)
