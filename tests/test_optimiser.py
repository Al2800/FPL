"""Tests for WP-07 transparent optimiser."""

from __future__ import annotations

import json
from pathlib import Path

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
