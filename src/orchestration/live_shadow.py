"""Immutable paired live-shadow orchestration with no FPL execution."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.evaluation.shadow_attribution import attribute_shadow_outcomes
from src.orchestration.policy_state import transition_policy_state
from src.orchestration.validated_plan import validate_and_freeze_plan


class LiveShadowError(ValueError):
    """Raised when a prospective shadow week cannot be frozen safely."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def shadow_hash(value: Mapping[str, Any]) -> str:
    projection = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveShadowError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveShadowError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _registered_source(
    source_registry: Mapping[str, Any], source_id: str
) -> dict[str, Any]:
    source = next(
        (
            dict(item)
            for item in source_registry.get("sources", [])
            if item.get("source_id") == source_id
        ),
        None,
    )
    if source is None:
        raise LiveShadowError(f"Evidence source is not registered: {source_id}")
    if not source.get("enabled"):
        raise LiveShadowError(f"Evidence source is disabled: {source_id}")
    if source.get("licence_status") in {None, "unknown", "prohibited"}:
        raise LiveShadowError(
            f"Evidence source licence is unresolved or prohibited: {source_id}"
        )
    if not source.get("allowed_use"):
        raise LiveShadowError(f"Evidence source has no allowed use: {source_id}")
    return source


def build_unstructured_evidence_capture(
    *,
    snapshots: Sequence[Mapping[str, Any]],
    source_registry: Mapping[str, Any],
    decision_cutoff: str,
) -> dict[str, Any]:
    """Validate local document snapshots and return a content-addressed index."""

    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    admitted: list[dict[str, Any]] = []
    seen_documents: set[str] = set()
    for index, source_value in enumerate(snapshots):
        source = deepcopy(dict(source_value))
        required = {
            "source_id",
            "document_id",
            "url",
            "title",
            "published_at",
            "observed_at",
            "available_at",
            "content",
            "content_sha256",
        }
        missing = sorted(required - set(source))
        if missing:
            raise LiveShadowError(
                f"Evidence snapshot {index} missing fields: {', '.join(missing)}"
            )
        source_id = str(source["source_id"])
        registry_entry = _registered_source(source_registry, source_id)
        document_id = str(source["document_id"])
        if document_id in seen_documents:
            raise LiveShadowError(f"Duplicate evidence document: {document_id}")
        seen_documents.add(document_id)
        published_text, published = _timestamp(
            source["published_at"], f"snapshot {document_id}.published_at"
        )
        observed_text, observed = _timestamp(
            source["observed_at"], f"snapshot {document_id}.observed_at"
        )
        available_text, available = _timestamp(
            source["available_at"], f"snapshot {document_id}.available_at"
        )
        if not published <= observed <= available:
            raise LiveShadowError(
                f"Evidence timestamps are out of order for {document_id}"
            )
        if available > cutoff:
            raise LiveShadowError(
                f"Evidence document is available after decision cutoff: {document_id}"
            )
        content = str(source["content"])
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if source["content_sha256"] != content_sha256:
            raise LiveShadowError(
                f"Evidence content hash mismatch for {document_id}"
            )
        identity = {
            "source_id": source_id,
            "document_id": document_id,
            "url": str(source["url"]),
            "published_at": published_text,
            "observed_at": observed_text,
            "available_at": available_text,
            "content_sha256": content_sha256,
        }
        admitted.append(
            {
                **identity,
                "snapshot_id": hashlib.sha256(
                    _canonical_bytes(identity)
                ).hexdigest(),
                "title": str(source["title"]),
                "attribution": str(registry_entry["attribution"]),
                "raw_file": str(source.get("raw_file", "")),
            }
        )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "complete" if admitted else "degraded",
        "decision_cutoff": cutoff_text,
        "snapshots": sorted(admitted, key=lambda row: row["snapshot_id"]),
        "degraded_reasons": (
            [] if admitted else ["no_governed_unstructured_evidence_available"]
        ),
    }
    result["content_sha256"] = shadow_hash(result)
    return result


def validate_unstructured_evidence_capture(value: Mapping[str, Any]) -> None:
    capture = dict(value)
    if capture.get("content_sha256") != shadow_hash(capture):
        raise LiveShadowError("Unstructured evidence capture hash mismatch")
    status = capture.get("status")
    snapshots = capture.get("snapshots")
    if status not in {"complete", "degraded"} or not isinstance(snapshots, list):
        raise LiveShadowError("Unstructured evidence capture shape is invalid")
    if status == "complete" and not snapshots:
        raise LiveShadowError("Complete evidence capture has no snapshots")
    if status == "degraded" and snapshots:
        raise LiveShadowError("Degraded evidence capture cannot admit snapshots")
    _, cutoff = _timestamp(capture.get("decision_cutoff"), "decision_cutoff")
    for snapshot in snapshots:
        _, available = _timestamp(snapshot.get("available_at"), "available_at")
        if available > cutoff:
            raise LiveShadowError("Evidence snapshot is available after cutoff")


