"""Trusted construction of hosted-agent response metadata.

The model supplies ``structured_output`` only.  Everything else in the
response envelope is produced and validated by the host.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator

from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
MODEL_ID = "gpt-5.6-sol"
PROVIDER_ID = "openai-chatgpt-subscription"
HOSTED_RESPONSE_POLICY_ID = "hosted-response-lint-v1"
HOSTED_RESPONSE_POLICY_VERSION = "1.0"
DEFAULT_HOSTED_RESPONSE_POLICY = {
    "policy_id": HOSTED_RESPONSE_POLICY_ID,
    "version": HOSTED_RESPONSE_POLICY_VERSION,
    "enabled": True,
    "max_repair_attempts": 1,
}
WHOLE_SECOND_UTC = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)
SHA256 = re.compile(r"[a-f0-9]{64}")
SAFE_EVENT_TYPES = (
    "thread_started",
    "turn_started",
    "agent_message",
    "turn_completed",
)
USAGE_FIELDS = (
    "wall_clock_ms",
    "tool_calls",
    "input_tokens",
    "output_tokens",
    "total_tokens",
)


class HostedResponseError(ValueError):
    """Raised when trusted host metadata cannot be constructed safely."""


def hosted_response_policy(*, enabled: bool | None = None) -> dict[str, Any]:
    """Return the versioned live policy, optionally selecting its rollback."""
    if enabled is not None and not isinstance(enabled, bool):
        raise HostedResponseError("hosted-response policy enabled must be a boolean")
    policy = deepcopy(DEFAULT_HOSTED_RESPONSE_POLICY)
    if enabled is False:
        policy["enabled"] = False
        policy["max_repair_attempts"] = 0
    policy["content_sha256"] = artifact_hash(policy)
    return policy


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            escaped = str(part).replace("~", "~0").replace("/", "~1")
            path += f"/{escaped}"
    return path


def _violation(
    code: str,
    path: str,
    message: str,
    *,
    expected: Any | None = None,
) -> dict[str, Any]:
    value = {"code": code, "path": path, "message": message}
    if expected is not None:
        value["expected"] = deepcopy(expected)
    return value


def _schema_for_arm(arm: str) -> dict[str, Any]:
    if arm == "evidence_agent":
        path = ROOT / "prompts/evidence-agent/output.schema.json"
    elif arm == "evidence_challenger":
        path = ROOT / "prompts/challenger/output.schema.json"
    else:
        raise HostedResponseError(f"unsupported hosted-response arm: {arm}")
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_code(validator: str) -> str:
    return {
        "additionalProperties": "schema_additional_property",
        "required": "schema_required",
        "type": "schema_type",
        "const": "schema_const",
        "enum": "schema_enum",
    }.get(validator, f"schema_{validator.lower()}")


def lint_semantic_output(
    *,
    arm: str,
    structured_output: Any,
    request: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return stable structural diagnostics without mutating model content."""
    if not isinstance(structured_output, Mapping):
        return [
            _violation(
                "structured_output_not_object",
                "$",
                "Return one JSON object, not prose, an encoded JSON string, or an array.",
                expected="object",
            )
        ]
    try:
        json.dumps(
            structured_output,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        return [
            _violation(
                "structured_output_not_serializable",
                "$",
                "Return JSON-serializable values only.",
                expected="valid JSON object",
            )
        ]

    schema = _schema_for_arm(arm)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(structured_output)),
        key=lambda error: (
            list(error.absolute_path),
            str(error.validator),
            error.message,
        ),
    )
    violations = [
        _violation(
            _schema_code(str(error.validator)),
            _json_path(error.absolute_path),
            error.message,
            expected=error.validator_value,
        )
        for error in errors
    ]

    if arm == "evidence_challenger" and request is not None:
        proposal = request.get("evidence_proposal")
        validated = (
            proposal.get("validated_output")
            if isinstance(proposal, Mapping)
            else None
        )
        adjustments = (
            validated.get("proposed_adjustments")
            if isinstance(validated, Mapping)
            else None
        )
        if isinstance(adjustments, list):
            expected_ids = sorted(
                str(row.get("adjustment_id"))
                for row in adjustments
                if isinstance(row, Mapping) and row.get("adjustment_id") is not None
            )
            reviewed = structured_output.get("reviewed_adjustment_ids")
            if (
                isinstance(reviewed, list)
                and sorted(str(value) for value in reviewed) != expected_ids
            ):
                violations.append(
                    _violation(
                        "challenger_adjustment_binding_mismatch",
                        "$/reviewed_adjustment_ids",
                        "Review exactly the adjustment IDs bound into this request.",
                        expected=expected_ids,
                    )
                )
    return sorted(
        violations,
        key=lambda value: (
            str(value["path"]),
            str(value["code"]),
            str(value["message"]),
        ),
    )


