"""Freeze a live evidence arm beside an immutable no-evidence control."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.evidence.live_evidence_ledger import (
    live_evidence_hash,
)
from src.forecasting.live_faithful import artifact_hash


class LiveEvidenceArmError(ValueError):
    """Raised when the live evidence arm cannot freeze safely."""


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveEvidenceArmError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveEvidenceArmError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _sha256(value: Any, field: str) -> str:
    digest = str(value)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise LiveEvidenceArmError(f"{field} must be a lower-case SHA-256")
    return digest


def _candidate_hash(candidate: Mapping[str, Any]) -> str:
    supplied = candidate.get("content_sha256")
    computed = artifact_hash(candidate)
    if supplied is not None and supplied != computed:
        raise LiveEvidenceArmError("Candidate content hash mismatch")
    return computed


def _fallback(
    reason: str,
    *,
    no_evidence_candidate: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        deepcopy(dict(no_evidence_candidate)),
        {
            "status": "fallback_to_no_evidence",
            "reason": reason,
        },
        {
            "status": "not_used",
            "reason": "agent_proposal_not_admitted",
        },
    )


def _agent_output(
    run: Mapping[str, Any] | None,
    *,
    engine_output_sha256: str,
    evidence_packet: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
    if not isinstance(run, Mapping):
        return None, {"status": "failed", "reason": "agent_run_missing"}, None
    if run.get("status") != config["agent_gate"]["required_agent_status"]:
        return None, {"status": "failed", "reason": "agent_run_incomplete"}, None
    if run.get("engine_output_sha256") != engine_output_sha256:
        return None, {
            "status": "failed",
            "reason": "agent_engine_binding_mismatch",
        }, None
    if run.get("evidence_packet_sha256") != evidence_packet["content_sha256"]:
        return None, {
            "status": "failed",
            "reason": "agent_packet_binding_mismatch",
        }, None
    output = run.get("validated_output")
    if not isinstance(output, Mapping):
        return None, {
            "status": "failed",
            "reason": "agent_validated_output_missing",
        }, None
    if output.get("schema_version") != "1.0":
        return None, {
            "status": "failed",
            "reason": "agent_output_schema_invalid",
        }, None
    action = output.get("action")
    if action not in {"abstain", "propose"}:
        return None, {
            "status": "failed",
            "reason": "agent_action_invalid",
        }, None
    accepted_ids = output.get("accepted_claim_ids")
    if not isinstance(accepted_ids, list) or any(
        not isinstance(item, str) or not item for item in accepted_ids
    ):
        return None, {
            "status": "failed",
            "reason": "agent_claim_ids_invalid",
        }, None
    packet_ids = {
        str(row["claim"]["claim_id"]) for row in evidence_packet["evidence"]
    }
    if not set(accepted_ids) <= packet_ids:
        return None, {
            "status": "failed",
            "reason": "agent_used_claim_outside_packet",
        }, None
    if action == "abstain":
        if output.get("proposal") is not None:
            return None, {
                "status": "failed",
                "reason": "abstention_must_not_include_proposal",
            }, None
        return None, {
            "status": "abstained",
            "reason": str(output.get("rationale", "")),
            "accepted_claim_ids": sorted(set(accepted_ids)),
        }, None
    proposal = output.get("proposal")
    if not isinstance(proposal, Mapping):
        return None, {
            "status": "failed",
            "reason": "agent_proposal_missing",
        }, None
    try:
        proposal_hash = _candidate_hash(proposal)
    except LiveEvidenceArmError:
        return None, {
            "status": "failed",
            "reason": "agent_proposal_hash_invalid",
        }, None
    if output.get("proposal_sha256") != proposal_hash:
        return None, {
            "status": "failed",
            "reason": "agent_proposal_hash_binding_mismatch",
        }, None
    confidence = output.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= float(confidence) <= 1
    ):
        return None, {
            "status": "failed",
            "reason": "agent_confidence_invalid",
        }, None
    return (
        deepcopy(dict(proposal)),
        {
            "status": "completed",
            "reason": None,
            "accepted_claim_ids": sorted(set(accepted_ids)),
            "confidence": float(confidence),
            "rationale": str(output.get("rationale", "")),
            "run_sha256": str(run.get("content_sha256", "")) or None,
        },
        proposal_hash,
    )


def _challenger_output(
    run: Mapping[str, Any] | None,
    *,
    proposal_sha256: str,
) -> tuple[bool, dict[str, Any]]:
    if not isinstance(run, Mapping):
        return False, {
            "status": "failed",
            "reason": "challenger_run_missing",
        }
    if run.get("status") != "completed":
        return False, {
            "status": "failed",
            "reason": "challenger_run_incomplete",
        }
    if run.get("proposal_sha256") != proposal_sha256:
        return False, {
            "status": "failed",
            "reason": "challenger_proposal_binding_mismatch",
        }
    output = run.get("validated_output")
    if not isinstance(output, Mapping) or output.get("schema_version") != "1.0":
        return False, {
            "status": "failed",
            "reason": "challenger_output_schema_invalid",
        }
    verdict = output.get("verdict")
    if verdict not in {"accept", "reject"}:
        return False, {
            "status": "failed",
            "reason": "challenger_verdict_invalid",
        }
    return (
        verdict == "accept",
        {
            "status": "completed",
            "verdict": verdict,
            "reason": str(output.get("rationale", "")),
            "run_sha256": str(run.get("content_sha256", "")) or None,
        },
    )


def freeze_live_evidence_arm(
    *,
    engine_output: Mapping[str, Any],
    no_evidence_candidate: Mapping[str, Any],
    evidence_packet: Mapping[str, Any],
    agent_run: Mapping[str, Any] | None,
    challenger_run: Mapping[str, Any] | None,
    frozen_at: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Freeze evidence and no-evidence plans before reveal, or degrade safely."""

    if evidence_packet.get("content_sha256") != live_evidence_hash(evidence_packet):
        raise LiveEvidenceArmError("Evidence packet content hash mismatch")
    engine_hash = _candidate_hash(engine_output)
    if evidence_packet.get("engine_output_sha256") != engine_hash:
        raise LiveEvidenceArmError(
            "Evidence packet is not bound to the supplied engine output"
        )
    frozen_text, frozen = _timestamp(frozen_at, "frozen_at")
    _, cutoff = _timestamp(evidence_packet.get("decision_at"), "decision_at")
    if frozen > cutoff:
        raise LiveEvidenceArmError("Evidence arm must freeze by decision cutoff")
    baseline_hash = _candidate_hash(no_evidence_candidate)
    no_evidence = deepcopy(dict(no_evidence_candidate))

    proposal: dict[str, Any] | None = None
    if evidence_packet.get("status") != "complete":
        selected, agent_gate, challenger_gate = _fallback(
            "evidence_packet_degraded",
            no_evidence_candidate=no_evidence,
        )
    else:
        proposal, agent_gate, proposal_hash = _agent_output(
            agent_run,
            engine_output_sha256=engine_hash,
            evidence_packet=evidence_packet,
            config=config,
        )
        if proposal is None:
            reason = (
                "agent_abstained"
                if agent_gate["status"] == "abstained"
                else str(agent_gate["reason"])
            )
            selected, _, challenger_gate = _fallback(
                reason, no_evidence_candidate=no_evidence
            )
            agent_gate = agent_gate
        elif config["agent_gate"].get("challenger_required"):
            admitted, challenger_gate = _challenger_output(
                challenger_run, proposal_sha256=str(proposal_hash)
            )
            if admitted:
                selected = deepcopy(proposal)
            else:
                selected, fallback_agent, _ = _fallback(
                    str(challenger_gate["reason"]),
                    no_evidence_candidate=no_evidence,
                )
                fallback_agent["proposal_status"] = agent_gate["status"]
                agent_gate = fallback_agent
        else:
            selected = deepcopy(proposal)
            challenger_gate = {
                "status": "not_required",
                "reason": None,
            }

    selected_hash = _candidate_hash(selected)
    changed = selected_hash != baseline_hash
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "mode": "advisory_only",
        "browser_actions": False,
        "account_writes": False,
        "frozen_at": frozen_text,
        "decision_at": evidence_packet["decision_at"],
        "shared_engine_output_sha256": engine_hash,
        "evidence_packet_sha256": evidence_packet["content_sha256"],
        "plans": {
            "frozen_no_evidence_control": {
                "candidate": no_evidence,
                "candidate_sha256": baseline_hash,
            },
            "evidence_actual": {
                "candidate": deepcopy(selected),
                "candidate_sha256": selected_hash,
            },
        },
        "agent_gate": agent_gate,
        "challenger_gate": challenger_gate,
        "effect_before_outcome": {
            "plan_changed": changed,
            "no_evidence_candidate_sha256": baseline_hash,
            "evidence_candidate_sha256": selected_hash,
            "accepted_claim_ids": deepcopy(
                agent_gate.get("accepted_claim_ids", [])
            ),
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def write_live_evidence_arm_artifact(
    path: Path, value: Mapping[str, Any]
) -> None:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise LiveEvidenceArmError(
                f"Refusing to overwrite live evidence arm artifact: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
