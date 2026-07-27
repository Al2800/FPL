"""Official set-piece roles are immutable, cutoff-safe and superseding."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.ingestion.set_piece_roles import (
    SetPieceRoleError,
    artifact_hash,
    build_set_piece_feature_payload,
    build_set_piece_role_ledger,
    normalise_official_set_piece_snapshot,
)


SOURCE_HASH = "a" * 64


def _bootstrap(*, duplicate_penalty_rank: bool = False) -> dict:
    return {
        "teams": [
            {"id": 1, "name": "Alpha"},
            {"id": 2, "name": "Beta"},
        ],
        "elements": [
            {
                "id": 11,
                "team": 1,
                "web_name": "One",
                "penalties_order": 1,
                "penalties_text": "Primary",
                "direct_freekicks_order": 2,
                "corners_and_indirect_freekicks_order": 1,
            },
            {
                "id": 12,
                "team": 1,
                "web_name": "Two",
                "penalties_order": 1 if duplicate_penalty_rank else 2,
                "direct_freekicks_order": 1,
                "corners_and_indirect_freekicks_order": None,
            },
            {
                "id": 21,
                "team": 2,
                "web_name": "Three",
                "penalties_order": 1,
                "direct_freekicks_order": None,
                "corners_and_indirect_freekicks_order": 1,
            },
        ],
    }


def _snapshot(
    *,
    bootstrap: dict | None = None,
    source_hash: str = SOURCE_HASH,
    observed_at: str = "2026-08-01T09:00:00Z",
    available_at: str = "2026-08-01T09:01:00Z",
    expiry_hours: int = 192,
) -> dict:
    return normalise_official_set_piece_snapshot(
        bootstrap or _bootstrap(),
        source_sha256=source_hash,
        observed_at=observed_at,
        available_at=available_at,
        expiry_hours=expiry_hours,
    )


def _group(snapshot: dict, team_id: int, role: str) -> dict:
    return next(
        row
        for row in snapshot["groups"]
        if row["official_team_id"] == team_id and row["role"] == role
    )


def test_snapshot_is_complete_deterministic_and_identity_resolved() -> None:
    first = _snapshot()
    second = _snapshot(bootstrap=deepcopy(_bootstrap()))
    assert first == second
    assert first["team_count"] == 2
    assert first["group_count"] == 6
    assert first["assignment_count"] == 7
    assert first["conflict_count"] == 0
    assert first["unknown_group_count"] == 1
    penalty = _group(first, 1, "penalty")
    assert [row["official_player_id"] for row in penalty["assignments"]] == [11, 12]
    assert [row["confidence"] for row in penalty["assignments"]] == [0.95, 0.8]
    assert first["content_sha256"] == artifact_hash(first)


def test_duplicate_rank_is_visible_and_excluded_from_features() -> None:
    snapshot = _snapshot(bootstrap=_bootstrap(duplicate_penalty_rank=True))
    group = _group(snapshot, 1, "penalty")
    assert group["status"] == "conflicted"
    assert group["conflicts"] == [
        {
            "type": "duplicate_rank",
            "rank": 1,
            "official_player_ids": [11, 12],
        }
    ]
    ledger = build_set_piece_role_ledger(
        [snapshot], as_of="2026-08-01T10:00:00Z"
    )
    assert any(
        row["official_team_id"] == 1 and row["role"] == "penalty"
        for row in ledger["conflicts"]
    )
    payload = build_set_piece_feature_payload(ledger)
    assert not any(
        row["official_team_id"] == 1 and row["role"] == "penalty"
        for row in payload["adjustments"]
    )


def test_later_snapshot_replaces_whole_group_and_future_is_excluded() -> None:
    first = _snapshot()
    later_bootstrap = _bootstrap()
    later_bootstrap["elements"][0]["penalties_order"] = None
    later_bootstrap["elements"][1]["penalties_order"] = 1
    later = _snapshot(
        bootstrap=later_bootstrap,
        source_hash="b" * 64,
        observed_at="2026-08-02T09:00:00Z",
        available_at="2026-08-02T09:01:00Z",
    )

    before = build_set_piece_role_ledger(
        [first, later], as_of="2026-08-01T12:00:00Z"
    )
    assert before["excluded_future_snapshot_ids"] == [later["content_sha256"]]
    before_penalties = [
        row
        for row in before["active_roles"]
        if row["official_team_id"] == 1 and row["role"] == "penalty"
    ]
    assert [row["official_player_id"] for row in before_penalties] == [11, 12]

    after = build_set_piece_role_ledger(
        [first, later], as_of="2026-08-02T12:00:00Z"
    )
    after_penalties = [
        row
        for row in after["active_roles"]
        if row["official_team_id"] == 1 and row["role"] == "penalty"
    ]
    assert [row["official_player_id"] for row in after_penalties] == [12]
    group = next(
        row
        for row in after["resolved_groups"]
        if row["official_team_id"] == 1 and row["role"] == "penalty"
    )
    assert group["superseded_group_ids"] == [
        _group(first, 1, "penalty")["group_id"]
    ]


def test_expired_or_missing_evidence_degrades_to_exact_baseline() -> None:
    expired = _snapshot(expiry_hours=1)
    ledger = build_set_piece_role_ledger(
        [expired], as_of="2026-08-01T10:01:00Z"
    )
    assert ledger["status"] == "degraded"
    assert ledger["active_roles"] == []
    payload = build_set_piece_feature_payload(ledger)
    assert payload["adjustments"] == []
    assert payload["fallback"] == "byte_identical_baseline"
    assert payload["effect_weights"] is None

    empty = build_set_piece_role_ledger(
        [], as_of="2026-08-01T10:01:00Z"
    )
    assert empty["status"] == "degraded"
    assert build_set_piece_feature_payload(empty)["fallback"] == (
        "byte_identical_baseline"
    )


def test_hash_tampering_and_bad_temporal_order_fail_closed() -> None:
    changed = _snapshot()
    changed["assignment_count"] += 1
    with pytest.raises(SetPieceRoleError, match="content hash mismatch"):
        build_set_piece_role_ledger(
            [changed], as_of="2026-08-01T10:00:00Z"
        )
    with pytest.raises(SetPieceRoleError, match="cannot be before"):
        _snapshot(
            observed_at="2026-08-01T09:00:00Z",
            available_at="2026-08-01T08:59:59Z",
        )
