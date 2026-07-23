"""Cross-season longitudinal contracts prevent small rule drift from compounding."""

from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest

from src.orchestration.policy_state import (
    POLICY_ARMS,
    _next_free_transfers,
    initialise_policy_states,
    transition_policy_state,
)
from src.scoring.rules_loader import (
    RulesetActivationError,
    assert_ruleset_activatable,
    get_rule,
    load_rules,
    ruleset_sha256,
)


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = ROOT / "control/rules/2025-26.yaml"
LIVE_PATH = ROOT / "control/rules/2026-27.yaml"
BASE = runpy.run_path(str(ROOT / "tests/unit/test_policy_state.py"))


def _canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _confirmed_live_rules() -> dict:
    rules = load_rules(LIVE_PATH)
    for rows in rules.values():
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("status") == "inherited":
                    row["status"] = "confirmed"
    boundary = get_rule(rules, "chips.gw1_and_boundary_restrictions")
    boundary["rule_id"] = "chips.boundary_restrictions"
    boundary["status"] = "confirmed"
    boundary["value"] = {
        "wildcard_unavailable_gameweeks": [1],
        "free_hit_unavailable_gameweeks": [1],
        "free_hit_cannot_span_adjacent_gameweeks": [19, 20],
    }
    return rules


def _initial_for(rules: dict) -> tuple[dict, str]:
    seed = deepcopy(BASE["_seed"]())
    seed["season"] = rules["meta"]["season"]
    digest = _canonical_hash(rules)
    states = initialise_policy_states(
        seed,
        policy_arms=POLICY_ARMS,
        rules=rules,
        ruleset_sha256=digest,
    )
    return states["forecast_optimizer"], digest


def _transition_for(
    state: dict,
    rules: dict,
    digest: str,
    *,
    transfers: list[dict[str, str]] | None = None,
    chip: str | None = None,
    decision_market: dict | None = None,
    next_market: dict | None = None,
    salt: str = "cross-season",
) -> tuple[dict, dict]:
    return transition_policy_state(
        state,
        BASE["_decision"](
            state,
            transfers=transfers,
            chip=chip,
            salt=salt,
            decision_market=decision_market or BASE["_market"](),
            rules=rules,
            rules_hash=digest,
        ),
        BASE["_outcome"](state),
        decision_market=decision_market or BASE["_market"](),
        next_market=next_market or BASE["_market"](),
        rules=rules,
        ruleset_sha256=digest,
    )


def test_refactor_preserves_exact_historical_state_and_transition_hashes():
    state = BASE["_initial"]()["forecast_optimizer"]
    assert state["content_sha256"] == (
        "437dacf98473a42a5743ab4398966877938d40626625c63cc4a8d7a8d6ef6780"
    )
    state, first = BASE["_transition"](
        state,
        transfers=[{"player_out_id": "7", "player_in_id": "19"}],
        next_market=BASE["_market"](decision_later=True),
        salt="open-gw2-with-used-transfer",
    )
    assert state["content_sha256"] == (
        "1a681a55b40c065c9144169c6838cc6e7fcede22e9965eddb0cb80b267078ac0"
    )
    assert first["content_sha256"] == (
        "79a1bf22194cb8a7df9b2a1824f5b5f0291bff097970f688a5d69581acb95924"
    )
    state, second = BASE["_transition"](
        state,
        transfers=[
            {"player_out_id": "3", "player_in_id": "16"},
            {"player_out_id": "8", "player_in_id": "17"},
        ],
        decision_market=BASE["_market"](decision_later=True),
        next_market=BASE["_market"](next_week=True),
    )
    assert state["content_sha256"] == (
        "53c7c4b23d5d6e935ab4037f4205836466e66851e7aca625bf44094e64a41249"
    )
    assert second["content_sha256"] == (
        "a6d00fcb16d683c4892ee415bc6e274e4a6cb229ad3702979e1744a3816a6214"
    )


def test_current_live_catalogue_is_rejected_before_initial_state_creation():
    rules = load_rules(LIVE_PATH)
    seed = deepcopy(BASE["_seed"]())
    seed["season"] = "2026-27"
    with pytest.raises(RulesetActivationError, match="not activatable"):
        initialise_policy_states(
            seed,
            policy_arms=POLICY_ARMS,
            rules=rules,
            ruleset_sha256=ruleset_sha256(LIVE_PATH),
        )


