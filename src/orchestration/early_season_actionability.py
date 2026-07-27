"""Host-owned actionability gate for retrospective GW2-GW11 evidence."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Mapping

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_arm import render_hosted_input
from src.orchestration.evidence_fork import EvidenceForkError, _sealed


ACTIONABLE_PLAYERS = {
    3: {"player:2025-26:235"},
    4: {"player:2025-26:235"},
    6: {"player:2025-26:235"},
    7: {"player:2025-26:5"},
    9: {"player:2025-26:5"},
}

CONTEXT_REASON_BY_GAMEWEEK = {
    2: "duplicate_of_structured_signal_and_unforeseeable_post_deadline_event",
    5: "reference_policy_not_forecast_evidence",
    8: "duplicate_of_structured_form_and_fixture_signal",
    10: "duplicate_of_structured_form_fixture_and_transfer_signal",
    11: "positive_recovery_signal_cannot_raise_forecast_under_current_policy",
}


def _default_expiry(decision_cutoff: str) -> str:
    parsed = datetime.fromisoformat(decision_cutoff.replace("Z", "+00:00"))
    return (parsed + timedelta(hours=72)).astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def build_actionability_assessment(
    *,
    gameweek: int,
    entry: Mapping[str, Any],
) -> dict[str, Any]:
    allowed = ACTIONABLE_PLAYERS.get(gameweek, set())
    uses: list[dict[str, Any]] = []
    for candidate in entry["admitted_candidates"]:
        for player_id in candidate["player_ids"]:
            player_id = str(player_id)
            actionable = player_id in allowed
            if gameweek == 6 and player_id == "player:2025-26:568":
                reason = "insufficient_passage_grounding"
            elif actionable:
                reason = "pre_deadline_availability_evidence"
            else:
                reason = CONTEXT_REASON_BY_GAMEWEEK.get(
                    gameweek,
                    "context_only_not_authorised_for_adjustment",
                )
            uses.append(
                {
                    "evidence_id": str(candidate["evidence_id"]),
                    "player_id": player_id,
                    "allowed_use": (
                        "availability_adjustment" if actionable else "context_only"
                    ),
                    "reason_codes": [reason],
                    "grounding_passed": not (
                        gameweek == 6 and player_id == "player:2025-26:568"
                    ),
                    "structured_overlap": reason.startswith(
                        "duplicate_of_structured"
                    ),
                    "default_expires_at": _default_expiry(
                        str(entry["decision_cutoff"])
                    ),
                }
            )
    return _sealed(
        {
            "schema_version": "1.0",
            "gameweek": gameweek,
            "manifest_entry_sha256": str(entry["content_sha256"]),
            "policy": {
                "only_downward_adjustments": True,
                "allowed_targets": ["expected_minutes", "start_probability"],
                "context_only_proposals_fail_completion_gate": True,
            },
            "candidate_player_uses": uses,
            "allowed_adjustment_player_ids": sorted(allowed),
        }
    )


def attach_actionability_to_request(
    request: Mapping[str, Any],
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind host constraints into the exact model input and request hashes."""
    value = deepcopy(dict(request))
    value.pop("content_sha256", None)
    value.pop("rendered_input_sha256", None)
    value["host_constraints"] = {
        "actionability_assessment": deepcopy(dict(assessment)),
        "instruction": (
            "Propose adjustments only for allowed_adjustment_player_ids, only "
            "when the cited passage grounds availability, and only as a "
            "downward change. Context-only evidence may be extracted as a "
            "claim but must not produce an adjustment."
        ),
    }
    value["rendered_input_sha256"] = hashlib.sha256(
        render_hosted_input(value).encode("utf-8")
    ).hexdigest()
    value["content_sha256"] = artifact_hash(value)
    return value


def enforce_actionability(
    *,
    evidence_run: Mapping[str, Any],
    assessment: Mapping[str, Any],
) -> None:
    """Fail the shared completion gate when a proposal exceeds host authority."""
    if evidence_run.get("status") != "completed":
        raise EvidenceForkError("Evidence run did not complete")
    validated = evidence_run.get("validated_output")
    if not isinstance(validated, Mapping):
        raise EvidenceForkError("Completed evidence run has no validated output")
    allowed = set(assessment["allowed_adjustment_player_ids"])
    for proposal in validated.get("proposed_adjustments", []):
        player_id = str(proposal["player_uid"])
        if player_id not in allowed:
            raise EvidenceForkError(
                f"Context-only evidence produced an adjustment for {player_id}"
            )
        if str(proposal["target"]) not in {"expected_minutes", "start_probability"}:
            raise EvidenceForkError("Early evidence proposed an unsupported target")
        if float(proposal["after_value"]) > float(proposal["before_value"]):
            raise EvidenceForkError("Early evidence may not increase a forecast")
