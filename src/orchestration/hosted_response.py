"""Trusted construction of hosted-agent response metadata.

The model supplies ``structured_output`` only.  Everything else in the
response envelope is produced and validated by the host.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
import re
from typing import Any

from src.forecasting.live_faithful import artifact_hash


MODEL_ID = "gpt-5.6-sol"
PROVIDER_ID = "openai-chatgpt-subscription"
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
