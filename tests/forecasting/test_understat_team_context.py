"""Contracts for Understat / ClubElo → attack/defence team-prior adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.live_initial_squad import build_live_faithful_initial_squad_horizon
from src.forecasting.team_prior import EloParameters
from src.forecasting.understat_team_context import (
    UnderstatTeamContextError,
    build_understat_attack_defence_team_prior,
    clubelo_expected_scores,
    load_clubelo_ratings_csv,
    understat_match_observations,
)


ROOT = Path(__file__).resolve().parents[2]


def _capture() -> dict:
    return {
        "schema_version": "understat-epl-capture-v1",
        "source_id": "understat",
        "client": "https://github.com/collinb9/understatAPI",
        "season": "2025",
        "observed_at": "2026-08-01T13:41:32Z",
        "available_at": "2026-08-01T13:41:32Z",
        "counts": {"matches": 2, "players": 0, "teams": 2},
        "matches": [
            {
                "id": "1",
                "isResult": True,
                "datetime": "2025-08-15 19:00:00",
                "h": {"id": "87", "title": "Liverpool"},
                "a": {"id": "73", "title": "Bournemouth"},
                "xG": {"h": "2.3", "a": "1.1"},
            },
            {
                "id": "2",
                "isResult": True,
                "datetime": "2025-08-16 15:00:00",
                "h": {"id": "83", "title": "Arsenal"},
                "a": {"id": "80", "title": "Burnley"},
                "xG": {"h": "1.8", "a": "0.4"},
            },
            {
                "id": "3",
                "isResult": False,
                "datetime": "2026-08-20 15:00:00",
                "h": {"id": "87", "title": "Liverpool"},
                "a": {"id": "89", "title": "Manchester City"},
                "xG": {"h": "0", "a": "0"},
            },
        ],
    }


def _bootstrap() -> dict:
    return {
        "teams": [
            {"id": 3, "name": "Bournemouth"},
            {"id": 7, "name": "Coventry City"},
            {"id": 14, "name": "Liverpool"},
            {"id": 15, "name": "Man City"},
            {"id": 1, "name": "Arsenal"},
        ],
        "elements": [
            {
                "id": 1,
                "code": 1001,
                "web_name": "Keeper",
                "element_type": 1,
                "team": 14,
                "now_cost": 50,
                "status": "a",
                "ep_next": "3.0",
            },
            {
                "id": 2,
                "code": 1002,
                "web_name": "Forward",
                "element_type": 4,
                "team": 3,
                "now_cost": 70,
                "status": "a",
                "ep_next": "5.0",
            },
        ],
    }


def _player_prior() -> dict:
    from src.forecasting.live_faithful import artifact_hash as _hash
    import json

    model = json.loads(
        (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
            encoding="utf-8"
        )
    )
    fallback = {
        "points_per_90": 4.0,
        "start_probability": 0.8,
        "minutes_per_start": 80.0,
        "expected_goals_per_90": 0.1,
        "expected_assists_per_90": 0.08,
        "clean_sheets_per_90": 0.2,
        "saves_per_90": 0.5,
        "bonus_per_90": 0.2,
        "yellow_cards_per_90": 0.1,
        "red_cards_per_90": 0.0,
        "sample_minutes": 900.0,
        "sample_fixtures": 10.0,
    }
    fallbacks = {}
    for position in ("GKP", "DEF", "MID", "FWD"):
        fallbacks[position] = dict(fallback)
        for band in ("0-5.5", "5.5-7.5", "7.5-10", "10-20"):
            fallbacks[f"{position}:{band}"] = dict(fallback)
    result = {
        "schema_version": "1.0",
        "season": "2025-26",
        "as_of": "2025-05-26T00:00:00Z",
        "source": {"test": True},
        "price_bands": model["price_bands"],
        "players": [],
        "fallbacks": fallbacks,
    }
    result["content_sha256"] = _hash(result)
    return result


def test_understat_observations_skip_unmapped_and_non_results() -> None:
    observations, meta = understat_match_observations(
        _capture(), cutoff="2026-08-02T10:00:00Z"
    )
    assert len(observations) == 1
    assert observations[0]["home_team"] == "Liverpool"
    assert observations[0]["away_team"] == "Bournemouth"
    assert meta["skipped_unmapped_sides"] == 1
    assert meta["skipped_not_result"] == 1


def test_build_understat_prior_marks_promoted_cold_start() -> None:
    prior = build_understat_attack_defence_team_prior(
        bootstrap=_bootstrap(),
        fixtures=[
            {
                "id": 10,
                "event": 1,
                "team_h": 14,
                "team_a": 7,
            }
        ],
        understat_capture=_capture(),
        observed_at="2026-08-02T10:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        season="2026-27",
        promoted_team_names=["Coventry City"],
    )
    assert prior["model"]["type"] == "separate_attack_defence_xg"
    assert "7" in prior["fallback_teams"]
    assert prior["content_sha256"] == artifact_hash(prior)
    liv = next(row for row in prior["fixture_adjustments"] if row["club_id"] == "14")
    cov = next(row for row in prior["fixture_adjustments"] if row["club_id"] == "7")
    assert liv["attack_multiplier"] != cov["attack_multiplier"]


def test_clubelo_csv_maps_and_scores(tmp_path: Path) -> None:
    csv_path = tmp_path / "clubelo-ranking.csv"
    csv_path.write_text(
        "Rank,Club,Country,Level,Elo,From,To\n"
        "1,Liverpool,ENG,1,1910.0,2026-05-01,2026-08-21\n"
        "2,Coventry,ENG,1,1661.0,2026-05-01,2026-08-21\n"
        "3,Paris SG,FRA,1,1960.0,2026-05-01,2026-08-21\n",
        encoding="utf-8",
    )
    ratings, body_hash = load_clubelo_ratings_csv(csv_path)
    assert ratings["Liverpool"] == pytest.approx(1910.0)
    assert ratings["Coventry City"] == pytest.approx(1661.0)
    assert len(body_hash) == 64
    scores, missing = clubelo_expected_scores(
        fixtures=[
            {
                "fixture_id": 10,
                "home_club_id": "14",
                "away_club_id": "7",
            }
        ],
        team_name_by_club_id={"14": "Liverpool", "7": "Coventry City"},
        ratings_by_fpl_name=ratings,
        elo_params=EloParameters(
            k=40.0,
            home_advantage=80.0,
            draw_factor=0.6,
            promoted_rating=1450.0,
            season_regression=1.0,
        ),
    )
    assert missing == []
    assert scores[(10, "14")] > scores[(10, "7")]


def test_horizon_uses_understat_prior_when_capture_joins() -> None:
    import json

    model = json.loads(
        (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
            encoding="utf-8"
        )
    )
    result = build_live_faithful_initial_squad_horizon(
        bootstrap=_bootstrap(),
        fixtures=[
            {
                "id": 10,
                "event": 1,
                "team_h": 14,
                "team_a": 3,
                "team_h_difficulty": 2,
                "team_a_difficulty": 4,
            }
        ],
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-08-02T10:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1],
        player_prior=_player_prior(),
        model_config=model,
        understat_capture=_capture(),
        promoted_team_names=["Coventry City"],
    )
    assert "understat_attack_defence_team_prior" in result["limitations"]
    assert "official_fdr_team_prior_baseline" not in result["limitations"]
    assert result["lineage"]["team_prior_source"] == "understat_attack_defence"


def test_horizon_falls_back_to_fdr_when_capture_cannot_join() -> None:
    import json

    model = json.loads(
        (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
            encoding="utf-8"
        )
    )
    bootstrap = {
        "teams": [{"id": 1, "name": "Home"}, {"id": 2, "name": "Away"}],
        "elements": _bootstrap()["elements"],
    }
    bootstrap["elements"][0]["team"] = 1
    bootstrap["elements"][1]["team"] = 2
    result = build_live_faithful_initial_squad_horizon(
        bootstrap=bootstrap,
        fixtures=[
            {
                "id": 1,
                "event": 1,
                "team_h": 1,
                "team_a": 2,
                "team_h_difficulty": 2,
                "team_a_difficulty": 4,
            }
        ],
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-08-02T10:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1],
        player_prior=_player_prior(),
        model_config=model,
        understat_capture=_capture(),
    )
    assert "official_fdr_team_prior_baseline" in result["limitations"]
    assert "understat_team_prior_unavailable_fallback_fdr" in result["limitations"]


def test_empty_observations_fail_closed() -> None:
    with pytest.raises(UnderstatTeamContextError, match="no cutoff-safe"):
        understat_match_observations(
            {
                **_capture(),
                "matches": [
                    {
                        "id": "9",
                        "isResult": True,
                        "datetime": "2026-08-20 15:00:00",
                        "h": {"title": "Liverpool"},
                        "a": {"title": "Bournemouth"},
                        "xG": {"h": "1", "a": "1"},
                    }
                ],
            },
            cutoff="2026-08-02T10:00:00Z",
        )
