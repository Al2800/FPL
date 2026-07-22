"""Longitudinal benchmark policy-state contracts and deterministic transitions."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.orchestration.policy_state import (
    POLICY_ARMS,
    PolicyStateError,
    PolicyStateLedger,
    initialise_policy_states,
    state_hash,
    transition_hash,
    transition_policy_state,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
STATE_SCHEMA = ROOT / "control/schemas/benchmark/policy-state.json"
TRANSITION_SCHEMA = ROOT / "control/schemas/benchmark/state-transition.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _players() -> list[dict[str, object]]:
    spec = (
        [(i, "GKP", 4.5) for i in (1, 2)]
        + [(i, "DEF", 4.5) for i in range(3, 8)]
        + [(i, "MID", 7.0) for i in range(8, 13)]
        + [(i, "FWD", 11.0) for i in range(13, 16)]
    )
    rows = []
    for player_id, position, purchase in spec:
        current = purchase
        rows.append(
            {
                "player_id": str(player_id),
                "position": position,
                "club_id": str(player_id),
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": selling_price(purchase, current, RULES),
            }
        )
    return rows


def _seed() -> dict[str, object]:
    return {
        "seed_id": "benchmark-v0-controlled-gw1",
        "season": "2025-26",
        "gameweek": 1,
        "bank": 0.5,
        "free_transfers": 1,
        "chips_available": [
            "wildcard_fh",
            "free_hit_fh",
            "triple_captain_fh",
            "bench_boost_fh",
            "wildcard_sh",
            "free_hit_sh",
            "triple_captain_sh",
            "bench_boost_sh",
        ],
        "squad": _players(),
    }


def _market(*, next_week: bool = False, decision_later: bool = False) -> dict[str, dict[str, object]]:
    rows = {player["player_id"]: dict(player) for player in _players()}
    for row in rows.values():
        row["now_cost"] = row.pop("current_price")
        row.pop("purchase_price")
        row.pop("selling_price")
    if next_week or decision_later:
        rows["3"]["now_cost"] = 5.0
        rows["8"]["now_cost"] = 7.5
    rows["16"] = {
        "player_id": "16",
        "position": "DEF",
        "club_id": "16",
        "now_cost": 5.2 if next_week else 4.8,
    }
    rows["17"] = {
        "player_id": "17",
        "position": "MID",
        "club_id": "17",
        "now_cost": 7.7 if next_week else 7.3,
    }
    rows["18"] = {
        "player_id": "18",
        "position": "FWD",
        "club_id": "18",
        "now_cost": 20.0,
    }
    rows["19"] = {
        "player_id": "19",
        "position": "DEF",
        "club_id": "19",
        "now_cost": 4.5,
    }
    if next_week:
        rows["4"]["now_cost"] = 5.5
    return rows


def _initial() -> dict[str, dict]:
    return initialise_policy_states(
        _seed(),
        policy_arms=POLICY_ARMS,
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def _decision(
    state: dict,
    *,
    transfers: list[dict[str, str]] | None = None,
    chip: str | None = None,
    salt: str = "a",
) -> dict[str, object]:
    gameweek = state["gameweek"]
    day = datetime(2025, 8, 1, tzinfo=timezone.utc) + timedelta(days=gameweek)
    return {
        "episode_id": f"benchmark-v0:2025-26:gw{gameweek:02d}:manager-neutral",
        "policy_arm": state["policy_arm"],
        "gameweek": gameweek,
        "previous_state_sha256": state["content_sha256"],
        "proposal_sha256": hashlib.sha256(f"{salt}:{gameweek}".encode()).hexdigest(),
        "frozen_at": day.isoformat().replace("+00:00", "Z"),
        "transfers": transfers or [],
        "active_chip": chip,
    }


def _outcome(state: dict, *, gross_points: int = 60) -> dict[str, object]:
    day = datetime(2025, 8, 1, tzinfo=timezone.utc) + timedelta(
        days=state["gameweek"], hours=4
    )
    return {
        "outcome_id": f"hidden:gw{state['gameweek']:02d}",
        "revealed_at": day.isoformat().replace("+00:00", "Z"),
        "gross_points": gross_points,
    }


def _transition(
    state: dict,
    *,
    transfers: list[dict[str, str]] | None = None,
    chip: str | None = None,
    decision_market: dict | None = None,
    next_market: dict | None = None,
    salt: str = "a",
    gross_points: int = 60,
) -> tuple[dict, dict]:
    return transition_policy_state(
        state,
        _decision(state, transfers=transfers, chip=chip, salt=salt),
        _outcome(state, gross_points=gross_points),
        decision_market=decision_market or _market(),
        next_market=next_market or _market(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def _schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_initial_states_are_schema_valid_shared_seed_but_arm_isolated():
    states = _initial()
    assert set(states) == set(POLICY_ARMS)
    assert len({state["origin"]["seed_sha256"] for state in states.values()}) == 1
    assert len({state["content_sha256"] for state in states.values()}) == len(POLICY_ARMS)

    validator = Draft202012Validator(_schema(STATE_SCHEMA), format_checker=FormatChecker())
    for arm, state in states.items():
        validator.validate(state)
        assert state["policy_arm"] == arm
        assert state_hash(state) == state["content_sha256"]

    states["naive_baseline"]["squad"][0]["purchase_price"] = 99.0
    assert states["forecast_optimizer"]["squad"][0]["purchase_price"] == 4.5


@pytest.mark.parametrize(
    ("mutation", "message"),
    [("price_history", "seed prices"), ("budget", "initial budget")],
)
def test_initial_state_rejects_inconsistent_seed_finances(mutation: str, message: str):
    seed = deepcopy(_seed())
    if mutation == "price_history":
        seed["squad"][0]["current_price"] = 4.6
        seed["squad"][0]["selling_price"] = 4.5
    else:
        seed["bank"] = 0.4

    with pytest.raises(PolicyStateError, match=message):
        initialise_policy_states(
            seed, policy_arms=POLICY_ARMS, rules=RULES, ruleset_sha256=RULES_HASH
        )


def test_ordinary_transfer_uses_purchase_history_hits_and_correct_next_free_transfer():
    state, _ = _transition(
        _initial()["forecast_optimizer"],
        transfers=[{"player_out_id": "7", "player_in_id": "19"}],
        next_market=_market(decision_later=True),
        salt="open-gw2-with-used-transfer",
    )
    assert state["free_transfers"] == 1
    moves = [
        {"player_out_id": "3", "player_in_id": "16"},
        {"player_out_id": "8", "player_in_id": "17"},
    ]
    next_state, transition = _transition(
        state,
        transfers=moves,
        decision_market=_market(decision_later=True),
        next_market=_market(next_week=True),
    )

    assert next_state["bank"] == 0.3
    assert next_state["free_transfers"] == 1
    assert transition["hit_cost"] == 4
    assert transition["gross_points"] == 60
    assert transition["net_points"] == 56
    assert next_state["cumulative_points"] == 116
    by_id = {player["player_id"]: player for player in next_state["squad"]}
    assert by_id["16"]["purchase_price"] == 4.8
    assert by_id["16"]["current_price"] == 5.2
    assert by_id["16"]["selling_price"] == 5.0
    assert by_id["4"]["purchase_price"] == 4.5
    assert by_id["4"]["selling_price"] == 5.0
    assert transition["moves"][0]["selling_price"] == 4.7
    assert transition["moves"][1]["selling_price"] == 7.2

    Draft202012Validator(
        _schema(TRANSITION_SCHEMA), format_checker=FormatChecker()
    ).validate(transition)
    assert transition_hash(transition) == transition["content_sha256"]
    assert next_state["previous_state_sha256"] == state["content_sha256"]
    assert transition["next_state_sha256"] == next_state["content_sha256"]


def test_no_transfer_banks_to_cap_and_gw16_exception_tops_up():
    state = _initial()["naive_baseline"]
    assert _transition(state)[0]["free_transfers"] == 2

    for gameweek in range(1, 16):
        assert state["gameweek"] == gameweek
        state, _ = _transition(state, salt=f"noop-{gameweek}")
    assert state["gameweek"] == 16
    assert state["free_transfers"] == 5


def test_wildcard_persists_squad_without_hit_and_keeps_exact_banked_transfers():
    state = _transition(
        _initial()["evidence_agent"],
        next_market=_market(decision_later=True),
        salt="open-gw2",
    )[0]
    assert state["free_transfers"] == 2
    next_state, transition = _transition(
        state,
        transfers=[{"player_out_id": "3", "player_in_id": "16"}],
        chip="wildcard_fh",
        next_market=_market(next_week=True),
        decision_market=_market(decision_later=True),
        salt="wildcard",
    )
    assert "16" in {player["player_id"] for player in next_state["squad"]}
    assert next_state["bank"] == 0.4
    assert next_state["free_transfers"] == 2
    assert transition["hit_cost"] == 0
    assert "wildcard_fh" not in next_state["chips_available"]
    assert next_state["chip_history"][-1] == {"chip": "wildcard_fh", "gameweek": 2}


def test_free_hit_validates_temporary_team_then_restores_permanent_finances():
    state = _transition(
        _initial()["evidence_challenger"],
        next_market=_market(decision_later=True),
        salt="open-gw2",
    )[0]
    next_state, transition = _transition(
        state,
        transfers=[{"player_out_id": "3", "player_in_id": "16"}],
        chip="free_hit_fh",
        next_market=_market(next_week=True),
        salt="free-hit",
        decision_market=_market(decision_later=True),
    )
    assert {p["player_id"] for p in next_state["squad"]} == {
        p["player_id"] for p in state["squad"]
    }
    assert next_state["bank"] == state["bank"]
    assert next_state["free_transfers"] == state["free_transfers"] == 2
    assert transition["hit_cost"] == 0
    assert transition["temporary_squad_sha256"]
    restored = {p["player_id"]: p for p in next_state["squad"]}
    assert restored["3"]["purchase_price"] == 4.5
    assert "free_hit_fh" not in next_state["chips_available"]


def test_unused_first_half_chips_expire_before_gameweek_20():
    state = _initial()["human_decision"]
    for gameweek in range(1, 20):
        state, _ = _transition(state, salt=f"to20-{gameweek}")
    assert state["gameweek"] == 20
    assert all(not chip.endswith("_fh") for chip in state["chips_available"])
    assert {chip for chip in state["chips_available"]} == {
        "wildcard_sh",
        "free_hit_sh",
        "triple_captain_sh",
        "bench_boost_sh",
    }


def test_free_hit_cannot_be_played_in_adjacent_gameweeks_19_and_20():
    state = _initial()["human_decision"]
    for gameweek in range(1, 19):
        state, _ = _transition(state, salt=f"to19-{gameweek}")
    assert state["gameweek"] == 19

    state, _ = _transition(state, chip="free_hit_fh", salt="fh-gw19")
    assert state["gameweek"] == 20
    assert state["chip_history"][-1] == {"chip": "free_hit_fh", "gameweek": 19}
    with pytest.raises(PolicyStateError, match="both Gameweek 19 and 20"):
        _transition(state, chip="free_hit_sh", salt="fh-gw20")


def test_ledger_keeps_independent_immutable_histories():
    states = _initial()
    ledger = PolicyStateLedger(states)
    arm = "forecast_optimizer"
    next_state, transition = _transition(states[arm])
    ledger.append(transition, next_state)

    assert len(ledger.history(arm)) == 2
    assert len(ledger.history("naive_baseline")) == 1
    borrowed = ledger.current(arm)
    borrowed["bank"] = 99.0
    assert ledger.current(arm)["bank"] != 99.0

    wrong = deepcopy(next_state)
    wrong["policy_arm"] = "naive_baseline"
    with pytest.raises(PolicyStateError, match="policy arm"):
        ledger.append(transition, wrong)
    assert len(ledger.history(arm)) == 2


def test_same_transition_sequence_reproduces_identical_hashes():
    state = _initial()["forecast_optimizer"]
    args = {
        "transfers": [{"player_out_id": "3", "player_in_id": "16"}],
        "next_market": _market(next_week=True),
        "salt": "deterministic",
    }
    first_state, first_transition = _transition(state, **args)
    second_state, second_transition = _transition(state, **args)
    assert first_state == second_state
    assert first_transition == second_transition
    assert first_state["content_sha256"] == second_state["content_sha256"]
    assert first_transition["content_sha256"] == second_transition["content_sha256"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_arm", "policy arm"),
        ("wrong_predecessor", "predecessor"),
        ("early_reveal", "after proposal freeze"),
        ("wrong_position", "same position"),
        ("unaffordable", "insufficient bank"),
        ("missing_chip", "not available"),
    ],
)
def test_invalid_or_impossible_transitions_fail_closed(mutation: str, message: str):
    state = _transition(_initial()["naive_baseline"], salt="open-gw2")[0]
    decision = _decision(
        state,
        transfers=[{"player_out_id": "3", "player_in_id": "16"}],
        salt=f"invalid-{mutation}",
    )
    outcome = _outcome(state)
    market = _market()

    if mutation == "wrong_arm":
        decision["policy_arm"] = "human_decision"
    elif mutation == "wrong_predecessor":
        decision["previous_state_sha256"] = "0" * 64
    elif mutation == "early_reveal":
        outcome["revealed_at"] = decision["frozen_at"]
    elif mutation == "wrong_position":
        market["16"]["position"] = "MID"
    elif mutation == "unaffordable":
        decision["transfers"] = [{"player_out_id": "13", "player_in_id": "18"}]
    elif mutation == "missing_chip":
        decision["active_chip"] = "assistant_manager"

    with pytest.raises(PolicyStateError, match=message):
        transition_policy_state(
            state,
            decision,
            outcome,
            decision_market=market,
            next_market=_market(next_week=True),
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )


def test_terminal_gameweek_39_state_is_season_complete():
    state = _initial()["naive_baseline"]
    for gameweek in range(1, 39):
        state, _ = _transition(state, salt=f"season-{gameweek}")
    assert state["gameweek"] == 39
    assert state["status"] == "season_complete"
    with pytest.raises(PolicyStateError, match="season-complete"):
        _transition(state)
