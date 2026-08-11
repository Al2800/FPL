"""Tests for bounded Wildcard / Free Hit rebuild (ADR-0022)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.optimisation.io import load_solver_input
from src.optimisation.rebuild import (
    build_rebuild_pools,
    enumerate_bounded_rebuild_squads,
    rebuild_budget,
)
from src.optimisation.solver import solve
from src.optimisation.transfers import index_players, owned_records
from src.optimisation.types import SOLVER_VERSION, SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "evals" / "golden-cases" / "optimiser-gw3-input.json"
RULES = load_rules(ROOT / "control/rules/2026-27.yaml")
RULES_HASH = ruleset_sha256(ROOT / "control/rules/2026-27.yaml")


def _solve(data: dict) -> dict:
    return solve(SolverInput.from_dict(data), rules=RULES, ruleset_sha256=RULES_HASH)


def test_rebuild_budget_includes_selling_prices() -> None:
    inp = load_solver_input(GOLDEN)
    market = index_players(inp.players)
    owned = owned_records(inp.squad_player_ids, market, rules=RULES)
    assert rebuild_budget(owned, bank=inp.bank) == round(
        inp.bank + sum(float(row["selling_price"]) for row in owned), 1
    )


def test_wildcard_rebuild_emits_hitless_candidates() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["solver_version"] = SOLVER_VERSION
    data["active_chip"] = "wildcard_fh"
    data["rebuild_beam_width"] = 6
    data["rebuild_max_expanded_nodes"] = 400
    data["rebuild_candidate_limit_per_position"] = 6
    out = _solve(data)
    # Bounded rebuild ran (rebuild_kind set) but must not claim an exhaustive
    # full-squad rebuild search (ADR-0022).
    assert out["search_scope"]["full_rebuild_search"] is False
    assert out["search_scope"]["rebuild_kind"] == "wildcard"
    rebuild = out["plans"]["wildcard_rebuild"]
    assert rebuild is not None
    assert rebuild["hit_cost"] == 0
    assert rebuild["validation"]["squad_ok"]
    assert rebuild["validation"]["lineup_ok"]
    assert out["selected"]["objective"] >= out["plans"]["no_transfer"]["objective"]


def test_free_hit_rebuild_strategy_label() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["solver_version"] = SOLVER_VERSION
    data["active_chip"] = "free_hit_fh"
    data["rebuild_beam_width"] = 5
    out = _solve(data)
    assert out["search_scope"]["rebuild_kind"] == "free_hit"
    assert out["plans"]["free_hit_rebuild"] is not None
    assert out["plans"]["free_hit_rebuild"]["hit_cost"] == 0


def test_destination_horizon_is_recorded_without_activating_multi_gw() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["solver_version"] = SOLVER_VERSION
    data["destination_horizon_gameweeks"] = 4
    data["destination_discount_factor"] = 0.9
    out = _solve(data)
    assert out["horizon_gameweeks"] == 1
    assert out["destination_horizon"]["horizon_gameweeks"] == 4
    assert out["destination_horizon"]["discount_factor"] == 0.9
    assert out["destination_horizon"]["live_active"] is False


def test_live_multi_gw_horizon_still_rejected() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["solver_version"] = SOLVER_VERSION
    data["horizon_gameweeks"] = 4
    data["discount_factors"] = [1.0, 0.9, 0.81, 0.729]
    with pytest.raises(ValueError, match="horizon_gameweeks=1"):
        _solve(data)


def test_rebuild_pools_keep_owned_players() -> None:
    inp = load_solver_input(GOLDEN)
    market = index_players(inp.players)
    owned = owned_records(inp.squad_player_ids, market, rules=RULES)
    pools = build_rebuild_pools(
        owned,
        market,
        position_counts={"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3},
        candidate_limit_per_position=3,
        availability_policy="available_only",
    )
    owned_ids = {row["player_id"] for row in owned}
    for pos, rows in pools.items():
        kept = {row["player_id"] for row in rows} & owned_ids
        assert kept == {
            row["player_id"] for row in owned if row["position"] == pos
        }


def test_enumerate_rebuild_is_deterministic() -> None:
    inp = load_solver_input(GOLDEN)
    market = index_players(inp.players)
    owned = owned_records(inp.squad_player_ids, market, rules=RULES)
    kwargs = dict(
        bank=inp.bank,
        position_counts={"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3},
        max_per_club=3,
        candidate_limit_per_position=5,
        beam_width=4,
        max_expanded_nodes=200,
        availability_policy="available_only",
        rules=RULES,
    )
    a = list(enumerate_bounded_rebuild_squads(owned, market, **kwargs))
    b = list(enumerate_bounded_rebuild_squads(owned, market, **kwargs))
    assert [row["transfers"] for row in a] == [row["transfers"] for row in b]
