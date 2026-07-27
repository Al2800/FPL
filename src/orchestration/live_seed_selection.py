"""Prospective, advisory-only orchestration for an FPL initial squad."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.optimisation.initial_squad import (
    InitialSquadError,
    apply_initial_squad_adjustments,
    initial_squad_hash,
    optimise_initial_squad,
    score_declared_initial_squad,
    validate_initial_squad_packet,
)


class LiveSeedSelectionError(ValueError):
    """Raised when the live seed-selection lab cannot fail closed."""


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveSeedSelectionError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveSeedSelectionError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _external_completion(
    source: Mapping[str, Any],
    *,
    packet_sha256: str,
) -> tuple[bool, str | None]:
    completion = source.get("completion")
    if not isinstance(completion, Mapping):
        return False, "completion_metadata_missing"
    if completion.get("status") != "completed":
        return False, "external_arm_incomplete"
    if completion.get("base_packet_sha256") != packet_sha256:
        return False, "base_packet_binding_mismatch"
    if not isinstance(completion.get("validated_output"), Mapping):
        return False, "validated_output_missing"
    return True, None


def _run_external_arm(
    arm_id: str,
    source: Mapping[str, Any] | None,
    *,
    packet: Mapping[str, Any],
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    if source is None:
        return {
            "status": "not_run",
            "reason": "external_arm_missing",
            "base_packet_sha256": packet["content_sha256"],
        }
    completed, reason = _external_completion(
        source, packet_sha256=packet["content_sha256"]
    )
    if not completed:
        return {
            "status": "rejected",
            "reason": reason,
            "base_packet_sha256": packet["content_sha256"],
        }
    try:
        if source.get("adjustments") is not None:
            adjusted = apply_initial_squad_adjustments(
                packet,
                source["adjustments"],
                maximum_absolute_delta=float(
                    policy["external_adjustments"][
                        "maximum_absolute_points_delta_per_gameweek"
                    ]
                ),
            )
            result = optimise_initial_squad(
                adjusted,
                policy=policy,
                arm_mode=arm_id,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
            selected_ids = result["selected"]["squad_player_ids"]
            base_evaluation = score_declared_initial_squad(
                packet,
                selected_ids,
                policy=policy,
                arm_mode=arm_id,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
            return {
                "status": "complete",
                "kind": "bounded_adjustments_then_optimiser",
                "base_packet_sha256": packet["content_sha256"],
                "adjusted_packet_sha256": adjusted["content_sha256"],
                "adjustment_ledger": deepcopy(adjusted["adjustment_ledger"]),
                "result": result,
                "base_packet_evaluation": base_evaluation,
                "completion": deepcopy(dict(source["completion"])),
            }
        squad_ids = source.get("squad_player_ids")
        if not isinstance(squad_ids, list):
            raise InitialSquadError(
                "External arm requires adjustments or squad_player_ids"
            )
        scored = score_declared_initial_squad(
            packet,
            squad_ids,
            policy=policy,
            arm_mode=arm_id,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
        return {
            "status": "complete",
            "kind": "declared_proposal",
            "base_packet_sha256": packet["content_sha256"],
            "result": {
                "schema_version": "1.0",
                "status": "complete",
                "arm_mode": arm_id,
                "packet_sha256": packet["content_sha256"],
                "policy_id": str(policy["policy_id"]),
                "policy_version": str(policy["policy_version"]),
                "ruleset_id": str(packet["ruleset_id"]),
                "ruleset_sha256": ruleset_sha256,
                "selected": scored,
                "alternatives": [],
            },
            "base_packet_evaluation": scored,
            "completion": deepcopy(dict(source["completion"])),
        }
    except InitialSquadError as exc:
        return {
            "status": "rejected",
            "reason": str(exc),
            "base_packet_sha256": packet["content_sha256"],
        }


def _selected_proposal(arm: Mapping[str, Any]) -> dict[str, Any]:
    result = arm.get("result")
    if not isinstance(result, Mapping) or not isinstance(
        result.get("selected"), Mapping
    ):
        raise LiveSeedSelectionError("Selected arm has no completed proposal")
    return deepcopy(dict(result["selected"]))


def _sensitivity(
    proposal: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    policy: Mapping[str, Any],
    arm_mode: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> list[dict[str, Any]]:
    base_penalty = float(policy["arms"][arm_mode]["uncertainty_penalty"])
    rows: list[dict[str, Any]] = []
    for multiplier in policy["sensitivity"]["uncertainty_penalty_multipliers"]:
        adjusted_policy = deepcopy(dict(policy))
        adjusted_policy["arms"][arm_mode]["uncertainty_penalty"] = (
            base_penalty * float(multiplier)
        )
        scored = score_declared_initial_squad(
            packet,
            proposal["squad_player_ids"],
            policy=adjusted_policy,
            arm_mode=arm_mode,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
        rows.append(
            {
                "factor": "uncertainty_penalty",
                "multiplier": float(multiplier),
                "value": float(scored["objective"]),
                "delta_from_selected_view": round(
                    float(scored["objective"]) - float(proposal["objective"]), 6
                ),
            }
        )
    return rows


def _approval_gate(
    *,
    arms: Mapping[str, Mapping[str, Any]],
    selected_arm: str,
    proposal: Mapping[str, Any],
    packet: Mapping[str, Any],
    policy: Mapping[str, Any],
    rules_activation: Mapping[str, Any] | None,
    approval: Mapping[str, Any] | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    for arm_id in policy["approval_gate"]["requires_completed_arms"]:
        if arms.get(str(arm_id), {}).get("status") != "complete":
            blockers.append(f"required_arm_incomplete:{arm_id}")
    if arms.get(selected_arm, {}).get("status") != "complete":
        blockers.append("selected_arm_incomplete")

    if policy["approval_gate"].get("requires_active_ruleset"):
        if not isinstance(rules_activation, Mapping):
            blockers.append("rules_activation_missing")
        else:
            if rules_activation.get("status") != "active":
                blockers.append("ruleset_not_active")
            if rules_activation.get("ruleset_sha256") != packet["ruleset_sha256"]:
                blockers.append("ruleset_activation_hash_mismatch")

    normalised_approval: dict[str, Any] | None = None
    if not isinstance(approval, Mapping):
        blockers.append("owner_approval_missing")
    else:
        normalised_approval = deepcopy(dict(approval))
        if approval.get("status") != "approved":
            blockers.append("owner_approval_not_approved")
        if not str(approval.get("approved_by", "")).strip():
            blockers.append("owner_identity_missing")
        try:
            approved_text, approved_at = _timestamp(
                approval.get("approved_at"), "approval.approved_at"
            )
            _, cutoff = _timestamp(packet["decision_cutoff"], "decision_cutoff")
            if approved_at > cutoff:
                blockers.append("owner_approval_after_cutoff")
            normalised_approval["approved_at"] = approved_text
        except LiveSeedSelectionError:
            blockers.append("owner_approval_time_invalid")
        if approval.get("selected_arm") != selected_arm:
            blockers.append("owner_approval_arm_mismatch")
        if approval.get("proposal_sha256") != proposal["proposal_sha256"]:
            blockers.append("owner_approval_proposal_hash_mismatch")
        if approval.get("base_packet_sha256") != packet["content_sha256"]:
            blockers.append("owner_approval_packet_hash_mismatch")

    return {
        "status": "ready_for_manual_entry" if not blockers else "blocked",
        "blockers": blockers,
        "owner_approval": normalised_approval,
        "manual_entry_only": True,
        "account_write_authorised": False,
    }


def run_live_seed_selection(
    *,
    packet: Mapping[str, Any],
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    external_arms: Mapping[str, Mapping[str, Any]] | None = None,
    selected_arm: str = "robust",
    rules_activation: Mapping[str, Any] | None = None,
    approval: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run every declared arm on one base packet and apply the approval gate."""

    validated = validate_initial_squad_packet(
        packet, rules=rules, ruleset_sha256=ruleset_sha256
    )
    arms: dict[str, dict[str, Any]] = {}
    for arm_id in ("deterministic", "robust"):
        result = optimise_initial_squad(
            validated,
            policy=policy,
            arm_mode=arm_id,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
        arms[arm_id] = {
            "status": "complete",
            "kind": "optimiser",
            "base_packet_sha256": validated["content_sha256"],
            "result": result,
        }
    supplied = external_arms or {}
    for arm_id in ("evidence_agent", "challenger", "human_reference"):
        arms[arm_id] = _run_external_arm(
            arm_id,
            supplied.get(arm_id),
            packet=validated,
            policy=policy,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )

    if selected_arm not in arms:
        raise LiveSeedSelectionError(f"Unknown selected arm: {selected_arm}")
    if arms[selected_arm]["status"] != "complete":
        selected_arm = "robust"
        selection_reason = "requested_arm_incomplete_fallback_to_robust"
    else:
        selection_reason = "requested_arm_complete"
    proposal = _selected_proposal(arms[selected_arm])
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "decision_id": str(validated["decision_id"]),
        "season": str(validated["season"]),
        "decision_cutoff": str(validated["decision_cutoff"]),
        "mode": "advisory_only",
        "browser_actions": False,
        "account_writes": False,
        "base_packet_sha256": validated["content_sha256"],
        "policy": {
            "policy_id": str(policy["policy_id"]),
            "policy_version": str(policy["policy_version"]),
            "content_sha256": initial_squad_hash(dict(policy)),
        },
        "ruleset": {
            "ruleset_id": str(validated["ruleset_id"]),
            "content_sha256": ruleset_sha256,
        },
        "arms": arms,
        "selection": {
            "selected_arm": selected_arm,
            "reason": selection_reason,
            "proposal": proposal,
            "alternatives": deepcopy(
                list(arms[selected_arm]["result"].get("alternatives", []))
            ),
        },
        "sensitivity": _sensitivity(
            proposal,
            packet=validated,
            policy=policy,
            arm_mode=selected_arm,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        ),
    }
    result["approval_gate"] = _approval_gate(
        arms=arms,
        selected_arm=selected_arm,
        proposal=proposal,
        packet=validated,
        policy=policy,
        rules_activation=rules_activation,
        approval=approval,
    )
    result["content_sha256"] = initial_squad_hash(result)
    return result


def write_live_seed_artifact(path: Path, value: Mapping[str, Any]) -> None:
    """Write an immutable advisory artifact, allowing only an identical rerun."""

    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise LiveSeedSelectionError(
                f"Refusing to overwrite live seed artifact: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
