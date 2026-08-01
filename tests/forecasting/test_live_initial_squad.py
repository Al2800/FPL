"""Contracts for the live-faithful initial-squad horizon adapter."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.live_initial_squad import (
    LiveInitialSquadForecastError,
    build_live_faithful_initial_squad_horizon,
    build_official_fdr_team_prior,
)
from src.orchestration.initial_squad_checkpoint import build_initial_squad_packet
from src.scoring.rules_loader import load_rules, ruleset_sha256


ROOT = Path(__file__).resolve().parents[2]
MODEL = json.loads(
    (ROOT / "control/models/live-faithful-v1.feature-complete.json").read_text(
        encoding="utf-8"
    )
)


def _fallback(position: str) -> dict[str, float]:
    return {
        "points_per_90": 4.0,
        "start_probability": 0.8,
        "minutes_per_start": 80.0,
        "expected_goals_per_90": 0.1 if position in {"MID", "FWD"} else 0.02,
        "expected_assists_per_90": 0.08 if position in {"MID", "FWD"} else 0.03,
        "clean_sheets_per_90": 0.2 if position in {"GKP", "DEF"} else 0.05,
        "saves_per_90": 0.5 if position == "GKP" else 0.0,
        "bonus_per_90": 0.2,
        "yellow_cards_per_90": 0.1,
        "red_cards_per_90": 0.0,
        "sample_minutes": 900.0,
        "sample_fixtures": 10.0,
    }


def _player_prior(season: str = "2024-25") -> dict:
    fallbacks = {}
    for position in ("GKP", "DEF", "MID", "FWD"):
        fallbacks[position] = _fallback(position)
        for band in ("0-5.5", "5.5-7.5", "7.5-10", "10-20"):
            fallbacks[f"{position}:{band}"] = _fallback(position)
    result = {
        "schema_version": "1.0",
        "season": season,
        "as_of": "2025-05-26T00:00:00Z",
        "source": {"test": True},
        "price_bands": MODEL["price_bands"],
        "players": [],
        "fallbacks": fallbacks,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _bootstrap() -> dict:
    return {
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
                "web_name": "Midfielder",
                "element_type": 3,
                "team": 2,
                "now_cost": 60,
                "status": "a",
                "ep_next": "5.0",
            },
        ],
        "teams": [
            {"id": 1, "name": "Home"},
            {"id": 2, "name": "Away"},
        ],
    }


def _fixtures() -> list[dict]:
    return [
        {
            "id": 1,
            "event": 1,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 5,
        },
        {
            "id": 2,
            "event": 2,
            "team_h": 2,
            "team_a": 1,
            "team_h_difficulty": 4,
            "team_a_difficulty": 1,
        },
    ]


def test_official_fdr_prior_is_hash_bound_and_explicit() -> None:
    prior = build_official_fdr_team_prior(
        fixtures=_fixtures(),
        observed_at="2026-07-31T08:00:00Z",
        source_sha256="a" * 64,
        season="2026-27",
    )
    assert prior["content_sha256"] == artifact_hash(prior)
    assert prior["model"]["type"] == "official_fdr_baseline"
    by_key = {
        (row["fixture_id"], row["club_id"]): row
        for row in prior["fixture_adjustments"]
    }
    assert by_key[(1, "1")]["attack_multiplier"] == 1.15
    assert by_key[(1, "2")]["attack_multiplier"] == 0.7
    assert by_key[(2, "1")]["attack_multiplier"] == 1.3


def test_live_faithful_horizon_materialises_vectors_and_lineage() -> None:
    result = build_live_faithful_initial_squad_horizon(
        bootstrap=_bootstrap(),
        fixtures=_fixtures(),
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-07-31T08:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1, 2],
        player_prior=_player_prior(),
        model_config=MODEL,
        launch_context_status="unavailable",
    )
    assert result["content_sha256"] == artifact_hash(result)
    assert result["model_config_id"] == "live-faithful-v1.feature-complete"
    assert result["status"] == "degraded"
    assert "official_fdr_team_prior_baseline" in result["limitations"]
    assert "historical_player_prior_2024_25" in result["limitations"]
    assert len(result["gameweek_forecast_hashes"]) == 2
    for vector in result["player_vectors"].values():
        assert len(vector["expected_points"]) == 2
        assert len(vector["start_probability"]) == 2
        assert len(vector["uncertainty"]) == 2
        assert all(0.0 <= value <= 1.0 for value in vector["start_probability"])


def test_horizon_labels_the_actual_player_prior_season() -> None:
    result = build_live_faithful_initial_squad_horizon(
        bootstrap=_bootstrap(),
        fixtures=_fixtures(),
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-07-31T08:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1],
        player_prior=_player_prior("2025-26"),
        model_config=MODEL,
    )

    assert "historical_player_prior_2025_26" in result["limitations"]
    assert "historical_player_prior_2024_25" not in result["limitations"]


def test_missing_fdr_does_not_invent_a_team_adjustment() -> None:
    fixtures = deepcopy(_fixtures())
    del fixtures[0]["team_h_difficulty"]
    with pytest.raises(LiveInitialSquadForecastError, match="difficulty"):
        build_live_faithful_initial_squad_horizon(
            bootstrap=_bootstrap(),
            fixtures=fixtures,
            official_bootstrap_sha256="a" * 64,
            official_fixtures_sha256="b" * 64,
            observed_at="2026-07-31T08:00:00Z",
            decision_cutoff="2026-08-21T17:30:00Z",
            horizon_gameweeks=[1, 2],
            player_prior=_player_prior(),
            model_config=MODEL,
        )


def test_initial_squad_packet_uses_live_faithful_vectors_when_available() -> None:
    positions = [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4]
    elements = [
        {
            "id": index,
            "code": 10_000 + index,
            "web_name": f"Player {index}",
            "element_type": position,
            "team": 1 if index % 2 else 2,
            "now_cost": 45,
            "status": "a",
            "ep_next": "4.0",
            "chance_of_playing_next_round": None,
        }
        for index, position in enumerate(positions, start=1)
    ]
    bootstrap = {
        "elements": elements,
        "teams": [{"id": 1, "name": "Home"}, {"id": 2, "name": "Away"}],
    }
    fixtures = [
        {
            "id": gameweek,
            "event": gameweek,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2 if gameweek % 2 else 4,
            "team_a_difficulty": 5 if gameweek % 2 else 1,
        }
        for gameweek in range(1, 7)
    ]
    rules_path = ROOT / "control/rules/2026-27.yaml"
    rules = load_rules(rules_path)
    verified = {
        "manifest": {
            "season": "2026-27",
            "checkpoint_id": "weekly-2026-07-31",
            "content_sha256": "c" * 64,
        },
        "manifest_path": ROOT / "control/manifests/2026-27-preseason.json",
        "bootstrap": bootstrap,
        "fixtures": fixtures,
        "observed_at": "2026-07-31T08:00:00Z",
        "available_at": "2026-07-31T08:00:00Z",
        "deadline": "2026-08-21T17:30:00Z",
        "family_states": {
            "official_bootstrap": {
                "state": "admitted",
                "artifact_sha256": "a" * 64,
            },
            "official_fixtures": {
                "state": "admitted",
                "artifact_sha256": "b" * 64,
            },
            "launch_context": {"state": "unavailable"},
        },
        "bound_paths": {},
    }
    result = build_initial_squad_packet(
        verified,
        policy=json.loads(
            (ROOT / "control/policies/initial-squad-2026-27.json").read_text(
                encoding="utf-8"
            )
        ),
        rules=rules,
        rules_hash=ruleset_sha256(rules_path),
    )
    assert result["packet"]["forecast_model_version"] == (
        "live-faithful-v1.feature-complete"
    )
    assert result["forecast_quality"]["status"] == "live_faithful_degraded"
    assert result["forecast_quality"]["manual_entry_eligible"] is False
    assert result["live_faithful_horizon"]["content_sha256"] == artifact_hash(
        result["live_faithful_horizon"]
    )
    assert all(
        len(player["expected_points"]) == 6
        for player in result["packet"]["players"]
    )


def test_understat_player_rates_do_not_move_ep_when_event_weight_zero() -> None:
    prior = _player_prior()
    prior["players"] = [
        {
            "fpl_code": 1002,
            "position": "MID",
            "points_per_90": 5.0,
            "start_probability": 0.85,
            "minutes_per_start": 80.0,
            "expected_goals_per_90": 0.1,
            "expected_assists_per_90": 0.1,
            "clean_sheets_per_90": 0.05,
            "saves_per_90": 0.0,
            "bonus_per_90": 0.2,
            "yellow_cards_per_90": 0.1,
            "red_cards_per_90": 0.0,
            "sample_minutes": 900,
            "sample_fixtures": 10,
        }
    ]
    prior["content_sha256"] = artifact_hash(prior)
    match = {
        "id": "1",
        "isResult": True,
        "datetime": "2025-08-15 15:00:00",
        "h": {"id": "1", "title": "Arsenal"},
        "a": {"id": "2", "title": "Chelsea"},
        "xG": {"h": "1.5", "a": "1.0"},
    }
    base_capture = {
        "schema_version": "understat-epl-capture-v1",
        "source_id": "understat",
        "season": "2025",
        "client": "test",
        "matches": [match],
        "players": [],
    }
    enriched_capture = {
        **base_capture,
        "players": [
            {
                "id": "9",
                "player_name": "Midfielder Player",
                "team_title": "Chelsea",
                "time": "900",
                "xG": "20.0",
                "xA": "15.0",
            }
        ],
    }
    bootstrap = _bootstrap()
    bootstrap["teams"] = [
        {"id": 1, "name": "Arsenal"},
        {"id": 2, "name": "Chelsea"},
    ]
    bootstrap["elements"][1]["first_name"] = "Midfielder"
    bootstrap["elements"][1]["second_name"] = "Player"
    bootstrap["elements"][0]["first_name"] = "Keeper"
    bootstrap["elements"][0]["second_name"] = "One"

    control = build_live_faithful_initial_squad_horizon(
        bootstrap=bootstrap,
        fixtures=_fixtures(),
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-07-31T08:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1, 2],
        player_prior=prior,
        model_config=MODEL,
        understat_capture=base_capture,
    )
    treated = build_live_faithful_initial_squad_horizon(
        bootstrap=bootstrap,
        fixtures=_fixtures(),
        official_bootstrap_sha256="a" * 64,
        official_fixtures_sha256="b" * 64,
        observed_at="2026-07-31T08:00:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        horizon_gameweeks=[1, 2],
        player_prior=prior,
        model_config=MODEL,
        understat_capture=enriched_capture,
    )
    assert MODEL["event_model_weight"] == 0.0
    assert (
        treated["lineage"]["understat_player_event_rates"]["players_enriched"] >= 1
    )
    assert control["lineage"]["team_prior_sha256"] == treated["lineage"][
        "team_prior_sha256"
    ]
    for player_id, vector in control["player_vectors"].items():
        assert vector["expected_points"] == treated["player_vectors"][player_id][
            "expected_points"
        ]


def test_challenger_event_weight_can_raise_without_prompt_edits() -> None:
    challenger = deepcopy(MODEL)
    challenger["event_model_weight"] = 0.25
    challenger.pop("content_sha256", None)
    challenger["content_sha256"] = artifact_hash(challenger)
    assert challenger["event_model_weight"] == 0.25
    assert challenger["content_sha256"] != MODEL["content_sha256"]
