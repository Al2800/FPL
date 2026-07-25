"""Independent team attack/defence and source-governance tests."""

from __future__ import annotations

import pytest

from src.forecasting.calibrate_team_context import select_team_context_parameters
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.team_context_challenger import (
    fixture_specs,
    historical_xg_observations,
    reforecast_with_team_context,
)

from src.forecasting.team_attack_defence import (
    AttackDefenceParameters,
    TeamContextError,
    build_attack_defence_prior,
    eligible_odds_snapshot,
    estimate_team_strengths,
)


CUTOFF = "2025-08-20T12:00:00Z"
IDENTITIES = [
    {"team_name": "Strong", "club_id": "team:1"},
    {"team_name": "Weak", "club_id": "team:2"},
    {"team_name": "Promoted", "club_id": "team:3"},
]
OBSERVATIONS = [
    {
        "kickoff_time": "2025-08-10T15:00:00Z",
        "home_team": "Strong",
        "away_team": "Weak",
        "home_xg": 3.0,
        "away_xg": 0.3,
    },
    {
        "kickoff_time": "2025-08-17T15:00:00Z",
        "home_team": "Weak",
        "away_team": "Strong",
        "home_xg": 0.5,
        "away_xg": 2.5,
    },
]


def test_attack_and_defence_are_independent_and_hashed() -> None:
    prior = build_attack_defence_prior(
        season="2025-26",
        cutoff=CUTOFF,
        team_identities=IDENTITIES,
        fixtures=[
            {
                "fixture_id": 11,
                "home_club_id": "team:1",
                "away_club_id": "team:2",
            }
        ],
        observations=OBSERVATIONS,
        promoted_teams={"Promoted"},
        elo_expected_scores={(11, "team:1"): 0.7, (11, "team:2"): 0.3},
        params=AttackDefenceParameters(multiplier_max=2.0),
    )
    strong = next(
        row for row in prior["fixture_adjustments"] if row["club_id"] == "team:1"
    )
    weak = next(
        row for row in prior["fixture_adjustments"] if row["club_id"] == "team:2"
    )
    assert strong["attack_multiplier"] != strong["defence_multiplier"]
    assert strong["attack_multiplier"] > weak["attack_multiplier"]
    assert strong["defence_multiplier"] > weak["defence_multiplier"]
    assert prior["status"] == "degraded"
    assert prior["degraded_reasons"] == ["odds_absent"]
    assert prior["content_sha256"] == artifact_hash(prior)


def test_promoted_team_uses_explicit_cold_start() -> None:
    strengths = estimate_team_strengths(
        teams=["Strong", "Weak", "Promoted"],
        observations=OBSERVATIONS,
        cutoff=CUTOFF,
        promoted_teams={"Promoted"},
    )
    assert strengths["Promoted"]["promoted_cold_start"] is True
    assert strengths["Promoted"]["attack_xg"] == pytest.approx(1.35 * 0.85)
    assert strengths["Promoted"]["attack_xg"] < 1.35
    assert strengths["Promoted"]["defence_xga"] > 1.35


def test_future_observation_fails_closed() -> None:
    with pytest.raises(TeamContextError, match="strictly before cutoff"):
        estimate_team_strengths(
            teams=["Strong", "Weak"],
            observations=[
                {
                    **OBSERVATIONS[0],
                    "kickoff_time": CUTOFF,
                }
            ],
            cutoff=CUTOFF,
        )


def test_closing_or_late_odds_are_never_accepted() -> None:
    closing = {
        "timing_label": "closing_or_unspecified",
        "captured_at": "2025-08-19T12:00:00Z",
        "p_home": 0.5,
        "p_draw": 0.3,
        "p_away": 0.2,
    }
    assert eligible_odds_snapshot(closing, cutoff=CUTOFF) == (
        None,
        "odds_rejected_unregistered_timing",
    )
    late = {
        **closing,
        "timing_label": "registered_predeadline",
        "captured_at": CUTOFF,
    }
    assert eligible_odds_snapshot(late, cutoff=CUTOFF) == (
        None,
        "odds_rejected_at_or_after_cutoff",
    )
    accepted = {
        **late,
        "captured_at": "2025-08-20T11:59:59Z",
    }
    odds, status = eligible_odds_snapshot(accepted, cutoff=CUTOFF)
    assert status == "odds_accepted"
    assert odds == {"p_home": 0.5, "p_draw": 0.3, "p_away": 0.2}


def test_walk_forward_strength_uses_only_rows_before_each_cutoff() -> None:
    first = estimate_team_strengths(
        teams=["Strong", "Weak"],
        observations=OBSERVATIONS[:1],
        cutoff="2025-08-15T12:00:00Z",
    )
    second = estimate_team_strengths(
        teams=["Strong", "Weak"],
        observations=OBSERVATIONS,
        cutoff=CUTOFF,
    )
    assert first["Strong"]["matches"] == 1
    assert second["Strong"]["matches"] == 2
    assert second["Strong"]["attack_xg"] > first["Strong"]["attack_xg"]

