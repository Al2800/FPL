"""Deadline-cycle scheduled evidence/challenger overlay (ticket 11).

Uses the subscription Codex sol surface (ADR-0021/0024). Stages are planned
relative to the Gameweek deadline; past T-90m the overlay degrades to the
deterministic plan without calling the host.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_arm import (
    MODEL_ID,
    PROVIDER_ID,
    run_agent_arm,
)
from src.orchestration.agent_trace import write_agent_trace
from src.orchestration.deadline_capture_scheduler import iso_utc, utc_timestamp


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "control" / "policies" / "scheduled-agent-overlay-v1.json"


class ScheduledAgentOverlayError(ValueError):
    """Raised when the scheduled overlay cannot run safely."""


InvokeFn = Callable[[Mapping[str, Any]], Mapping[str, Any] | None]


def load_overlay_policy(path: Path | None = None) -> dict[str, Any]:
    """Load and lightly validate the versioned overlay schedule policy."""

    policy_path = path or DEFAULT_POLICY_PATH
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ScheduledAgentOverlayError("overlay policy must be a JSON object")
    if payload.get("policy_version") != "scheduled-agent-overlay-v1":
        raise ScheduledAgentOverlayError("unsupported overlay policy version")
    if int(payload.get("t90m_offset_minutes", 0)) != 90:
        raise ScheduledAgentOverlayError("t90m_offset_minutes must be 90")
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ScheduledAgentOverlayError("overlay policy requires stages")
    return payload


def minutes_before_deadline(deadline: str | datetime, now: str | datetime) -> float:
    """Return signed minutes from ``now`` until ``deadline`` (positive = before)."""

    return (utc_timestamp(deadline) - utc_timestamp(now)).total_seconds() / 60.0


def past_t90m_cutoff(
    deadline: str | datetime,
    now: str | datetime,
    *,
    offset_minutes: int = 90,
) -> bool:
    """True when agent stages must stop and the deterministic plan wins."""

    return minutes_before_deadline(deadline, now) < float(offset_minutes)


def plan_due_overlay_stages(
    policy: Mapping[str, Any],
    *,
    deadline: str | datetime,
    now: str | datetime,
) -> list[dict[str, Any]]:
    """Return stages whose open window contains ``now``, excluding post-T-90m."""

    if past_t90m_cutoff(
        deadline,
        now,
        offset_minutes=int(policy.get("t90m_offset_minutes", 90)),
    ):
        return []
    due: list[dict[str, Any]] = []
    current = utc_timestamp(now)
    cut = utc_timestamp(deadline)
    for row in policy["stages"]:
        if not isinstance(row, Mapping):
            raise ScheduledAgentOverlayError("each stage must be an object")
        offset = int(row["offset_minutes"])
        window = int(row["window_minutes"])
        opens = cut - timedelta(minutes=offset)
        closes = opens + timedelta(minutes=window)
        if opens <= current < closes:
            due.append(
                {
                    "checkpoint": str(row["checkpoint"]),
                    "arms": list(row["arms"]),
                    "opens_at": iso_utc(opens),
                    "closes_at": iso_utc(closes),
                    "evidence_budget_ms": int(row["evidence_budget_ms"]),
                    "challenger_budget_ms": int(row["challenger_budget_ms"]),
                }
            )
    return due


def build_forced_timeout_hosted_response(
    request: Mapping[str, Any],
    *,
    completed_at: str,
    wall_clock_ms: int | None = None,
) -> dict[str, Any]:
    """Construct a host envelope that declares a model-call timeout."""

    budget = request.get("budget") if isinstance(request.get("budget"), Mapping) else {}
    used_ms = int(wall_clock_ms if wall_clock_ms is not None else budget.get("wall_clock_ms", 1))
    return {
        "provider_id": PROVIDER_ID,
        "model_id": MODEL_ID,
        "model_version": MODEL_ID,
        "request_sha256": request["rendered_input_sha256"],
        "response_sha256": artifact_hash({"failure": {"category": "timeout"}}),
        "structured_output": None,
        "cache_hit": False,
        "cli_version": "scheduled-overlay-forced-timeout",
        "completed_at": completed_at,
        "failure": {
            "category": "timeout",
            "stage": "model_call",
            "message_code": "forced_timeout",
            "retriable": True,
        },
        "attestation": {
            "auth_mode": "chatgpt_subscription",
            "sandbox": "read-only",
            "network_access": False,
            "rendered_input_sha256": request["rendered_input_sha256"],
            "event_types": [
                "thread_started",
                "turn_started",
                "turn_completed",
            ],
        },
        "usage": {
            "wall_clock_ms": used_ms,
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": {
                "currency": "GBP",
                "amount": None,
                "metering_status": "unavailable",
            },
        },
    }


def run_overlay_arm(
    *,
    request: Mapping[str, Any],
    deterministic_candidate: Mapping[str, Any],
    code_commit: str,
    invoke: InvokeFn | None = None,
    force_timeout: bool = False,
    evidence_proposal: Mapping[str, Any] | None = None,
    completed_at: str | None = None,
    traces_dir: Path | None = None,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Run one evidence or challenger arm with optional forced timeout."""

    stamp = completed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if force_timeout:
        hosted: Mapping[str, Any] | None = build_forced_timeout_hosted_response(
            request,
            completed_at=stamp,
        )
    elif invoke is None:
        hosted = None
    else:
        hosted = invoke(request)
    result = run_agent_arm(
        request=request,
        hosted_response=hosted,
        deterministic_candidate=deterministic_candidate,
        code_commit=code_commit,
        evidence_proposal=evidence_proposal,
    )
    if write_trace:
        write_agent_trace(result, traces_dir=traces_dir)
    return result


