"""WP-08 evidence lifecycle and injection/escalation golden cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evidence.lifecycle import (
    evaluate_challenger_outcomes,
    extract_claims_safe,
    load_policy,
    make_claim,
    make_conflict,
    make_document,
    make_signal,
    merge_claims_forbidden,
    propose_adjustment,
    round_trip,
    scan_injection,
    utc_now,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden-cases" / "evidence"


def test_lifecycle_round_trip_example_chain() -> None:
    doc = make_document(
        document_id="doc_rt",
        source_id="manual-entry",
        body="Player X trained today and will be assessed",
        title="PC notes",
        observed_at="2026-07-21T12:00:00Z",
    )
    claim = make_claim(
        claim_id="cl_rt",
        document_id=doc["document_id"],
        claim_text="Player X trained today and will be assessed",
        confidence=0.7,
        expires_at="2026-07-22T12:00:00Z",
        observed_at="2026-07-21T12:00:00Z",
        provenance={"source_ids": ["manual-entry"], "transformation_version": "0.1.0"},
    )
    signal = make_signal(
        signal_id="sig_rt",
        claim_ids=[claim["claim_id"]],
        interpretation="Availability uncertain; start not confirmed",
        player_uid="pl_x",
        observed_at="2026-07-21T12:00:00Z",
    )
    adj = propose_adjustment(
        adjustment_id="adj_rt",
        signal_ids=[signal["signal_id"]],
        target="start_probability",
        before_value=0.72,
        after_value=0.61,
        confidence=0.65,
        expires_at="2026-07-22T12:00:00Z",
        player_uid="pl_x",
        rationale="Trained but start not confirmed",
        unit="probability",
        observed_at="2026-07-21T12:00:00Z",
        provenance={"source_ids": ["manual-entry"], "transformation_version": "0.1.0"},
    )
    assert round_trip("source_documents", doc)["document_id"] == "doc_rt"
    assert round_trip("extracted_claims", claim)["claim_id"] == "cl_rt"
    assert round_trip("decision_signals", signal)["signal_id"] == "sig_rt"
    assert round_trip("proposed_adjustments", adj)["status"] == "proposed"


def test_conflicts_are_surfaced_not_merged() -> None:
    case = json.loads((GOLDEN / "conflict-lineups.json").read_text(encoding="utf-8"))
    claims = [round_trip("extracted_claims", c) for c in case["claims"]]
    conflict = make_conflict(**case["conflict"])
    preserved = merge_claims_forbidden(claims)
    assert len(preserved) == 2
    assert preserved[0]["claim_text"] != preserved[1]["claim_text"]
    assert set(conflict["claim_ids"]) == {"cl_a", "cl_b"}
    assert all("starts and benched" not in c["claim_text"].lower() for c in preserved)


def test_injection_golden_quarantines_and_blocks_adjustment() -> None:
    case = json.loads((GOLDEN / "injection-presser.json").read_text(encoding="utf-8"))
    assert scan_injection(case["body"]).quarantined
    doc = make_document(
        document_id=case["document"]["document_id"],
        source_id=case["document"]["source_id"],
        body=case["body"],
        title=case["document"]["title"],
        url=case["document"]["url"],
        observed_at="2026-07-21T12:00:00Z",
    )
    result = extract_claims_safe(
        document=doc, body=case["body"], claim_specs=case["claim_specs"]
    )
    assert result["quarantined"] is case["expect"]["document_quarantined"]
    assert [c["claim_id"] for c in result["claims"]] == case["expect"]["accepted_claim_ids"]
    assert [r["claim_id"] for r in result["rejected"]] == case["expect"]["rejected_claim_ids"]
    with pytest.raises(ValueError, match="quarantined"):
        propose_adjustment(
            adjustment_id="adj_blocked",
            signal_ids=["sig_none"],
            target="start_probability",
            before_value=0.5,
            after_value=1.0,
            confidence=0.99,
            expires_at="2026-08-01T12:00:00Z",
            quarantined=True,
        )


def test_escalation_blocks_automatic_approval() -> None:
    case = json.loads((GOLDEN / "escalation-blocks-approval.json").read_text(encoding="utf-8"))
    gate = evaluate_challenger_outcomes(case["reviews"])
    assert gate.automatic_approval_allowed is case["expect"]["automatic_approval_allowed"]
    assert gate.requires_human_review is case["expect"]["requires_human_review"]
    assert gate.unresolved_challenges == case["expect"]["unresolved_challenges"]


def test_dismissed_challenge_allows_auto_approval() -> None:
    review = {
        "review_id": "rv_ok",
        "agent_run_id": "ar_1",
        "escalation_outcome": "dismissed",
        "notes": "Not material",
        "observed_at": "2026-07-21T12:00:00Z",
        "available_at": "2026-07-21T12:00:00Z",
        "provenance": {"source_ids": ["challenger-agent"], "transformation_version": "0.1.0"},
    }
    gate = evaluate_challenger_outcomes([review])
    assert gate.automatic_approval_allowed
    assert not gate.requires_human_review


def test_policy_rejects_low_confidence_adjustment() -> None:
    policy = load_policy()
    with pytest.raises(ValueError, match="confidence"):
        propose_adjustment(
            adjustment_id="adj_low",
            signal_ids=["sig_1"],
            target="start_probability",
            before_value=0.7,
            after_value=0.6,
            confidence=0.2,
            expires_at="2026-08-01T12:00:00Z",
            policy=policy,
        )


def test_forced_rerun_blocks_approval() -> None:
    review = {
        "review_id": "rv_rerun",
        "agent_run_id": "ar_1",
        "escalation_outcome": "forced_re_run",
        "notes": "Stale minutes assumption",
        "observed_at": utc_now(),
        "available_at": utc_now(),
        "provenance": {"source_ids": ["challenger-agent"], "transformation_version": "0.1.0"},
    }
    gate = evaluate_challenger_outcomes([review])
    assert gate.force_rerun
    assert not gate.automatic_approval_allowed
