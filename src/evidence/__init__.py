"""Evidence pipeline — document/claim/signal/adjustment lifecycle (WP-08)."""

from src.evidence.lifecycle import (
    ApprovalGate,
    EvidenceEligibility,
    assess_claim_for_decision,
    eligible_claims_for_decision,
    evaluate_approval_path,
    evaluate_challenger_outcomes,
    extract_claims_safe,
    make_claim,
    make_conflict,
    make_document,
    make_signal,
    merge_claims_forbidden,
    propose_adjustment,
    resolve_conflict,
    round_trip,
    scan_injection,
)

__all__ = [
    "ApprovalGate",
    "EvidenceEligibility",
    "assess_claim_for_decision",
    "eligible_claims_for_decision",
    "evaluate_approval_path",
    "evaluate_challenger_outcomes",
    "extract_claims_safe",
    "make_claim",
    "make_conflict",
    "make_document",
    "make_signal",
    "merge_claims_forbidden",
    "propose_adjustment",
    "resolve_conflict",
    "round_trip",
    "scan_injection",
]
