"""Contracts for Odds API → team-prior snapshot projection."""

from __future__ import annotations

from src.forecasting.live_odds_team_prior import odds_snapshots_from_capture
from src.forecasting.team_attack_defence import (
    AttackDefenceParameters,
    build_attack_defence_prior,
    eligible_odds_snapshot,
)


SLOTS = {
    "T-24h": {
        "exclusive_minimum_lead_hours": 18.0,
        "inclusive_maximum_lead_hours": 30.0,
    }
}


def _capture(*, observed_at: str, cutoff: str, slot: str = "T-24h") -> dict:
    return {
        "status": "complete",
        "snapshot": {
            "source_id": "the-odds-api",
            "slot": slot,
            "observed_at": observed_at,
            "available_at": observed_at,
            "decision_cutoff": cutoff,
            "source_sha256": "abc",
            "payload": {
                "fixtures": [
                    {
                        "event_id": "e1",
                        "commence_time": "2026-08-21T19:00:00Z",
                        "home_team": "Arsenal",
                        "away_team": "Coventry City",
                    }
                ],
                "markets": [
                    {
                        "event_id": "e1",
                        "market_key": "h2h",
                        "home_team": "Arsenal",
                        "away_team": "Coventry City",
                        "bookmaker_key": "skybet",
                        "outcomes": [
                            {"name": "Arsenal", "price": 1.4},
                            {"name": "Draw", "price": 4.5},
                            {"name": "Coventry City", "price": 8.0},
                        ],
                    }
                ],
            },
        },
    }


def _bootstrap() -> dict:
    return {
        "teams": [
            {"id": 1, "name": "Arsenal"},
            {"id": 7, "name": "Coventry City"},
        ]
    }


def test_cutoff_safe_slot_maps_to_fixture_and_clears_odds_absent() -> None:
    snapshots, summary = odds_snapshots_from_capture(
        _capture(
            observed_at="2026-08-20T17:30:00Z",
            cutoff="2026-08-21T17:30:00Z",
        ),
        fixtures=[
            {
                "id": 1,
                "event": 1,
                "team_h": 1,
                "team_a": 7,
                "kickoff_time": "2026-08-21T19:00:00Z",
            }
        ],
        bootstrap=_bootstrap(),
        decision_cutoff="2026-08-21T17:30:00Z",
        slots_config=SLOTS,
    )
    assert summary["status"] == "applied"
    assert 1 in snapshots
    probs, status = eligible_odds_snapshot(
        snapshots[1], cutoff="2026-08-21T17:30:00Z"
    )
    assert status == "odds_accepted"
    assert probs is not None
    assert abs(sum(probs.values()) - 1.0) < 1e-6

    prior = build_attack_defence_prior(
        season="2026-27",
        # Team-prior as_of must be strictly after odds captured_at.
        cutoff="2026-08-20T18:00:00Z",
        team_identities=[
            {"team_name": "Arsenal", "club_id": "1"},
            {"team_name": "Coventry City", "club_id": "7"},
        ],
        fixtures=[{"fixture_id": 1, "home_club_id": "1", "away_club_id": "7"}],
        observations=[
            {
                "kickoff_time": "2025-08-15T15:00:00Z",
                "home_team": "Arsenal",
                "away_team": "Coventry City",
                "home_xg": 2.0,
                "away_xg": 0.5,
            }
        ],
        odds_snapshots=snapshots,
        params=AttackDefenceParameters(multiplier_max=2.0),
    )
    assert "odds_absent" not in prior["degraded_reasons"]
    arsenal = next(row for row in prior["fixture_adjustments"] if row["club_id"] == "1")
    assert "odds_expected_score" in arsenal


def test_outside_slot_window_degrades_cleanly() -> None:
    snapshots, summary = odds_snapshots_from_capture(
        _capture(
            observed_at="2026-08-01T13:36:26Z",
            cutoff="2026-08-02T13:36:26Z",
        ),
        fixtures=[
            {
                "id": 1,
                "event": 1,
                "team_h": 1,
                "team_a": 7,
                "kickoff_time": "2026-08-21T19:00:00Z",
            }
        ],
        bootstrap=_bootstrap(),
        decision_cutoff="2026-08-21T17:30:00Z",
        slots_config=SLOTS,
    )
    assert snapshots == {}
    assert summary["reason"] == "odds_rejected_outside_slot_window_for_decision_cutoff"