def test_full_transfer_recurrence_matrix_and_unlimited_chip_retention():
    historical = assert_ruleset_activatable(
        load_rules(HISTORICAL_PATH),
        ruleset_sha256(HISTORICAL_PATH),
        mode="historical_replay",
    )["transition_profile"]
    live_rules = _confirmed_live_rules()
    live = assert_ruleset_activatable(
        live_rules, _canonical_hash(live_rules), mode="live"
    )["transition_profile"]

    for profile in (historical, live):
        for available in range(0, 6):
            for used in range(0, 7):
                expected = min(5, max(0, available - used) + 1)
                assert _next_free_transfers(
                    available=available,
                    used=used,
                    chip_base=None,
                    next_gameweek=2,
                    profile=profile,
                ) == expected
                for chip in ("wildcard", "free_hit"):
                    assert _next_free_transfers(
                        available=available,
                        used=used,
                        chip_base=chip,
                        next_gameweek=2,
                        profile=profile,
                    ) == available


def test_afcon_event_is_historical_only_without_type_or_season_conditionals():
    historical = assert_ruleset_activatable(
        load_rules(HISTORICAL_PATH),
        ruleset_sha256(HISTORICAL_PATH),
        mode="historical_replay",
    )["transition_profile"]
    live_rules = _confirmed_live_rules()
    live = assert_ruleset_activatable(
        live_rules, _canonical_hash(live_rules), mode="live"
    )["transition_profile"]

    assert _next_free_transfers(
        available=5,
        used=2,
        chip_base=None,
        next_gameweek=16,
        profile=historical,
    ) == 5
    assert _next_free_transfers(
        available=5,
        used=2,
        chip_base=None,
        next_gameweek=16,
        profile=live,
    ) == 4


def test_confirmed_live_free_hit_restores_permanent_state_and_transfer_count():
    rules = _confirmed_live_rules()
    state, digest = _initial_for(rules)
    state, _ = _transition_for(
        state,
        rules,
        digest,
        next_market=BASE["_market"](decision_later=True),
        salt="open-live-gw2",
    )
    successor, transition = _transition_for(
        state,
        rules,
        digest,
        transfers=[{"player_out_id": "3", "player_in_id": "16"}],
        chip="free_hit_fh",
        decision_market=BASE["_market"](decision_later=True),
        next_market=BASE["_market"](next_week=True),
        salt="live-free-hit",
    )

    assert {row["player_id"] for row in successor["squad"]} == {
        row["player_id"] for row in state["squad"]
    }
    assert successor["bank"] == state["bank"]
    assert successor["free_transfers"] == state["free_transfers"] == 2
    assert transition["temporary_squad_sha256"]


def test_chip_expiry_and_terminal_state_follow_compiled_rule_values():
    rules = _confirmed_live_rules()
    get_rule(rules, "chips.first_half_expiry")["value"]["expires_at_gameweek"] = 18
    get_rule(rules, "chips.boundary_restrictions")["value"][
        "free_hit_cannot_span_adjacent_gameweeks"
    ] = [18, 19]
    digest = _canonical_hash(rules)
    profile = assert_ruleset_activatable(rules, digest, mode="live")[
        "transition_profile"
    ]
    assert profile["regular_gameweeks"] == 36
    assert profile["terminal_state_gameweek"] == 37

    state, _ = _initial_for(rules)
    for gameweek in range(1, 19):
        state, _ = _transition_for(state, rules, digest, salt=f"expiry-{gameweek}")
    assert state["gameweek"] == 19
    assert all(not chip.endswith("_fh") for chip in state["chips_available"])

    for gameweek in range(19, 37):
        state, _ = _transition_for(state, rules, digest, salt=f"terminal-{gameweek}")
    assert state["gameweek"] == 37
    assert state["status"] == "season_complete"


def test_initial_chip_inventory_is_derived_from_rules():
    rules = _confirmed_live_rules()
    sets = get_rule(rules, "chips.sets_per_season")["value"]
    sets["chips_per_set"] = ["wildcard", "free_hit", "triple_captain"]
    seed = deepcopy(BASE["_seed"]())
    seed["season"] = "2026-27"
    seed["chips_available"] = [
        "wildcard_fh",
        "free_hit_fh",
        "triple_captain_fh",
        "wildcard_sh",
        "free_hit_sh",
        "triple_captain_sh",
    ]
    digest = _canonical_hash(rules)

    states = initialise_policy_states(
        seed,
        policy_arms=POLICY_ARMS,
        rules=rules,
        ruleset_sha256=digest,
    )
    assert states["forecast_optimizer"]["chips_available"] == seed["chips_available"]
