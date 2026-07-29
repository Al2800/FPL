"""Contracts for contingency-aware transfer search budgets and equivalence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.transfers import enumerate_transfer_sets, index_players, owned_records
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
CALIBRATION_PATH = ROOT / "control/models/appearance-distribution-v1.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)
CALIBRATION = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
DECLARED = {1: 120, 2: 5_856, 3: 151_672}


def _scale_input(max_transfers: int, *, deadline_ms: int | None = None) -> SolverInput:
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
                    "start_probability": min(0.95, max(0.05, float(offset + 1) / 20.0)),
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
                    "start_probability": min(
                        0.95, max(0.05, float(20 - offset) / 20.0)
                    ),
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
        squad_contingency_policy="probabilistic_v1",
        appearance_calibration=CALIBRATION,
        search_deadline_ms=deadline_ms,
    )


@pytest.mark.parametrize(("width", "expected"), [(1, 120), (2, 5_856), (3, 151_672)])
def test_declared_contingency_widths_match_policy_off_counts(
    width: int, expected: int
) -> None:
    solver_input = _scale_input(width)
    market = index_players(solver_input.players)
    owned = owned_records(solver_input.squad_player_ids, market, rules=RULES)
    count = sum(
        1
        for _ in enumerate_transfer_sets(
            owned,
            market,
            n_transfers=width,
            sell_pool_per_pos=5,
            buy_pool_per_pos=8,
            bank=solver_input.bank,
            availability_policy="available_only",
            rules=RULES,
        )
    )
    assert count == expected == DECLARED[width]


def test_one_transfer_contingency_is_deterministic_and_fingerprint_stable() -> None:
    solver_input = _scale_input(1)
    first = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)
    second = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)
    assert first["output_fingerprint"] == second["output_fingerprint"]
    assert first["n_candidates"] == 122
    assert first["selected"]["objective"] == second["selected"]["objective"]
    assert first["selected"]["lineup"] == second["selected"]["lineup"]
    assert first["search_scope"]["search_degraded"] is False
    assert (
        first["output_fingerprint"]
        == "692ffa8cbc8ff6837ef0e40518a9ec20d1d55e060723c395484914406b4fad66"
    )


def test_deadline_returns_deterministic_degraded_partial_pool() -> None:
    solver_input = _scale_input(2, deadline_ms=250)
    first = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)
    second = solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)
    assert first["search_scope"]["search_degraded"] is True
    assert (
        first["search_scope"]["optimality"]
        == "highest_ev_in_partial_deadline_bounded_pool"
    )
    assert first["output_fingerprint"] == second["output_fingerprint"]
    assert first["n_candidates"] == second["n_candidates"]
    assert first["n_candidates"] < 5978
    # Must not claim full-search equivalence.
    assert "declared_candidate_pool" not in first["search_scope"]["optimality"]


def test_policy_off_scale_fingerprints_remain_unchanged() -> None:
    """Regression lock against the sealed FPL-kcc policy-off report."""

    from scripts.profile_optimiser_scale import scale_input

    for width, expected_fp in (
        (1, "1dd1334ef56a0b95dae89f8cc914fb7a568abd55b4f53236c2b45ff7ddcab90f"),
        (2, "57608507a606870a5e5b9b8b48879496f4fc4351df696688b214f847377d4cd5"),
    ):
        result = solve(scale_input(width), rules=RULES, ruleset_sha256=RULES_HASH)
        assert result["output_fingerprint"] == expected_fp