def lint_hosted_response(
    *,
    request: Mapping[str, Any],
    hosted_response: Any,
) -> list[dict[str, Any]]:
    """Lint a host envelope and semantic payload before admission."""
    if not isinstance(hosted_response, Mapping):
        return [
            _violation(
                "hosted_response_not_object",
                "$",
                "The host must return one response-envelope object.",
                expected="object",
            )
        ]
    try:
        json.dumps(
            hosted_response,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        return [
            _violation(
                "hosted_response_not_serializable",
                "$",
                "The host response must contain JSON-serializable values only.",
                expected="valid JSON object",
            )
        ]
    violations: list[dict[str, Any]] = []
    expected_bindings = {
        "envelope_version": "1.0",
        "metadata_owner": "host",
        "provider_id": PROVIDER_ID,
        "model_id": MODEL_ID,
        "request_sha256": request.get("rendered_input_sha256"),
    }
    for field, expected in expected_bindings.items():
        if hosted_response.get(field) != expected:
            violations.append(
                _violation(
                    f"envelope_{field}_mismatch",
                    f"$/{field}",
                    f"{field} must be supplied by the trusted host and match the request.",
                    expected=expected,
                )
            )

    completed_at = hosted_response.get("completed_at")
    try:
        _whole_second_utc(completed_at)
    except HostedResponseError as exc:
        violations.append(
            _violation(
                "envelope_completed_at_invalid",
                "$/completed_at",
                str(exc),
                expected="YYYY-MM-DDTHH:MM:SSZ",
            )
        )

    attestation = hosted_response.get("attestation")
    if not isinstance(attestation, Mapping):
        violations.append(
            _violation(
                "envelope_attestation_missing",
                "$/attestation",
                "The trusted host must supply an attestation object.",
                expected="object",
            )
        )
    else:
        expected_attestation = {
            "auth_mode": "chatgpt_subscription",
            "sandbox": "read-only",
            "network_access": False,
            "rendered_input_sha256": request.get("rendered_input_sha256"),
        }
        for field, expected in expected_attestation.items():
            if attestation.get(field) != expected:
                violations.append(
                    _violation(
                        f"attestation_{field}_mismatch",
                        f"$/attestation/{field}",
                        f"Host attestation {field} does not match the admitted request.",
                        expected=expected,
                    )
                )

    usage = hosted_response.get("usage")
    if not isinstance(usage, Mapping):
        violations.append(
            _violation(
                "envelope_usage_missing",
                "$/usage",
                "The trusted host must supply resource usage.",
                expected="object",
            )
        )
    else:
        for field in USAGE_FIELDS:
            item = usage.get(field)
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                violations.append(
                    _violation(
                        "envelope_usage_invalid",
                        f"$/usage/{field}",
                        f"{field} must be a non-negative integer.",
                        expected="non-negative integer",
                    )
                )
        if all(
            isinstance(usage.get(field), int)
            and not isinstance(usage.get(field), bool)
            for field in ("input_tokens", "output_tokens", "total_tokens")
        ) and usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
            violations.append(
                _violation(
                    "envelope_usage_total_mismatch",
                    "$/usage/total_tokens",
                    "total_tokens must equal input_tokens plus output_tokens.",
                    expected=usage["input_tokens"] + usage["output_tokens"],
                )
            )

    structured = hosted_response.get("structured_output")
    violations.extend(
        lint_semantic_output(
            arm=str(request.get("arm")),
            structured_output=structured,
            request=request,
        )
    )
    if isinstance(structured, Mapping):
        expected_hash = artifact_hash(structured)
        if hosted_response.get("response_sha256") != expected_hash:
            violations.append(
                _violation(
                    "envelope_response_hash_mismatch",
                    "$/response_sha256",
                    "response_sha256 must hash the exact structured_output object.",
                    expected=expected_hash,
                )
            )
    return sorted(
        violations,
        key=lambda value: (
            str(value["path"]),
            str(value["code"]),
            str(value["message"]),
        ),
    )


def build_repair_request(
    *,
    request: Mapping[str, Any],
    failed_payload: Any,
    violations: list[Mapping[str, Any]],
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, input-preserving repair instruction."""
    selected_policy = deepcopy(dict(policy or hosted_response_policy()))
    if selected_policy.get("content_sha256") != artifact_hash(selected_policy):
        raise HostedResponseError("hosted-response policy hash mismatch")
    if not violations:
        raise HostedResponseError("repair request requires at least one violation")
    try:
        failed_sha256 = artifact_hash(failed_payload)
    except (TypeError, ValueError):
        failed_sha256 = artifact_hash(
            {"unserializable_type": type(failed_payload).__qualname__}
        )
    repair = {
        "schema_version": "1.0",
        "kind": "hosted_response_repair",
        "policy": selected_policy,
        "original_request_sha256": request.get("rendered_input_sha256"),
        "observed_episode_sha256": request.get("episode", {}).get(
            "observed_episode_sha256"
        ),
        "failed_payload_sha256": failed_sha256,
        "violations": [deepcopy(dict(value)) for value in violations],
        "instruction": (
            "Return only a corrected semantic structured-output JSON object. "
            "Do not add evidence, change the episode, widen authority, or explain."
        ),
    }
    repair["content_sha256"] = artifact_hash(repair)
    return repair


def _whole_second_utc(value: str) -> str:
    if not isinstance(value, str) or WHOLE_SECOND_UTC.fullmatch(value) is None:
        raise HostedResponseError(
            "completed_at must be a whole-second UTC timestamp ending in Z"
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise HostedResponseError(
            "completed_at must be a valid whole-second UTC timestamp ending in Z"
        ) from exc
    return value


def _host_usage(value: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = dict(value or {})
    allowed = set(USAGE_FIELDS)
    unknown = set(raw) - allowed
    if unknown:
        raise HostedResponseError(
            f"host usage contains unsupported fields: {sorted(unknown)}"
        )
    usage: dict[str, Any] = {}
    for field in USAGE_FIELDS:
        item = raw.get(field, 0)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise HostedResponseError(
                f"host usage field {field} must be a non-negative integer"
            )
        usage[field] = item
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise HostedResponseError(
            "host usage total_tokens must equal input_tokens plus output_tokens"
        )
    if usage["tool_calls"] != 0:
        raise HostedResponseError(
            "hosted semantic payload execution cannot report tool calls"
        )
    usage["cost"] = {
        "currency": "GBP",
        "amount": None,
        "metering_status": "unavailable",
    }
    return usage


def build_hosted_response(
    *,
    request: Mapping[str, Any],
    structured_output: Mapping[str, Any],
    completed_at: str,
    usage: Mapping[str, Any] | None = None,
    model_version: str = MODEL_ID,
    cli_version: str = "host-owned-envelope-v1",
    cache_hit: bool = False,
) -> dict[str, Any]:
    """Wrap one semantic model payload in deterministic, host-owned metadata."""
    if not isinstance(request, Mapping):
        raise HostedResponseError("request must be an object")
    request_hash = request.get("rendered_input_sha256")
    if not isinstance(request_hash, str) or SHA256.fullmatch(request_hash) is None:
        raise HostedResponseError("request requires a valid rendered input hash")
    if request.get("content_sha256") != artifact_hash(request):
        raise HostedResponseError("request content hash mismatch")
    if not isinstance(structured_output, Mapping):
        raise HostedResponseError("structured_output must be an object")
    if not isinstance(model_version, str) or not model_version:
        raise HostedResponseError("model_version must be a non-empty string")
    if not isinstance(cli_version, str) or not cli_version:
        raise HostedResponseError("cli_version must be a non-empty string")
    if not isinstance(cache_hit, bool):
        raise HostedResponseError("cache_hit must be a boolean")

    semantic = deepcopy(dict(structured_output))
    return {
        "envelope_version": "1.0",
        "metadata_owner": "host",
        "provider_id": PROVIDER_ID,
        "model_id": MODEL_ID,
        "model_version": model_version,
        "request_sha256": request_hash,
        "response_sha256": artifact_hash(semantic),
        "structured_output": semantic,
        "cache_hit": cache_hit,
        "cli_version": cli_version,
        "completed_at": _whole_second_utc(completed_at),
        "attestation": {
            "auth_mode": "chatgpt_subscription",
            "sandbox": "read-only",
            "network_access": False,
            "rendered_input_sha256": request_hash,
            "event_types": list(SAFE_EVENT_TYPES),
        },
        "usage": _host_usage(usage),
    }
