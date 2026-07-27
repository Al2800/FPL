from copy import deepcopy

import pytest

from src.evidence.availability_ledger import (
    AvailabilityLedgerError,
    append_availability_claim,
    new_availability_ledger,
    project_availability,
    validate_availability_ledger,
)
from src.forecasting.live_faithful import artifact_hash


def _claim(
    claim_id: str,
    *,
    player_uid: str = "player:2025-26:8",
    status: str = "unavailable",
    published_at: str = "2026-04-24T00:00:00Z",
    observed_at: str = "2026-04-24T08:00:00Z",
    available_at: str = "2026-04-24T08:00:00Z",
    expires_at: str = "2026-05-11T00:00:00Z",
    confidence: float = 0.98,
    **extra,
) -> dict:
    return {
        "claim_id": claim_id,
        "player_uid": player_uid,
        "status": status,
        "confidence": confidence,
        "published_at": published_at,
        "observed_at": observed_at,
        "available_at": available_at,
        "expires_at": expires_at,
        "provenance": {
            "source_ids": ["ffs-gw34-timber-out-2026-04-24"],
            "transformation_version": "availability-ledger-v1",
        },
        **extra,
    }


def test_timber_absence_persists_across_gw34_to_gw36_without_reinsertion():
    ledger = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    ledger = append_availability_claim(
        ledger, _claim("claim-gw34-timber-out")
    )

    for cutoff in (
        "2026-04-24T17:30:00Z",
        "2026-05-01T17:30:00Z",
        "2026-05-09T10:00:00Z",
    ):
        view = project_availability(
            ledger,
            decision_at=cutoff,
            player_uids=["player:2025-26:8"],
        )
        assert view["content_sha256"] == artifact_hash(view)
        assert [row["claim_id"] for row in view["accepted"]] == [
            "claim-gw34-timber-out"
        ]
        assert view["abstentions"] == []

    expired = project_availability(
        ledger,
        decision_at="2026-05-11T00:00:00Z",
        player_uids=["player:2025-26:8"],
    )
    assert expired["accepted"] == []
    assert expired["history"]["stale"][0]["eligibility"]["reasons"] == [
        "expired"
    ]
    assert expired["abstentions"] == [
        {
            "player_uid": "player:2025-26:8",
            "reason": "no_active_evidence",
        }
    ]


def test_recovery_requires_condition_and_permanently_supersedes_absence():
    ledger = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    ledger = append_availability_claim(ledger, _claim("absence"))
    recovery = _claim(
        "recovery",
        status="available",
        published_at="2026-05-02T09:00:00Z",
        observed_at="2026-05-02T09:05:00Z",
        available_at="2026-05-02T09:05:00Z",
        expires_at="2026-05-04T00:00:00Z",
        supersedes_claim_ids=["absence"],
    )
    with pytest.raises(
        AvailabilityLedgerError, match="explicit observed recovery condition"
    ):
        append_availability_claim(ledger, recovery)

    recovery["recovery"] = {
        "condition": "returned_to_training",
        "condition_met": True,
    }
    ledger = append_availability_claim(ledger, recovery)
    recovered = project_availability(
        ledger, decision_at="2026-05-03T12:00:00Z"
    )
    assert recovered["accepted"][0]["claim_id"] == "recovery"
    assert recovered["history"]["superseded"][0]["claim_id"] == "absence"

    later = project_availability(
        ledger,
        decision_at="2026-05-09T10:00:00Z",
        player_uids=["player:2025-26:8"],
    )
    assert later["accepted"] == []
    assert later["history"]["superseded"][0]["claim_id"] == "absence"
    assert later["history"]["stale"][0]["claim_id"] == "recovery"


def test_conflicts_stay_visible_and_force_abstention():
    ledger = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    ledger = append_availability_claim(ledger, _claim("source-a"))
    ledger = append_availability_claim(
        ledger,
        _claim(
            "source-b",
            status="doubtful",
            observed_at="2026-04-24T08:05:00Z",
            available_at="2026-04-24T08:05:00Z",
        ),
    )
    view = project_availability(
        ledger,
        decision_at="2026-04-24T17:30:00Z",
        player_uids=["player:2025-26:8"],
    )
    assert view["accepted"] == []
    assert view["conflicts"] == [
        {
            "player_uid": "player:2025-26:8",
            "claim_ids": ["source-a", "source-b"],
            "statuses": ["doubtful", "unavailable"],
            "resolution": "abstain_pending_explicit_supersession",
        }
    ]
    assert view["abstentions"][0]["reason"] == "unresolved_conflict"


def test_same_status_claims_are_deduplicated_with_corroboration_visible():
    ledger = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    ledger = append_availability_claim(ledger, _claim("source-a"))
    ledger = append_availability_claim(
        ledger,
        _claim(
            "source-b",
            observed_at="2026-04-24T08:05:00Z",
            available_at="2026-04-24T08:05:00Z",
            confidence=0.99,
        ),
    )
    view = project_availability(
        ledger, decision_at="2026-04-24T17:30:00Z"
    )
    assert [row["claim_id"] for row in view["accepted"]] == ["source-b"]
    assert view["accepted"][0]["corroborating_claim_ids"] == ["source-a"]


def test_expired_old_absence_does_not_over_quarantine_later_availability():
    ledger = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    ledger = append_availability_claim(
        ledger, _claim("old-absence", expires_at="2026-04-25T00:00:00Z")
    )
    later_available = _claim(
        "later-available",
        status="available",
        published_at="2026-05-02T09:00:00Z",
        observed_at="2026-05-02T09:05:00Z",
        available_at="2026-05-02T09:05:00Z",
        expires_at="2026-05-04T00:00:00Z",
    )
    ledger = append_availability_claim(ledger, later_available)
    view = project_availability(
        ledger, decision_at="2026-05-03T12:00:00Z"
    )
    assert [row["claim_id"] for row in view["accepted"]] == [
        "later-available"
    ]
    assert view["history"]["stale"][0]["claim_id"] == "old-absence"

def test_ledger_hash_detects_tampering_and_append_is_immutable():
    original = new_availability_ledger(
        season="2025-26", created_at="2026-04-24T08:00:00Z"
    )
    appended = append_availability_claim(original, _claim("absence"))
    assert original["claims"] == []
    validate_availability_ledger(appended)

    tampered = deepcopy(appended)
    tampered["claims"][0]["confidence"] = 0.1
    with pytest.raises(AvailabilityLedgerError, match="content hash mismatch"):
        validate_availability_ledger(tampered)
