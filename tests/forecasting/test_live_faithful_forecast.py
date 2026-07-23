"""Contract tests for the point-in-time live-faithful forecast view."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from src.forecasting.live_faithful import (
    LiveFaithfulForecastError,
    artifact_hash,
    build_live_faithful_forecast,
)
from src.forecasting.replay_adapter import ReplayAdapterError, build_replay_solver_input
from src.forecasting.player_priors import PlayerPriorError, build_player_prior
from src.orchestration.historical_feature_state import feature_state_hash


def _feature_state(*, fixtures: int = 1, points: float = 17, minutes: float = 90) -> dict:
    components = [
        {
            "fixture_id": 201 + index,
            "opponent_club_id": "team:b",
            "was_home": index == 0,
            "difficulty": 3,
            "expected_minutes": 71.2,
            "expected_points": points,
        }
        for index in range(fixtures)
    ]
    state = {
        "schema_version": "1.0",
        "feature_state_id": "feature:gw02",
        "content_sha256": "",
        "episode_id": "benchmark-v0:2025-26:gw02:manager-neutral",
        "season": "2025-26",
        "gameweek": 2,
        "cutoff": "2025-08-22T17:30:00Z",
        "lineage": {"ruleset_id": "2025-26-v1.0"},
        "players": [
            {
                "player_id": "player:new-element-id",
                "name": "Changed Name",
                "position": "MID",
                "club_id": "team:a",
                "quote": {
                    "now_cost": 7.5,
                    "source_gameweek": 1,
                    "age_gameweeks": 1,
                    "price_confidence": "historical_post_gameweek_export",
                },
                "history": [
                    {
                        "gameweek": 1,
                        "minutes": minutes,
                        "started": int(minutes > 60),
                        "total_points": points,
                    }
                ],
                "projection": {
                    "model_version": "historical-rolling-v1",
                    "expected_points": points * fixtures,
                    "expected_minutes": 71.2 * fixtures,
                    "start_probability": 0.95,
                    "fixture_count": fixtures,
                    "fixture_components": components,
                },
            }
        ],
    }
    state["content_sha256"] = feature_state_hash(state)
    return state


def _identity() -> dict:
    return {
        "season": "2025-26",
        "players": [
            {
                "canonical_id": "player:new-element-id",
                "fpl_player_id": 999,
                "fpl_code": 12345,
                "team_canonical_id": "team:a",
            }
        ],
    }


def _seal(payload: dict) -> dict:
    result = deepcopy(payload)
    result["content_sha256"] = artifact_hash(result)
    return result


def _player_prior() -> dict:
    return _seal(
        {
            "schema_version": "1.0",
            "season": "2024-25",
            "as_of": "2025-05-26T00:00:00Z",
            "players": [
                {
                    "fpl_code": 12345,
                    "position": "MID",
                    "points_per_90": 5.0,
                    "start_probability": 0.8,
                    "minutes_per_start": 82.0,
                    "sample_minutes": 2400,
                }
            ],
            "fallbacks": {
                "MID:7.5-10": {
                    "points_per_90": 3.5,
                    "start_probability": 0.55,
                    "minutes_per_start": 76.0,
                    "sample_minutes": 900,
                }
            },
        }
    )


def _team_prior(*, multiplier: float = 1.0, as_of: str = "2025-08-22T12:00:00Z") -> dict:
    return _seal(
        {
            "schema_version": "1.0",
            "season": "2025-26",
            "as_of": as_of,
            "fixture_adjustments": [
                {
                    "fixture_id": 201,
                    "club_id": "team:a",
                    "attack_multiplier": multiplier,
                    "defence_multiplier": 1.0,
                },
                {
                    "fixture_id": 202,
                    "club_id": "team:a",
                    "attack_multiplier": multiplier,
                    "defence_multiplier": 1.0,
                },
            ],
        }
    )


def _config() -> dict:
    return _seal(
        {
            "model_version": "live-faithful-v1",
            "status": "provisional_pending_calibration",
            "prior_equivalent_minutes": 900.0,
            "start_prior_equivalent_matches": 8.0,
            "cameo_minutes": 18.0,
            "price_bands": [[0, 5.5], [5.5, 7.5], [7.5, 10], [10, 20]],
            "fixture_multiplier_bounds": [0.7, 1.3],
            "position_attack_weight": {
                "GKP": 0.0,
                "DEF": 0.2,
                "MID": 0.85,
                "FWD": 1.0,
            },
            "optional_components": {
                "timestamped_odds": "degrade_when_absent",
                "unstructured_evidence": "degrade_when_absent",
            },
        }
    )


def _build(**overrides: object) -> dict:
    values = {
        "feature_state": _feature_state(),
        "identity_map": _identity(),
        "player_prior": _player_prior(),
        "team_prior": _team_prior(),
        "model_config": _config(),
    }
    values.update(overrides)
    return build_live_faithful_forecast(**values)


def test_one_exceptional_gameweek_is_shrunk_and_raw_ablation_is_retained() -> None:
    forecast = _build()
    player = forecast["players"][0]
    assert player["raw_rolling_expected_points"] == 17
    assert 0 < player["expected_points"] < 17
    assert player["prior"]["source"] == "fpl_code"
    assert player["prior"]["fpl_code"] == 12345


def test_expected_minutes_changes_points_for_same_rate() -> None:
    starter = _build(feature_state=_feature_state(minutes=90))
    substitute = _build(feature_state=_feature_state(minutes=0, points=0))
    assert starter["players"][0]["expected_minutes"] > substitute["players"][0]["expected_minutes"]
    assert starter["players"][0]["expected_points"] > substitute["players"][0]["expected_points"]


def test_fpl_code_join_survives_changed_element_name_and_club() -> None:
    player = _build()["players"][0]
    assert player["player_id"] == "player:new-element-id"
    assert player["prior"]["source"] == "fpl_code"
    assert player["prior"]["sample_minutes"] == 2400


def test_unmatched_player_uses_declared_position_fallback() -> None:
    identity = _identity()
    identity["players"][0]["fpl_code"] = 54321
    player = _build(identity_map=identity)["players"][0]
    assert player["prior"]["source"] == "position_price_fallback"
    assert player["prior"]["fallback_key"] == "MID:7.5-10"
    assert player["prior"]["reason"] == "no_fpl_code_prior"
    assert "player_prior_position_price_fallback" in player["limitations"]


def test_duplicate_fpl_code_prior_fails_closed() -> None:
    prior = _player_prior()
    prior["players"].append(deepcopy(prior["players"][0]))
    prior["content_sha256"] = artifact_hash(prior)
    with pytest.raises(LiveFaithfulForecastError, match="Duplicate player prior"):
        _build(player_prior=prior)


def test_blank_is_zero_and_double_sums_independent_fixture_components() -> None:
    blank = _build(feature_state=_feature_state(fixtures=0))
    double = _build(feature_state=_feature_state(fixtures=2))
    assert blank["players"][0]["expected_points"] == 0
    assert blank["players"][0]["expected_minutes"] == 0
    assert len(double["players"][0]["fixture_components"]) == 2
    assert double["players"][0]["expected_points"] == round(
        sum(row["expected_points"] for row in double["players"][0]["fixture_components"]),
        2,
    )


def test_team_adjustment_is_bounded_and_changes_projection() -> None:
    neutral = _build()
    strong = _build(team_prior=_team_prior(multiplier=5.0))
    neutral_player = neutral["players"][0]
    strong_player = strong["players"][0]
    assert strong_player["expected_points"] > neutral_player["expected_points"]
    assert strong_player["fixture_components"][0]["team_multiplier"] == 1.3


def test_artifact_is_deterministic_and_hashes_all_inputs() -> None:
    first = _build()
    reordered_prior = _player_prior()
    reordered_prior["players"] = list(reversed(reordered_prior["players"]))
    reordered_prior["content_sha256"] = artifact_hash(reordered_prior)
    second = _build(player_prior=reordered_prior)
    assert first == second

    changed = _config()
    changed["cameo_minutes"] = 19.0
    changed["content_sha256"] = artifact_hash(changed)
    assert _build(model_config=changed)["content_sha256"] != first["content_sha256"]


def test_post_cutoff_team_prior_and_tampered_artifacts_fail_closed() -> None:
    with pytest.raises(LiveFaithfulForecastError, match="after feature cutoff"):
        _build(team_prior=_team_prior(as_of="2025-08-23T00:00:00Z"))

    prior = _player_prior()
    prior["players"][0]["points_per_90"] = 99
    with pytest.raises(LiveFaithfulForecastError, match="content hash"):
        _build(player_prior=prior)


def test_optional_absence_is_visible_not_silently_imputed() -> None:
    forecast = _build()
    assert forecast["status"] == "degraded"
    assert forecast["limitations"] == [
        "timestamped_odds_absent",
        "unstructured_evidence_absent",
    ]


def test_replay_adapter_uses_only_an_explicit_complete_forecast_view() -> None:
    state = _feature_state()
    policy = {
        "season": "2025-26",
        "gameweek": 2,
        "ruleset_id": "2025-26-v1.0",
        "bank": 0,
        "free_transfers": 1,
        "squad": [],
    }
    baseline = build_replay_solver_input(feature_state=state, policy_state=policy)
    forecast = _build(feature_state=state)
    live = build_replay_solver_input(
        feature_state=state,
        policy_state=policy,
        forecast_view=forecast,
    )
    assert baseline.players[0]["expected_points"] == 17
    assert live.players[0]["expected_points"] == forecast["players"][0]["expected_points"]
    assert live.players[0]["forecast_view_sha256"] == forecast["content_sha256"]
    assert live.players[0]["forecast_model_status"] == "provisional_pending_calibration"

    incomplete = deepcopy(forecast)
    incomplete["players"] = []
    incomplete["content_sha256"] = artifact_hash(incomplete)
    with pytest.raises(ReplayAdapterError, match="player market differs"):
        build_replay_solver_input(
            feature_state=state,
            policy_state=policy,
            forecast_view=incomplete,
        )


def test_prior_builder_aggregates_by_stable_code_and_builds_price_fallbacks() -> None:
    identity = {
        "players": [
            {"fpl_player_id": 1, "fpl_code": 101},
            {"fpl_player_id": 2, "fpl_code": 102},
        ]
    }
    rows = [
        {
            "element": 1,
            "fixture": 1,
            "position": "MID",
            "minutes": 90,
            "starts": 1,
            "total_points": 6,
            "value": 75,
        },
        {
            "element": 1,
            "fixture": 2,
            "position": "MID",
            "minutes": 30,
            "starts": 0,
            "total_points": 1,
            "value": 76,
        },
        {
            "element": 2,
            "fixture": 1,
            "position": "MID",
            "minutes": 90,
            "starts": 1,
            "total_points": 3,
            "value": 80,
        },
    ]
    prior = build_player_prior(
        season="2024-25",
        as_of="2025-05-26T00:00:00Z",
        rows=rows,
        identity_map=identity,
        price_bands=[[0, 5.5], [5.5, 7.5], [7.5, 10], [10, 20]],
    )
    first = prior["players"][0]
    assert first["fpl_code"] == 101
    assert first["sample_minutes"] == 120
    assert first["start_probability"] == 0.5
    assert first["price_band"] == "7.5-10"
    assert "MID:7.5-10" in prior["fallbacks"]
    assert prior["content_sha256"] == artifact_hash(prior)


def test_prior_builder_rejects_duplicate_player_fixture() -> None:
    row = {
        "element": 1,
        "fixture": 1,
        "position": "MID",
        "minutes": 90,
        "starts": 1,
        "total_points": 6,
        "value": 75,
    }
    with pytest.raises(PlayerPriorError, match="Duplicate player-fixture"):
        build_player_prior(
            season="2024-25",
            as_of="2025-05-26T00:00:00Z",
            rows=[row, row],
            identity_map={"players": [{"fpl_player_id": 1, "fpl_code": 101}]},
            price_bands=[[0, 20]],
        )
