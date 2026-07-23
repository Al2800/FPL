"""Contracts for replayable, budgeted and privacy-safe agent traces."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "control" / "schemas"
SHA = "a" * 64


def _rewrite_external_refs(value, defs):
    if isinstance(value, dict):
        if set(value) == {"$ref"} and "/$defs/" in value["$ref"] and value["$ref"].startswith("../"):
            return defs[value["$ref"].split("/$defs/")[-1]]
        return {key: _rewrite_external_refs(item, defs) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_external_refs(item, defs) for item in value]
    return value


def _schema(relative: str) -> dict:
    schema = json.loads((SCHEMAS / relative).read_text(encoding="utf-8"))
    defs = json.loads((SCHEMAS / "_defs.json").read_text(encoding="utf-8"))["$defs"]
    return _rewrite_external_refs(schema, defs)


def _validate(relative: str, record: dict) -> None:
    Draft202012Validator(_schema(relative), format_checker=FormatChecker()).validate(record)


def _run() -> dict:
    return json.loads((SCHEMAS / "examples/agent_runs.json").read_text(encoding="utf-8"))


def _assert_budget_within_limit(record: dict) -> None:
    limit = record["budget"]["limit"]
    used = record["budget"]["used"]
    for field in ["wall_clock_ms", "tool_calls", "input_tokens", "output_tokens", "total_tokens"]:
        assert used[field] <= limit[field], field
    assert used["cost"]["currency"] == limit["cost"]["currency"]
    assert used["cost"]["amount"] <= limit["cost"]["amount"]


def _assert_contiguous_sequences(record: dict) -> None:
    for field in ["tool_calls", "model_calls"]:
        assert [item["sequence"] for item in record[field]] == list(range(len(record[field])))


def test_valid_agent_trace_and_run_manifest() -> None:
    record = _run()
    _validate("decisions/agent_runs.json", record)
    _assert_budget_within_limit(record)
    _assert_contiguous_sequences(record)
    ref = {"artifact_id": "agent-run-ar-evidence-gw01", "content_sha256": SHA}
    manifest = {
        "schema_version": "1.0",
        "run_manifest_id": "manifest-gw01",
        "episode_id": record["episode_id"],
        "observed_episode_sha256": record["observed_episode_sha256"],
        "created_at": record["available_at"],
        "runs": [{
            "run_id": record["run_id"],
            "policy_arm": record["policy_arm"],
            "agent_run_ref": ref,
            "input_sha256": record["inputs"]["input_sha256"],
            "output_sha256": record["output"]["output_sha256"],
            "execution_status": record["execution_status"],
        }],
    }
    _validate("benchmark/run-manifest.json", manifest)


@pytest.mark.parametrize(
    "path",
    [
        ("episode_id",),
        ("observed_episode_sha256",),
        ("snapshot_ids",),
        ("provider",),
        ("model",),
        ("versions", "prompt"),
        ("versions", "policy"),
        ("versions", "tools"),
        ("inputs", "input_sha256"),
        ("output", "output_sha256"),
        ("budget",),
    ],
)
def test_trace_rejects_missing_identity_version_budget_or_hash_provenance(path) -> None:
    record = _run()
    target = record
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    with pytest.raises(ValidationError):
        _validate("decisions/agent_runs.json", record)


def test_ordered_calls_and_cached_responses_are_replay_sufficient() -> None:
    record = _run()
    _assert_contiguous_sequences(record)
    assert all(call["arguments_sha256"] and call["result_ref"]["content_sha256"] for call in record["tool_calls"])
    assert all(call["request_sha256"] and call["response_sha256"] for call in record["model_calls"])
    assert all(call["cached_response_ref"]["artifact_id"] for call in record["model_calls"])
    assert "prompt_text" not in record["inputs"]
    assert "response_body" not in record["output"]


@pytest.mark.parametrize(
    "category",
    ["timeout", "tool_failure", "source_failure", "budget_exhaustion"],
)
def test_structured_failure_taxonomy_and_degraded_fallback(category: str) -> None:
    record = _run()
    record["execution_status"] = "degraded"
    record["failure"] = {
        "category": category,
        "stage": "tool_call" if category != "timeout" else "planning",
        "message_code": f"test_{category}",
        "retriable": category != "budget_exhaustion",
    }
    record["degradation"] = {
        "used": True,
        "fallback_arm": "forecast_optimizer",
        "reason_code": f"fallback_{category}",
    }
    if category == "budget_exhaustion":
        record["budget"]["exhausted"] = ["tool_calls"]
    _validate("decisions/agent_runs.json", record)


def test_completed_run_rejects_failure_and_degraded_run_requires_failure() -> None:
    completed = _run()
    completed["failure"] = {"category": "timeout", "stage": "planning", "message_code": "late_timeout", "retriable": True}
    with pytest.raises(ValidationError):
        _validate("decisions/agent_runs.json", completed)

    degraded = _run()
    degraded["execution_status"] = "degraded"
    degraded["degradation"] = {"used": True, "fallback_arm": "forecast_optimizer", "reason_code": "fallback_timeout"}
    with pytest.raises(ValidationError):
        _validate("decisions/agent_runs.json", degraded)


def test_schema_rejects_secret_cookie_and_personal_data_fields() -> None:
    attempts = [
        (("provider",), "authorization", "Bearer secret"),
        (("tool_calls", 0), "cookies", {"session": "secret"}),
        ((), "personal_data", {"manager_email": "person@example.invalid"}),
    ]
    for path, key, value in attempts:
        record = _run()
        target = record
        for part in path:
            target = target[part]
        target[key] = value
        with pytest.raises(ValidationError):
            _validate("decisions/agent_runs.json", record)
    assert record["privacy"]["forbidden_categories"] == ["credentials", "cookies", "tokens", "personal_data"]


def test_semantic_guards_detect_budget_and_sequence_overruns() -> None:
    record = _run()
    record["budget"]["used"]["tool_calls"] = record["budget"]["limit"]["tool_calls"] + 1
    with pytest.raises(AssertionError):
        _assert_budget_within_limit(record)

    record = _run()
    record["tool_calls"][0]["sequence"] = 2
    with pytest.raises(AssertionError):
        _assert_contiguous_sequences(record)
