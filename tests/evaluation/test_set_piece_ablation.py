"""Tests for set-piece effect-weight ablation (ticket 15)."""

from __future__ import annotations

import pytest

from src.evaluation.set_piece_ablation import (
    SetPieceAblationError,
    apply_set_piece_effect_weights,
    assess_set_piece_ablation_corpus,
    load_set_piece_weight_policy,
    run_set_piece_ablation,
    weight_for_role_rank,
)
from src.ingestion.set_piece_roles import artifact_hash


def _ledger() -> dict:
    value = {
        "schema_version": "1.0",
        "as_of": "2026-07-30T10:00:00Z",
        "status": "complete",
        "admissible_snapshot_ids": ["a" * 64],
        "excluded_future_snapshot_ids": [],
        "resolved_groups": [],
        "active_roles": [
            {
                "official_player_id": 1,
                "official_team_id": 10,
                "role": "penalty",
                "rank": 1,
                "confidence": 0.95,
                "observation_id": "obs-1",
            },
            {
                "official_player_id": 2,
                "official_team_id": 10,
                "role": "corner_or_indirect_free_kick",
                "rank": 2,
                "confidence": 0.8,
                "observation_id": "obs-2",
            },
        ],
        "unknowns": [],
        "conflicts": [],
        "expired": [],
    }
    value["content_sha256"] = artifact_hash(value)
    return value


def test_policy_loads_as_ablation_only() -> None:
    policy = load_set_piece_weight_policy()
    assert policy["live_active"] is False
    assert policy["policy_id"] == "set-piece-effect-weights-v1"
    assert len(policy["content_sha256"]) == 64


def test_weight_for_role_rank_respects_confidence_and_cap() -> None:
    policy = load_set_piece_weight_policy()
    assert weight_for_role_rank(policy, role="penalty", rank=1, confidence=0.95) == 0.18
    assert weight_for_role_rank(policy, role="penalty", rank=1, confidence=0.1) == 0.0
    assert weight_for_role_rank(policy, role="penalty", rank=5, confidence=0.95) == 0.0


def test_apply_weights_adds_expected_goals_addend() -> None:
    from src.ingestion.set_piece_roles import build_set_piece_feature_payload

    policy = load_set_piece_weight_policy()
    base = build_set_piece_feature_payload(_ledger())
    assert base["effect_weights"] is None
    applied = apply_set_piece_effect_weights(base, policy)
    assert applied["effect_weights"]["policy_id"] == policy["policy_id"]
    by_player = {row["official_player_id"]: row for row in applied["adjustments"]}
    assert by_player[1]["expected_goals_addend"] == 0.18
    assert by_player[2]["expected_goals_addend"] == 0.012


def test_corpus_without_pit_rows_is_not_ready() -> None:
    corpus = assess_set_piece_ablation_corpus()
    assert corpus["ready_for_promotion_folds"] is False
    assert "insufficient_cutoff_safe_set_piece_ledgers" in corpus["gaps"]


def test_run_ablation_remain_shadow_only() -> None:
    decision = run_set_piece_ablation(sample_ledger=_ledger())
    assert decision["decision"] == "remain_shadow_only"
    assert decision["promotion_eligible"] is False
    assert decision["live_effect_weights"] is None
    assert decision["example_adjustment_count"] == 2


def test_refuse_live_active_policy(tmp_path) -> None:
    import json

    policy = load_set_piece_weight_policy()
    policy["live_active"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(SetPieceAblationError, match="live_active"):
        load_set_piece_weight_policy(path)
