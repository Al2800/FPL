"""Tests for Rotowire / official lineup evidence consolidation (ticket 19)."""

from __future__ import annotations

from src.evidence.lineup_consolidator import (
    consolidate_lineup_evidence,
    evaluate_trial_admission,
    load_trial_policy,
)


def _aliases() -> dict:
    return {
        "aliases": [
            {
                "entity_type": "fixture",
                "provider_id": "rotowire-lineups",
                "provider_entity_id": "rw:fx1",
                "fpl_entity_id": "fixture:1",
            },
            {
                "entity_type": "player",
                "provider_id": "rotowire-lineups",
                "provider_entity_id": "rw:p1",
                "fpl_entity_id": "101",
            },
            {
                "entity_type": "player",
                "provider_id": "rotowire-lineups",
                "provider_entity_id": "rw:p2",
                "fpl_entity_id": "102",
            },
            {
                "entity_type": "fixture",
                "provider_id": "official-team-sheets",
                "provider_entity_id": "ots:fx1",
                "fpl_entity_id": "fixture:1",
            },
            {
                "entity_type": "player",
                "provider_id": "official-team-sheets",
                "provider_entity_id": "ots:p1",
                "fpl_entity_id": "101",
            },
            {
                "entity_type": "player",
                "provider_id": "official-team-sheets",
                "provider_entity_id": "ots:p2",
                "fpl_entity_id": "102",
            },
        ]
    }


def _rotowire_pack() -> dict:
    xi = [
        {
            "provider_player_id": "rw:p1",
            "name": "Starter",
            "slot": "FW",
            "status": "expected",
            "started": True,
            "role": "starting_xi",
        },
        {
            "provider_player_id": "rw:p2",
            "name": "Also",
            "slot": "MID",
            "status": "expected",
            "started": True,
            "role": "starting_xi",
        },
    ]
    # Pad to satisfy pack shape locally without full 11 — consolidator reads rows as listed.
    return {
        "source_id": "rotowire-lineups",
        "fixtures": [
            {
                "provider_fixture_id": "rw:fx1",
                "home_xi": xi,
                "away_xi": [],
                "home_injury_notes": [],
                "away_injury_notes": [],
            }
        ],
    }


def test_load_trial_policy() -> None:
    policy = load_trial_policy()
    assert policy["live_influence_default"] is False
    assert policy["never_average_feeds"] is True


def test_official_wins_and_disagreement_is_quarantined() -> None:
    official = [
        {
            "provider_fixture_id": "ots:fx1",
            "players": [
                {
                    "provider_player_id": "ots:p1",
                    "started": False,
                },
                {
                    "provider_player_id": "ots:p2",
                    "started": True,
                },
            ],
        }
    ]
    result = consolidate_lineup_evidence(
        fpl_availability=[
            {"fpl_player_id": "101", "chance_of_playing": 100, "status": "a"},
            {"fpl_player_id": "102", "chance_of_playing": 100, "status": "a"},
        ],
        aliases=_aliases(),
        rotowire_pack=_rotowire_pack(),
        official_snapshots=official,
        observed_at="2026-08-05T12:00:00Z",
        decision_cutoff="2026-08-21T17:00:00Z",
        live_influence_admitted=False,
    )
    by_id = {row["fpl_player_id"]: row for row in result["players"] if row["fpl_fixture_id"]}
    assert by_id["101"]["selected_source"] == "official-team-sheets"
    assert by_id["101"]["predicted_started"] is False
    assert by_id["101"]["shadow_only"] is True
    assert result["disagreement_count"] >= 1
    assert result["quarantined_count"] >= 1
    assert result["live_influence_admitted"] is False


def test_trial_admission_fails_closed_on_insufficient_sample() -> None:
    verdict = evaluate_trial_admission(
        {
            "fixture_coverage": 1.0,
            "identity_match_rate": 1.0,
            "brier_improvement_vs_chance_of_playing": 0.1,
            "brier_improvement_vs_started_last_gw": 0.1,
            "confirmed_minutes_mae": 5.0,
            "citation_latency_hours": 1.0,
            "scored_fixtures": 1,
            "matchdays": 1,
        }
    )
    assert verdict["live_influence_admitted"] is False
    assert verdict["negative_result_recorded"] is True
    assert any(
        row["metric"] == "scored_fixtures" and row["ok"] is False
        for row in verdict["checks"]
    )
