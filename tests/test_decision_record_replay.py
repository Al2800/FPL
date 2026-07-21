"""WP-09 Gameweek Decision Record, baseline comparison, and replay harness."""

from __future__ import annotations

import json
from pathlib import Path

from src.orchestration.replay_harness import replay_batch, replay_gameweek
from src.reporting.baseline_comparison import (
    compare_to_do_nothing,
    retrospective_metrics,
)
from src.reporting.decision_record import (
    SECTION_31_FIELDS,
    section_31_coverage,
    validate_decision_record,
)

REPO = Path(__file__).resolve().parents[1]
GOLDEN_INPUT = REPO / "evals" / "golden-cases" / "optimiser-gw3-input.json"
GDR_EXAMPLE = REPO / "control" / "schemas" / "examples" / "gameweek_decision_records.json"


def test_gdr_example_validates_and_covers_section_31() -> None:
    record = json.loads(GDR_EXAMPLE.read_text(encoding="utf-8"))
    validate_decision_record(record)
    coverage = section_31_coverage(record)
    assert set(coverage) == set(SECTION_31_FIELDS)
    assert all(coverage.values()), coverage


def test_compare_to_do_nothing() -> None:
    cmp = compare_to_do_nothing(recommended_objective=60.4, do_nothing_objective=54.0)
    assert cmp["expected_advantage"] == 6.4


def test_retrospective_metrics_from_record_alone() -> None:
    record = json.loads(GDR_EXAMPLE.read_text(encoding="utf-8"))
    metrics = retrospective_metrics(
        record=record, realised_points=58.0, hindsight_best_points=62.0
    )
    assert metrics["expected_advantage_vs_do_nothing"] == 6.4
    assert metrics["decision_regret"] == 4.0
    assert metrics["n_transfers"] == 1


def test_replay_harness_writes_valid_gdr(tmp_path: Path) -> None:
    out = tmp_path / "replay"
    record = replay_gameweek(GOLDEN_INPUT, out_dir=out)
    validate_decision_record(record)
    assert all(section_31_coverage(record).values())
    assert record["baseline_comparison"]["expected_advantage"] >= 0
    assert (out / "decision-record.json").exists()
    assert (out / "replay-meta.json").exists()
    again = replay_gameweek(GOLDEN_INPUT)
    assert again["repro_hash"] == record["repro_hash"]


def test_replay_with_retrospective_metrics(tmp_path: Path) -> None:
    record = replay_gameweek(
        GOLDEN_INPUT,
        out_dir=tmp_path / "retro",
        attach_outcome_points=55.0,
        hindsight_best_points=61.0,
    )
    assert record["outcome"]["points"] == 55.0
    assert record["retrospective"]["metrics"]["decision_regret"] == 6.0
    validate_decision_record(record)


def test_replay_batch_is_cheap_and_deterministic() -> None:
    summary = replay_batch(GOLDEN_INPUT, n=3)
    assert summary["n"] == 3
    assert summary["deterministic"] is True
    assert summary["mean_elapsed_ms"] < 30_000
