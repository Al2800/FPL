"""Offline contracts for the Monte Carlo simulation layer (ticket 05)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.calibration import calibration_summary
from src.forecasting.appearance_distribution import AppearanceDistribution
from src.forecasting.monte_carlo import (
    FixtureSimulationInput,
    MonteCarloError,
    PlayerSimulationInput,
    attach_monte_carlo_to_decision_record,
    percentile_summary,
    plan_points_samples,
    simulate_gameweek,
    write_calibration_report,
)
from src.scoring.engine import score_match_stats
from src.scoring.rules_loader import load_rules


REPO = Path(__file__).resolve().parents[2]
RULES = load_rules(REPO / "control" / "rules" / "2026-27.yaml")


def _fixture() -> FixtureSimulationInput:
    return FixtureSimulationInput(
        fixture_id="fx1",
        home_club_id="club_a",
        away_club_id="club_b",
        expected_home_xg=1.4,
        expected_away_xg=0.9,
    )


def _midfielder(*, club_id: str = "club_a") -> PlayerSimulationInput:
    return PlayerSimulationInput(
        player_id="p1",
        position="MID",
        club_id=club_id,
        fixture_id="fx1",
        appearance=AppearanceDistribution(zero=0.1, under_60=0.2, sixty_plus=0.7),
        goals_per_90=0.35,
        assists_per_90=0.25,
    )


def test_percentile_summary_is_ordered() -> None:
    summary = percentile_summary([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    assert summary["p10"] <= summary["p50"] <= summary["p90"]
    assert summary["mean"] == pytest.approx(5.5)


def test_simulate_gameweek_is_seed_reproducible() -> None:
    fixtures = [_fixture()]
    players = [
        _midfielder(),
        PlayerSimulationInput(
            player_id="p2",
            position="DEF",
            club_id="club_b",
            fixture_id="fx1",
            appearance=AppearanceDistribution(zero=0.05, under_60=0.15, sixty_plus=0.8),
            goals_per_90=0.05,
            assists_per_90=0.08,
        ),
    ]
    first = simulate_gameweek(
        fixtures=fixtures, players=players, n_paths=200, seed=42, rules=RULES
    )
    second = simulate_gameweek(
        fixtures=fixtures, players=players, n_paths=200, seed=42, rules=RULES
    )
    third = simulate_gameweek(
        fixtures=fixtures, players=players, n_paths=200, seed=43, rules=RULES
    )
    assert first["content_sha256"] == second["content_sha256"]
    assert first["content_sha256"] != third["content_sha256"]
    assert first["players"]["p1"]["p10"] <= first["players"]["p1"]["p50"]
    assert first["players"]["p1"]["p50"] <= first["players"]["p1"]["p90"]


def test_shared_scoreline_correlates_teammate_clean_sheets() -> None:
    """Two defenders on the same side share clean-sheet outcomes across paths."""

    fixtures = [_fixture()]
    defenders = [
        PlayerSimulationInput(
            player_id=f"d{i}",
            position="DEF",
            club_id="club_a",
            fixture_id="fx1",
            appearance=AppearanceDistribution(zero=0.0, under_60=0.0, sixty_plus=1.0),
            goals_per_90=0.0,
            assists_per_90=0.0,
        )
        for i in (1, 2)
    ]
    result = simulate_gameweek(
        fixtures=fixtures, players=defenders, n_paths=300, seed=7, rules=RULES
    )
    # With fixed 90 minutes and zero attacking rates, points differ only via CS/GC.
    # Shared scorelines => identical path totals for both defenders.
    assert result["player_path_points"]["d1"] == result["player_path_points"]["d2"]


def test_scoring_uses_engine_not_hard_coded_points() -> None:
    fixtures = [_fixture()]
    bench = PlayerSimulationInput(
        player_id="bench",
        position="MID",
        club_id="club_a",
        fixture_id="fx1",
        appearance=AppearanceDistribution(zero=1.0, under_60=0.0, sixty_plus=0.0),
        goals_per_90=5.0,
        assists_per_90=5.0,
    )
    result = simulate_gameweek(
        fixtures=fixtures, players=[bench], n_paths=20, seed=3, rules=RULES
    )
    assert result["player_path_points"]["bench"] == [0.0] * 20
    assert score_match_stats(
        {"position": "MID", "minutes": 0, "goals": 0, "assists": 0, "clean_sheet": False},
        RULES,
    )["total"] == 0


def test_plan_distribution_applies_captain_multiplier() -> None:
    path_points = {
        "p1": [2.0, 4.0, 6.0],
        "p2": [1.0, 1.0, 1.0],
    }
    samples = plan_points_samples(
        path_points,
        starting_xi=["p1", "p2"],
        captain_id="p1",
        hit_cost=0,
    )
    assert samples == [5.0, 9.0, 13.0]


def test_attach_monte_carlo_updates_gdr_projections_and_plans() -> None:
    simulation = simulate_gameweek(
        fixtures=[_fixture()],
        players=[_midfielder()],
        n_paths=50,
        seed=1,
        rules=RULES,
    )
    record = {
        "projections_summary": {"n_players": 1, "model_versions": ["live_forecast"]},
        "candidate_plans": [
            {
                "strategy": "no_transfer",
                "objective": 40.0,
                "starting_xi": ["p1"],
                "captain_id": "p1",
                "hit_cost": 0,
            }
        ],
    }
    updated = attach_monte_carlo_to_decision_record(record, simulation)
    summary = updated["projections_summary"]
    assert "p10" in summary
    assert "p50" in summary
    assert "p90" in summary
    assert summary["simulation"]["seed"] == 1
    assert "points_distribution" in updated["candidate_plans"][0]
    dist = updated["candidate_plans"][0]["points_distribution"]
    assert dist["p10"] <= dist["p50"] <= dist["p90"]


def test_calibration_report_written_under_reports_forecasting(tmp_path: Path) -> None:
    simulation = simulate_gameweek(
        fixtures=[_fixture()],
        players=[_midfielder()],
        n_paths=100,
        seed=11,
        rules=RULES,
    )
    # Synthetic realised points near the simulated mean for a smoke calibration.
    predicted = [simulation["players"]["p1"]["p50"]] * 5
    actuals = [simulation["players"]["p1"]["mean"]] * 5
    summary = calibration_summary(predicted, actuals)
    out_dir = tmp_path / "forecasting"
    paths = write_calibration_report(
        out_dir,
        simulation=simulation,
        calibration=summary,
        notes="Synthetic offline calibration smoke for ticket 05.",
    )
    assert paths["json"].is_file()
    assert paths["markdown"].is_file()
    body = paths["markdown"].read_text(encoding="utf-8")
    assert "Monte Carlo" in body
    assert "p50" in body.lower() or "P50" in body


def test_rejects_unknown_fixture_for_player() -> None:
    with pytest.raises(MonteCarloError, match="fixture"):
        simulate_gameweek(
            fixtures=[_fixture()],
            players=[
                PlayerSimulationInput(
                    player_id="p1",
                    position="MID",
                    club_id="club_a",
                    fixture_id="missing",
                    appearance=AppearanceDistribution(
                        zero=0.1, under_60=0.2, sixty_plus=0.7
                    ),
                    goals_per_90=0.2,
                    assists_per_90=0.1,
                )
            ],
            n_paths=10,
            seed=1,
            rules=RULES,
        )
