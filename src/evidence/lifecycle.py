"""Evidence lifecycle helpers — document → claim → signal → proposed adjustment."""

from __future__ import annotations

import hashlib
import json
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
        "published_at": published_at or ts,
        "provenance": provenance
        or {
            "source_ids": [source_id],
            "transformation_version": "0.1.0",
            "content_hash_sha256": content_hash(body),
        },
    }
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
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts = observed_at or utc_now()
    claim = {
        "claim_id": claim_id,
        "document_id": document_id,
        "claim_text": claim_text,
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
        "provenance": provenance
        or {
            "source_ids": ["manual-entry"],
            "transformation_version": "0.1.0",
        },
    }
    validate_record("claim_conflicts", conflict)
    return conflict


def merge_claims_forbidden(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conflicts are surfaced, never merged — return claims unchanged (identity)."""
    return [deepcopy(c) for c in claims]


def make_signal(
    *,
    signal_id: str,
    claim_ids: list[str],
    interpretation: str,
    player_uid: str | None = None,
    observed_at: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts = observed_at or utc_now()
    signal = {
        "signal_id": signal_id,
        "claim_ids": list(claim_ids),
        "interpretation": interpretation,
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


@dataclass(frozen=True)
class ApprovalGate:
    automatic_approval_allowed: bool
    requires_human_review: bool
    confidence_downgraded: bool
    force_rerun: bool
    unresolved_challenges: list[str]
    notes: list[str]


def evaluate_challenger_outcomes(reviews: list[dict[str, Any]]) -> ApprovalGate:
    """Map Section 13.4 outcomes onto the approval path."""
    if not reviews:
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


def extract_claims_safe(
    *,
    document: dict[str, Any],
    body: str,
    claim_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic extraction stub: quarantine injection text; emit only clean claims.

    claim_specs items: claim_id, claim_text, confidence, expires_at
    """
    q = scan_injection(body)
    claims: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for spec in claim_specs:
        text = spec["claim_text"]
        local_q = scan_injection(text)
        if q.quarantined or local_q.quarantined:
            rejected.append(
                {
                    "claim_id": spec["claim_id"],
                    "reason": "quarantined_injection",
                    "matched_patterns": q.matched_patterns or local_q.matched_patterns,
                }
            )
            continue
        claims.append(
            make_claim(
                claim_id=spec["claim_id"],
                document_id=document["document_id"],
                claim_text=text,
                confidence=float(spec["confidence"]),
                expires_at=spec["expires_at"],
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
        "quarantined": q.quarantined,
        "quarantine": {
            "matched_patterns": q.matched_patterns,
            "reason": q.reason,
        },
        "claims": claims,
        "rejected": rejected,
    }
