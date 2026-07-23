"""Leakage-first tests for the historical replay feature and market adapter."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.forecasting.replay_adapter import ReplayAdapterError, build_replay_solver_input
from src.orchestration.historical_feature_state import (
    HistoricalFeatureStateError,
    build_feature_state,
    feature_state_hash,
)


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _identity() -> dict:
    payload = {
        "identity_map_version": "1.0",
        "season": "2025-26",
        "teams": [
            {
                "canonical_id": "team:2025-26:1",
                "fpl_team_id": 1,
                "fpl_name": "Alpha",
            },
            {
                "canonical_id": "team:2025-26:2",
                "fpl_team_id": 2,
                "fpl_name": "Beta",
            },
            {
                "canonical_id": "team:2025-26:3",
                "fpl_team_id": 3,
                "fpl_name": "Gamma",
            },
        ],
        "players": [
            {
                "canonical_id": "player:2025-26:1",
                "fpl_player_id": 1,
                "fpl_code": 101,
                "team_canonical_id": "team:2025-26:1",
            },
            {
                "canonical_id": "player:2025-26:2",
                "fpl_player_id": 2,
                "fpl_code": 102,
                "team_canonical_id": "team:2025-26:3",
            },
        ],
        "metrics": {"teams": 3, "players": 2},
    }
    payload["identity_map_id"] = _canonical_hash(payload)
    return payload


def _row(
    *,
    gameweek: int,
    element: int = 1,
    fixture: int = 10,
    team: str = "Alpha",
    position: str = "MID",
    minutes: int = 90,
    starts: int = 1,
    points: int = 2,
    value: int = 50,
) -> dict:
    return {
        "GW": gameweek,
        "element": element,
        "fixture": fixture,
        "name": f"Player {element}",
        "position": position,
        "team": team,
        "opponent_team": 2,
        "kickoff_time": f"2025-08-{10 + gameweek:02d}T14:00:00Z",
        "minutes": minutes,
        "starts": starts,
        "total_points": points,
        "goals_scored": 0,
        "assists": 0,
        "clean_sheets": 0,
        "goals_conceded": 0,
        "saves": 0,
        "bonus": 0,
        "bps": 10,
        "yellow_cards": 0,
        "red_cards": 0,
        "expected_goals": 0.1,
        "expected_assists": 0.1,
        "expected_goal_involvements": 0.2,
        "expected_goals_conceded": 0.4,
        "influence": 10.0,
        "creativity": 10.0,
        "threat": 10.0,
        "ict_index": 3.0,
        "value": value,
        "selected": 100,
        "transfers_balance": 0,
        "transfers_in": 0,
        "transfers_out": 0,
    }


def _inputs(
    gameweek: int,
    rows: list[dict],
    *,
    fixtures: list[dict] | None = None,
) -> tuple[dict, dict, dict]:
    observed = {
        "observed_partition_version": "1.0",
        "episode_id": f"benchmark-v0:2025-26:gw{gameweek:02d}:manager-neutral",
        "season": "2025-26",
        "gameweek": gameweek,
        "cutoff": f"2025-08-{10 + gameweek:02d}T12:00:00Z",
        "deadline": f"2025-08-{10 + gameweek:02d}T12:00:00Z",
        "dataset_id": "benchmark-v0-2025-26",
        "dataset_hash": "b" * 64,
        "lagged_from_gameweek": gameweek - 1 if gameweek > 1 else None,
        "lagged_player_features": rows,
        "fixtures": fixtures
        if fixtures is not None
        else [
            {
                "id": 100 + gameweek,
                "event": gameweek,
                "kickoff_time": f"2025-08-{10 + gameweek:02d}T14:00:00Z",
                "team_h": 1,
                "team_a": 2,
                "team_h_difficulty": 3,
                "team_a_difficulty": 3,
                "provisional_start_time": False,
            }
        ],
        "prior_match_results": [],
        "identity_map_ref": {
            "artifact_id": _identity()["identity_map_id"],
            "content_sha256": _canonical_hash(_identity()),
        },
        "limitations": [],
    }
    manifest = {
        "schema_version": "1.0",
        "episode_id": observed["episode_id"],
        "season": "2025-26",
        "gameweek": gameweek,
        "mode": "historical_structured",
        "cutoff": observed["cutoff"],
        "deadline": observed["deadline"],
        "created_at": "2026-07-22T12:57:20Z",
        "code_commit": "c" * 40,
        "ruleset": {
            "ruleset_id": "2025-26-v1.0",
            "content_sha256": SHA,
        },
        "observed": {
            "feature_snapshot_ref": {
                "artifact_id": f"observed:{observed['episode_id']}",
                "content_sha256": _canonical_hash(observed),
            }
        },
    }
    return manifest, observed, _identity()


def _build(
    gameweek: int,
    rows: list[dict],
    *,
    previous_state: dict | None = None,
    fixtures: list[dict] | None = None,
) -> dict:
    manifest, observed, identity = _inputs(gameweek, rows, fixtures=fixtures)
    return build_feature_state(
        episode_manifest=manifest,
        observed=observed,
        identity_map=identity,
        previous_state=previous_state,
    )


def _player(state: dict, player_id: str = "player:2025-26:1") -> dict:
    return next(row for row in state["players"] if row["player_id"] == player_id)


def test_official_scout_seed_is_source_backed_legal_and_exact_budget() -> None:
    seed = json.loads(
        (
            ROOT
            / "control"
            / "seeds"
            / "2025-26"
            / "official-scout-gw1.json"
        ).read_text(encoding="utf-8")
    )
    assert seed["seed_id"] == "benchmark-v0-official-scout-gw1"
    assert seed["evidence"][0]["published_at"] < seed["deadline"]
    assert seed["evidence"][0]["source_url"] == (
        "https://www.premierleague.com/en/news/4373986"
    )
    assert len(seed["squad"]) == len({row["player_id"] for row in seed["squad"]}) == 15
    assert Counter(row["position"] for row in seed["squad"]) == {
        "GKP": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }
    assert max(Counter(row["club_id"] for row in seed["squad"]).values()) <= 3
    assert round(sum(row["purchase_price"] for row in seed["squad"]) + seed["bank"], 1) == 100.0
    assert not {"points", "minutes", "outcome"} & set(json.dumps(seed).lower())


def test_double_gameweek_rows_are_aggregated_before_rolling_features() -> None:
    gw2 = _build(2, [_row(gameweek=1, points=2)])
    gw3 = _build(
        3,
        [
            _row(gameweek=2, fixture=20, minutes=90, starts=1, points=4),
            _row(gameweek=2, fixture=21, minutes=80, starts=1, points=6),
        ],
        previous_state=gw2,
    )
    player = _player(gw3)
    assert [row["gameweek"] for row in player["history"]] == [1, 2]
    assert player["history"][1]["fixture_count"] == 2
    assert player["history"][1]["minutes"] == 170
    assert player["history"][1]["started"] == 1
    assert player["history"][1]["total_points"] == 10
    assert player["projection"]["rolling_gameweeks"] == [1, 2]
    assert player["projection"]["expected_points"] == 6.0


def test_blank_keeps_known_player_and_ages_last_quote() -> None:
    gw2 = _build(2, [_row(gameweek=1, value=50)])
    gw3 = _build(
        3,
        [_row(gameweek=2, element=2, team="Gamma", position="DEF", value=45)],
        previous_state=gw2,
        fixtures=[
            {
                "id": 103,
                "event": 3,
                "kickoff_time": "2025-08-13T14:00:00Z",
                "team_h": 2,
                "team_a": 3,
                "team_h_difficulty": 3,
                "team_a_difficulty": 3,
                "provisional_start_time": False,
            }
        ],
    )
    player = _player(gw3)
    assert player["quote"] == {
        "now_cost": 5.0,
        "source_gameweek": 1,
        "age_gameweeks": 2,
        "price_confidence": "historical_post_gameweek_export",
    }
    assert player["projection"]["fixture_count"] == 0
    assert player["projection"]["expected_points"] == 0.0
    assert "market_quote_carried_forward" in player["limitations"]


def test_price_and_model_lineage_are_explicit_and_hashes_reproduce() -> None:
    first = _build(2, [_row(gameweek=1, value=53)])
    second = _build(2, list(reversed([_row(gameweek=1, value=53)])))
    assert first == second
    assert first["content_sha256"] == feature_state_hash(first)
    assert _player(first)["quote"]["source_gameweek"] == 1
    assert len(first["lineage"]["history_chain_sha256"]) == 64
    assert len(first["lineage"]["model_sha256"]) == 64
    schema = json.loads(
        (
            ROOT / "control" / "schemas" / "benchmark" / "feature-state.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(first)


@pytest.mark.parametrize("forbidden", ["xP", "ep_next", "player_outcomes"])
def test_hidden_or_same_gameweek_fields_fail_closed(forbidden: str) -> None:
    row = _row(gameweek=1)
    row[forbidden] = 99
    with pytest.raises(HistoricalFeatureStateError, match="forbidden"):
        _build(2, [row])


def test_non_prior_gameweek_rows_fail_closed() -> None:
    with pytest.raises(HistoricalFeatureStateError, match="exact prior Gameweek"):
        _build(3, [_row(gameweek=1)])


def test_state_must_advance_chronologically() -> None:
    gw2 = _build(2, [_row(gameweek=1)])
    with pytest.raises(HistoricalFeatureStateError, match="advance exactly one Gameweek"):
        _build(4, [_row(gameweek=3)], previous_state=gw2)


def test_solver_input_retains_owned_purchase_price_and_complete_known_market() -> None:
    state = _build(
        2,
        [
            _row(gameweek=1, element=1, value=50),
            _row(gameweek=1, element=2, team="Gamma", position="DEF", value=45),
        ],
    )
    policy = {
        "season": "2025-26",
        "gameweek": 2,
        "ruleset_id": "2025-26-v1.0",
        "bank": 1.0,
        "free_transfers": 1,
        "chips_available": ["wildcard_fh"],
        "squad": [
            {
                "player_id": "player:2025-26:1",
                "position": "MID",
                "club_id": "team:2025-26:1",
                "purchase_price": 4.8,
                "current_price": 5.0,
                "selling_price": 4.9,
            }
        ],
    }
    solver_input = build_replay_solver_input(
        feature_state=state,
        policy_state=policy,
        max_transfers=2,
    )
    assert len(solver_input.players) == 2
    owned = next(
        row
        for row in solver_input.players
        if row["player_id"] == "player:2025-26:1"
    )
    assert owned["purchase_price"] == 4.8
    assert solver_input.squad_player_ids == ["player:2025-26:1"]
    assert solver_input.max_transfers == 2


def test_solver_input_rejects_owned_player_absent_from_known_market() -> None:
    state = _build(2, [_row(gameweek=1)])
    policy = {
        "season": "2025-26",
        "gameweek": 2,
        "ruleset_id": "2025-26-v1.0",
        "bank": 0.0,
        "free_transfers": 1,
        "chips_available": [],
        "squad": [
            {
                "player_id": "player:2025-26:999",
                "position": "MID",
                "club_id": "team:2025-26:1",
                "purchase_price": 5.0,
                "current_price": 5.0,
                "selling_price": 5.0,
            }
        ],
    }
    with pytest.raises(ReplayAdapterError, match="missing owned player"):
        build_replay_solver_input(feature_state=state, policy_state=policy)


def test_inputs_are_not_mutated() -> None:
    manifest, observed, identity = _inputs(2, [_row(gameweek=1)])
    originals = deepcopy((manifest, observed, identity))
    build_feature_state(
        episode_manifest=manifest,
        observed=observed,
        identity_map=identity,
    )
    assert (manifest, observed, identity) == originals
