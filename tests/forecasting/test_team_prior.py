"""Tests for longitudinal Elo and episode-safe team priors."""

from __future__ import annotations

import pandas as pd
import pytest

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.team_prior import (
    EloParameters,
    TeamPriorError,
    build_episode_team_prior,
    attach_pre_match_elo_scores,
    fit_longitudinal_elo,
)


PARAMS = EloParameters(20, 60, 0.8, 1450, 0.75)


def test_longitudinal_elo_carries_and_regresses_ratings() -> None:
    first = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2023-08-01"]),
            "HomeTeam": ["A"],
            "AwayTeam": ["B"],
            "FTHG": [3],
            "FTAG": [0],
        }
    )
    second = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-08-01"]),
            "HomeTeam": ["A"],
            "AwayTeam": ["C"],
            "FTHG": [1],
            "FTAG": [1],
        }
    )
    _, forecasts = fit_longitudinal_elo(
        [("2023-24", first), ("2024-25", second)],
        PARAMS,
    )
    assert forecasts.iloc[1]["home_rating_pre"] > 1450
    assert forecasts.iloc[1]["away_rating_pre"] == 1450


def test_episode_prior_marks_promoted_fallback_and_is_hashed() -> None:
    identity = {
        "teams": [
            {"fpl_team_id": 1, "fpl_name": "A", "canonical_id": "team:a"},
            {"fpl_team_id": 2, "fpl_name": "C", "canonical_id": "team:c"},
        ]
    }
    result = build_episode_team_prior(
        season="2025-26",
        cutoff="2025-08-22T17:30:00Z",
        identity_map=identity,
        fixtures=[{"id": 11, "team_h": 1, "team_a": 2}],
        prior_match_results=[],
        previous_ratings={"A": 1550},
        params=PARAMS,
        lineage={"source": "test"},
    )
    assert result["fallback_teams"] == ["team:c"]
    assert len(result["fixture_adjustments"]) == 2
    assert result["content_sha256"] == artifact_hash(result)


def test_same_or_post_cutoff_result_fails_closed() -> None:
    identity = {
        "teams": [
            {"fpl_team_id": 1, "fpl_name": "A", "canonical_id": "team:a"},
            {"fpl_team_id": 2, "fpl_name": "B", "canonical_id": "team:b"},
        ]
    }
    with pytest.raises(TeamPriorError, match="strictly before cutoff"):
        build_episode_team_prior(
            season="2025-26",
            cutoff="2025-08-22T17:30:00Z",
            identity_map=identity,
            fixtures=[],
            prior_match_results=[
                {
                    "kickoff_time": "2025-08-22T17:30:00Z",
                    "home_team_name": "A",
                    "away_team_name": "B",
                    "home_goals": 1,
                    "away_goals": 0,
                }
            ],
            previous_ratings={"A": 1500, "B": 1500},
            params=PARAMS,
            lineage={},
        )


def test_player_fixtures_join_pre_match_scores_by_date_and_alias() -> None:
    players = pd.DataFrame(
        {
            "kickoff_time": ["2024-08-01T15:00:00Z"],
            "team": ["Spurs"],
            "element": [1],
        }
    )
    forecasts = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-08-01"]),
            "HomeTeam": ["Tottenham"],
            "AwayTeam": ["Arsenal"],
            "p_home": [0.5],
            "p_draw": [0.3],
            "p_away": [0.2],
        }
    )
    joined = attach_pre_match_elo_scores(players, forecasts)
    assert joined["expected_result_score"].iloc[0] == 0.65
