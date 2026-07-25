"""Planning-only appearance and squad-contingency valuation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.appearance_distribution import (
    AppearanceDistribution,
    AppearanceDistributionError,
    calibration_hash,
    distribution_for_probability,
    fit_binned_calibration,
)
from src.optimisation.io import load_solver_input
from src.optimisation.solver import solve
from src.optimisation.squad_contingency import (
    choose_contingency_lineup,
    evaluate_contingency_lineup,
)
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import get_rule, load_rules, ruleset_sha256


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)
SOLVER_RULES_PATH = ROOT / "control/rules/2026-27.yaml"
SOLVER_RULES = load_rules(SOLVER_RULES_PATH)
SOLVER_RULES_HASH = ruleset_sha256(SOLVER_RULES_PATH)
CONSTRAINTS = get_rule(RULES, "lineup.formation_constraints")["value"]
GOLDEN = ROOT / "evals/golden-cases/optimiser-gw3-input.json"


def _calibration(
    probabilities: tuple[float, float, float] = (0.1, 0.15, 0.75),
) -> dict:
    value = {
        "schema_version": "1.0",
        "model_version": "appearance-test-v1",
        "status": "test",
        "training_seasons": ["synthetic"],
        "states": ["zero", "under_60", "60_plus"],
        "smoothing_prior": {"zero": 1, "under_60": 1, "60_plus": 1},
        "bins": [
            {
                "lower": 0.0,
                "upper": 1.0,
                "n_observations": 100,
                "probabilities": {
                    "zero": probabilities[0],
                    "under_60": probabilities[1],
                    "60_plus": probabilities[2],
                },
            }
        ],
    }
    value["content_sha256"] = calibration_hash(value)
    return value


def _player(
    player_id: str,
    position: str,
    points: float,
    distribution: tuple[float, float, float],
) -> dict:
    return {
        "player_id": player_id,
        "position": position,
        "club_id": player_id,
        "expected_points": points,
        "appearance_distribution": {
            "zero": distribution[0],
            "under_60": distribution[1],
            "60_plus": distribution[2],
            "source": "test",
        },
    }


def _lineup() -> tuple[list[dict], list[dict]]:
    certain = (0.0, 0.0, 1.0)
    xi = [
        _player("g1", "GKP", 4.0, certain),
        *[_player(f"d{i}", "DEF", 4.0, certain) for i in range(1, 4)],
        *[_player(f"m{i}", "MID", 5.0, certain) for i in range(1, 5)],
        *[_player(f"f{i}", "FWD", 5.0, certain) for i in range(1, 4)],
    ]
    bench = [
        _player("g2", "GKP", 3.0, certain),
        _player("d4", "DEF", 2.0, certain),
        _player("m5", "MID", 3.0, certain),
        _player("d5", "DEF", 1.0, certain),
    ]
    return xi, bench


def test_three_state_distribution_and_double_gameweek_aggregation() -> None:
    distribution = AppearanceDistribution(0.2, 0.3, 0.5)
    aggregate = distribution.across_fixtures(2)

    assert aggregate.zero == pytest.approx(0.04)
    assert aggregate.under_60 == pytest.approx(0.21)
    assert aggregate.sixty_plus == pytest.approx(0.75)
    assert aggregate.appears == pytest.approx(0.96)


def test_binned_calibration_is_smoothed_hashed_and_fail_closed() -> None:
    fitted = fit_binned_calibration(
        [
            {"start_probability": 0.1, "minutes": 0},
            {"start_probability": 0.1, "minutes": 20},
            {"start_probability": 0.9, "minutes": 90},
        ],
        model_version="test-fit-v1",
        training_seasons=["2022-23"],
        bin_edges=(0.0, 0.5, 1.0),
    )
    low = distribution_for_probability(0.1, fitted)
    high = distribution_for_probability(0.9, fitted)

    assert low.zero > high.zero
    assert high.sixty_plus > low.sixty_plus
    assert fitted["content_sha256"] == calibration_hash(fitted)

    tampered = deepcopy(fitted)
    tampered["bins"][0]["probabilities"]["zero"] = 0.9
    with pytest.raises(AppearanceDistributionError, match="hash"):
        distribution_for_probability(0.1, tampered)


def test_goalkeeper_sub_and_vice_fallback_are_expected_not_realised() -> None:
    xi, bench = _lineup()
    xi[0]["appearance_distribution"] = {
        "zero": 0.5,
        "under_60": 0.0,
        "60_plus": 0.5,
    }
    xi[4]["expected_points"] = 10.0
    xi[4]["appearance_distribution"] = {
        "zero": 0.4,
        "under_60": 0.0,
        "60_plus": 0.6,
    }
    result = evaluate_contingency_lineup(
        starting_xi=xi,
        bench=bench,
        formation={"DEF": 3, "MID": 4, "FWD": 3},
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )

    assert result["auto_sub"]["goalkeeper"] == pytest.approx(1.5)
    assert result["captain_id"] == "m1"
    assert result["vice_fallback_component"] > 0.0


def test_bench_order_honours_first_legal_outfield_substitute() -> None:
    xi, bench = _lineup()
    # One midfielder misses out. Both the first DEF (4-3-3) and MID (3-4-3)
    # are legal, so bench order must determine which value enters.
    xi[4]["appearance_distribution"] = {
        "zero": 1.0,
        "under_60": 0.0,
        "60_plus": 0.0,
    }
    bench[1]["expected_points"] = 1.0
    bench[2]["expected_points"] = 8.0
    first_defender = evaluate_contingency_lineup(
        starting_xi=xi,
        bench=bench,
        formation={"DEF": 3, "MID": 4, "FWD": 3},
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )
    reordered = [bench[0], bench[2], bench[1], bench[3]]
    first_midfielder = evaluate_contingency_lineup(
        starting_xi=xi,
        bench=reordered,
        formation={"DEF": 3, "MID": 4, "FWD": 3},
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )

    assert first_defender["auto_sub"]["outfield"] == pytest.approx(1.0)
    assert first_midfielder["auto_sub"]["outfield"] == pytest.approx(8.0)


def test_formation_constraint_skips_an_illegal_earlier_bench_player() -> None:
    xi, bench = _lineup()
    xi[1]["appearance_distribution"] = {
        "zero": 1.0,
        "under_60": 0.0,
        "60_plus": 0.0,
    }
    # With a defender absent from a 3-4-3, MID first is illegal; DEF second enters.
    ordered = [bench[0], bench[2], bench[1], bench[3]]
    result = evaluate_contingency_lineup(
        starting_xi=xi,
        bench=ordered,
        formation={"DEF": 3, "MID": 4, "FWD": 3},
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )

    assert result["auto_sub"]["outfield"] == pytest.approx(2.0)
    assert (
        result["auto_sub"]["outfield_selection_probability"]["m5"]
        == pytest.approx(0.0)
    )
    assert (
        result["auto_sub"]["outfield_selection_probability"]["d4"]
        == pytest.approx(1.0)
    )


@pytest.mark.parametrize("position", ["GKP", "DEF", "MID", "FWD"])
def test_deterministic_lineup_covers_every_position(position: str) -> None:
    xi, bench = _lineup()
    starter = next(player for player in xi if player["position"] == position)
    starter["appearance_distribution"] = {
        "zero": 1.0,
        "under_60": 0.0,
        "60_plus": 0.0,
    }
    result = evaluate_contingency_lineup(
        starting_xi=xi,
        bench=bench,
        formation={"DEF": 3, "MID": 4, "FWD": 3},
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )
    assert result["bench_contingency_value"] >= 0.0


def test_selector_optimises_bench_order_and_keeps_bench_boost_separate() -> None:
    xi, bench = _lineup()
    squad = [*xi, *bench]
    regular = choose_contingency_lineup(
        squad,
        formations=[{"DEF": 3, "MID": 4, "FWD": 3}],
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip=None,
    )
    boosted = choose_contingency_lineup(
        squad,
        formations=[{"DEF": 3, "MID": 4, "FWD": 3}],
        calibration=_calibration(),
        constraints=CONSTRAINTS,
        active_chip="bench_boost_fh",
    )

    assert len(regular["bench"]) == 4
    assert boosted["contingency"]["auto_sub"]["total"] == 0.0
    assert boosted["contingency"]["bench_contingency_value"] == pytest.approx(
        sum(player["expected_points"] for player in boosted["bench"])
    )


def test_solver_policy_is_opt_in_and_decomposes_planning_value() -> None:
    legacy_input = load_solver_input(GOLDEN)
    legacy = solve(legacy_input, rules=SOLVER_RULES, ruleset_sha256=SOLVER_RULES_HASH)
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    data["max_transfers"] = 0
    data["squad_contingency_policy"] = "probabilistic_v1"
    data["appearance_calibration"] = _calibration()
    for player in data["players"]:
        player["start_probability"] = 0.8
        player["fixture_count"] = 1
    challenger = solve(
        SolverInput.from_dict(data), rules=SOLVER_RULES, ruleset_sha256=SOLVER_RULES_HASH
    )

    assert "squad_contingency_policy" not in legacy
    assert "contingency" not in legacy["selected"]
    assert challenger["squad_contingency_policy"]["realised_scorer_changed"] is False
    selected = challenger["selected"]
    assert selected["objective"] == pytest.approx(
        selected["objective_without_hits"]
    )
    assert selected["objective"] == pytest.approx(
        selected["contingency"]["planning_value"]
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("squad_contingency_policy", "magic", "squad_contingency_policy"),
        ("appearance_calibration", None, "appearance_calibration"),
    ],
)
def test_solver_contingency_controls_fail_closed(
    field: str, value: object, message: str
) -> None:
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    data["max_transfers"] = 0
    data["squad_contingency_policy"] = "probabilistic_v1"
    data["appearance_calibration"] = _calibration()
    data[field] = value

    with pytest.raises(ValueError, match=message):
        solve(
            SolverInput.from_dict(data), rules=SOLVER_RULES, ruleset_sha256=SOLVER_RULES_HASH
        )
