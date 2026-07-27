"""Evidence lifecycle helpers — document → claim → signal → proposed adjustment."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "control" / "schemas"
POLICY_PATH = REPO / "control" / "policies" / "evidence-adjustments.yaml"

ESCALATION_OUTCOMES = frozenset(
    {"dismissed", "confidence_downgrade", "forced_re_run", "escalation"}
)
AVAILABILITY_CLAIM_STATUSES = frozenset(
    {"unavailable", "doubtful", "available"}
)
RECOVERY_CONDITIONS = frozenset(
    {"declared_fit", "returned_to_training", "started_match"}
)

INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|rules)",
        r"system\s*:\s*",
        r"<\s*/?\s*system\s*>",
        r"you\s+are\s+now\s+(?:in\s+)?(?:developer|DAN|jailbreak)\s+mode",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"do\s+not\s+follow\s+your\s+policies",
    )
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_timestamp(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_policy(path: Path | None = None) -> dict[str, Any]:
    return yaml.safe_load((path or POLICY_PATH).read_text(encoding="utf-8"))


def _load_schema(rel: str) -> dict[str, Any]:
    schema = json.loads((SCHEMAS / rel).read_text(encoding="utf-8"))
    defs = json.loads((SCHEMAS / "_defs.json").read_text(encoding="utf-8"))["$defs"]

    def rewrite(obj: Any) -> Any:
        if isinstance(obj, dict):
            if set(obj.keys()) == {"$ref"} and "/$defs/" in obj["$ref"]:
                return defs[obj["$ref"].split("/$defs/")[-1]]
            return {k: rewrite(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [rewrite(v) for v in obj]
        return obj

    return rewrite(schema)


ENTITY_SCHEMAS = {
    "source_documents": "evidence/source_documents.json",
    "extracted_claims": "evidence/extracted_claims.json",
    "claim_conflicts": "evidence/claim_conflicts.json",
    "claim_entities": "evidence/claim_entities.json",
    "decision_signals": "evidence/decision_signals.json",
    "proposed_adjustments": "evidence/proposed_adjustments.json",
    "agent_reviews": "decisions/agent_reviews.json",
}


def validate_record(entity: str, record: dict[str, Any]) -> None:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required")
    schema = _load_schema(ENTITY_SCHEMAS[entity])
    Draft202012Validator(schema).validate(record)


def round_trip(entity: str, record: dict[str, Any]) -> dict[str, Any]:
    """Validate → serialise → deserialise → validate again."""
    validate_record(entity, record)
    blob = json.dumps(record, sort_keys=True)
    restored = json.loads(blob)
    validate_record(entity, restored)
    return restored


@dataclass(frozen=True)
class QuarantineResult:
    quarantined: bool
    matched_patterns: list[str]
    reason: str | None = None


@dataclass(frozen=True)
class EvidenceEligibility:
    eligible: bool
    reasons: list[str]
    warnings: list[str]


def scan_injection(text: str) -> QuarantineResult:
    matched = [p.pattern for p in INJECTION_PATTERNS if p.search(text)]
    if matched:
        return QuarantineResult(True, matched, "prompt_injection_like_text")
    return QuarantineResult(False, [])


def make_document(
    *,
    document_id: str,
    source_id: str,
    body: str,
    title: str = "",
    url: str | None = None,
    published_at: str | None = None,
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts = observed_at or utc_now()
    doc = {
        "document_id": document_id,
        "source_id": source_id,
        "title": title,
        "content_hash_sha256": content_hash(body),
        "observed_at": ts,
        "available_at": ts,
        "provenance": provenance
        or {
            "source_ids": [source_id],
            "transformation_version": "0.1.0",
            "content_hash_sha256": content_hash(body),
        },
    }
    # Unknown publication time stays unknown. Observation time is not evidence
    # that the source was published at the same instant.
    if published_at is not None:
        _parse_timestamp(published_at, field="published_at")
        doc["published_at"] = published_at
    if url:
        doc["url"] = url
    validate_record("source_documents", doc)
    return doc


def make_claim(
    *,
    claim_id: str,
    document_id: str,
    claim_text: str,
    confidence: float,
    expires_at: str,
    published_at: str | None = None,
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if published_at is None:
        raise ValueError(
            "published_at is required for claims; observed_at must never substitute for it"
        )
    _parse_timestamp(published_at, field="published_at")
    _parse_timestamp(expires_at, field="expires_at")
    ts = observed_at or utc_now()
    claim = {
        "claim_id": claim_id,
        "document_id": document_id,
        "claim_text": claim_text,
        "confidence": confidence,
        "expires_at": expires_at,
        "observed_at": ts,
        "available_at": ts,
        "published_at": published_at,
        "provenance": provenance
        or {
            "source_ids": ["manual-entry"],
            "transformation_version": "0.1.0",
        },
    }
    validate_record("extracted_claims", claim)
    return claim


def make_conflict(
    *,
    conflict_id: str,
    claim_ids: list[str],
    description: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if len(claim_ids) < 2:
        raise ValueError("claim_conflicts require at least two claim_ids")
    conflict = {
        "conflict_id": conflict_id,
        "claim_ids": list(claim_ids),
        "description": description,
        "status": "unresolved",
        "provenance": provenance
        or {
            "source_ids": ["manual-entry"],
            "transformation_version": "0.1.0",
        },
    }
    validate_record("claim_conflicts", conflict)
    return conflict


def resolve_conflict(
    conflict: dict[str, Any],
    *,
    escalation_outcome: str,
    review_id: str,
    resolution_notes: str,
) -> dict[str, Any]:
    """Resolve a conflict only through a policy-defined challenger outcome."""
    validate_record("claim_conflicts", conflict)
    if escalation_outcome not in ESCALATION_OUTCOMES:
        raise ValueError(f"invalid escalation_outcome: {escalation_outcome}")
    if not review_id or not resolution_notes:
        raise ValueError("conflict resolution requires review_id and resolution_notes")
    resolved = deepcopy(conflict)
    resolved.update(
        {
            "status": "resolved",
            "resolution_outcome": escalation_outcome,
            "resolved_by_review_id": review_id,
            "resolution_notes": resolution_notes,
        }
    )
    validate_record("claim_conflicts", resolved)
    return resolved


def merge_claims_forbidden(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conflicts are surfaced, never merged — return claims unchanged (identity)."""
    return [deepcopy(c) for c in claims]


