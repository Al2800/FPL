"""Phase 1 residual: golden runner and replay pilot set."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.scoring.golden_runner import run_all

REPO = Path(__file__).resolve().parents[1]


def test_rules_golden_runner_all_pass() -> None:
    report = run_all()
    assert report["failed"] == [], report["failed"]
    assert report["passed"] == report["n"]
    assert report["n"] >= 20
    assert all(
        result["detail"] != "catalogue_acknowledged" for result in report["results"]
    )


def test_replay_pilot_set_lists_wp04_gameweeks() -> None:
    cfg = yaml.safe_load(
        (REPO / "evals" / "replay-set" / "structured-pilot-gameweeks.yaml").read_text(
            encoding="utf-8"
        )
    )
    seasons = {b["season"]: b["gameweeks"] for b in cfg["pilots"]}
    assert seasons["2023-24"] == [1, 10, 20, 30, 38]
    assert seasons["2024-25"] == [1, 10, 20, 30]
