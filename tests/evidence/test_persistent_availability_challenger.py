from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import yaml

from src.evidence.availability_ledger import (
    apply_persistent_availability_challenger,
    append_availability_claim,
    new_availability_ledger,
)
from src.forecasting.live_faithful import artifact_hash


REPO = Path(__file__).resolve().parents[2]
POLICY = yaml.safe_load(
    (REPO / "control/policies/evidence-adjustments-v2.yaml").read_text(
        encoding="utf-8"
    )
)
REGISTRY = yaml.safe_load(
    (REPO / "control/sources/source-registry.yaml").read_text(encoding="utf-8")
)
EVIDENCE_CONFIG = json.loads(
    (REPO / "config/data_sources/2026-27-evidence.json").read_text(
        encoding="utf-8"
    )
)


def _claim(
    claim_id: str,
    *,
    status: str = "unavailable",
    player_uid: str = "player:2026-27:1",
    available_at: str = "2026-08-14T08:00:00Z",
    expires_at: str = "2026-08-31T00:00:00Z",
    source_id: str = "fpl-official-endpoints",
    **extra: object,
) -> dict:
    return {
        "claim_id": claim_id,
        "player_uid": player_uid,
        "status": status,
        "confidence": 0.95,
        "published_at": available_at,
        "observed_at": available_at,
        "available_at": available_at,
        "expires_at": expires_at,
        "provenance": {
            "source_ids": [source_id],
            "source_hashes": {
                source_id: hashlib.sha256(claim_id.encode("utf-8")).hexdigest()
            },
            "identity_resolution": "exact",
            "transformation_version": "availability-ledger-v1",
        },
        **extra,
    }


def _solver_input() -> dict:
    return {
        "season": "2026-27",
        "gameweek": 2,
        "players": [
            {
                "player_id": "player:2026-27:1",
                "status": "a",
                "start_probability": 0.95,
                "expected_minutes": 85.0,
                "expected_points": 6.2,
            },
            {
                "player_id": "player:2026-27:2",
                "status": "a",
                "start_probability": 0.8,
                "expected_minutes": 70.0,
                "expected_points": 4.5,
            },
        ],
    }


def _enabled_policy() -> dict:
    policy = deepcopy(POLICY)
    policy["persistent_availability"]["enabled"] = True
    return policy


def _apply(
    solver_input: dict,
    ledger: dict,
    *,
    decision_at: str,
    policy: dict = POLICY,
) -> tuple[dict, dict]:
    return apply_persistent_availability_challenger(
        solver_input,
        ledger=ledger,
        decision_at=decision_at,
        checkpoint_id=f"checkpoint:{decision_at}",
        policy=policy,
        source_registry=REGISTRY,
        evidence_config=EVIDENCE_CONFIG,
    )


def test_disabled_policy_returns_byte_identical_structured_solver_input() -> None:
    ledger = append_availability_claim(
        new_availability_ledger(
            season="2026-27", created_at="2026-08-14T08:00:00Z"
        ),
        _claim("player-out"),
    )
    baseline = _solver_input()

    output, audit = _apply(
        baseline, ledger, decision_at="2026-08-14T10:00:00Z"
    )

    assert output == baseline
    assert artifact_hash(output) == artifact_hash(baseline)
    assert audit["status"] == "disabled"
    assert audit["output_solver_input_sha256"] == artifact_hash(baseline)
    assert audit["content_sha256"] == artifact_hash(audit)


def test_unavailability_persists_across_checkpoints_until_expiry() -> None:
    ledger = append_availability_claim(
        new_availability_ledger(
            season="2026-27", created_at="2026-08-14T08:00:00Z"
        ),
        _claim("player-out", expires_at="2026-08-28T00:00:00Z"),
    )
    policy = _enabled_policy()

    for checkpoint in (
        "2026-08-14T10:00:00Z",
        "2026-08-21T10:00:00Z",
        "2026-08-27T10:00:00Z",
    ):
        output, audit = _apply(
            _solver_input(), ledger, decision_at=checkpoint, policy=policy
        )
        assert output["players"][0] == {
            "player_id": "player:2026-27:1",
            "status": "i",
            "start_probability": 0.0,
            "expected_minutes": 0.0,
            "expected_points": 0.0,
        }
        assert audit["status"] == "applied"
        assert [row["claim_id"] for row in audit["applied"]] == ["player-out"]

    expired, expired_audit = _apply(
        _solver_input(),
        ledger,
        decision_at="2026-08-28T00:00:00Z",
        policy=policy,
    )
    assert expired == _solver_input()
    assert expired_audit["status"] == "enabled_no_effect"
    assert expired_audit["abstentions"] == [
        {"player_uid": "player:2026-27:1", "reason": "no_active_evidence"},
        {"player_uid": "player:2026-27:2", "reason": "no_active_evidence"},
    ]


