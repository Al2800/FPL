"""Tests for ICT feature-weight ablation (ticket 16)."""

from __future__ import annotations

import pytest

from src.evaluation.ict_ablation import (
    IctAblationError,
    apply_ict_effect_weights,
    assess_ict_ablation_corpus,
    build_ict_feature_payload,
    load_ict_weight_policy,
    run_ict_ablation,
    weight_for_component,
)


def _players() -> list[dict]:
    return [
        {
            "official_player_id": 1,
            "position": "MID",
            "influence": 30.0,
            "creativity": 20.0,
            "threat": 50.0,
            "ict_index": 10.0,
        },
        {
            "official_player_id": 2,
            "position": "MID",
            "influence": 10.0,
            "creativity": 5.0,
            "threat": 10.0,
            "ict_index": 2.0,
        },
        {
            "official_player_id": 3,
            "position": "FWD",
            "influence": 0.0,
            "creativity": 0.0,
            "threat": 0.0,
            "ict_index": 0.0,
        },
    ]


def test_policy_loads_as_ablation_only() -> None:
    policy = load_ict_weight_policy()
    assert policy["live_active"] is False
    assert policy["policy_id"] == "ict-feature-weights-v1"
    assert policy["lag_window_gameweeks"] == 3
    assert len(policy["content_sha256"]) == 64


def test_weight_for_component_scales_by_std() -> None:
    policy = load_ict_weight_policy()
    assert weight_for_component(policy, component="threat", zscore=1.0) == 0.05
    assert weight_for_component(policy, component="threat", zscore=0.0) == 0.0


def test_apply_weights_adds_expected_points_addend() -> None:
    policy = load_ict_weight_policy()
    base = build_ict_feature_payload(_players())
    assert base["effect_weights"] is None
    applied = apply_ict_effect_weights(base, policy, arm="threat_only")
    assert applied["effect_weights"]["policy_id"] == policy["policy_id"]
    by_player = {row["official_player_id"]: row for row in applied["adjustments"]}
    assert by_player[1]["expected_points_addend"] > by_player[2]["expected_points_addend"]
    assert by_player[3]["expected_points_addend"] == 0.0


def test_corpus_without_pit_rows_is_not_ready() -> None:
    corpus = assess_ict_ablation_corpus()
    assert corpus["ready_for_promotion_folds"] is False
    assert "insufficient_cutoff_safe_ict_lag_snapshots" in corpus["gaps"]


def test_run_ablation_remain_shadow_only() -> None:
    decision = run_ict_ablation(sample_players=_players())
    assert decision["decision"] == "remain_shadow_only"
    assert decision["promotion_eligible"] is False
    assert decision["live_effect_weights"] is None
    assert decision["frozen_four_family_prereg"] is False
    assert decision["example_adjustment_count"] == 3


def test_refuse_live_active_policy(tmp_path) -> None:
    import json

    policy = load_ict_weight_policy()
    policy["live_active"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(IctAblationError, match="live_active"):
        load_ict_weight_policy(path)
