"""Tests for WP-07 transparent optimiser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import fingerprint, load_solver_input
from src.optimisation.solver import solve
from src.optimisation.types import SOLVER_VERSION, SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import transfer_hit_cost

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden-cases" / "optimiser-gw3-input.json"
RULES_PATH = ROOT / "control/rules/2026-27.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _solve(solver_input: SolverInput) -> dict:
    return solve(solver_input, rules=RULES, ruleset_sha256=RULES_HASH)


def test_transfer_hit_cost_from_rules() -> None:
    assert transfer_hit_cost(1, 1) == 0
    assert transfer_hit_cost(2, 1) == 4
    assert transfer_hit_cost(3, 1) == 8


def test_solve_golden_is_deterministic() -> None:
    inp = load_solver_input(GOLDEN)
    a = _solve(inp)
    b = _solve(inp)
    assert a["input_fingerprint"] == b["input_fingerprint"]
    assert a["output_fingerprint"] == b["output_fingerprint"]
    assert a["selected"] == b["selected"]
    assert fingerprint(a["selected"]) == fingerprint(b["selected"])


def test_committed_golden_output_reproduces() -> None:
    """Saved solver input must reproduce the committed selected plan fingerprint."""
    out_path = ROOT / "evals" / "golden-cases" / "optimiser-gw3-output.json"
    committed = json.loads(out_path.read_text(encoding="utf-8"))
    fresh = _solve(load_solver_input(GOLDEN))
    assert fresh["output_fingerprint"] == committed["output_fingerprint"]
    assert fresh["selected"]["transfers"] == committed["selected"]["transfers"]
    assert fresh["selected"]["objective"] == committed["selected"]["objective"]


def test_golden_plans_satisfy_hard_constraints() -> None:
    inp = load_solver_input(GOLDEN)
    out = _solve(inp)
    assert out["selected"] is not None
    assert out["plans"]["no_transfer"] is not None
    assert out["plans"]["no_transfer"]["validation"]["squad_ok"]
    assert out["plans"]["no_transfer"]["validation"]["lineup_ok"]
    # Injured MidE (id 12, EP 1.0) should be an attractive free transfer out
    selected = out["selected"]
    assert selected["validation"]["squad_ok"]
    assert selected["validation"]["lineup_ok"]
    assert selected["objective"] >= out["plans"]["no_transfer"]["objective"]


def test_club_change_overflow_allows_only_the_zero_transfer_exception() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["max_transfers"] = 1
    for player in data["players"]:
        if player["player_id"] in {"2", "4"}:
            player["club_id"] = "1"

    out = _solve(SolverInput.from_dict(data))

    assert out["plans"]["no_transfer"] is not None
    assert out["plans"]["no_transfer"]["transfers"] == []
    transferred = [
        candidate
        for candidate in out["all_candidates"]
        if candidate["transfers"]
    ]
    assert transferred
    owned_clubs = {
        player["player_id"]: player["club_id"]
        for player in data["players"]
        if player["player_id"] in data["squad_player_ids"]
    }
    market_clubs = {
        player["player_id"]: player["club_id"] for player in data["players"]
    }
    for candidate in transferred:
        clubs = dict(owned_clubs)
        for move in candidate["transfers"]:
            clubs.pop(move["player_out_id"])
            clubs[move["player_in_id"]] = market_clubs[move["player_in_id"]]
        counts = {
            club_id: list(clubs.values()).count(club_id)
            for club_id in set(clubs.values())
        }
        assert max(counts.values()) <= 3


def test_no_hit_never_exceeds_free_transfers() -> None:
    inp = load_solver_input(GOLDEN)
    out = _solve(inp)
    no_hit = out["plans"]["no_hit"]
    assert no_hit is not None
    assert no_hit["hit_cost"] == 0
    assert len(no_hit["transfers"]) <= inp.free_transfers or no_hit["strategy"] == "no_transfer"


def test_saved_input_round_trip() -> None:
    raw = json.loads(GOLDEN.read_text(encoding="utf-8"))
    inp = SolverInput.from_dict(raw)
    assert SolverInput.from_dict(inp.as_dict()).as_dict() == inp.as_dict()
    out1 = _solve(inp)
    out2 = _solve(SolverInput.from_dict(inp.as_dict()))
    assert out1["output_fingerprint"] == out2["output_fingerprint"]


def test_transfer_option_policy_is_explicit_and_decomposes_objective() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data.update(
        {
            "free_transfers": 2,
            "max_transfers": 2,
            "transfer_value_policy": "expected_hit_avoidance_v1",
            "probability_extra_transfer_needed": 0.5,
            "future_transfer_discount": 0.9,
        }
    )

    out = _solve(SolverInput.from_dict(data))
    legacy_data = dict(data)
    legacy_data.pop("transfer_value_policy")
    legacy_data.pop("probability_extra_transfer_needed")
    legacy_data.pop("future_transfer_discount")
    legacy = _solve(SolverInput.from_dict(legacy_data))

    assert out["transfer_value_policy"]["option_unit_value"] == 1.8
    assert set(out["best_by_transfer_count"]) == {"0", "1", "2"}
    assert (
        out["best_by_transfer_count"]["0"]["immediate_objective"]
        == legacy["plans"]["no_transfer"]["objective"]
    )
    for transfer_count, candidate in out["best_by_transfer_count"].items():
        assert len(candidate["transfers"]) == int(transfer_count)
        assert candidate["objective"] == round(
            candidate["immediate_objective"]
            + candidate["transfer_option_value"],
            4,
        )
        assert candidate["next_gameweek_free_transfers"] == 3 - int(
            transfer_count
        )
        assert candidate["banked_option_units"] == 2 - int(transfer_count)


def test_transfer_option_policy_respects_bank_cap() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data.update(
        {
            "free_transfers": 5,
            "max_transfers": 1,
            "transfer_value_policy": "expected_hit_avoidance_v1",
        }
    )

    out = _solve(SolverInput.from_dict(data))

    zero = out["best_by_transfer_count"]["0"]
    one = out["best_by_transfer_count"]["1"]
    assert zero["next_gameweek_free_transfers"] == 5
    assert one["next_gameweek_free_transfers"] == 5
    assert zero["transfer_option_value"] == one["transfer_option_value"]


def test_inactive_transfer_option_policy_preserves_legacy_output_shape() -> None:
    out = _solve(load_solver_input(GOLDEN))

    assert "transfer_value_policy" not in out
    assert "best_by_transfer_count" not in out
    assert "immediate_objective" not in out["selected"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("transfer_value_policy", "magic", "transfer_value_policy"),
        ("probability_extra_transfer_needed", -0.1, "probability"),
        ("probability_extra_transfer_needed", 1.1, "probability"),
        ("future_transfer_discount", -0.1, "discount"),
        ("future_transfer_discount", 1.1, "discount"),
    ],
)
def test_transfer_option_policy_rejects_invalid_controls(
    field: str, value: object, message: str
) -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data[field] = value

    with pytest.raises(ValueError, match=message):
        _solve(SolverInput.from_dict(data))


def test_allow_hits_false_caps_search() -> None:
    inp = load_solver_input(GOLDEN)
    data = inp.as_dict()
    data["allow_hits"] = False
    data["max_transfers"] = 3
    out = _solve(SolverInput.from_dict(data))
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

    out = _solve(SolverInput.from_dict(data))

    assert out["selected"]["transfers"] == [
        {"player_out_id": "12", "player_in_id": "19"}
    ]
    assert out["search_scope"]["affordability_filter_before_ranking"] is True


def test_ruleset_mismatch_fails_closed_unless_explicitly_allowed() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["ruleset_id"] = "different-rules"
    with pytest.raises(ValueError, match="differs from loaded"):
        _solve(SolverInput.from_dict(data))

    data["ruleset_mismatch_policy"] = "allow_loaded"
    out = _solve(SolverInput.from_dict(data))
    assert "explicit allow_loaded policy applied" in out["ruleset_note"]
    assert out["search_scope"]["ruleset_mismatch_policy"] == "allow_loaded"


def test_unavailable_buy_is_excluded_by_recorded_policy() -> None:
    data = load_solver_input(GOLDEN).as_dict()
    data["max_transfers"] = 1
    for player in data["players"]:
        if player["player_id"] == "16":
            player["status"] = "i"
            player["expected_points"] = 100.0

    out = _solve(SolverInput.from_dict(data))

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
        _solve(SolverInput.from_dict(data))

    data = load_solver_input(GOLDEN).as_dict()
    data["active_chip"] = "bench_boost_fh"
    data["chips_available"] = []
    with pytest.raises(ValueError, match="active_chip"):
        _solve(SolverInput.from_dict(data))


def test_selected_plan_is_not_labelled_as_a_global_optimum() -> None:
    out = _solve(load_solver_input(GOLDEN))
    assert out["selected"]["optimality"] == "highest_ev_in_declared_candidate_pool"
    assert out["search_scope"]["global_optimality_guaranteed"] is False


def test_solver_requires_explicit_rules_and_accepts_historical_catalogue() -> None:
    inp = load_solver_input(GOLDEN)
    with pytest.raises(TypeError, match="rules"):
        solve(inp)  # type: ignore[call-arg]

    historical_path = ROOT / "control/rules/2025-26.yaml"
    historical = load_rules(historical_path)
    data = inp.as_dict()
    data["season"] = "2025-26"
    data["ruleset_id"] = historical["meta"]["ruleset_id"]
    out = solve(
        SolverInput.from_dict(data),
        rules=historical,
        ruleset_sha256=ruleset_sha256(historical_path),
    )
    assert out["ruleset_id"] == "2025-26-v1.0"
    assert out["ruleset_sha256"] == ruleset_sha256(historical_path)
    again = solve(
        SolverInput.from_dict(data),
        rules=historical,
        ruleset_sha256=ruleset_sha256(historical_path),
    )
    assert again["output_fingerprint"] == out["output_fingerprint"]
    assert out["solver_version"] == SOLVER_VERSION
    assert len(out["output_fingerprint"]) == 64