def _policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(policy))
    if result.get("content_sha256") != shadow_hash(result):
        raise LiveShadowError("Live-shadow policy hash mismatch")
    if result.get("mode") != "observation_only_no_fpl_execution":
        raise LiveShadowError("Live-shadow policy is not observation-only")
    return result


def _agent_completed(
    run: Mapping[str, Any] | None,
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[bool, str | None]:
    if run is None:
        return False, "agent_run_missing"
    gate = policy["agent_completion_gate"]
    if run.get("status") != gate["required_status"]:
        return False, "agent_run_incomplete"
    if gate.get("requires_validated_output") and not isinstance(
        run.get("validated_output"), Mapping
    ):
        return False, "validated_output_missing"
    if dict(run.get("selected_candidate", {})) != dict(candidate):
        return False, "selected_candidate_binding_mismatch"
    return True, None


def freeze_live_shadow_week(
    *,
    episode_manifest: Mapping[str, Any],
    structured_context: Mapping[str, Any],
    decision_market: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    control_state: Mapping[str, Any],
    evidence_state: Mapping[str, Any],
    control_candidate: Mapping[str, Any],
    evidence_baseline_candidate: Mapping[str, Any],
    evidence_candidate: Mapping[str, Any],
    evidence_capture: Mapping[str, Any],
    agent_run: Mapping[str, Any] | None,
    frozen_at: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    policy: Mapping[str, Any],
    control_chip: str | None = None,
    evidence_baseline_chip: str | None = None,
    evidence_chip: str | None = None,
) -> dict[str, Any]:
    """Freeze control, same-state bridge, and evidence plans before cutoff."""

    live_policy = _policy(policy)
    manifest = deepcopy(dict(episode_manifest))
    if manifest.get("mode") != "live_shadow":
        raise LiveShadowError("Paired shadow requires a live_shadow episode")
    cutoff_text, cutoff = _timestamp(manifest.get("cutoff"), "episode cutoff")
    frozen_text, frozen = _timestamp(frozen_at, "frozen_at")
    if frozen > cutoff:
        raise LiveShadowError("All live-shadow plans must freeze by the episode cutoff")
    if control_state.get("policy_arm") != "forecast_optimizer":
        raise LiveShadowError("Control state must belong to forecast_optimizer")
    if evidence_state.get("policy_arm") != "evidence_agent":
        raise LiveShadowError("Evidence state must belong to evidence_agent")
    if (
        control_state.get("season") != manifest.get("season")
        or evidence_state.get("season") != manifest.get("season")
        or control_state.get("gameweek") != manifest.get("gameweek")
        or evidence_state.get("gameweek") != manifest.get("gameweek")
    ):
        raise LiveShadowError("Arm states do not match the live episode")
    validate_unstructured_evidence_capture(evidence_capture)
    if evidence_capture.get("decision_cutoff") != cutoff_text:
        raise LiveShadowError("Evidence capture cutoff differs from episode cutoff")

    context = {
        "structured_context": deepcopy(dict(structured_context)),
        "decision_market": deepcopy(
            list(decision_market)
            if not isinstance(decision_market, Mapping)
            else dict(decision_market)
        ),
    }
    structured_sha256 = hashlib.sha256(_canonical_bytes(context)).hexdigest()
    completed, fallback_reason = _agent_completed(
        agent_run, evidence_candidate, live_policy
    )
    evidence_available = evidence_capture.get("status") == "complete"
    use_evidence = completed and evidence_available
    if not evidence_available:
        fallback_reason = "evidence_capture_degraded"
    selected_evidence_candidate = (
        deepcopy(dict(evidence_candidate))
        if use_evidence
        else deepcopy(dict(evidence_baseline_candidate))
    )
    selected_evidence_chip = evidence_chip if use_evidence else evidence_baseline_chip

    common = {
        "episode_id": str(manifest["episode_id"]),
        "decision_market": decision_market,
        "frozen_at": frozen_text,
        "rules": rules,
        "ruleset_sha256": ruleset_sha256,
    }
    control_plan = validate_and_freeze_plan(
        policy_arm="forecast_optimizer",
        state=control_state,
        candidate=control_candidate,
        active_chip=control_chip,
        **common,
    )
    evidence_baseline_plan = validate_and_freeze_plan(
        policy_arm="evidence_agent",
        state=evidence_state,
        candidate=evidence_baseline_candidate,
        active_chip=evidence_baseline_chip,
        **common,
    )
    evidence_actual_plan = validate_and_freeze_plan(
        policy_arm="evidence_agent",
        state=evidence_state,
        candidate=selected_evidence_candidate,
        active_chip=selected_evidence_chip,
        **common,
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "shadow_week_id": (
            f"live-shadow-pair:{manifest['season']}:gw{int(manifest['gameweek']):02d}"
        ),
        "episode_id": str(manifest["episode_id"]),
        "season": str(manifest["season"]),
        "gameweek": int(manifest["gameweek"]),
        "cutoff": cutoff_text,
        "frozen_at": frozen_text,
        "mode": "advisory_only",
        "browser_actions": False,
        "account_writes": False,
        "shared_structured_context_sha256": structured_sha256,
        "arm_inputs": {
            "forecast_optimizer": {
                "structured_context_sha256": structured_sha256,
                "state_sha256": str(control_state["content_sha256"]),
                "evidence_allowed": False,
            },
            "evidence_agent": {
                "structured_context_sha256": structured_sha256,
                "state_sha256": str(evidence_state["content_sha256"]),
                "evidence_allowed": True,
                "evidence_capture_sha256": str(
                    evidence_capture["content_sha256"]
                ),
            },
        },
        "agent_gate": {
            "status": "completed" if use_evidence else "fallback_to_control_policy",
            "reason": None if use_evidence else fallback_reason,
            "run_sha256": (
                str(agent_run.get("content_sha256", "")) if agent_run else None
            ),
        },
        "plans": {
            "deterministic_control": control_plan,
            "evidence_state_no_evidence": evidence_baseline_plan,
            "evidence_actual": evidence_actual_plan,
        },
        "policy_sha256": str(live_policy["content_sha256"]),
    }
    result["content_sha256"] = shadow_hash(result)
    return result


def reveal_live_shadow_week(
    *,
    frozen_week: Mapping[str, Any],
    control_state: Mapping[str, Any],
    evidence_state: Mapping[str, Any],
    control_outcome: Mapping[str, Any],
    evidence_baseline_outcome: Mapping[str, Any],
    evidence_actual_outcome: Mapping[str, Any],
    decision_market: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    next_market: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Reveal one shared Gameweek and advance only the two actual trajectories."""

    frozen = deepcopy(dict(frozen_week))
    if frozen.get("content_sha256") != shadow_hash(frozen):
        raise LiveShadowError("Frozen live-shadow week hash mismatch")
    plans = frozen["plans"]
    control_next, control_transition = transition_policy_state(
        control_state,
        plans["deterministic_control"],
        control_outcome,
        decision_market=decision_market,
        next_market=next_market,
        rules=rules,
        ruleset_sha256=ruleset_sha256,
    )
    evidence_next, evidence_transition = transition_policy_state(
        evidence_state,
        plans["evidence_actual"],
        evidence_actual_outcome,
        decision_market=decision_market,
        next_market=next_market,
        rules=rules,
        ruleset_sha256=ruleset_sha256,
    )
    attribution = attribute_shadow_outcomes(
        control_plan=plans["deterministic_control"],
        evidence_baseline_plan=plans["evidence_state_no_evidence"],
        evidence_actual_plan=plans["evidence_actual"],
        control_outcome=control_outcome,
        evidence_baseline_outcome=evidence_baseline_outcome,
        evidence_actual_outcome=evidence_actual_outcome,
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "shadow_week_id": str(frozen["shadow_week_id"]),
        "episode_id": str(frozen["episode_id"]),
        "mode": "advisory_only",
        "browser_actions": False,
        "account_writes": False,
        "frozen_week_sha256": str(frozen["content_sha256"]),
        "attribution": attribution,
        "transitions": {
            "forecast_optimizer": control_transition,
            "evidence_agent": evidence_transition,
        },
        "next_states": {
            "forecast_optimizer": control_next,
            "evidence_agent": evidence_next,
        },
    }
    result["content_sha256"] = shadow_hash(result)
    return result


def write_shadow_artifact(path: Path, value: Mapping[str, Any]) -> None:
    """Write one canonical artifact, refusing a conflicting rerun."""

    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise LiveShadowError(f"Refusing to overwrite shadow artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
