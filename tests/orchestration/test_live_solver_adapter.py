"""Offline contracts for the live manager-state → SolverInput adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import load_solver_input
from src.optimisation.solver import solve
from src.orchestration.live_solver_adapter import (
    LiveSolverAdapterError,
    adapt_solve_and_record,
    build_live_decision_record,
    build_live_solver_input,
)
from src.reporting.decision_record import validate_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "evals" / "golden-cases" / "optimiser-gw3-input.json"
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _manager_state_from_golden() -> dict:
    golden = load_solver_input(GOLDEN).as_dict()
    squad = []
    for player in golden["players"]:
        if player["player_id"] not in golden["squad_player_ids"]:
            continue
        purchase = float(player.get("purchase_price", player["now_cost"]))
        current = float(player["now_cost"])
        squad.append(
            {
                "player_id": str(player["player_id"]),
                "fpl_code": int(player["player_id"]),
                "web_name": player["web_name"],
                "position": player["position"],
                "club_id": str(player["club_id"]),
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": selling_price(purchase, current, dict(RULES)),
            }
        )
    return {
        "manager_state_version": "1.0",
        "manager_state_id": "manager-state:fixture:gw03:lab",
        "manager_id": "lab-manager",
        "season": golden["season"],
        "gameweek": golden["gameweek"],
        "observed_at": "2026-08-21T10:00:00Z",
        "available_at": "2026-08-21T10:00:00Z",
        "cutoff": "2026-08-21T16:00:00Z",
        "deadline": "2026-08-21T17:30:00Z",
        "ruleset_id": golden["ruleset_id"],
        "ruleset_sha256": RULES_HASH,
        "bank": golden["bank"],
        "free_transfers": golden["free_transfers"],
        "chips_available": list(golden["chips_available"]),
        "chip_history": [],
        "squad": squad,
        "content_sha256": "a" * 64,
    }


def _forecast_from_golden() -> dict:
    golden = load_solver_input(GOLDEN).as_dict()
    return {
        "season": golden["season"],
        "gameweek": golden["gameweek"],
        "model_version": "fixture-forecast-v0",
        "players": [
            {
                "player_id": str(player["player_id"]),
                "web_name": player["web_name"],
                "position": player["position"],
                "club_id": str(player["club_id"]),
                "now_cost": float(player["now_cost"]),
                "expected_points": float(player["expected_points"]),
                "status": player.get("status", "a"),
            }
            for player in golden["players"]
        ],
    }


def test_adapter_round_trips_to_solver_input_with_selling_prices() -> None:
    state = _manager_state_from_golden()
    forecast = _forecast_from_golden()
    solver_input = build_live_solver_input(manager_state=state, forecast=forecast)

    assert solver_input.season == "2026-27"
    assert solver_input.gameweek == 3
    assert solver_input.bank == 0.5
    assert solver_input.free_transfers == 1
    assert solver_input.squad_player_ids == [str(i) for i in range(1, 16)]
    owned = {
        player["player_id"]: player
        for player in solver_input.players
        if player["player_id"] in solver_input.squad_player_ids
    }
    assert len(owned) == 15
    for player_id, player in owned.items():
        expected = next(
            row for row in state["squad"] if row["player_id"] == player_id
        )
        assert player["purchase_price"] == expected["purchase_price"]
        assert player["selling_price"] == expected["selling_price"]
        assert player["now_cost"] == expected["current_price"]


def test_adapter_plans_validate_against_2026_27_ruleset() -> None:
    state = _manager_state_from_golden()
    forecast = _forecast_from_golden()
    solver_input = build_live_solver_input(manager_state=state, forecast=forecast)
    output = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)

    assert output["selected"] is not None
    assert output["plans"]["no_transfer"] is not None
    assert output["plans"]["no_transfer"]["validation"]["squad_ok"]
    assert output["plans"]["no_transfer"]["validation"]["lineup_ok"]
    assert output["selected"]["validation"]["squad_ok"]
    assert output["selected"]["validation"]["lineup_ok"]


def test_adapter_feeds_decision_record_without_manual_surgery() -> None:
    state = _manager_state_from_golden()
    forecast = _forecast_from_golden()
    bundle = adapt_solve_and_record(
        manager_state=state,
        forecast=forecast,
        rules_path=RULES_PATH,
        validate_record=True,
    )
    record = bundle["decision_record"]
    validate_decision_record(record)
    assert record["manager_state"]["bank"] == 0.5
    assert record["validation"]["squad"]["ok"] is True
    assert record["validation"]["lineup"]["ok"] is True
    assert record["recommendation"]["validated_plan_sha256"] == (
        record["validated_plan"]["content_sha256"]
    )


def test_forecast_price_mismatch_fails_closed() -> None:
    state = _manager_state_from_golden()
    forecast = _forecast_from_golden()
    forecast["players"][0]["now_cost"] = 9.9
    with pytest.raises(LiveSolverAdapterError, match="current price"):
        build_live_solver_input(manager_state=state, forecast=forecast)


def test_build_decision_record_helper_matches_selected_plan() -> None:
    state = _manager_state_from_golden()
    forecast = _forecast_from_golden()
    solver_input = build_live_solver_input(manager_state=state, forecast=forecast)
    output = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)
    record = build_live_decision_record(
        manager_state=state,
        solver_input=solver_input,
        solver_output=output,
        rules=RULES,
        ruleset_sha256_value=RULES_HASH,
        validate=True,
    )
    assert record["gameweek"] == 3
    assert record["validated_plan"]["gameweek"] == 3
