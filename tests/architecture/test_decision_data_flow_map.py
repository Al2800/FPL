"""Architect data-flow map stays the single join-point reference."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = (
    ROOT / "docs/architecture/2026-27-decision-data-flow.md"
).read_text(encoding="utf-8")


def test_data_flow_map_covers_planes_join_and_weighting() -> None:
    lowered = DOC.lower()
    assert "plane a" in lowered
    assert "plane b" in lowered
    assert "plane c" in lowered
    assert "plane d" in lowered
    assert "same place" in lowered
    assert "live evidence ledger" in lowered
    assert "prior_equivalent_minutes" in DOC or "1350" in DOC
    assert "primary advisory" in lowered
    assert "comparator" in lowered
    assert "fpl-official-endpoints" in DOC
    assert "the-odds-api" in DOC
    assert "vaastav-fpl" in DOC