def test_recovery_supersession_restores_the_exact_structured_baseline() -> None:
    ledger = append_availability_claim(
        new_availability_ledger(
            season="2026-27", created_at="2026-08-14T08:00:00Z"
        ),
        _claim("absence", expires_at="2026-08-31T00:00:00Z"),
    )
    ledger = append_availability_claim(
        ledger,
        _claim(
            "recovery",
            status="available",
            available_at="2026-08-20T08:00:00Z",
            expires_at="2026-08-24T00:00:00Z",
            supersedes_claim_ids=["absence"],
            recovery={
                "condition": "returned_to_training",
                "condition_met": True,
            },
        ),
    )
    baseline = _solver_input()

    output, audit = _apply(
        baseline,
        ledger,
        decision_at="2026-08-21T10:00:00Z",
        policy=_enabled_policy(),
    )

    assert output == baseline
    assert audit["applied"] == []
    assert [row["claim_id"] for row in audit["restored"]] == ["recovery"]
    assert audit["restored"][0]["baseline"] == {
        "status": "a",
        "start_probability": 0.95,
        "expected_minutes": 85.0,
        "expected_points": 6.2,
    }


def test_doubt_is_bounded_and_bad_source_identity_or_cutoff_never_apply() -> None:
    ledger = new_availability_ledger(
        season="2026-27", created_at="2026-08-14T08:00:00Z"
    )
    ledger = append_availability_claim(ledger, _claim("doubt", status="doubtful"))
    ledger = append_availability_claim(
        ledger,
        _claim(
            "unknown-source",
            player_uid="player:2026-27:2",
            available_at="2026-08-14T08:01:00Z",
            source_id="unregistered-source",
        ),
    )
    ledger = append_availability_claim(
        ledger,
        _claim(
            "future",
            player_uid="player:2026-27:2",
            available_at="2026-08-15T08:00:00Z",
        ),
    )

    output, audit = _apply(
        _solver_input(),
        ledger,
        decision_at="2026-08-14T10:00:00Z",
        policy=_enabled_policy(),
    )

    assert output["players"][0]["start_probability"] == 0.7
    assert output["players"][0]["expected_minutes"] == 62.6
    assert output["players"][0]["expected_points"] == 4.57
    assert output["players"][1] == _solver_input()["players"][1]
    assert audit["quarantined"] == [
        {
            "claim_id": "unknown-source",
            "player_uid": "player:2026-27:2",
            "reason": "source_not_registry_approved",
        }
    ]
    assert audit["abstentions"] == []

import pytest


def test_exact_duplicate_claim_is_idempotent_but_changed_duplicate_fails_closed() -> None:
    original_claim = _claim("idempotent")
    ledger = append_availability_claim(
        new_availability_ledger(
            season="2026-27", created_at="2026-08-14T08:00:00Z"
        ),
        original_claim,
    )

    repeated = append_availability_claim(ledger, deepcopy(original_claim))
    assert repeated == ledger

    conflicting = deepcopy(original_claim)
    conflicting["confidence"] = 0.7
    with pytest.raises(ValueError, match="conflicting duplicate"):
        append_availability_claim(ledger, conflicting)

from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    new_live_evidence_ledger,
)
from src.evidence.availability_ledger import (
    synchronise_availability_from_live_evidence,
)


