"""Offline contracts for official FPL field benchmarks (ticket 06)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.forecasting.official_field_benchmarks import (
    OfficialFieldBenchmarkError,
    assess_element_summary_adoption,
    evaluate_official_fields,
    write_official_field_benchmark_report,
)


def test_insufficient_predeadline_outcomes_are_documented() -> None:
    report = evaluate_official_fields(
        paired_rows=[],
        bootstrap_strength_pairs=[],
        element_summary_paths=[],
        predeadline_snapshot_count=6,
        notes="Synthetic insufficiency case.",
    )
    assert report["status"] == "insufficient_sample"
    assert report["n_paired_outcomes"] == 0
    assert report["fields"]["ep_next"]["status"] == "insufficient_sample"
    assert report["fields"]["fdr"]["status"] == "insufficient_sample"
    assert report["fields"]["bootstrap_team_strength"]["status"] == "insufficient_sample"
    assert report["fields"]["element_summary"]["status"] == "no_corpus"
    assert report["promotion"]["promoted_fields"] == []


def test_ep_next_mae_when_paired_sample_exists() -> None:
    paired = [
        {
            "player_id": "1",
            "ep_next": 4.0,
            "naive_points": 3.0,
            "actual_points": 5.0,
            "fdr": 2,
            "fdr_multiplier": 1.1,
            "actual_cs": 1,
            "team_strength_multiplier": 1.05,
        },
        {
            "player_id": "2",
            "ep_next": 6.0,
            "naive_points": 5.5,
            "actual_points": 6.0,
            "fdr": 4,
            "fdr_multiplier": 0.9,
            "actual_cs": 0,
            "team_strength_multiplier": 0.95,
        },
        {
            "player_id": "3",
            "ep_next": 2.0,
            "naive_points": 2.5,
            "actual_points": 1.0,
            "fdr": 3,
            "fdr_multiplier": 1.0,
            "actual_cs": 0,
            "team_strength_multiplier": 1.0,
        },
    ]
    report = evaluate_official_fields(
        paired_rows=paired,
        bootstrap_strength_pairs=[
            {"official_attack": 1200, "model_attack": 1.2, "club_id": "a"},
            {"official_attack": 1100, "model_attack": 1.1, "club_id": "b"},
            {"official_attack": 1000, "model_attack": 1.0, "club_id": "c"},
        ],
        element_summary_paths=[],
        predeadline_snapshot_count=3,
        minimum_paired_outcomes=3,
    )
    assert report["status"] == "ok"
    assert report["fields"]["ep_next"]["status"] == "ok"
    assert report["fields"]["ep_next"]["mae"] == pytest.approx(2 / 3)
    assert report["fields"]["ep_next"]["naive_mae"] == pytest.approx(4 / 3)
    # ep_next MAE beats naive → candidate only; promotion requires an owner gate
    assert "ep_next" in report["promotion"]["improved_vs_naive"]
    assert report["promotion"]["promoted_fields"] == []


def test_element_summary_assessment_documents_leakage_and_retention() -> None:
    assessment = assess_element_summary_adoption(summary_paths=[])
    assert assessment["status"] == "no_corpus"
    assert "vaastav" in assessment["duplication_note"].lower()
    assert "leakage" in assessment["leakage_note"].lower()
    assert assessment["adopt"] is False


def test_write_report_is_deterministic(tmp_path: Path) -> None:
    report = evaluate_official_fields(
        paired_rows=[],
        bootstrap_strength_pairs=[],
        element_summary_paths=[],
        predeadline_snapshot_count=0,
    )
    paths = write_official_field_benchmark_report(tmp_path, report)
    assert paths["json"].is_file()
    assert paths["markdown"].is_file()
    first = paths["json"].read_text(encoding="utf-8")
    write_official_field_benchmark_report(tmp_path, report)
    assert paths["json"].read_text(encoding="utf-8") == first
    body = paths["markdown"].read_text(encoding="utf-8")
    assert "insufficient" in body.lower()
    assert "element-summary" in body.lower()


def test_rejects_malformed_paired_row() -> None:
    with pytest.raises(OfficialFieldBenchmarkError, match="naive_points"):
        evaluate_official_fields(
            paired_rows=[{"player_id": "1", "ep_next": 1.0}],
            bootstrap_strength_pairs=[],
            element_summary_paths=[],
            predeadline_snapshot_count=1,
        )
