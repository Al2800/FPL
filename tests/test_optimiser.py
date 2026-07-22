"""Tests for WP-07 transparent optimiser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import fingerprint, load_solver_input
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.scoring.validator import transfer_hit_cost

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden-cases" / "optimiser-gw3-input.json"


def test_transfer_hit_cost_from_rules() -> None:
    assert transfer_hit_cost(1, 1) == 0
    assert transfer_hit_cost(2, 1) == 4
    assert transfer_hit_cost(3, 1) == 8


def test_solve_golden_is_deterministic() -> None:
    inp = load_solver_input(GOLDEN)
    a = solve(inp)
    b = solve(inp)
    assert a["input_fingerprint"] == b["input_fingerprint"]
    assert a["output_fingerprint"] == b["output_fingerprint"]
    assert a["selected"] == b["selected"]
    assert fingerprint(a["selected"]) == fingerprint(b["selected"])


def test_committed_golden_output_reproduces() -> None:
    """Saved solver input must reproduce the committed selected plan fingerprint."""
    out_path = ROOT / "evals" / "golden-cases" / "optimiser-gw3-output.json"
    committed = json.loads(out_path.read_text(encoding="utf-8"))
    fresh = solve(load_solver_input(GOLDEN))
    assert fresh["output_fingerprint"] == committed["output_fingerprint"]
    assert fresh["selected"]["transfers"] == committed["selected"]["transfers"]
    assert fresh["selected"]["objective"] == committed["selected"]["objective"]


def test_golden_plans_satisfy_hard_constraints() -> None:
    inp = load_solver_input(GOLDEN)
    out = solve(inp)
    assert out["selected"] is not None
    assert out["plans"]["no_transfer"] is not None
    assert out["plans"]["no_transfer"]["validation"]["squad_ok"]
    assert out["plans"]["no_transfer"]["validation"]["lineup_ok"]
    # Injured MidE (id 12, EP 1.0) should be an attractive free transfer out
    selected = out["selected"]
    assert selected["validation"]["squad_ok"]
    assert selected["validation"]["lineup_ok"]
    assert selected["objective"] >= out["plans"]["no_transfer"]["objective"]


def test_no_hit_never_exceeds_free_transfers() -> None:
    inp = load_solver_input(GOLDEN)
    out = solve(inp)
    no_hit = out["plans"]["no_hit"]
    assert no_hit is not None
    assert no_hit["hit_cost"] == 0
    assert len(no_hit["transfers"]) <= inp.free_transfers or no_hit["strategy"] == "no_transfer"


def test_saved_input_round_trip() -> None:
    raw = json.loads(GOLDEN.read_text(encoding="utf-8"))
    inp = SolverInput.from_dict(raw)
    assert SolverInput.from_dict(inp.as_dict()).as_dict() == inp.as_dict()
    out1 = solve(inp)
    out2 = solve(SolverInput.from_dict(inp.as_dict()))
    assert out1["output_fingerprint"] == out2["output_fingerprint"]


def test_allow_hits_false_caps_search() -> None:
    inp = load_solver_input(GOLDEN)
    data = inp.as_dict()
    data["allow_hits"] = False
    data["max_transfers"] = 3
    out = solve(SolverInput.from_dict(data))
    for c in out["all_candidates"]:
        assert c["hit_cost"] == 0


def test_affordability_is_applied_before_buy_pool_truncation() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["max_transfers"] = 1
    data["buy_pool_per_pos"] = 1
    for player in data["players"]:
        if player["player_id"] == "16":
            player["now_cost"] = 20.0
            player["expected_points"] = 100.0
        elif player["player_id"] == "19":
            player["now_cost"] = 5.0
            player["expected_points"] = 6.9

    out = solve(SolverInput.from_dict(data))

    assert out["selected"]["transfers"] == [
        {"player_out_id": "12", "player_in_id": "19"}
    ]
    assert out["search_scope"]["affordability_filter_before_ranking"] is True


def test_ruleset_mismatch_fails_closed_unless_explicitly_allowed() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["ruleset_id"] = "different-rules"
    with pytest.raises(ValueError, match="differs from loaded"):
        solve(SolverInput.from_dict(data))

    data["ruleset_mismatch_policy"] = "allow_loaded"
    out = solve(SolverInput.from_dict(data))
    assert "explicit allow_loaded policy applied" in out["ruleset_note"]
    assert out["search_scope"]["ruleset_mismatch_policy"] == "allow_loaded"


def test_unavailable_buy_is_excluded_by_recorded_policy() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["max_transfers"] = 1
    for player in data["players"]:
        if player["player_id"] == "16":
            player["status"] = "i"
            player["expected_points"] = 100.0

    out = solve(SolverInput.from_dict(data))

    incoming = {
        transfer["player_in_id"]
        for candidate in out["all_candidates"]
        for transfer in candidate["transfers"]
    }
    assert "16" not in incoming
    assert out["search_scope"]["availability_policy"] == "available_only"


def test_unsupported_single_gameweek_controls_fail_instead_of_being_inert() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["horizon_gameweeks"] = 2
    data["discount_factors"] = [1.0, 0.9]
    with pytest.raises(ValueError, match="supports only horizon_gameweeks=1"):
        solve(SolverInput.from_dict(data))

    data = load_solver_input(GOLDEN).as_dict()
    data["active_chip"] = "bench_boost_fh"
    data["chips_available"] = []
    with pytest.raises(ValueError, match="active_chip"):
        solve(SolverInput.from_dict(data))


def test_selected_plan_is_not_labelled_as_a_global_optimum() -> None:
    out = solve(load_solver_input(GOLDEN))
    assert out["selected"]["optimality"] == "highest_ev_in_declared_candidate_pool"
    assert out["search_scope"]["global_optimality_guaranteed"] is False