def _official_live_claim(
    claim_id: str,
    *,
    status: str,
    available_at: str,
    supersedes: list[str] | None = None,
    player_uid: str = "player:2026-27:1",
) -> dict:
    return {
        "claim_id": claim_id,
        "source_id": "fpl-official-endpoints",
        "document_id": f"bootstrap-static:{claim_id}",
        "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/",
        "source_hash_sha256": hashlib.sha256(claim_id.encode("utf-8")).hexdigest(),
        "claim_text": f"Official FPL status {status} for Fixture Player.",
        "claim_precision": "official_structured_field_and_derived_summary",
        "claim_type": "player_availability",
        "value": {"status": status},
        "confidence": 0.98,
        "published_at": available_at,
        "observed_at": available_at,
        "available_at": available_at,
        "expires_at": "2026-08-31T00:00:00Z",
        "identity_bindings": [
            {
                "entity_type": "player_uid",
                "stable_id": player_uid,                "source_label": "Fixture Player",
                "match_status": "exact",
            }
        ],
        "decision_boundary_ids": [f"availability:{player_uid}"],        "estimated_impact_points": 6.0,
        "supersedes_claim_ids": supersedes or [],
    }


def test_live_ledger_bridge_is_hash_bound_idempotent_and_restores_on_recovery() -> None:
    live = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    live = append_live_evidence_claim(
        live,
        _official_live_claim(
            "official-out", status="i", available_at="2026-08-14T08:00:00Z"
        ),
        source_registry=REGISTRY,
        config=EVIDENCE_CONFIG,
    )
    persistent = new_availability_ledger(
        season="2026-27", created_at="2026-08-14T08:00:00Z"
    )

    persistent, first = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=live,
        decision_at="2026-08-14T10:00:00Z",
    )
    assert first["appended_claim_ids"] == ["official-out"]
    assert persistent["claims"][0]["provenance"]["source_hashes"] == {
        "fpl-official-endpoints": hashlib.sha256(b"official-out").hexdigest()
    }
    second_ledger, second = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=live,
        decision_at="2026-08-14T10:00:00Z",
    )
    assert second_ledger == persistent
    assert second["idempotent_claim_ids"] == ["official-out"]

    suppressed, suppressed_audit = _apply(
        _solver_input(),
        persistent,
        decision_at="2026-08-14T10:00:00Z",
        policy=_enabled_policy(),
    )
    assert suppressed["players"][0]["expected_minutes"] == 0.0
    assert suppressed_audit["applied"][0]["claim_id"] == "official-out"

    live = append_live_evidence_claim(
        live,
        _official_live_claim(
            "official-recovery",
            status="a",
            available_at="2026-08-20T08:00:00Z",
            supersedes=["official-out"],
        ),
        source_registry=REGISTRY,
        config=EVIDENCE_CONFIG,
    )
    recovered, recovery_audit = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=live,
        decision_at="2026-08-20T10:00:00Z",
    )
    assert recovery_audit["appended_claim_ids"] == ["official-recovery"]

    restored, restored_audit = _apply(
        _solver_input(),
        recovered,
        decision_at="2026-08-20T10:00:00Z",
        policy=_enabled_policy(),
    )
    assert restored == _solver_input()
    assert [row["claim_id"] for row in restored_audit["restored"]] == [
        "official-recovery"
    ]


def test_live_bridge_remains_idempotent_after_unrelated_ledger_growth() -> None:
    live = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    live = append_live_evidence_claim(
        live,
        _official_live_claim(
            "official-out", status="i", available_at="2026-08-14T08:00:00Z"
        ),
        source_registry=REGISTRY,
        config=EVIDENCE_CONFIG,
    )
    persistent = new_availability_ledger(
        season="2026-27", created_at="2026-08-14T08:00:00Z"
    )
    persistent, _ = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=live,
        decision_at="2026-08-14T10:00:00Z",
    )
    live = append_live_evidence_claim(
        live,
        _official_live_claim(
            "official-other",
            status="d",
            available_at="2026-08-14T09:00:00Z",
            player_uid="player:2026-27:2",
        ),
        source_registry=REGISTRY,
        config=EVIDENCE_CONFIG,
    )

    updated, audit = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=live,
        decision_at="2026-08-14T10:00:00Z",
    )

    assert audit["appended_claim_ids"] == ["official-other"]
    assert audit["idempotent_claim_ids"] == ["official-out"]
    assert [row["claim_id"] for row in updated["claims"]] == [
        "official-out",
        "official-other",
    ]
