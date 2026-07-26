"""Deterministic validation boundary for a hosted evidence-agent result."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from src.evidence.lifecycle import (
    assess_claim_for_decision,
    make_signal,
    propose_adjustment,
    scan_injection,
    validate_record,
)
from src.forecasting.live_faithful import artifact_hash


class EvidenceAgentError(ValueError):
    """Raised when a hosted evidence proposal violates the bounded contract."""


ALLOWED_TARGETS = frozenset({"expected_minutes", "start_probability"})
ROOT = Path(__file__).resolve().parents[2]
OUTPUT_SCHEMA = ROOT / "prompts" / "evidence-agent" / "output.schema.json"


def _citation_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_evidence_result(
    result: Mapping[str, Any],
    *,
    decision_at: str,
    known_player_ids: set[str],
    policy: Mapping[str, Any],
    approved_evidence: Mapping[str, Mapping[str, Any]],
    player_baselines: Mapping[str, Mapping[str, float]],
    run_observed_at: str,
) -> dict[str, Any]:
    """Validate and normalise a proposal; never apply it."""
    schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(result)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise EvidenceAgentError(
            "evidence output schema violation: " + errors[0].message
        )
    if result.get("schema_version") != "1.0":
        raise EvidenceAgentError("unsupported evidence-agent output version")
    if result.get("role") != "evidence":
        raise EvidenceAgentError("hosted output role must be evidence")
    raw_claims = result.get("claims")
    raw_adjustments = result.get("proposed_adjustments")
    if not isinstance(raw_claims, list) or not isinstance(raw_adjustments, list):
        raise EvidenceAgentError("claims and proposed_adjustments must be arrays")
    raw_conflicts = result.get("conflicts", [])
    if not isinstance(raw_conflicts, list):
        raise EvidenceAgentError("conflicts must be an array")
    unresolved_conflicts: list[dict[str, Any]] = []
    for raw in raw_conflicts:
        if not isinstance(raw, Mapping):
            raise EvidenceAgentError("conflict must be an object")
        conflict = {
            "conflict_id": str(raw.get("conflict_id", "")),
            "claim_ids": sorted(str(value) for value in raw.get("claim_ids", [])),
            "status": str(raw.get("status", "unresolved")),
        }
        if not conflict["conflict_id"] or len(conflict["claim_ids"]) < 2:
            raise EvidenceAgentError("conflict requires an id and at least two claims")
        if conflict["status"] != "resolved":
            unresolved_conflicts.append(conflict)
    if unresolved_conflicts:
        raise EvidenceAgentError("unresolved evidence conflicts")

    claims: list[dict[str, Any]] = []
    claim_index: dict[str, dict[str, Any]] = {}
    claim_player_index: dict[str, str] = {}
    for raw in raw_claims:
        if not isinstance(raw, Mapping):
            raise EvidenceAgentError("claim must be an object")
        player_id = str(raw.get("player_uid", ""))
        if player_id not in known_player_ids:
            raise EvidenceAgentError(f"unknown player identity: {player_id}")
        document_id = str(raw["document_id"])
        approved = approved_evidence.get(document_id)
        if approved is None:
            raise EvidenceAgentError(f"unknown evidence document: {document_id}")
        if str(raw["source_id"]) != str(approved["source_id"]):
            raise EvidenceAgentError("claim source identity mismatch")
        passage_id = str(raw["passage_id"])
        passages = approved.get("passages", {})
        if not isinstance(passages, Mapping) or passage_id not in passages:
            raise EvidenceAgentError("claim cites unknown passage")
        excerpt = str(raw.get("citation_excerpt", ""))
        approved_excerpt = str(passages[passage_id])
        if excerpt != approved_excerpt:
            raise EvidenceAgentError("claim citation is not an approved passage")
        if not excerpt or raw.get("citation_excerpt_sha256") != _citation_hash(excerpt):
            raise EvidenceAgentError("claim citation excerpt hash mismatch")
        if scan_injection(excerpt).quarantined or scan_injection(
            str(raw.get("claim_text", ""))
        ).quarantined:
            raise EvidenceAgentError("claim contains prompt-injection-like text")
        claim = {
            "claim_id": str(raw["claim_id"]),
            "document_id": document_id,
            "claim_text": str(raw["claim_text"]),
            "published_at": str(approved["published_at"]),
            "observed_at": str(approved["observed_at"]),
            "available_at": str(approved["available_at"]),
            "expires_at": str(raw["expires_at"]),
            "confidence": float(raw["confidence"]),
            "provenance": {
                "source_ids": [str(approved["source_id"])],
                "transformation_version": "evidence-agent-v1",
                "content_hash_sha256": str(approved["content_sha256"]),
            },
        }
        validate_record("extracted_claims", claim)
        eligibility = assess_claim_for_decision(
            claim, decision_at, dict(policy)
        )
        if not eligibility.eligible:
            raise EvidenceAgentError(
                f"ineligible claim {claim['claim_id']}: "
                + ",".join(eligibility.reasons)
            )
        if claim["claim_id"] in claim_index:
            raise EvidenceAgentError("duplicate claim_id")
        claim_index[claim["claim_id"]] = claim
        claim_player_index[claim["claim_id"]] = player_id
        claims.append(claim)

    for conflict in raw_conflicts:
        unknown = sorted(set(conflict["claim_ids"]) - set(claim_index))
        if unknown:
            raise EvidenceAgentError(
                "conflict cites unknown claims: " + ",".join(unknown)
            )

    signals: list[dict[str, Any]] = []
    claim_entities: list[dict[str, Any]] = []
    adjustments: list[dict[str, Any]] = []
    seen_adjustments: set[str] = set()
    for raw in raw_adjustments:
        if not isinstance(raw, Mapping):
            raise EvidenceAgentError("proposed adjustment must be an object")
        adjustment_id = str(raw["adjustment_id"])
        if adjustment_id in seen_adjustments:
            raise EvidenceAgentError("duplicate adjustment_id")
        seen_adjustments.add(adjustment_id)
        player_id = str(raw.get("player_uid", ""))
        if player_id not in known_player_ids:
            raise EvidenceAgentError(f"unknown player identity: {player_id}")
        target = str(raw["target"])
        if target not in ALLOWED_TARGETS:
            raise EvidenceAgentError(f"agent cannot propose target: {target}")
        before_value = raw["before_value"]
        after_value = raw["after_value"]
        if (
            isinstance(before_value, bool)
            or isinstance(after_value, bool)
            or not isinstance(before_value, (int, float))
            or not isinstance(after_value, (int, float))
            or not math.isfinite(float(before_value))
            or not math.isfinite(float(after_value))
        ):
            raise EvidenceAgentError("adjustment values must be finite numbers")
        baseline = player_baselines.get(player_id, {}).get(target)
        if baseline is None or float(before_value) != float(baseline):
            raise EvidenceAgentError("adjustment before_value mismatches baseline")
        lower, upper = (0.0, 120.0) if target == "expected_minutes" else (0.0, 1.0)
        if not lower <= float(after_value) <= upper:
            raise EvidenceAgentError(f"{target} after_value outside valid range")
        supporting_ids = [str(value) for value in raw["claim_ids"]]
        if not supporting_ids:
            raise EvidenceAgentError("adjustment must cite at least one claim")
        try:
            supporting = [claim_index[value] for value in supporting_ids]
        except KeyError as exc:
            raise EvidenceAgentError(
                f"adjustment cites unknown claim: {exc.args[0]}"
            ) from exc
        if any(claim_player_index[value] != player_id for value in supporting_ids):
            raise EvidenceAgentError(
                "adjustment player does not match supporting claims"
            )
        signal_id = f"signal:{adjustment_id}"
        published_at = max(str(claim["published_at"]) for claim in supporting)
        signal = make_signal(
            signal_id=signal_id,
            claim_ids=supporting_ids,
            interpretation=str(raw["rationale"]),
            player_uid=player_id,
            published_at=published_at,
            observed_at=run_observed_at,
            provenance={
                "source_ids": sorted(
                    {
                        source
                        for claim in supporting
                        for source in claim["provenance"]["source_ids"]
                    }
                ),
                "transformation_version": "evidence-agent-v1",
            },
        )
        adjustment = propose_adjustment(
            adjustment_id=adjustment_id,
            signal_ids=[signal_id],
            target=target,
            before_value=before_value,
            after_value=after_value,
            confidence=float(raw["confidence"]),
            expires_at=str(raw["expires_at"]),
            player_uid=player_id,
            rationale=str(raw["rationale"]),
            unit=raw.get("unit"),
            observed_at=run_observed_at,
            provenance=deepcopy(signal["provenance"]),
            policy=dict(policy),
            decision_at=decision_at,
            supporting_claims=supporting,
            conflicts=raw_conflicts,
        )
        signals.append(signal)
        adjustments.append(adjustment)

    for claim_id, claim in claim_index.items():
        player_id = next(
            str(raw["player_uid"])
            for raw in raw_claims
            if str(raw["claim_id"]) == claim_id
        )
        entity = {
            "claim_id": claim_id,
            "entity_type": "player",
            "entity_uid": player_id,
            "provenance": deepcopy(claim["provenance"]),
        }
        validate_record("claim_entities", entity)
        claim_entities.append(entity)

    normalised = {
        "schema_version": "1.0",
        "role": "evidence",
        "claims": claims,
        "claim_entities": claim_entities,
        "conflicts": [deepcopy(dict(value)) for value in raw_conflicts],
        "signals": signals,
        "proposed_adjustments": adjustments,
        "notes": [str(value) for value in result.get("notes", [])],
        "authority": "proposal_only_not_applied",
    }
    normalised["content_sha256"] = artifact_hash(normalised)
    return normalised
