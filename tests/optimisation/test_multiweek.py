"""Bounded receding-horizon planning and state transitions."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.optimisation.multiweek import (
    MultiweekPlanningError,
    multiweek_plan_hash,
    plan_multiweek,
)
from src.optimisation.trajectory import (
    advance_trajectory_state,
    initial_trajectory_state,
)
from src.optimisation.types import SolverInput
from src.orchestration.multiweek_challenger import (
    MultiweekChallengerError,
    build_same_cutoff_horizon,
    multiweek_report_hash,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != "content_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _players(gameweek: int) -> list[dict]:
    counts = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    players: list[dict] = []
    number = 1
    for position, count in counts.items():
        for offset in range(count):
            players.append(
                {
                    "player_id": str(number),
                    "position": position,
                    "club_id": f"team:2025-26:{number}",
                    "now_cost": 5.0,
                    "purchase_price": 5.0,
                    "expected_points": 2.0 + offset,
                    "status": "a",
                }
            )
            number += 1
    # One affordable challenger per position; their value rotates by week.
    for position in counts:
        players.append(
            {
                "player_id": str(number),
                "position": position,
                "club_id": f"team:2025-26:{number}",
                "now_cost": 5.0,
                "purchase_price": None,
                "expected_points": 7.0 + (gameweek % 2),
                "status": "a",
            }
        )
        number += 1
    return players


def _input(gameweek: int = 10) -> SolverInput:
    return SolverInput(
        season="2025-26",
        gameweek=gameweek,
        ruleset_id=RULES["meta"]["ruleset_id"],
        bank=0.0,
        free_transfers=1,
        squad_player_ids=[str(value) for value in range(1, 16)],
        players=_players(gameweek),
        max_transfers=2,
    )


def _horizon(gameweek: int = 10, length: int = 3) -> list[dict]:
    return [
        {
            "gameweek": gameweek + offset,
            "cutoff": "2025-10-01T10:00:00Z",
            "feature_state_sha256": "a" * 64,
            "players": _players(gameweek + offset),
        }
        for offset in range(length)
    ]


def _config(**overrides) -> dict:
    value = {
        "policy_version": "test",
        "horizon_gameweeks": 3,
        "discount_factor": 0.9,
        "beam_width": 3,
        "branch_width": 3,
        "max_expanded_nodes": 20,
        "max_transfers_per_week": 1,
        "sell_pool_per_pos": 2,
        "buy_pool_per_pos": 2,
        "allow_hits": False,
    }
    value.update(overrides)
    value["content_sha256"] = _hash(value)
    return value


def test_horizon_rejects_leakage_nonconsecutive_and_wrong_length() -> None:
    base = _input()
    leaked = _horizon()
    leaked[1]["cutoff"] = "2025-10-08T10:00:00Z"
    with pytest.raises(MultiweekPlanningError, match="share one cutoff"):
        plan_multiweek(
            base, leaked, config=_config(), rules=RULES, ruleset_sha256=RULES_HASH
        )
    nonconsecutive = _horizon()
    nonconsecutive[1]["gameweek"] = 15
    with pytest.raises(MultiweekPlanningError, match="consecutive"):
        plan_multiweek(
            base,
            nonconsecutive,
            config=_config(),
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )
    with pytest.raises(MultiweekPlanningError, match="three to six"):
        plan_multiweek(
            base,
            _horizon(length=2),
            config=_config(horizon_gameweeks=2),
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )


def test_planner_is_deterministic_decomposes_value_and_exposes_only_first_action() -> None:
    first = plan_multiweek(
        _input(), _horizon(), config=_config(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    second = plan_multiweek(
        _input(), _horizon(), config=_config(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    # Runtime is observational; all decisions and hashes are deterministic.
    first["search"].pop("elapsed_seconds")
    second["search"].pop("elapsed_seconds")
    first.pop("content_sha256")
    second.pop("content_sha256")
    assert first == second
    assert first["status"] == "complete"
    assert first["selected"] == first["executable_action"]
    assert all(not item["executable"] for item in first["advisory_trajectory"])
    assert first["value"]["immediate"] + first["value"]["future"] == pytest.approx(
        first["value"]["total"]
    )


def test_state_carries_purchase_prices_bank_free_transfers_and_gw16_topup() -> None:
    base = _input(gameweek=15)
    state = initial_trajectory_state(base, rules=RULES)
    candidate = {
        "transfers": [],
        "hit_cost": 0,
        "bank_after": 0.0,
    }
    next_state = advance_trajectory_state(
        state,
        candidate,
        current_players=_players(15),
        next_players=_players(16),
        rules=RULES,
    )
    assert next_state["gameweek"] == 16
    assert next_state["free_transfers"] == 5
    assert next_state["bank"] == 0.0
    assert {row["purchase_price"] for row in next_state["squad"]} == {5.0}


def test_node_budget_uses_declared_deterministic_one_week_fallback() -> None:
    result = plan_multiweek(
        _input(),
        _horizon(),
        config=_config(max_expanded_nodes=1),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    assert result["status"] == "deterministic_fallback"
    assert result["fallback_reason"] == "expanded_node_budget_exhausted"
    assert result["advisory_trajectory"] == []
    assert result["selected"] == result["executable_action"]
    assert result["content_sha256"] == multiweek_plan_hash(result)


def test_replanning_does_not_execute_or_bind_the_previous_tail() -> None:
    original = plan_multiweek(
        _input(), _horizon(), config=_config(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    replanned_horizon = _horizon(gameweek=11)
    for row in replanned_horizon[0]["players"]:
        row["expected_points"] = 1.0
    replanned = plan_multiweek(
        _input(gameweek=11),
        replanned_horizon,
        config=_config(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    assert replanned["lineage"]["horizon_fingerprint"] != original["lineage"][
        "horizon_fingerprint"
    ]
    assert all(item["gameweek"] >= 12 for item in replanned["advisory_trajectory"])


def test_historical_horizon_uses_frozen_rates_and_rejects_outcome_fields() -> None:
    base = _input().as_dict()
    forecast = {
        "season": "2025-26",
        "gameweek": 10,
        "cutoff": "2025-10-01T10:00:00Z",
        "players": [
            {
                "player_id": row["player_id"],
                "expected_minutes": 90.0,
                "fixture_count": 1,
                "posterior_points_per_90": 4.0,
            }
            for row in base["players"]
        ],
    }
    forecast["content_sha256"] = _hash(forecast)
    fixtures = [
        {
            "event": 10,
            "id": 100,
            "kickoff_time": "2025-10-02T19:00:00Z",
            "provisional_start_time": False,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
        }
    ]
    config = {
        "fixture_projection": {
            "difficulty_multiplier": {
                "1": 1.2,
                "2": 1.1,
                "3": 1.0,
                "4": 0.9,
                "5": 0.8,
            }
        }
    }
    horizon = build_same_cutoff_horizon(
        base_input=base,
        locked_forecast=forecast,
        fixture_weeks=[
            {
                "gameweek": 10,
                "fixtures": fixtures,
                "schedule_provenance": {"source": "test"},
            },
            {
                "gameweek": 11,
                "fixtures": fixtures,
                "schedule_provenance": {"source": "test"},
            },
        ],
        feature_state_sha256="a" * 64,
        config=config,
    )
    assert horizon[0]["players"][0]["expected_points"] == 2.0
    assert horizon[1]["players"][0]["expected_points"] == 4.4
    assert horizon[1]["players"][1]["expected_points"] == 3.6
    leaked = deepcopy(fixtures)
    leaked[0]["team_h_score"] = 3
    with pytest.raises(MultiweekChallengerError, match="outcome-capable"):
        build_same_cutoff_horizon(
            base_input=base,
            locked_forecast=forecast,
            fixture_weeks=[
                {
                    "gameweek": 10,
                    "fixtures": leaked,
                    "schedule_provenance": {"source": "test"},
                }
            ],
            feature_state_sha256="a" * 64,
            config=config,
        )


def test_sealed_gw12_challenger_is_hash_bound_and_first_action_only() -> None:
    path = (
        ROOT
        / "reports/benchmarks/2025-26-multiweek/gw-12/comparison.json"
    )
    if not path.exists():
        pytest.skip("sealed GW12 multiweek challenger is not installed")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["content_sha256"] == multiweek_report_hash(report)
    assert report["plan"]["content_sha256"] == multiweek_plan_hash(report["plan"])
    assert report["first_action_evaluation"]["net_points_delta"] == 18
    assert report["first_action_evaluation"]["tail_executed"] is False
    assert report["promotion_eligible"] is False
