"""Equivalence-oracle and measurement-contract tests.

These tests intentionally contain no latency threshold: shared CI hardware makes
such thresholds noisy. Performance regressions are reviewed against stored
reports, while deterministic outputs and domain invariants fail normally.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.profile_core_performance import percentile
from src.optimisation.io import fingerprint


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "evals/golden-cases/optimiser-gw3-input.json"
OUTPUT = ROOT / "evals/golden-cases/optimiser-gw3-input.output.json"
EPISODE_INDEX = (
    ROOT / "evals/episodes/structured/benchmark-v0-index-v2.json"
)


def test_percentile_contract_is_ordered_and_interpolated():
    values = [5.0, 1.0, 4.0, 2.0, 3.0]
    assert percentile(values, 0.0) == 1.0
    assert percentile(values, 0.5) == 3.0
    assert percentile(values, 0.95) == pytest.approx(4.8)
    assert percentile(values, 0.99) == pytest.approx(4.96)
    assert percentile(values, 1.0) == 5.0


def test_committed_solver_output_is_bound_to_input_and_domain_invariants():
    solver_input = json.loads(INPUT.read_text(encoding="utf-8"))
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert output["input_fingerprint"] == fingerprint(solver_input)
    assert output["output_fingerprint"] == fingerprint(
        {
            "solver_version": output["solver_version"],
            "selected": output["selected"],
            "plans": output["plans"],
        }
    )
    selected = output["selected"]
    assert selected["validation"] == {
        "chips_ok": True,
        "lineup_ok": True,
        "squad_ok": True,
    }
    assert len(selected["lineup"]["starting_xi_ids"]) == 11
    assert len(selected["lineup"]["bench_ids"]) == 4
    assert selected["lineup"]["captain_id"] in selected["lineup"]["starting_xi_ids"]
    assert selected["lineup"]["vice_captain_id"] in selected["lineup"]["starting_xi_ids"]
    assert selected["lineup"]["captain_id"] != selected["lineup"]["vice_captain_id"]


def test_historical_episode_index_has_one_distinct_partition_per_gameweek():
    index = json.loads(EPISODE_INDEX.read_text(encoding="utf-8"))
    rows = index["episodes"]
    assert index["episode_count"] == 38
    assert len(rows) == 38
    assert sorted(row["gameweek"] for row in rows) == list(range(1, 39))
    assert len({row["episode_id"] for row in rows}) == 38
    assert len({row["observed_partition_sha256"] for row in rows}) == 38
    assert all("player_outcomes" not in row for row in rows)
    assert all("hidden_outcome" not in row for row in rows)
