"""Tests for distributional chip-now vs later EV (ticket 09)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.chip_distributional_ev import (
    ChipDistributionalEvError,
    annotate_chip_candidates_with_distributions,
    attach_distributional_chip_annotation_to_gdr,
    build_horizon_comparison_from_transfer_hit_evaluation,
    build_horizon_policy_comparison,
    compare_plan_distributions,
    plan_samples_from_chip_candidates,
)


REPO = Path(__file__).resolve().parents[2]
GW34_HIT = (
    REPO
    / "reports/benchmarks/2025-26-counterfactuals/gw-34/transfer-hit-evaluation.json"
)


def test_compare_plan_distributions_reports_win_probability() -> None:
    comparison = compare_plan_distributions(
        candidate_id="triple_captain_fh",
        samples=[60.0, 70.0, 80.0, 90.0],
        alternative_id="no_chip_0_transfers",
        alternative_samples=[55.0, 65.0, 85.0, 80.0],
    )
    assert comparison["n_paths"] == 4
    assert comparison["prob_candidate_beats_alternative"] == 0.75
    assert comparison["prob_alternative_beats_candidate"] == 0.25
    assert comparison["mean_delta"] == 3.75


def test_annotate_chip_selection_against_no_chip_control() -> None:
    selection = {
        "no_chip_control_id": "no_chip_0_transfers",
        "selected_candidate_id": "bench_boost_fh",
        "selected_active_chip": "bench_boost_fh",
        "candidates": [
            {
                "candidate_id": "no_chip_0_transfers",
                "active_chip": None,
                "expected": {"policy_value": 50.0},
            },
            {
                "candidate_id": "bench_boost_fh",
                "active_chip": "bench_boost_fh",
                "expected": {"policy_value": 56.0},
            },
        ],
    }
    annotated = annotate_chip_candidates_with_distributions(
        selection,
        plan_samples_by_candidate={
            "no_chip_0_transfers": [50.0, 52.0, 48.0, 51.0],
            "bench_boost_fh": [58.0, 60.0, 55.0, 57.0],
        },
    )
    assert annotated["distributional_justification"]["selected_vs_later"][
        "prob_candidate_beats_alternative"
    ] == 1.0
    assert (
        annotated["candidates"][1]["points_distribution"]["mean"] == 57.5
    )


def test_plan_samples_from_chip_candidates_uses_captain_multiplier() -> None:
    samples = plan_samples_from_chip_candidates(
        [
            {
                "candidate_id": "no_chip",
                "candidate": {
                    "hit_cost": 0,
                    "lineup": {
                        "starting_xi_ids": ["a", "b"],
                        "captain_id": "a",
                    },
                },
            }
        ],
        player_path_points={"a": [10.0, 12.0], "b": [5.0, 6.0]},
    )
    assert samples["no_chip"] == [25.0, 30.0]


def test_horizon_comparison_marks_destination_inactive() -> None:
    comparison = build_horizon_policy_comparison(
        baseline_label="single_gw_adr0020",
        baseline_metrics={"mean_season_points": 2100.0},
        destination_label="four_gw_destination",
        destination_metrics={"mean_season_points": 2110.0},
        paired_delta={"mean_season_points": 10.0},
    )
    assert comparison["destination"]["live_active"] is False
    assert comparison["destination"]["horizon_gameweeks"] == 4
    assert len(comparison["content_sha256"]) == 64


@pytest.mark.artifact_backed
def test_horizon_comparison_from_sealed_gw34_hit_gate() -> None:
    evaluation = json.loads(GW34_HIT.read_text(encoding="utf-8"))
    comparison = build_horizon_comparison_from_transfer_hit_evaluation(evaluation)
    assert comparison["destination"]["live_active"] is False
    assert comparison["baseline"]["metrics"]["selected_candidate_id"] == (
        "transfer_count:3"
    )
    assert comparison["paired_delta"]["horizon_minus_immediate_net_points"] == (
        round(
            float(comparison["destination"]["metrics"]["horizon_net_value"])
            - float(comparison["baseline"]["metrics"]["immediate_net_points"]),
            6,
        )
    )


def test_attach_to_gdr_requires_annotation() -> None:
    with pytest.raises(ChipDistributionalEvError, match="distributional_justification"):
        attach_distributional_chip_annotation_to_gdr(
            {"gameweek": 1},
            chip_selection={"selected_candidate_id": "x"},
        )


def test_attach_to_gdr_surfaces_justification() -> None:
    selection = annotate_chip_candidates_with_distributions(
        {
            "no_chip_control_id": "no_chip",
            "selected_candidate_id": "tc",
            "selected_active_chip": "triple_captain_fh",
            "candidates": [
                {"candidate_id": "no_chip", "active_chip": None},
                {"candidate_id": "tc", "active_chip": "triple_captain_fh"},
            ],
        },
        plan_samples_by_candidate={
            "no_chip": [40.0, 42.0],
            "tc": [50.0, 44.0],
        },
    )
    horizon = build_horizon_policy_comparison(
        baseline_label="baseline",
        baseline_metrics={"x": 1},
        destination_label="destination",
        destination_metrics={"x": 2},
    )
    gdr = attach_distributional_chip_annotation_to_gdr(
        {"gameweek": 3},
        chip_selection=selection,
        horizon_comparison=horizon,
    )
    assert gdr["chip_distributional_ev"]["selected_active_chip"] == (
        "triple_captain_fh"
    )
    assert gdr["chip_horizon_policy_comparison"]["content_sha256"] == (
        horizon["content_sha256"]
    )