def build_overlay_evidence_summary(overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Map overlay execution into the ``run_gameweek`` evidence input shape."""

    status = str(overlay.get("status") or "absent")
    if status == "completed":
        evidence_status = "ok"
    elif status in {"degraded", "timeout", "t90m_cutoff"}:
        evidence_status = "late"
    else:
        evidence_status = "absent"
    return {
        "status": evidence_status,
        "overlay_status": status,
        "source": "scheduled-agent-overlay-v1",
        "run_ids": list(overlay.get("run_ids") or []),
        "degraded_reasons": list(overlay.get("degraded_reasons") or []),
        "accepted_adjustment_ids": list(overlay.get("accepted_adjustment_ids") or []),
        "supporting_claim_ids": list(overlay.get("supporting_claim_ids") or []),
        "content_sha256": overlay.get("content_sha256"),
    }


def attach_overlay_to_decision_record(
    record: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach scheduled overlay provenance and citations onto a GDR."""

    result = deepcopy(dict(record))
    evidence = dict(result.get("evidence") or {})
    evidence.update(
        {
            "supporting_claim_ids": list(overlay.get("supporting_claim_ids") or []),
            "conflicting_claim_ids": list(overlay.get("conflicting_claim_ids") or []),
            "conflict_ids": list(overlay.get("conflict_ids") or []),
            "proposed_adjustment_ids": list(
                overlay.get("proposed_adjustment_ids") or []
            ),
            "accepted_adjustment_ids": list(
                overlay.get("accepted_adjustment_ids") or []
            ),
        }
    )
    result["evidence"] = evidence
    result["agent_overlay"] = {
        "policy_version": "scheduled-agent-overlay-v1",
        "status": overlay.get("status"),
        "checkpoint": overlay.get("checkpoint"),
        "run_ids": list(overlay.get("run_ids") or []),
        "trace_paths": list(overlay.get("trace_paths") or []),
        "degraded_reasons": list(overlay.get("degraded_reasons") or []),
        "accepted_adjustments": list(overlay.get("accepted_adjustments") or []),
        "content_sha256": overlay.get("content_sha256"),
    }
    if overlay.get("status") in {"degraded", "timeout", "t90m_cutoff"}:
        reasons = list(result.get("degraded_reasons") or [])
        for reason in overlay.get("degraded_reasons") or ["agent_overlay_degraded"]:
            if reason not in reasons:
                reasons.append(str(reason))
        result["degraded"] = True
        result["degraded_reasons"] = sorted(set(reasons))
        result["data_quality"] = "degraded"
    pipeline = dict(result.get("pipeline") or {})
    components = list(pipeline.get("components") or [])
    if "orchestration.scheduled_agent_overlay" not in components:
        components.append("orchestration.scheduled_agent_overlay")
    pipeline["components"] = components
    result["pipeline"] = pipeline
    return result


def run_scheduled_overlay(
    *,
    deadline: str,
    now: str,
    evidence_request: Mapping[str, Any] | None,
    challenger_request: Mapping[str, Any] | None,
    deterministic_candidate: Mapping[str, Any],
    code_commit: str,
    policy: Mapping[str, Any] | None = None,
    invoke_evidence: InvokeFn | None = None,
    invoke_challenger: InvokeFn | None = None,
    force_timeout: bool = False,
    checkpoint: str | None = None,
    traces_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute due overlay arms or degrade at/after the T-90m cutoff.

    ``force_timeout`` injects a hosted timeout for the first arm that would
    otherwise run — the forced-timeout contract for ticket 11.
    """

    loaded = dict(policy or load_overlay_policy())
    if past_t90m_cutoff(
        deadline,
        now,
        offset_minutes=int(loaded.get("t90m_offset_minutes", 90)),
    ):
        overlay = {
            "schema_version": "scheduled-agent-overlay-result-v1",
            "status": "t90m_cutoff",
            "checkpoint": None,
            "run_ids": [],
            "trace_paths": [],
            "degraded_reasons": ["agent_t90m_fallback_deterministic"],
            "accepted_adjustment_ids": [],
            "accepted_adjustments": [],
            "supporting_claim_ids": [],
            "conflicting_claim_ids": [],
            "conflict_ids": [],
            "proposed_adjustment_ids": [],
            "evidence_run": None,
            "challenger_run": None,
        }
        overlay["content_sha256"] = artifact_hash(overlay)
        return overlay

    due = plan_due_overlay_stages(loaded, deadline=deadline, now=now)
    if checkpoint is not None:
        due = [row for row in due if row["checkpoint"] == checkpoint]
    if not due:
        overlay = {
            "schema_version": "scheduled-agent-overlay-result-v1",
            "status": "absent",
            "checkpoint": checkpoint,
            "run_ids": [],
            "trace_paths": [],
            "degraded_reasons": ["agent_overlay_stage_not_due"],
            "accepted_adjustment_ids": [],
            "accepted_adjustments": [],
            "supporting_claim_ids": [],
            "conflicting_claim_ids": [],
            "conflict_ids": [],
            "proposed_adjustment_ids": [],
            "evidence_run": None,
            "challenger_run": None,
        }
        overlay["content_sha256"] = artifact_hash(overlay)
        return overlay

    stage = due[0]
    arms = {str(arm) for arm in stage["arms"]}
    run_ids: list[str] = []
    trace_paths: list[str] = []
    degraded_reasons: list[str] = []
    evidence_run: dict[str, Any] | None = None
    challenger_run: dict[str, Any] | None = None

    if "evidence_agent" in arms:
        if evidence_request is None:
            raise ScheduledAgentOverlayError("evidence_request required for stage")
        evidence_run = run_overlay_arm(
            request=evidence_request,
            deterministic_candidate=deterministic_candidate,
            code_commit=code_commit,
            invoke=invoke_evidence,
            force_timeout=force_timeout,
            traces_dir=traces_dir,
        )
        run_ids.append(str(evidence_run["run_id"]))
        declared = evidence_run.get("trace", {}).get("trace_path")
        if declared:
            trace_paths.append(str(declared))
        if evidence_run["status"] != "completed":
            degraded_reasons.append(
                f"evidence_{evidence_run.get('trace', {}).get('failure', {}).get('category', 'degraded')}"
            )

    need_challenger = "evidence_challenger" in arms and evidence_run is not None
    if need_challenger and evidence_run and evidence_run["status"] == "completed":
        if challenger_request is None:
            raise ScheduledAgentOverlayError("challenger_request required for stage")
        challenger_run = run_overlay_arm(
            request=challenger_request,
            deterministic_candidate=deterministic_candidate,
            code_commit=code_commit,
            invoke=invoke_challenger,
            force_timeout=False,
            evidence_proposal=evidence_run,
            traces_dir=traces_dir,
        )
        run_ids.append(str(challenger_run["run_id"]))
        declared = challenger_run.get("trace", {}).get("trace_path")
        if declared:
            trace_paths.append(str(declared))
        if challenger_run["status"] != "completed":
            degraded_reasons.append(
                f"challenger_{challenger_run.get('trace', {}).get('failure', {}).get('category', 'degraded')}"
            )
    elif need_challenger and evidence_run and evidence_run["status"] != "completed":
        degraded_reasons.append("challenger_skipped_after_evidence_degrade")

    accepted: list[dict[str, Any]] = []
    supporting: list[str] = []
    conflicting: list[str] = []
    conflicts: list[str] = []
    proposed_ids: list[str] = []
    status = "degraded"
    if (
        evidence_run is not None
        and evidence_run["status"] == "completed"
        and (
            "evidence_challenger" not in arms
            or (
                challenger_run is not None
                and challenger_run["status"] == "completed"
            )
        )
    ):
        status = "completed"
        output = evidence_run.get("validated_output") or {}
        if isinstance(output, Mapping):
            supporting = [str(row.get("claim_id")) for row in output.get("claims") or [] if row.get("claim_id")]
            proposed = list(output.get("proposed_adjustments") or [])
            proposed_ids = [
                str(row.get("adjustment_id"))
                for row in proposed
                if row.get("adjustment_id")
            ]
            if challenger_run and isinstance(challenger_run.get("validated_output"), Mapping):
                review = challenger_run["validated_output"]
                unopposed = set(review.get("unopposed_proposed_adjustment_ids") or [])
                accepted = [
                    deepcopy(dict(row))
                    for row in proposed
                    if str(row.get("adjustment_id")) in unopposed
                ]
            else:
                accepted = [deepcopy(dict(row)) for row in proposed]
            conflicting = [
                str(row.get("claim_id"))
                for row in (output.get("conflicting_claims") or [])
                if isinstance(row, Mapping) and row.get("claim_id")
            ]
            conflicts = [
                str(row.get("conflict_id"))
                for row in (output.get("conflicts") or [])
                if isinstance(row, Mapping) and row.get("conflict_id")
            ]

    if any("timeout" in reason for reason in degraded_reasons):
        status = "timeout"

    overlay = {
        "schema_version": "scheduled-agent-overlay-result-v1",
        "status": status,
        "checkpoint": stage["checkpoint"],
        "run_ids": run_ids,
        "trace_paths": trace_paths,
        "degraded_reasons": degraded_reasons,
        "accepted_adjustment_ids": [
            str(row.get("adjustment_id"))
            for row in accepted
            if row.get("adjustment_id")
        ],
        "accepted_adjustments": accepted,
        "supporting_claim_ids": supporting,
        "conflicting_claim_ids": conflicting,
        "conflict_ids": conflicts,
        "proposed_adjustment_ids": proposed_ids,
        "evidence_run_sha256": (
            None if evidence_run is None else evidence_run.get("content_sha256")
        ),
        "challenger_run_sha256": (
            None if challenger_run is None else challenger_run.get("content_sha256")
        ),
    }
    overlay["content_sha256"] = artifact_hash(overlay)
    overlay["evidence_run"] = evidence_run
    overlay["challenger_run"] = challenger_run
    return overlay
