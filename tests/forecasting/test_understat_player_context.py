"""Contracts for identity-safe Understat player event-rate joins."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.understat_player_context import (
    UnderstatPlayerContextError,
    build_understat_player_join,
    enrich_player_prior_with_understat_event_rates,
)


def _bootstrap() -> dict:
    return {
        "teams": [
            {"id": 1, "name": "Arsenal"},
            {"id": 6, "name": "Chelsea"},
            {"id": 2, "name": "Aston Villa"},
        ],
        "elements": [
            {
                "id": 10,
                "code": 2001,
                "web_name": "Saka",
                "first_name": "Bukayo",
                "second_name": "Saka",
                "team": 1,
                "element_type": 3,
            },
            {
                "id": 40,
                "code": 2002,
                "web_name": "Rogers",
                "first_name": "Morgan",
                "second_name": "Rogers",
                "team": 6,
                "element_type": 3,
            },
            {
                "id": 451,
                "code": 2003,
                "web_name": "A.Murphy",
                "first_name": "Alex",
                "second_name": "Murphy",
                "team": 1,
                "element_type": 2,
            },
            {
                "id": 457,
                "code": 2004,
                "web_name": "J.Murphy",
                "first_name": "Jacob",
                "second_name": "Murphy",
                "team": 1,
                "element_type": 3,
            },
        ],
    }


def _capture() -> dict:
    return {
        "schema_version": "understat-epl-capture-v1",
        "source_id": "understat",
        "season": "2025",
        "players": [
            {
                "id": "1",
                "player_name": "Bukayo Saka",
                "team_title": "Arsenal",
                "time": "900",
                "xG": "5.0",
                "xA": "4.0",
            },
            {
                "id": "2",
                "player_name": "Morgan Rogers",
                "team_title": "Aston Villa",
                "time": "1800",
                "xG": "8.0",
                "xA": "6.0",
            },
            {
                "id": "3",
                "player_name": "Jacob Murphy",
                "team_title": "Arsenal",
                "time": "450",
                "xG": "1.0",
                "xA": "1.0",
            },
            {
                "id": "4",
                "player_name": "Absent Star",
                "team_title": "West Ham",
                "time": "900",
                "xG": "10.0",
                "xA": "2.0",
            },
        ],
    }


def _player_prior() -> dict:
    result = {
        "schema_version": "1.0",
        "season": "2025-26",
        "as_of": "2025-05-26T00:00:00Z",
        "source": {"test": True},
        "price_bands": [[0.0, 20.0]],
        "players": [
            {
                "fpl_code": 2001,
                "position": "MID",
                "points_per_90": 5.0,
                "start_probability": 0.9,
                "minutes_per_start": 85.0,
                "expected_goals_per_90": 0.2,
                "expected_assists_per_90": 0.2,
                "clean_sheets_per_90": 0.1,
                "saves_per_90": 0.0,
                "bonus_per_90": 0.2,
                "yellow_cards_per_90": 0.1,
                "red_cards_per_90": 0.0,
                "sample_minutes": 900,
                "sample_fixtures": 10,
            },
            {
                "fpl_code": 2002,
                "position": "MID",
                "points_per_90": 4.5,
                "start_probability": 0.8,
                "minutes_per_start": 80.0,
                "expected_goals_per_90": 0.15,
                "expected_assists_per_90": 0.15,
                "clean_sheets_per_90": 0.1,
                "saves_per_90": 0.0,
                "bonus_per_90": 0.2,
                "yellow_cards_per_90": 0.1,
                "red_cards_per_90": 0.0,
                "sample_minutes": 1800,
                "sample_fixtures": 20,
            },
        ],
        "fallbacks": {},
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def test_join_matches_unique_and_quarantines_ambiguous() -> None:
    report = build_understat_player_join(
        bootstrap=_bootstrap(), understat_capture=_capture()
    )
    assert report["content_sha256"] == artifact_hash(report)
    assert report["counts"]["matched_unique_fpl_codes"] == 2
    assert report["counts"]["quarantined_ambiguous"] == 1
    assert report["counts"]["unmatched"] == 1
    saka = report["rates_by_fpl_code"]["2001"]
    assert saka["expected_goals_per_90"] == pytest.approx(0.5)
    assert saka["expected_assists_per_90"] == pytest.approx(0.4)
    rogers = report["rates_by_fpl_code"]["2002"]
    assert rogers["match_basis"] == "cross_club_unique_full_name"
    assert any(
        row["reason"] == "ambiguous_name_match" for row in report["quarantined"]
    )
    assert any(
        row["reason"] == "not_in_current_bootstrap_universe"
        for row in report["unmatched"]
    )


def test_enrichment_updates_event_rates_only() -> None:
    prior = _player_prior()
    before = deepcopy(prior)
    report = build_understat_player_join(
        bootstrap=_bootstrap(), understat_capture=_capture()
    )
    enriched, summary = enrich_player_prior_with_understat_event_rates(
        prior, join_report=report
    )
    assert summary["status"] in {"applied", "partial"}
    assert summary["players_enriched"] == 2
    by_code = {int(row["fpl_code"]): row for row in enriched["players"]}
    assert by_code[2001]["expected_goals_per_90"] == pytest.approx(0.5)
    assert by_code[2001]["points_per_90"] == before["players"][0]["points_per_90"]
    assert by_code[2001]["start_probability"] == before["players"][0]["start_probability"]
    assert enriched["content_sha256"] == artifact_hash(enriched)
    assert enriched["content_sha256"] != before["content_sha256"]


def test_malformed_players_fail_closed() -> None:
    with pytest.raises(UnderstatPlayerContextError, match="players must be a list"):
        build_understat_player_join(
            bootstrap=_bootstrap(),
            understat_capture={"players": {"bad": True}},
        )