def make_signal(
    *,
    signal_id: str,
    claim_ids: list[str],
    interpretation: str,
    player_uid: str | None = None,
    published_at: str | None = None,
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if published_at is None:
        raise ValueError(
            "published_at is required for signals and must derive from supporting claims"
        )
    _parse_timestamp(published_at, field="published_at")
    ts = observed_at or utc_now()
    signal = {
        "signal_id": signal_id,
        "claim_ids": list(claim_ids),
        "interpretation": interpretation,
        "observed_at": ts,
        "available_at": ts,
        "published_at": published_at,
        "provenance": provenance
        or {
            "source_ids": ["manual-entry"],
            "transformation_version": "0.1.0",
        },
    }
    if player_uid:
        signal["player_uid"] = player_uid
    validate_record("decision_signals", signal)
    return signal


def propose_adjustment(
    *,
    adjustment_id: str,
    signal_ids: list[str],
    target: str,
    before_value: float | str | bool,
    after_value: float | str | bool,
    confidence: float,
    expires_at: str,
    player_uid: str | None = None,
    rationale: str = "",
    unit: str | None = None,
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
    quarantined: bool = False,
    decision_at: str | None = None,
    supporting_claims: list[dict[str, Any]] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a *proposed* adjustment; raises if policy thresholds fail."""
    policy = policy or load_policy()
    thr = policy["thresholds"]
    if quarantined and policy.get("injection", {}).get("block_adjustment_from_quarantined", True):
        raise ValueError("adjustment blocked: source text quarantined for injection-like content")
    if confidence < float(thr["min_adjustment_confidence"]):
        raise ValueError(
            f"adjustment confidence {confidence} below min {thr['min_adjustment_confidence']}"
        )
    if target == "start_probability" and isinstance(before_value, (int, float)) and isinstance(
        after_value, (int, float)
    ):
        delta = abs(float(after_value) - float(before_value))
        if delta > float(thr["max_start_probability_delta"]):
            raise ValueError(
                f"start_probability delta {delta} exceeds max {thr['max_start_probability_delta']}"
            )
    ts = observed_at or utc_now()
    expiry = _parse_timestamp(expires_at, field="expires_at")
    if decision_at is not None:
        cutoff = _parse_timestamp(decision_at, field="decision_at")
        if expiry <= cutoff:
            raise ValueError("adjustment blocked: adjustment is expired at decision time")
        if not supporting_claims:
            raise ValueError("adjustment blocked: decision-time adjustment requires supporting claims")
        ineligible = [
            (claim.get("claim_id", "?"), assess_claim_for_decision(claim, decision_at, policy))
            for claim in supporting_claims
        ]
        ineligible = [(claim_id, result) for claim_id, result in ineligible if not result.eligible]
        if ineligible:
            details = "; ".join(
                f"{claim_id}:{','.join(result.reasons)}" for claim_id, result in ineligible
            )
            raise ValueError(f"adjustment blocked: ineligible supporting evidence ({details})")
        unresolved = [
            conflict.get("conflict_id", "?")
            for conflict in (conflicts or [])
            if conflict.get("status", "unresolved") != "resolved"
        ]
        if unresolved:
            raise ValueError(
                "adjustment blocked: unresolved evidence conflicts " + ", ".join(unresolved)
            )
    adj = {
        "adjustment_id": adjustment_id,
        "signal_ids": list(signal_ids),
        "target": target,
        "before_value": before_value,
        "after_value": after_value,
        "status": "proposed",
        "confidence": confidence,
        "expires_at": expires_at,
        "observed_at": ts,
        "available_at": ts,
        "published_at": ts,
        "provenance": provenance
        or {
            "source_ids": ["manual-entry"],
            "transformation_version": "0.1.0",
        },
    }
    if player_uid:
        adj["player_uid"] = player_uid
    if rationale:
        adj["rationale"] = rationale
    if unit:
        adj["unit"] = unit
    if thr.get("require_citation") and not adj["provenance"].get("source_ids"):
        raise ValueError("adjustment requires provenance.source_ids")
    validate_record("proposed_adjustments", adj)
    return adj


def assess_claim_for_decision(
    claim: dict[str, Any],
    decision_at: str,
    policy: dict[str, Any] | None = None,
) -> EvidenceEligibility:
    """Determine whether a claim was usable at a particular decision cutoff."""
    policy = policy or load_policy()
    reasons: list[str] = []
    warnings: list[str] = []
    cutoff = _parse_timestamp(decision_at, field="decision_at")

    published_raw = claim.get("published_at")
    if not published_raw:
        reasons.append("missing_published_at")
        published = None
    else:
        published = _parse_timestamp(published_raw, field="published_at")
        if published > cutoff:
            reasons.append("published_after_decision")

    for field in ("observed_at", "available_at"):
        raw = claim.get(field)
        if not raw:
            reasons.append(f"missing_{field}")
            continue
        if _parse_timestamp(raw, field=field) > cutoff:
            reasons.append(f"{field}_after_decision")

    expires_raw = claim.get("expires_at")
    if not expires_raw:
        reasons.append("missing_expires_at")
    elif _parse_timestamp(expires_raw, field="expires_at") <= cutoff:
        reasons.append("expired")

    confidence = claim.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        reasons.append("missing_or_invalid_confidence")
    elif not math.isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
        reasons.append("invalid_confidence")
    elif float(confidence) < float(policy["thresholds"]["min_claim_confidence"]):
        reasons.append("claim_confidence_below_threshold")

    if published is not None:
        max_age = float(policy.get("staleness", {}).get("warn_if_age_hours_gt", 72))
        age_hours = (cutoff - published).total_seconds() / 3600
        if age_hours > max_age:
            warnings.append("published_age_exceeds_warning_threshold")

    return EvidenceEligibility(not reasons, reasons, warnings)


def eligible_claims_for_decision(
    claims: list[dict[str, Any]],
    decision_at: str,
    policy: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, EvidenceEligibility]]:
    """Return eligible claims while preserving a reasoned result for every claim."""
    results: dict[str, EvidenceEligibility] = {}
    eligible: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        claim_id = claim.get("claim_id", f"claim_{index}")
        result = assess_claim_for_decision(claim, decision_at, policy)
        results[claim_id] = result
        if result.eligible:
            eligible.append(deepcopy(claim))
    return eligible, results


def validate_availability_claim_semantics(claim: dict[str, Any]) -> None:
    """Validate the domain fields used by the stateful availability ledger."""

    required = {
        "claim_id",
        "player_uid",
        "status",
        "confidence",
        "published_at",
        "observed_at",
        "available_at",
        "expires_at",
        "provenance",
    }
    missing = sorted(required - set(claim))
    if missing:
        raise ValueError(
            "availability claim missing required fields: " + ", ".join(missing)
        )
    if not isinstance(claim["claim_id"], str) or not claim["claim_id"]:
        raise ValueError("availability claim_id must be a non-empty string")
    if not isinstance(claim["player_uid"], str) or not claim["player_uid"]:
        raise ValueError("availability player_uid must be a non-empty string")
    if claim["status"] not in AVAILABILITY_CLAIM_STATUSES:
        raise ValueError(
            "availability status must be one of "
            + ", ".join(sorted(AVAILABILITY_CLAIM_STATUSES))
        )
    published = _parse_timestamp(claim["published_at"], field="published_at")
    observed = _parse_timestamp(claim["observed_at"], field="observed_at")
    available = _parse_timestamp(claim["available_at"], field="available_at")
    expires = _parse_timestamp(claim["expires_at"], field="expires_at")
    if observed < published:
        raise ValueError("observed_at must not precede published_at")
    if available < observed:
        raise ValueError("available_at must not precede observed_at")
    if expires <= available:
        raise ValueError("expires_at must be later than available_at")
    confidence = claim["confidence"]
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not math.isfinite(float(confidence))
        or not 0 <= float(confidence) <= 1
    ):
        raise ValueError("availability confidence must be between 0 and 1")
    provenance = claim["provenance"]
    if (
        not isinstance(provenance, dict)
        or not isinstance(provenance.get("source_ids"), list)
        or not provenance["source_ids"]
    ):
        raise ValueError("availability provenance requires source_ids")
    supersedes = claim.get("supersedes_claim_ids", [])
    if (
        not isinstance(supersedes, list)
        or any(not isinstance(value, str) or not value for value in supersedes)
        or len(supersedes) != len(set(supersedes))
    ):
        raise ValueError(
            "supersedes_claim_ids must contain unique non-empty strings"
        )
    recovery = claim.get("recovery")
    if recovery is not None:
        if claim["status"] != "available":
            raise ValueError("recovery evidence requires status=available")
        if not isinstance(recovery, dict):
            raise ValueError("recovery must be an object")
        if recovery.get("condition") not in RECOVERY_CONDITIONS:
            raise ValueError(
                "recovery condition must be one of "
                + ", ".join(sorted(RECOVERY_CONDITIONS))
            )
        if recovery.get("condition_met") is not True:
            raise ValueError("recovery condition must be explicitly met")


@dataclass(frozen=True)
class ApprovalGate:
    automatic_approval_allowed: bool
    requires_human_review: bool
    confidence_downgraded: bool
    force_rerun: bool
    unresolved_challenges: list[str]
    notes: list[str]


def evaluate_challenger_outcomes(
    reviews: list[dict[str, Any]], *, review_required: bool = False
) -> ApprovalGate:
    """Map Section 13.4 outcomes onto the approval path."""
    if not reviews:
        if review_required:
            return ApprovalGate(
                False,
                True,
                False,
                False,
                ["missing_required_challenger_review"],
                ["required_challenger_review_missing"],
            )
        return ApprovalGate(True, False, False, False, [], ["no_challenger_reviews"])

    unresolved: list[str] = []
    notes: list[str] = []
    confidence_downgraded = False
    force_rerun = False
    requires_human = False

    for rev in reviews:
        outcome = rev.get("escalation_outcome")
        if outcome not in ESCALATION_OUTCOMES:
            raise ValueError(f"invalid escalation_outcome: {outcome}")
        validate_record("agent_reviews", rev)
        rid = rev.get("review_id", "?")
        if outcome == "dismissed":
            notes.append(f"{rid}:dismissed")
        elif outcome == "confidence_downgrade":
            confidence_downgraded = True
            notes.append(f"{rid}:confidence_downgrade")
        elif outcome == "forced_re_run":
            force_rerun = True
            unresolved.append(rid)
            notes.append(f"{rid}:forced_re_run")
        elif outcome == "escalation":
            requires_human = True
            unresolved.append(rid)
            notes.append(f"{rid}:escalation")

    auto = not unresolved and not requires_human and not force_rerun
    # Unresolved challenge blocks any automatic approval path (plan §13.4)
    if unresolved:
        auto = False
        requires_human = requires_human or True
    return ApprovalGate(
        automatic_approval_allowed=auto,
        requires_human_review=requires_human or bool(unresolved),
        confidence_downgraded=confidence_downgraded,
        force_rerun=force_rerun,
        unresolved_challenges=unresolved,
        notes=notes,
    )


def evaluate_approval_path(
    *,
    claims: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    decision_at: str,
    review_required: bool,
    policy: dict[str, Any] | None = None,
) -> ApprovalGate:
    """Fail closed when evidence or required challenger review is unresolved."""
    gate = evaluate_challenger_outcomes(reviews, review_required=review_required)
    _, eligibility = eligible_claims_for_decision(claims, decision_at, policy)
    invalid = [
        f"{claim_id}:{','.join(result.reasons)}"
        for claim_id, result in eligibility.items()
        if not result.eligible
    ]
    unresolved_conflicts = [
        conflict.get("conflict_id", "?")
        for conflict in conflicts
        if conflict.get("status", "unresolved") != "resolved"
    ]
    if not invalid and not unresolved_conflicts:
        return gate
    blockers = list(gate.unresolved_challenges)
    blockers.extend(f"evidence:{item}" for item in invalid)
    blockers.extend(f"conflict:{conflict_id}" for conflict_id in unresolved_conflicts)
    notes = list(gate.notes)
    notes.extend("blocked_" + blocker for blocker in blockers if blocker not in gate.unresolved_challenges)
    return ApprovalGate(
        automatic_approval_allowed=False,
        requires_human_review=True,
        confidence_downgraded=gate.confidence_downgraded,
        force_rerun=gate.force_rerun,
        unresolved_challenges=blockers,
        notes=notes,
    )


def _validate_extraction_boundary(
    *,
    body: str,
    claim_specs: list[dict[str, Any]],
    requested_tools: list[str],
    policy: dict[str, Any],
) -> list[str]:
    """Validate untrusted extractor output as data, never as instructions."""
    cfg = policy.get("extraction", {})
    allowed_tools = set(cfg.get("allowed_read_only_tools", []))
    violations = [
        f"disallowed_tool:{tool}" for tool in requested_tools if tool not in allowed_tools
    ]
    allowed_fields = {"claim_id", "claim_text", "confidence", "expires_at"}
    normalised_body = " ".join(body.split())
    max_claims = int(cfg.get("max_claims_per_document", 50))
    if len(claim_specs) > max_claims:
        violations.append("claim_count_exceeds_limit")
    for index, spec in enumerate(claim_specs):
        extra = sorted(set(spec) - allowed_fields)
        if extra:
            violations.append(f"claim_{index}:unexpected_fields:{','.join(extra)}")
        text = spec.get("claim_text")
        if not isinstance(text, str) or not text.strip():
            violations.append(f"claim_{index}:invalid_claim_text")
        elif cfg.get("require_grounded_text", True) and " ".join(text.split()) not in normalised_body:
            violations.append(f"claim_{index}:ungrounded_claim_text")
        confidence = spec.get("confidence")
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not math.isfinite(float(confidence))
            or not 0 <= float(confidence) <= 1
        ):
            violations.append(f"claim_{index}:invalid_confidence")
        try:
            _parse_timestamp(spec.get("expires_at"), field=f"claim_{index}.expires_at")
        except ValueError:
            violations.append(f"claim_{index}:invalid_expires_at")
    return violations


def extract_claims_safe(
    *,
    document: dict[str, Any],
    body: str,
    claim_specs: list[dict[str, Any]],
    requested_tools: list[str] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the extraction boundary and emit only grounded, timestamped claims."""
    policy = policy or load_policy()
    requested_tools = requested_tools or []
    q = scan_injection(body)
    boundary_violations = _validate_extraction_boundary(
        body=body,
        claim_specs=claim_specs,
        requested_tools=requested_tools,
        policy=policy,
    )
    if not document.get("published_at"):
        boundary_violations.append("missing_source_published_at")
    claims: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for spec in claim_specs:
        text_value = spec.get("claim_text", "")
        local_q = scan_injection(text_value) if isinstance(text_value, str) else QuarantineResult(False, [])
        if q.quarantined or local_q.quarantined or boundary_violations:
            rejected.append(
                {
                    "claim_id": spec.get("claim_id", "?"),
                    "reason": (
                        "quarantined_injection"
                        if q.quarantined or local_q.quarantined
                        else "structured_boundary_violation"
                    ),
                    "matched_patterns": q.matched_patterns or local_q.matched_patterns,
                    "boundary_violations": list(boundary_violations),
                }
            )
            continue
        claims.append(
            make_claim(
                claim_id=spec["claim_id"],
                document_id=document["document_id"],
                claim_text=spec["claim_text"],
                confidence=float(spec["confidence"]),
                expires_at=spec["expires_at"],
                published_at=document["published_at"],
                observed_at=document.get("observed_at"),
                provenance={
                    "source_ids": [document["source_id"]],
                    "transformation_version": "0.1.0",
                    "content_hash_sha256": document.get("content_hash_sha256"),
                },
            )
        )
    return {
        "document_id": document["document_id"],
        "quarantined": q.quarantined or bool(boundary_violations),
        "quarantine": {
            "matched_patterns": q.matched_patterns,
            "reason": q.reason or ("structured_boundary_violation" if boundary_violations else None),
            "boundary_violations": boundary_violations,
        },
        "claims": claims,
        "rejected": rejected,
    }
