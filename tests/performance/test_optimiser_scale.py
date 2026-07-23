"""Differential and realistic-width contracts for the streamed optimiser."""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
import pytest

from src.optimisation.simple_plan import (
    choose_starting_xi_reference,
    choose_starting_xi_rows,
)
from src.optimisation.io import fingerprint
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.optimisation.solver import solve
from src.optimisation.transfers import enumerate_transfer_sets, index_players, owned_records
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import legal_formations, validate_lineup, validate_squad


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _scale_input(*, max_transfers: int) -> SolverInput:
    counts = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    players: list[dict[str, object]] = []
    squad_ids: list[str] = []
    player_number = 1
    for position, count in counts.items():
        for offset in range(count):
            player_id = str(player_number)
            squad_ids.append(player_id)
            players.append(
                {
                    "player_id": player_id,
                    "web_name": f"Owned{player_id}",
                    "position": position,
                    "club_id": f"owned-{player_id}",
                    "now_cost": 4.5,
                    "purchase_price": 4.5,
                    "expected_points": float(offset + 1),
                    "status": "a",
                }
            )
            player_number += 1
    for position in counts:
        for offset in range(8):
            player_id = str(player_number)
            players.append(
                {
                    "player_id": player_id,
                    "web_name": f"Buy{player_id}",
                    "position": position,
                    "club_id": f"buy-{player_id}",
                    "now_cost": 4.5,
                    "expected_points": float(20 - offset),
                    "status": "a",
                }
            )
            player_number += 1
    return SolverInput(
        season="2025-26",
        gameweek=2,
        ruleset_id=RULES["meta"]["ruleset_id"],
        bank=32.5,
        free_transfers=1,
        squad_player_ids=squad_ids,
        players=players,
        max_transfers=max_transfers,
        sell_pool_per_pos=5,
        buy_pool_per_pos=8,
    )


def _lineup_identity(lineup: dict) -> dict:
    return {
        "formation": lineup["formation"],
        "starting_xi_ids": [
            str(player["player_id"]) for player in lineup["starting_xi"]
        ],
        "bench_ids": [str(player["player_id"]) for player in lineup["bench"]],
        "captain_id": lineup["captain_id"],
        "vice_captain_id": lineup["vice_captain_id"],
        "expected_xi_points": lineup["expected_xi_points"],
    }


def test_pure_lineup_selector_matches_independent_reference_with_ties() -> None:
    base = _scale_input(max_transfers=1)
    owned = [
        dict(player)
        for player in base.players
        if str(player["player_id"]) in base.squad_player_ids
    ]
    formations = legal_formations(RULES)
    for seed in range(25):
        rows = [dict(player) for player in owned]
        random.Random(seed).shuffle(rows)
        for index, player in enumerate(rows):
            player["expected_points"] = float((index + seed) % 5)
        reference = choose_starting_xi_reference(
            pd.DataFrame(rows), rules=RULES
        )
        pure = choose_starting_xi_rows(rows, formations=formations)
        assert _lineup_identity(pure) == _lineup_identity(reference)


@pytest.mark.parametrize(
    ("n_transfers", "expected"),
    [(1, 120), (2, 5_856), (3, 151_672)],
)
def test_streamed_transfer_pool_has_exact_declared_width(
    n_transfers: int, expected: int
) -> None:
    solver_input = _scale_input(max_transfers=n_transfers)
    market = index_players(solver_input.players)
    owned = owned_records(
        solver_input.squad_player_ids, market, rules=RULES
    )
    iterator = enumerate_transfer_sets(
        owned,
        market,
        n_transfers=n_transfers,
        sell_pool_per_pos=5,
        buy_pool_per_pos=8,
        bank=solver_input.bank,
        availability_policy="available_only",
        rules=RULES,
    )
    assert iter(iterator) is iterator
    assert sum(1 for _ in iterator) == expected


def test_complete_three_transfer_search_is_bounded_and_emits_legal_plans() -> None:
    solver_input = _scale_input(max_transfers=3)
    out = solve(
        solver_input, rules=RULES, ruleset_sha256=RULES_HASH
    )
    assert out["n_candidates"] == 2 + 120 + 5_856 + 151_672
    assert len(out["all_candidates"]) == 50
    assert out["search_scope"]["candidate_generation"] == "lazy"
    assert out["search_scope"]["retained_ranked_candidates"] == 50
    assert out["search_scope"]["full_rebuild_search"] is False
    assert out["search_scope"]["wildcard_free_hit_hit_accounting"] is True

    market = index_players(solver_input.players)
    owned_by_id = {
        player_id: dict(market[player_id])
        for player_id in solver_input.squad_player_ids
    }
    emitted = list(out["all_candidates"])
    emitted.extend(plan for plan in out["plans"].values() if plan is not None)
    for candidate in emitted:
        squad = dict(owned_by_id)
        for transfer in candidate["transfers"]:
            del squad[transfer["player_out_id"]]
            incoming = dict(market[transfer["player_in_id"]])
            incoming["purchase_price"] = incoming["now_cost"]
            squad[transfer["player_in_id"]] = incoming
        squad_rows = list(squad.values())
        assert validate_squad(squad_rows, bank=candidate["bank_after"], rules=RULES).ok
        by_id = {str(player["player_id"]): player for player in squad_rows}
        lineup = candidate["lineup"]
        assert validate_lineup(
            [by_id[player_id] for player_id in lineup["starting_xi_ids"]],
            [by_id[player_id] for player_id in lineup["bench_ids"]],
            captain_id=lineup["captain_id"],
            vice_captain_id=lineup["vice_captain_id"],
            rules=RULES,
        ).ok

    state = {
        "policy_arm": "forecast_optimizer",
        "season": solver_input.season,
        "gameweek": solver_input.gameweek,
        "ruleset_id": solver_input.ruleset_id,
        "ruleset_sha256": RULES_HASH,
        "squad": [
            {
                "player_id": player_id,
                "position": market[player_id]["position"],
                "club_id": market[player_id]["club_id"],
                "purchase_price": market[player_id]["purchase_price"],
                "current_price": market[player_id]["now_cost"],
                "selling_price": market[player_id]["now_cost"],
            }
            for player_id in solver_input.squad_player_ids
        ],
        "bank": solver_input.bank,
        "free_transfers": solver_input.free_transfers,
        "chips_available": [],
    }
    state["content_sha256"] = fingerprint(state)
    plan = validate_and_freeze_plan(
        episode_id="scale:2025-26:gw02",
        policy_arm="forecast_optimizer",
        state=state,
        candidate=out["selected"],
        decision_market=market,
        active_chip=None,
        frozen_at="2025-08-22T17:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    assert plan["content_sha256"]


@pytest.mark.parametrize("chip", ["wildcard_fh", "free_hit_fh"])
def test_unlimited_transfer_chips_do_not_overstate_rebuild_capability(
    chip: str,
) -> None:
    data = _scale_input(max_transfers=2).as_dict()
    data["active_chip"] = chip
    data["chips_available"] = [chip]
    out = solve(
        SolverInput.from_dict(data), rules=RULES, ruleset_sha256=RULES_HASH
    )
    assert all(candidate["hit_cost"] == 0 for candidate in out["all_candidates"])
    assert out["search_scope"]["full_rebuild_search"] is False
    assert out["search_scope"]["optimality"] == "highest_ev_in_declared_candidate_pool"