def _player(player_id: str, position: str) -> dict:
    return {
        "player_id": player_id,
        "club_id": "team:1",
        "position": position,
        "start_probability": 0.9,
        "posterior_event_rates": {
            "expected_goals": 0.5,
            "expected_assists": 0.2,
            "clean_sheets": 0.4,
            "saves": 0.0,
            "bonus": 0.2,
            "yellow_cards": 0.1,
            "red_cards": 0.0,
        },
        "expected_points": 4.0,
        "fixture_components": [
            {
                "fixture_id": 11,
                "opponent_club_id": "team:2",
                "was_home": True,
                "expected_minutes": 80.0,
                "posterior_points_per_90": 4.0,
                "rate_expected_points": 4.0,
                "event_expected_points": 4.0,
                "event_model_weight": 0.0,
                "expected_points": 4.0,
            }
        ],
    }


def test_reforecast_routes_attack_and_defence_by_position() -> None:
    forecast = {
        "content_sha256": "a" * 64,
        "model_version": "live-faithful-v1",
        "model_status": "locked",
        "lineage": {"model_sha256": "b" * 64},
        "players": [_player("def", "DEF"), _player("fwd", "FWD")],
    }
    team_prior = {
        "content_sha256": "c" * 64,
        "fixture_adjustments": [
            {
                "fixture_id": 11,
                "club_id": "team:1",
                "attack_multiplier": 1.4,
                "defence_multiplier": 0.8,
            }
        ],
    }
    result = reforecast_with_team_context(forecast, team_prior)
    defender, forward = result["players"]
    assert defender["fixture_components"][0]["team_multiplier"] == 0.92
    assert forward["fixture_components"][0]["team_multiplier"] == 1.4
    assert defender["fixture_components"][0]["attack_multiplier"] == 1.4
    assert defender["fixture_components"][0]["defence_multiplier"] == 0.8
    assert result["content_sha256"] == artifact_hash(result)
    assert forecast["players"][0]["expected_points"] == 4.0


def test_fixture_and_xg_adapters_are_deterministic() -> None:
    forecast = {"players": [_player("def", "DEF"), _player("fwd", "FWD")]}
    assert fixture_specs(forecast) == [
        {
            "fixture_id": 11,
            "home_club_id": "team:1",
            "away_club_id": "team:2",
        }
    ]
    import pandas as pd

    rows = pd.DataFrame(
        [
            {"round": 1, "fixture": 5, "team": "Strong", "was_home": True, "kickoff_time": "2025-08-10T15:00:00Z", "expected_goals": 1.0},
            {"round": 1, "fixture": 5, "team": "Strong", "was_home": True, "kickoff_time": "2025-08-10T15:00:00Z", "expected_goals": 0.5},
            {"round": 1, "fixture": 5, "team": "Weak", "was_home": False, "kickoff_time": "2025-08-10T15:00:00Z", "expected_goals": 0.4},
            {"round": 2, "fixture": 15, "team": "Strong", "was_home": True, "kickoff_time": "2025-08-20T15:00:00Z", "expected_goals": 9.0},
        ]
    )
    assert historical_xg_observations(rows, before_gameweek=2) == [
        {
            "kickoff_time": "2025-08-10T15:00:00Z",
            "home_team": "Strong",
            "away_team": "Weak",
            "home_xg": 1.5,
            "away_xg": 0.4,
            "fixture_id": 5,
        }
    ]

def test_parameter_selection_keeps_validation_out_of_candidate_grid() -> None:
    import pandas as pd

    def season(home_xg: float, away_xg: float) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"round": 1, "fixture": 1, "team": "A", "was_home": True, "kickoff_time": "2024-08-01T15:00:00Z", "expected_goals": home_xg},
                {"round": 1, "fixture": 1, "team": "B", "was_home": False, "kickoff_time": "2024-08-01T15:00:00Z", "expected_goals": away_xg},
            ]
        )

    params, report = select_team_context_parameters(
        {
            "2022-23": season(1.0, 0.5),
            "2023-24": season(1.2, 0.6),
            "2024-25": season(9.0, 9.0),
        },
        training_seasons=("2022-23", "2023-24"),
        validation_season="2024-25",
    )
    assert isinstance(params, AttackDefenceParameters)
    assert report["forbidden_fit_seasons"] == ["2024-25", "2025-26"]
    assert "2024-25" in report["selected"]["metrics"]
    assert "2024-25" not in report["top_5"][0]["metrics"]

def test_materialised_team_context_decision_is_sealed_and_rejected() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    config = json.loads(
        (root / "control/models/live-faithful-v2.team-context.json").read_text(
            encoding="utf-8"
        )
    )
    report = json.loads(
        (root / "reports/forecasting/live-faithful-v2-team-context/evaluation.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["content_sha256"] == artifact_hash(config)
    assert report["content_sha256"] == artifact_hash(report)
    assert config["source_policy"]["closing_or_unspecified_odds"] == "forbidden"
    assert config["calibration"]["forbidden_fit_seasons"] == ["2024-25", "2025-26"]
    assert report["out_of_sample"]["decision"] == "reject"
    assert not any(report["out_of_sample"]["promotion_rule"].values())
