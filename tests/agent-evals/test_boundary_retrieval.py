from src.evidence.availability_ledger import (
    append_availability_claim,
    new_availability_ledger,
    project_availability,
)
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.boundary_retrieval import (
    build_boundary_evidence_pack,
    build_shadow_effect_record,
)
from src.orchestration.weekly_evidence_programme import (
    build_weekly_evidence_context,
)


def _claim(claim_id: str, player_uid: str, confidence: float) -> dict:
    return {
        "claim_id": claim_id,
        "player_uid": player_uid,
        "status": "unavailable",
        "confidence": confidence,
        "published_at": "2026-08-14T08:00:00Z",
        "observed_at": "2026-08-14T08:05:00Z",
        "available_at": "2026-08-14T08:05:00Z",
        "expires_at": "2026-08-16T00:00:00Z",
        "provenance": {
            "source_ids": [f"source:{claim_id}"],
            "transformation_version": "availability-ledger-v1",
        },
    }


def _ledger() -> dict:
    ledger = new_availability_ledger(
        season="2026-27", created_at="2026-08-14T08:00:00Z"
    )
    ledger = append_availability_claim(
        ledger, _claim("claim-transfer", "player:a", 0.9)
    )
    return append_availability_claim(
        ledger, _claim("claim-lineup", "player:b", 0.8)
    )


def _boundaries() -> list[dict]:
    return [
        {
            "boundary_id": "lineup:b",
            "decision_type": "lineup",
            "incumbent_id": "player:b",
            "alternative_id": "player:d",
            "margin_points": 2.0,
            "player_uids": ["player:b"],
            "max_swing_points": 1.0,
        },
        {
            "boundary_id": "transfer:a",
            "decision_type": "transfer",
            "incumbent_id": "hold",
            "alternative_id": "sell-player:a",
            "margin_points": 0.2,
            "player_uids": ["player:a"],
            "max_swing_points": 1.0,
        },
        {
            "boundary_id": "captain:a",
            "decision_type": "captaincy",
            "incumbent_id": "player:a",
            "alternative_id": "player:c",
            "margin_points": 0.5,
            "player_uids": ["player:a"],
            "max_swing_points": 1.0,
        },
        {
            "boundary_id": "chip:a",
            "decision_type": "chip",
            "incumbent_id": "no-chip",
            "alternative_id": "free-hit",
            "margin_points": 4.0,
            "player_uids": ["player:a"],
            "max_swing_points": 2.0,
        },
    ]


def test_boundary_ranking_is_deterministic_bounded_and_margin_aware():
    view = project_availability(
        _ledger(),
        decision_at="2026-08-14T17:30:00Z",
        player_uids=["player:a", "player:b", "player:missing"],
    )
    first = build_boundary_evidence_pack(
        availability_view=view,
        boundaries=_boundaries(),
        max_evidence=1,
    )
    second = build_boundary_evidence_pack(
        availability_view=view,
        boundaries=list(reversed(_boundaries())),
        max_evidence=1,
    )
    assert first == second
    assert first["content_sha256"] == artifact_hash(first)
    assert first["ranking"][0]["claim_id"] == "claim-transfer"
    assert first["ranking"][0]["can_flip_any_boundary"] is True
    assert first["ranking"][0]["ranked_boundaries"][0] == {
        "boundary_id": "transfer:a",
        "decision_type": "transfer",
        "margin_points": 0.2,
        "estimated_impact_points": 0.9,
        "can_flip": True,
    }
    assert first["omitted_accepted_claim_ids"] == ["claim-lineup"]
    assert first["limits"] == {
        "max_evidence": 1,
        "accepted_count": 1,
        "candidate_count": 2,
    }
    assert first["abstentions"] == [
        {"player_uid": "player:missing", "reason": "no_active_evidence"}
    ]


def test_weekly_context_keeps_ledger_view_and_pack_separately_sealed():
    context = build_weekly_evidence_context(
        ledger=_ledger(),
        decision_at="2026-08-14T17:30:00Z",
        boundaries=_boundaries(),
        player_uids=["player:a", "player:b", "player:missing"],
        max_evidence=2,
    )
    assert context["content_sha256"] == artifact_hash(context)
    assert (
        context["availability_view"]["content_sha256"]
        == artifact_hash(context["availability_view"])
    )
    assert (
        context["boundary_evidence_pack"]["content_sha256"]
        == artifact_hash(context["boundary_evidence_pack"])
    )


def test_shadow_effect_artifact_separates_evidence_plan_transfer_and_score():
    control = {
        "content_sha256": "control-plan",
        "transfers": [],
        "captain_id": "player:a",
    }
    evidence = {
        "content_sha256": "evidence-plan",
        "transfers": [{"player_out_id": "player:a", "player_in_id": "player:c"}],
        "captain_id": "player:c",
    }
    pending = build_shadow_effect_record(
        accepted_evidence_ids=["claim-transfer"],
        control_plan=control,
        evidence_plan=evidence,
    )
    assert pending["plan_effect"]["changed"] is True
    assert pending["transfer_effect"]["changed"] is True
    assert pending["score_effect"] == {
        "status": "pending",
        "control_score": None,
        "evidence_score": None,
        "delta": None,
    }

    revealed = build_shadow_effect_record(
        accepted_evidence_ids=["claim-transfer"],
        control_plan=control,
        evidence_plan=evidence,
        control_score=58,
        evidence_score=64,
    )
    assert revealed["score_effect"]["delta"] == 6
