"""Contracts for fixture audit, availability blend, set-pieces and gap panel."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evidence.availability_ledger import (
    append_availability_claim,
    new_availability_ledger,
)
from src.forecasting.initial_squad_context import (
    attach_set_piece_roles,
    blend_availability_into_horizon_players,
    bounded_fixture_audit_view,
    build_gap_panel,
)
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.live_initial_squad import build_live_faithful_initial_squad_horizon


ROOT = Path(__file__).resolve().parents[2]
MODEL = json.loads(
    (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
        encoding="utf-8"
    )
)


def _player_prior() -> dict:
    fallback = {
        "points_per_90": 4.0,
        "start_probability": 0.8,
        "minutes_per_start": 80.0,
        "expected_goals_per_90": 0.1,
        "expected_assists_per_90": 0.08,
        "clean_sheets_per_90": 0.05,
        "saves_per_90": 0.0,
        "bonus_per_90": 0.2,
        "yellow_cards_per_90": 0.1,
        "red_cards_per_90": 0.0,
        "sample_minutes": 900.0,
        "sample_fixtures": 10.0,
    }
    fallbacks = {position: deepcopy(fallback) for position in ("GKP", "DEF", "MID", "FWD")}
    for position in ("GKP", "DEF", "MID", "FWD"):
        for band in ("0-5.5", "5.5-7.5", "7.5-10", "10-20"):
            fallbacks[f"{position}:{band}"] = deepcopy(fallback)
    result = {
        "schema_version": "1.0",
        "season": "2025-26",
        "as_of": "2025-05-26T00:00:00Z",
        "source": {"test": True},
        "price_bands": MODEL["price_bands"],
        "players": [],
        "fallbacks": fallbacks,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _bootstrap_and_fixtures() -> tuple[dict, list[dict]]:
    bootstrap = {
        "elements": [
            {
                "id": 1,
                "code": 1001,
                "web_name": "Keeper",
                "element_type": 1,
                "team": 1,
                "now_cost": 50,
                "status": "a",
                "ep_next": "3.0",
            },
            {
                "id": 2,
                "code": 1002,
                "web_name": "Forward",
                "element_type": 4,
                "team": 2,
                "now_cost": 70,
                "status": "a",
                "ep_next": "5.0",
            },
        ],
        "teams": [{"id": 1, "name": "Home"}, {"id": 2, "name": "Away"}],
    }
    fixtures = [
        {
            "id": 1,
            "event": 1,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 5,
            "kickoff_time": "2026-08-21T19:00:00Z",
        },
        {
            "id": 2,
            "event": 2,
            "team_h": 2,
            "team_a": 1,
            "team_h_difficulty": 4,
            "team_a_difficulty": 1,
            "kickoff_time": "2026-08-28T19:00:00Z",
        },
    ]
    return bootstrap, fixtures


def test_fixture_audit_has_opponents_and_blank_double_markers() -> None:
    bootstrap, fixtures = _bootstrap_and_fixtures()
    horizon = build_live_faithful_initial_squad_horizon(
        bootstrap=bootstrap,
        fixtures=fixtures,
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-07-31T08:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1, 2],
        player_prior=_player_prior(),
        model_config=MODEL,
    )
    audit = horizon["fixture_audit"]
    assert audit["content_sha256"] == artifact_hash(audit)
    home = audit["players"]["1"]
    assert home["gameweeks"][0]["blank"] is False
    assert home["gameweeks"][0]["double"] is False
    assert home["gameweeks"][0]["fixtures"][0]["opponent_name"] == "Away"
    assert home["gameweeks"][0]["fixtures"][0]["was_home"] is True
    assert home["gameweeks"][0]["fixtures"][0]["fdr"] == 2
    view = bounded_fixture_audit_view(audit, player_ids=["1"])
    assert set(view["players"]) == {"1"}
    assert view["content_sha256"] == artifact_hash(view)


def test_availability_blend_depresses_doubtful_and_leaves_others() -> None:
    players = [
        {
            "player_id": "40",
            "web_name": "Rogers",
            "club_id": "6",
            "expected_points": [5.0, 5.0],
            "start_probability": [0.9, 0.9],
            "uncertainty": [0.1, 0.1],
        },
        {
            "player_id": "2",
            "web_name": "Other",
            "club_id": "1",
            "expected_points": [4.0, 4.0],
            "start_probability": [0.8, 0.8],
            "uncertainty": [0.2, 0.2],
        },
    ]
    unchanged = deepcopy(players[1])
    ledger = new_availability_ledger(
        season="2026-27",
        created_at="2026-08-01T09:00:00Z",
    )
    claim = {
        "claim_id": "rogers-doubtful",
        "player_uid": "player:2026-27:40",
        "status": "doubtful",
        "confidence": 0.8,
        "published_at": "2026-08-01T09:00:00Z",
        "observed_at": "2026-08-01T09:00:00Z",
        "available_at": "2026-08-01T09:00:00Z",
        "expires_at": "2026-09-01T00:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
        },
    }
    ledger = append_availability_claim(ledger, claim)
    blended, audit = blend_availability_into_horizon_players(
        players,
        ledger=ledger,
        season="2026-27",
        as_of="2026-08-02T10:00:00Z",
        fixtures=[
            {
                "id": 1,
                "event": 1,
                "team_h": 6,
                "team_a": 1,
                "kickoff_time": "2026-08-21T19:00:00Z",
            },
            {
                "id": 2,
                "event": 2,
                "team_h": 1,
                "team_a": 6,
                "kickoff_time": "2026-08-28T19:00:00Z",
            },
        ],
        horizon_gameweeks=[1, 2],
        trust_admitted_ledger=True,
    )
    assert audit["status"] == "applied"
    rogers = next(row for row in blended if row["player_id"] == "40")
    other = next(row for row in blended if row["player_id"] == "2")
    assert rogers["start_probability"][0] == pytest.approx(0.65)
    assert rogers["expected_points"][0] < 5.0
    assert other["start_probability"] == unchanged["start_probability"]
    assert other["expected_points"] == unchanged["expected_points"]


def test_mid_horizon_expiry_cuts_later_gameweeks() -> None:
    players = [
        {
            "player_id": "40",
            "web_name": "Rogers",
            "club_id": "6",
            "expected_points": [5.0, 5.0],
            "start_probability": [0.9, 0.9],
            "uncertainty": [0.1, 0.1],
        }
    ]
    ledger = new_availability_ledger(
        season="2026-27",
        created_at="2026-08-01T09:00:00Z",
    )
    claim = {
        "claim_id": "rogers-mid",
        "player_uid": "player:2026-27:40",
        "status": "doubtful",
        "confidence": 0.8,
        "published_at": "2026-08-01T09:00:00Z",
        "observed_at": "2026-08-01T09:00:00Z",
        "available_at": "2026-08-01T09:00:00Z",
        "expires_at": "2026-08-25T00:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
        },
    }
    ledger = append_availability_claim(ledger, claim)
    blended, audit = blend_availability_into_horizon_players(
        players,
        ledger=ledger,
        season="2026-27",
        as_of="2026-08-02T10:00:00Z",
        fixtures=[
            {
                "id": 1,
                "event": 1,
                "team_h": 6,
                "team_a": 1,
                "kickoff_time": "2026-08-21T19:00:00Z",
            },
            {
                "id": 2,
                "event": 2,
                "team_h": 1,
                "team_a": 6,
                "kickoff_time": "2026-08-28T19:00:00Z",
            },
        ],
        horizon_gameweeks=[1, 2],
        trust_admitted_ledger=True,
    )
    assert audit["status"] == "applied"
    row = blended[0]
    assert row["start_probability"][0] == pytest.approx(0.65)
    assert row["start_probability"][1] == pytest.approx(0.9)


def test_set_piece_surface_does_not_change_ep() -> None:
    players = [
        {
            "player_id": "13",
            "web_name": "Rice",
            "expected_points": [3.0, 3.0],
            "start_probability": [0.9, 0.9],
            "uncertainty": [0.1, 0.1],
        }
    ]
    before = deepcopy(players[0]["expected_points"])
    artifact = {
        "effect_weights": None,
        "promotion_status": "shadow_only_pending_point_in_time_ablation",
        "ledger": {
            "content_sha256": "a" * 64,
            "active_roles": [
                {
                    "official_player_id": 13,
                    "role": "penalty",
                    "rank": 1,
                    "confidence": 0.5,
                    "expires_at": "2026-08-10T10:00:00Z",
                    "observation_id": "obs",
                }
            ],
        },
    }
    tagged, summary = attach_set_piece_roles(players, set_pieces_artifact=artifact)
    assert summary["status"] == "applied"
    assert tagged[0]["expected_points"] == before
    assert tagged[0]["set_piece_roles"]["roles"][0]["role"] == "penalty"
    assert summary["effect_weights"] is None


def test_gap_panel_records_degraded_families() -> None:
    panel = build_gap_panel(
        source_families={
            "licensed_odds": {
                "state": "unavailable",
                "manifest_status": "degraded",
                "reasons": ["optional_licensed_odds_not_configured"],
                "artifact_sha256": None,
            },
            "player_ratings": {
                "state": "unavailable",
                "manifest_status": "degraded",
                "reasons": ["optional_player_ratings_not_supplied"],
                "artifact_sha256": None,
            },
            "availability_role_evidence": {
                "state": "admitted",
                "manifest_status": "admitted",
                "reasons": [],
                "artifact_sha256": "b" * 64,
            },
            "set_pieces": {
                "state": "admitted",
                "manifest_status": "admitted",
                "reasons": [],
                "artifact_sha256": "c" * 64,
            },
            "official_bootstrap": {"state": "admitted"},
            "official_fixtures": {"state": "admitted"},
            "transfers_and_signings": {"state": "unavailable"},
            "promoted_team_priors": {"state": "unavailable"},
            "launch_context": {"state": "admitted"},
            "world_cup_return_fatigue": {"state": "admitted"},
        },
        forecast_limitations=["timestamped_odds_absent"],
        availability_blend={"status": "applied"},
        odds_summary={"status": "absent", "reason": "odds_absent"},
        set_piece_summary={
            "status": "applied",
            "effect_weights": None,
            "promotion_status": "shadow_only_pending_point_in_time_ablation",
        },
        fixture_audit_sha256="d" * 64,
    )
    assert panel["content_sha256"] == artifact_hash(panel)
    assert panel["families"]["licensed_odds"]["integration"] == "odds_absent"
    assert (
        panel["families"]["availability_role_evidence"]["integration"]
        == "blended_into_start_probability"
    )
    assert panel["families"]["set_pieces"]["effect_weights"] is None
