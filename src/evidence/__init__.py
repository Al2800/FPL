"""Evidence pipeline — document/claim/signal/adjustment lifecycle (WP-08)."""

from src.evidence.lifecycle import (
    ApprovalGate,
    evaluate_challenger_outcomes,
    extract_claims_safe,
    make_claim,
    make_conflict,
    make_document,
    make_signal,
    merge_claims_forbidden,
    propose_adjustment,
    round_trip,
    scan_injection,
)

__all__ = [
    "ApprovalGate",
    "evaluate_challenger_outcomes",
    "extract_claims_safe",
    "make_claim",
    "make_conflict",
    "make_document",
    "make_signal",
    "merge_claims_forbidden",
    "propose_adjustment",
    "round_trip",
    "scan_injection",
]
