"""Independent challenger review for validated evidence proposals."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from src.evidence.lifecycle import evaluate_challenger_outcomes, validate_record
from src.forecasting.live_faithful import artifact_hash


class ChallengerAgentError(ValueError):
    """Raised when a challenger result is incomplete or exceeds authority."""


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_SCHEMA = ROOT / "prompts" / "challenger" / "output.schema.json"


def validate_challenger_result(
    result: Mapping[str, Any],
    *,
    evidence_run_id: str,
    proposal: Mapping[str, Any],
    observed_at: str,
) -> dict[str, Any]:
    schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(result)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ChallengerAgentError(
            "challenger output schema violation: " + errors[0].message
        )
    if result.get("schema_version") != "1.0" or result.get("role") != "challenger":
        raise ChallengerAgentError("invalid challenger output identity")
    expected = {
        str(row["adjustment_id"]) for row in proposal["proposed_adjustments"]
    }
    reviewed = {str(value) for value in result.get("reviewed_adjustment_ids", [])}
    if reviewed != expected:
        raise ChallengerAgentError("challenger must review every proposed adjustment")
    outcome = str(result.get("escalation_outcome", ""))
    review = {
        "review_id": str(result["review_id"]),
        "agent_run_id": evidence_run_id,
        "escalation_outcome": outcome,
        "notes": str(result["notes"]),
        "observed_at": observed_at,
        "available_at": observed_at,
        "provenance": {
            "source_ids": ["gpt-5.6-sol-challenger"],
            "transformation_version": "challenger-agent-v1",
            "agent_run_id": evidence_run_id,
        },
    }
    validate_record("agent_reviews", review)
    gate = evaluate_challenger_outcomes([review], review_required=True)
    unopposed = (
        sorted(expected)
        if outcome == "dismissed"
        and not gate.force_rerun
        and not gate.requires_human_review
        else []
    )
    automatic_approval = False
    requires_human = gate.requires_human_review or outcome == "confidence_downgrade"
    notes = list(gate.notes)
    if outcome == "confidence_downgrade":
        notes.append("deterministic_downgrade_rule_required")
    normalised = {
        "schema_version": "1.0",
        "role": "challenger",
        "review": review,
        "unopposed_proposed_adjustment_ids": unopposed,
        "approval_gate": {
            "automatic_approval_allowed": automatic_approval,
            "requires_human_review": requires_human,
            "confidence_downgraded": gate.confidence_downgraded,
            "force_rerun": gate.force_rerun,
            "unresolved_challenges": list(gate.unresolved_challenges),
            "notes": notes,
        },
        "authority": "review_only_not_applied",
        "proposal_sha256": str(proposal["content_sha256"]),
    }
    normalised["content_sha256"] = artifact_hash(normalised)
    return normalised
