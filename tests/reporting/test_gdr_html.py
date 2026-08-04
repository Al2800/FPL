"""Offline contracts for static GDR HTML rendering (ticket 14)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.reporting.gdr_html import (
    GdrHtmlError,
    render_gdr_html,
    render_season_index_html,
    scan_gameweek_records,
    write_gdr_html,
)


REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "control" / "schemas" / "examples" / "gameweek_decision_records.json"


@pytest.fixture
def example_record() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_render_gdr_html_is_deterministic_and_offline(example_record: dict) -> None:
    first = render_gdr_html(example_record)
    second = render_gdr_html(example_record)
    assert first == second
    assert "gdr_skeleton_gw3" in first
    assert "Decision cutoff" in first
    assert "ruleset" in first.lower() or "Ruleset" in first
    assert "Validation" in first
    assert "Approval journal" in first
    assert "Monte Carlo distributions unavailable" in first
    assert "Price-risk annotations unavailable" in first
    assert "button" not in first.lower()
    assert 'lang="en-GB"' in first


def test_render_includes_freshness_and_distributions(example_record: dict) -> None:
    example_record["degraded"] = True
    example_record["degraded_reasons"] = ["capture_missed:T-2h"]
    example_record["data_quality"] = "degraded"
    example_record["freshness"] = {
        "capture": {"status": "degraded", "missed_job_count": 2, "stale_source_count": 0}
    }
    example_record["projections_summary"]["p10"] = 20.0
    example_record["projections_summary"]["p50"] = 35.0
    example_record["projections_summary"]["p90"] = 48.0
    example_record["candidate_plans"][0]["points_distribution"] = {
        "p10": 23.0,
        "p50": 35.0,
        "p90": 48.0,
        "mean": 35.5,
    }
    html = render_gdr_html(example_record)
    assert "DEGRADED" in html
    assert "capture_missed:T-2h" in html
    assert "P10=23.0" in html
    assert "P50=35.0" in html
    assert 'data-status="DEGRADED"' in html


def test_accessibility_headings_table_and_status_text(example_record: dict) -> None:
    html = render_gdr_html(example_record)
    for heading in (
        "Cutoff, rules and provenance",
        "Freshness and degraded state",
        "Recommendation",
        "Candidate plans",
        "Evidence",
        "Validation",
    ):
        assert heading in html
    assert "<caption>" in html
    assert 'scope="col"' in html
    assert "status-text" in html
    assert "[OK]" in html or "data-status=" in html


def test_season_index_lists_records(tmp_path: Path, example_record: dict) -> None:
    gw = tmp_path / "2025-26-gw02"
    gw.mkdir()
    (gw / "decision-record.json").write_text(
        json.dumps(example_record, indent=2) + "\n", encoding="utf-8"
    )
    write_gdr_html(example_record, gw / "decision-record.html")
    entries = scan_gameweek_records(tmp_path)
    assert len(entries) == 1
    assert entries[0]["gameweek"] == 2
    index = render_season_index_html(entries)
    assert "gdr_skeleton_gw3" in index
    assert "not attached" in index
    assert "<caption>" in index


def test_missing_record_id_refused() -> None:
    with pytest.raises(GdrHtmlError):
        render_gdr_html({"gameweek": 1})
