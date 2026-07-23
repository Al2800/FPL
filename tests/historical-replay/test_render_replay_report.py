from __future__ import annotations

from pathlib import Path

import pytest

from scripts.render_replay_report import render_report


REPO = Path(__file__).resolve().parents[2]
CHECKPOINT = REPO / "reports" / "benchmarks" / "2025-26" / "gw-01"
SEED = REPO / "control" / "seeds" / "2025-26" / "official-scout-gw1.json"


def test_gw1_report_renders_checkpoint_and_handoff(tmp_path: Path) -> None:
    if not (CHECKPOINT / "run-summary.json").exists():
        pytest.skip("committed GW1 checkpoint is unavailable")

    target = render_report(
        checkpoint_dir=CHECKPOINT,
        seed_path=SEED,
        output_path=tmp_path / "index.html",
    )
    document = target.read_text(encoding="utf-8")

    assert "<title>FPL Benchmark · 2025-26 · GW1</title>" in document
    assert '<div class="score">56<span>points</span></div>' in document
    assert "Rodon returned 7" in document
    assert "Ready, not decided" in document
    assert "No Gameweek 2 proposal or outcome exists yet" in document
    assert "b82f4f2288426d905da7c28fc9148374" in document
