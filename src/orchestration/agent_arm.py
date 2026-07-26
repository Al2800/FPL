"""Subscription-hosted agent seam with deterministic validation and fallback."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from src.agents.challenger_agent import validate_challenger_result
from src.agents.evidence_agent import validate_evidence_result
from src.evidence.lifecycle import load_policy
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
MODEL_ID = "gpt-5.6-sol"
PROVIDER_ID = "openai-chatgpt-subscription"
API_SURFACE = "codex_subscription_subagent"
FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "hidden_outcome",
        "realised_outcome",
        "outcome_points",
        "final_points",
        "cookies",
        "authorization",
        "api_key",
        "manager_email",
    }
)


class AgentArmError(ValueError):
    """Raised when a hosted run cannot safely enter the benchmark."""


def _message_code(value: str) -> str:
    code = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return (code or "agent_arm_failure")[:80]


def _bytes_hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _walk_forbidden(value: Any, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in FORBIDDEN_INPUT_KEYS:
                raise AgentArmError(f"forbidden field at {path or '$'}.{key}")
            _walk_forbidden(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(
            marker in lowered
            for marker in ("hidden_outcome", "hidden-outcome", "realised-outcome")
        ):
            raise AgentArmError(f"forbidden hidden-outcome reference at {path or '$'}")


def _prompt(arm: str) -> tuple[Path, str, str]:
    if arm == "evidence_agent":
        path = ROOT / "prompts/evidence-agent/v1.md"
        prompt_id = "evidence-agent"
    elif arm == "evidence_challenger":
        path = ROOT / "prompts/challenger/v1.md"
        prompt_id = "challenger"
    else:
        raise AgentArmError(f"unsupported agent arm: {arm}")
    content = path.read_bytes()
    return path, prompt_id, _bytes_hash(content)


def render_hosted_input(request: Mapping[str, Any]) -> str:
    """Render the exact prompt bytes submitted to the isolated hosted run."""
    path, _, _ = _prompt(str(request["arm"]))
    context = {
        key: deepcopy(value)
        for key, value in request.items()
        if key not in {"content_sha256", "rendered_input_sha256"}
    }
    return (
        path.read_text(encoding="utf-8").rstrip()
        + "\n\nHOST_CONTEXT_JSON\n"
        + _canonical_json(context)
        + "\n"
    )


def _proposal_binding(proposal: Mapping[str, Any]) -> dict[str, Any]:
    if proposal.get("content_sha256") != artifact_hash(proposal):
        raise AgentArmError("evidence proposal hash mismatch")
    validated = proposal.get("validated_output")
    if not isinstance(validated, Mapping):
        raise AgentArmError("evidence proposal has no validated output")
    return {
        "run_id": str(proposal["run_id"]),
        "content_sha256": str(proposal["content_sha256"]),
        "validated_output": deepcopy(dict(validated)),
    }


def build_hosted_request(
    *,
    arm: str,
    run_id: str,
    episode_id: str,
    observed_episode_sha256: str,
    snapshot_ids: list[str],
    decision_at: str,
    ruleset_id: str,
    player_ids: list[str],
    player_baselines: Mapping[str, Mapping[str, float]],
    evidence_documents: list[dict[str, Any]],
    deterministic_candidate_sha256: str,
    budget: Mapping[str, Any],
    evidence_proposal: Mapping[str, Any] | None = None,
    reasoning_effort: str = "high",
) -> dict[str, Any]:
    """Render the object handed to a subscription-backed Codex run."""
    if re.fullmatch(r"[A-Za-z0-9_-]{3,}", run_id) is None:
        raise AgentArmError("run_id must use trace-safe characters")
    _, prompt_id, prompt_hash = _prompt(arm)
    request = {
        "schema_version": "1.0",
        "run_id": run_id,
        "arm": arm,
        "episode": {
            "episode_id": episode_id,
            "observed_episode_sha256": observed_episode_sha256,
            "snapshot_ids": list(snapshot_ids),
            "decision_at": decision_at,
            "ruleset_id": ruleset_id,
        },
        "provider": {
            "provider_id": PROVIDER_ID,
            "surface": API_SURFACE,
            "model_id": MODEL_ID,
            "reasoning_effort": reasoning_effort,
        },
        "prompt": {
            "prompt_id": prompt_id,
            "version": "1.0",
            "content_sha256": prompt_hash,
        },
        "allowed_tools": [],
        "authority": {
            "may_propose": True,
            "may_apply_adjustment": False,
            "may_modify_rules": False,
            "may_approve": False,
            "may_execute_fpl": False,
            "may_read_hidden_outcome": False,
        },
        "player_ids": sorted(set(player_ids)),
        "player_baselines": deepcopy(
            {
                str(player_id): dict(values)
                for player_id, values in player_baselines.items()
            }
        ),
        "evidence_documents": deepcopy(evidence_documents),
        "deterministic_candidate_sha256": deterministic_candidate_sha256,
        "budget": deepcopy(dict(budget)),
        "evidence_proposal": (
            _proposal_binding(evidence_proposal)
            if evidence_proposal is not None
            else None
        ),
    }
    _walk_forbidden(request)
    for document in request["evidence_documents"]:
        if not isinstance(document, Mapping):
            raise AgentArmError("evidence document must be an object")
        if artifact_hash(document) != document.get("content_sha256"):
            raise AgentArmError("evidence document hash mismatch")
        passages = document.get("passages")
        if not isinstance(passages, Mapping) or not passages:
            raise AgentArmError("evidence document requires immutable passages")
    request["rendered_input_sha256"] = _bytes_hash(
        render_hosted_input(request).encode("utf-8")
    )
    request["content_sha256"] = artifact_hash(request)
    return request


def _resource_usage(
    value: Mapping[str, Any] | None,
    *,
    subscription_cost: bool,
) -> dict[str, Any]:
    raw = value or {}
    usage: dict[str, Any] = {}
    for field in (
        "wall_clock_ms",
        "tool_calls",
        "input_tokens",
        "output_tokens",
        "total_tokens",
    ):
        item = raw.get(field, 0)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise AgentArmError(f"invalid resource usage field: {field}")
        usage[field] = item
    cost = raw.get("cost", {})
    if not isinstance(cost, Mapping):
        raise AgentArmError("invalid resource usage field: cost")
    amount = cost.get("amount")
    if subscription_cost:
        if amount is not None:
            raise AgentArmError("subscription cost must be recorded as unavailable")
        usage["cost"] = {
            "currency": "GBP",
            "amount": None,
            "metering_status": "unavailable",
        }
    else:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise AgentArmError("invalid budget cost amount")
        usage["cost"] = {
            "currency": str(cost.get("currency", "GBP")),
            "amount": float(amount),
            "metering_status": "limit_only",
        }
    return usage


def _budget_failure(limit: Mapping[str, Any], used: Mapping[str, Any]) -> list[str]:
    exhausted: list[str] = []
    mapping = {
        "wall_clock_ms": "wall_clock",
        "tool_calls": "tool_calls",
        "input_tokens": "input_tokens",
        "output_tokens": "output_tokens",
        "total_tokens": "total_tokens",
    }
    for field, label in mapping.items():
        if int(used.get(field, 0)) > int(limit[field]):
            exhausted.append(label)
    if used["cost"]["amount"] is not None and (
        used["cost"]["currency"] != limit["cost"]["currency"]
        or float(used["cost"]["amount"]) > float(limit["cost"]["amount"])
    ):
        exhausted.append("cost")
    return exhausted


def agent_cache_key(request: Mapping[str, Any], *, cli_version: str) -> str:
    """Bind a raw response to every input that can affect model output."""
    return artifact_hash(
        {
            "request_sha256": request["content_sha256"],
            "observed_episode_sha256": request["episode"][
                "observed_episode_sha256"
            ],
            "model_id": request["provider"]["model_id"],
            "reasoning_effort": request["provider"]["reasoning_effort"],
            "cli_version": cli_version,
            "prompt_sha256": request["prompt"]["content_sha256"],
            "policy_sha256": _bytes_hash(
                (ROOT / "control/policies/evidence-adjustments.yaml").read_bytes()
            ),
        }
    )


def cached_or_invoke(
    *,
    request: Mapping[str, Any],
    cli_version: str,
    cache: dict[str, dict[str, Any]],
    invoke,
) -> dict[str, Any]:
    """Use a hash-verified raw response cache; revalidation occurs downstream."""
    key = agent_cache_key(request, cli_version=cli_version)
    cached = cache.get(key)
    if cached is not None:
        if cached.get("content_sha256") != artifact_hash(cached):
            raise AgentArmError("cached response hash mismatch")
        response = deepcopy(dict(cached["hosted_response"]))
        response["cache_hit"] = True
        response["usage"] = {
            **response["usage"],
            "wall_clock_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        return response
    invoked = invoke()
    if not isinstance(invoked, Mapping):
        raise AgentArmError("host returned a non-object response")
    response = deepcopy(dict(invoked))
    _walk_forbidden(response)
    entry = {"hosted_response": deepcopy(response)}
    entry["content_sha256"] = artifact_hash(entry)
    cache[key] = entry
    return response


def run_agent_arm(
    *,
    request: Mapping[str, Any],
    hosted_response: Mapping[str, Any] | None,
    deterministic_candidate: Mapping[str, Any],
    code_commit: str,
    evidence_proposal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a hosted result or select the exact deterministic fallback."""
    if request.get("content_sha256") != artifact_hash(request):
        raise AgentArmError("hosted request hash mismatch")
    if request.get("rendered_input_sha256") != _bytes_hash(
        render_hosted_input(request).encode("utf-8")
    ):
        raise AgentArmError("rendered hosted input hash mismatch")
    _walk_forbidden(request)
    if artifact_hash(deterministic_candidate) != request[
        "deterministic_candidate_sha256"
    ]:
        raise AgentArmError("deterministic fallback hash mismatch")
    arm = str(request["arm"])
    limit = _resource_usage(request.get("budget"), subscription_cost=False)
    usage_error: AgentArmError | None = None
    try:
        used = _resource_usage(
            hosted_response.get("usage") if hosted_response is not None else None,
            subscription_cost=True,
        )
    except AgentArmError as exc:
        usage_error = exc
        used = _resource_usage(None, subscription_cost=True)
    exhausted = _budget_failure(limit, used)
    failure: dict[str, Any] | None = None
    validated: dict[str, Any] | None = None
    reported_completed_at = (
        hosted_response.get("completed_at")
        if hosted_response is not None
        else None
    )
    completed_at_valid = bool(
        isinstance(reported_completed_at, str)
        and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
            reported_completed_at,
        )
    )
    actual_at = str(reported_completed_at) if completed_at_valid else _utc_now()

    try:
        if usage_error is not None:
            raise usage_error
        if hosted_response is None:
            raise AgentArmError("provider_unavailable")
        if not completed_at_valid:
            raise AgentArmError("invalid_host_completed_at")
        _walk_forbidden(hosted_response)
        declared_failure = hosted_response.get("failure")
        if declared_failure is not None:
            if not isinstance(declared_failure, Mapping):
                raise AgentArmError("invalid_hosted_failure")
            failure_category = str(declared_failure.get("category", "provider_failure"))
            if failure_category not in {
                "timeout",
                "tool_failure",
                "source_failure",
                "provider_failure",
            }:
                raise AgentArmError("invalid_hosted_failure_category")
            raise AgentArmError(f"hosted_{failure_category}")
        if hosted_response.get("provider_id") != PROVIDER_ID:
            raise AgentArmError("provider_identity_mismatch")
        if hosted_response.get("model_id") != MODEL_ID:
            raise AgentArmError("model_identity_mismatch")
        if (
            hosted_response.get("request_sha256")
            != request["rendered_input_sha256"]
        ):
            raise AgentArmError("model_request_hash_mismatch")
        attestation = hosted_response.get("attestation")
        if not isinstance(attestation, Mapping):
            raise AgentArmError("missing_host_attestation")
        if (
            attestation.get("auth_mode") != "chatgpt_subscription"
            or attestation.get("sandbox") != "read-only"
            or attestation.get("network_access") is not False
            or attestation.get("rendered_input_sha256")
            != request["rendered_input_sha256"]
        ):
            raise AgentArmError("invalid_host_attestation")
        event_types = attestation.get("event_types")
        if not isinstance(event_types, list) or any(
            str(event).lower()
            in {
                "command_execution",
                "file_change",
                "mcp_tool_call",
                "web_search",
            }
            for event in event_types
        ):
            raise AgentArmError("disallowed_host_event")
        structured = hosted_response.get("structured_output")
        if not isinstance(structured, Mapping):
            raise AgentArmError("missing_structured_output")
        if hosted_response.get("response_sha256") != artifact_hash(structured):
            raise AgentArmError("model_response_hash_mismatch")
        _walk_forbidden(structured)
        if exhausted:
            raise AgentArmError("budget_exhaustion")
        if arm == "evidence_agent":
            validated = validate_evidence_result(
                structured,
                decision_at=str(request["episode"]["decision_at"]),
                known_player_ids=set(request["player_ids"]),
                policy=load_policy(),
                approved_evidence={
                    str(document["document_id"]): document
                    for document in request["evidence_documents"]
                },
                player_baselines=request["player_baselines"],
                run_observed_at=actual_at,
            )
        else:
            if evidence_proposal is None:
                raise AgentArmError("challenger_missing_evidence_proposal")
            request_proposal = request.get("evidence_proposal")
            if request_proposal != _proposal_binding(evidence_proposal):
                raise AgentArmError("challenger_proposal_binding_mismatch")
            validated = validate_challenger_result(
                structured,
                evidence_run_id=str(evidence_proposal["run_id"]),
                proposal=evidence_proposal["validated_output"],
                observed_at=actual_at,
            )
    except (AgentArmError, KeyError, TypeError, ValueError) as exc:
        message = str(exc)
        if "budget_exhaustion" in message:
            category, stage = "budget_exhaustion", "model_call"
        elif "tool_failure" in message:
            category, stage = "tool_failure", "tool_call"
        elif "source_failure" in message:
            category, stage = "source_failure", "tool_call"
        elif "timeout" in message:
            category, stage = "timeout", "model_call"
        elif "provider" in message or "model_identity" in message:
            category, stage = "provider_failure", "model_call"
        elif "unavailable" in message:
            category, stage = "provider_failure", "planning"
        elif "injection" in message or "forbidden" in message:
            category, stage = "policy_denial", "evidence_validation"
        else:
            category, stage = "invalid_output", "evidence_validation"
        failure = {
            "category": category,
            "stage": stage,
            "message_code": _message_code(message),
            "retriable": category in {
                "provider_failure",
                "tool_failure",
                "source_failure",
                "timeout",
            },
        }

    degraded = failure is not None
    output_value = validated if validated is not None else deterministic_candidate
    output_hash = artifact_hash(output_value)
    response_hash = (
        str(hosted_response["response_sha256"])
        if hosted_response is not None
        and isinstance(hosted_response.get("response_sha256"), str)
        else artifact_hash({"failure": failure})
    )
    response_payload = (
        deepcopy(dict(hosted_response))
        if hosted_response is not None
        and not (
            failure is not None
            and "forbidden" in str(failure.get("message_code", ""))
        )
        else {"failure": deepcopy(failure)}
    )
    response_artifact_hash = artifact_hash(response_payload)
    _, prompt_id, prompt_hash = _prompt(arm)
    trace = {
        "schema_version": "1.0",
        "run_id": str(request["run_id"]),
        "episode_id": str(request["episode"]["episode_id"]),
        "observed_episode_sha256": str(
            request["episode"]["observed_episode_sha256"]
        ),
        "snapshot_ids": list(request["episode"]["snapshot_ids"]),
        "agent_role": "evidence" if arm == "evidence_agent" else "challenger",
        "policy_arm": arm,
        "provider": {
            "provider_id": PROVIDER_ID,
            "api_surface": API_SURFACE,
            "auth_mode": "chatgpt_subscription",
            "cli_version": str((hosted_response or {}).get("cli_version", "unknown")),
        },
        "model": {
            "requested_model": MODEL_ID,
            "reported_model": (hosted_response or {}).get("model_version"),
            "reasoning_effort": str(request["provider"]["reasoning_effort"]),
        },
        "versions": {
            "code_commit": code_commit,
            "ruleset_id": str(request["episode"]["ruleset_id"]),
            "prompt": {
                "prompt_id": prompt_id,
                "version": "1.0",
                "content_sha256": prompt_hash,
            },
            "policy": {
                "policy_id": "evidence-adjustments-v0.1",
                "version": "0.1",
                "content_sha256": _bytes_hash(
                    (
                        ROOT / "control/policies/evidence-adjustments.yaml"
                    ).read_bytes()
                ),
            },
            "tools": [],
        },
        "inputs": {
            "input_sha256": str(request["content_sha256"]),
            "rendered_prompt_sha256": str(request["rendered_input_sha256"]),
            "context_refs": [
                {
                    "artifact_id": f"hosted-request:{request['run_id']}",
                    "content_sha256": str(request["content_sha256"]),
                }
            ],
        },
        "output": {
            "output_sha256": output_hash,
            "response_ref": {
                "artifact_id": f"cached-response:{request['run_id']}",
                "content_sha256": response_artifact_hash,
            },
            "structured_output_ref": {
                "artifact_id": f"validated-output:{request['run_id']}",
                "content_sha256": output_hash,
            },
        },
        "tool_calls": [],
        "model_calls": ([
            {
                "sequence": 0,
                "call_id": f"model:{request['run_id']}",
                "request_sha256": str(request["rendered_input_sha256"]),
                "response_sha256": response_hash,
                "cached_response_ref": {
                    "artifact_id": f"cached-response:{request['run_id']}",
                    "content_sha256": response_artifact_hash,
                },
                "cache_hit": bool((hosted_response or {}).get("cache_hit", False)),
                "input_tokens": int(used["input_tokens"]),
                "output_tokens": int(used["output_tokens"]),
            }
        ] if hosted_response is not None else []),
        "budget": {
            "limit": limit,
            "used": used,
            "exhausted": exhausted,
        },
        "execution_status": "degraded" if degraded else "completed",
        "degradation": (
            {
                "used": True,
                "fallback_arm": "forecast_optimizer",
                "reason_code": f"fallback_{failure['category']}",
            }
            if degraded
            else {"used": False}
        ),
        "privacy": {
            "redaction_status": "passed",
            "prohibited_data_detected": False,
            "forbidden_categories": [
                "credentials",
                "cookies",
                "tokens",
                "personal_data",
            ],
        },
        "trace_path": f"reports/traces/{request['run_id']}.jsonl",
        "observed_at": actual_at,
        "available_at": actual_at,
        "provenance": {
            "source_ids": ["benchmark-kernel", PROVIDER_ID],
            "transformation_version": "agent-arm-v1",
            "model_version": MODEL_ID,
            "prompt_version": "1.0",
            "agent_run_id": str(request["run_id"]),
        },
        "decision_cutoff": str(request["episode"]["decision_at"]),
        "run_mode": "retrospective" if actual_at > str(request["episode"]["decision_at"]) else "live",
    }
    if failure is not None:
        trace["failure"] = failure
    result = {
        "schema_version": "1.0",
        "run_id": str(request["run_id"]),
        "arm": arm,
        "status": trace["execution_status"],
        "validated_output": validated,
        "selected_candidate": deepcopy(dict(deterministic_candidate)),
        "adjustments_applied": [],
        "trace": trace,
        "artifacts": {
            "response": {
                "artifact_id": f"cached-response:{request['run_id']}",
                "content_sha256": response_artifact_hash,
                "payload": response_payload,
            },
            "validated_output": {
                "artifact_id": f"validated-output:{request['run_id']}",
                "content_sha256": output_hash,
                "payload": deepcopy(output_value),
            },
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result
