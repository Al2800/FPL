"""Fixture-state wiring into multiweek and chip future projections."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.data.fixture_state import build_fixture_revision_log
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.multiweek import MultiweekPlanningError, validate_horizon
from src.optimisation.types import SolverInput
from src.orchestration.multiweek_challenger import (
    MultiweekChallengerError,
    build_same_cutoff_horizon,
    build_same_cutoff_horizon_from_fixture_state,
)


ROOT = Path(__file__).resolve().parents[2]
SEASON = "2026-27"


def _fixture(
    fixture_id: int,
    event: int,
    home: int,
    away: int,
) -> dict[str, object]:
    return {
        "id": fixture_id,
        "event": event,
        "kickoff_time": f"2026-08-{14 + event:02d}T14:00:00Z",
        "provisional_start_time": False,
        "team_h": home,
        "team_a": away,
        "team_h_difficulty": 3,
        "team_a_difficulty": 3,
    }


def _revision_log() -> dict:
    original = [
        _fixture(10, 1, 1, 4),
        _fixture(11, 2, 1, 2),
        _fixture(12, 3, 1, 3),
    ]
    rescheduled = deepcopy(original)
    rescheduled[1]["event"] = 3
    rescheduled[1]["kickoff_time"] = "2026-08-30T14:00:00Z"
    return build_fixture_revision_log(
        [
            {
                "snapshot_id": "original",
                "observed_at": "2026-07-01T09:00:00Z",
                "fixtures": original,
            },
            {
                "snapshot_id": "rescheduled",
                "observed_at": "2026-07-15T09:00:00Z",
                "fixtures": rescheduled,
            },
        ],
        season=SEASON,
    )


def _base_input() -> dict:
    return {
        "season": SEASON,
        "gameweek": 1,
        "ruleset_id": "2026-27-v0.1",
        "bank": 95.0,
        "free_transfers": 1,
        "squad_player_ids": ["p1"],
        "players": [
            {
                "player_id": "p1",
                "position": "MID",
                "club_id": f"team:{SEASON}:1",
                "now_cost": 5.0,
                "purchase_price": 5.0,
                "expected_points": 2.6667,
                "expected_minutes": 60.0,
                "fixture_count": 1,
                "status": "a",
            }
        ],
    }


def _forecast() -> dict:
    value = {
        "season": SEASON,
        "gameweek": 1,
        "cutoff": "2026-07-15T09:00:00Z",
        "players": [
            {
                "player_id": "p1",
                "expected_minutes": 60.0,
                "expected_minutes_per_fixture": 60.0,
                "fixture_count": 1,
                "posterior_points_per_90": 4.0,
            }
        ],
    }
    value["content_sha256"] = artifact_hash(value)
    return value


def _config() -> dict:
    return {
        "fixture_projection": {
            "difficulty_multiplier": {
                str(value): 1.0 for value in range(1, 6)
            }
        }
    }


def test_live_projection_uses_zero_one_and_two_fixture_counts() -> None:
    revision_log = _revision_log()
    horizon = build_same_cutoff_horizon_from_fixture_state(
        base_input=_base_input(),
        locked_forecast=_forecast(),
        fixture_revision_log=revision_log,
        gameweeks=[1, 2, 3],
        feature_state_sha256="a" * 64,
        config=_config(),
    )

    player_weeks = [week["players"][0] for week in horizon]
    assert [row["fixture_count"] for row in player_weeks] == [1, 0, 2]
    assert [row["expected_minutes"] for row in player_weeks] == [60.0, 0.0, 120.0]
    assert player_weeks[1]["expected_points"] == 0.0
    assert player_weeks[2]["expected_points"] == pytest.approx(5.3333)
    assert horizon[1]["team_fixture_counts"][f"team:{SEASON}:1"] == 0
    assert horizon[2]["team_fixture_counts"][f"team:{SEASON}:1"] == 2
    assert len({week["fixture_state_sha256"] for week in horizon}) == 1
    assert horizon[2]["schedule_provenance"]["revision_log_sha256"] == (
        revision_log["content_sha256"]
    )

    validate_horizon(
        horizon,
        base_input=SolverInput.from_dict(_base_input()),
    )


def test_current_blank_uses_explicit_per_fixture_minutes_for_future_weeks() -> None:
    base = _base_input()
    base["gameweek"] = 2
    base["players"][0].update(
        {
            "expected_points": 0.0,
            "expected_minutes": 0.0,
            "fixture_count": 0,
        }
    )
    forecast = _forecast()
    forecast["gameweek"] = 2
    forecast["players"][0].update(
        {
            "expected_minutes": 0.0,
            "fixture_count": 0,
        }
    )
    forecast["content_sha256"] = artifact_hash(forecast)
    horizon = build_same_cutoff_horizon_from_fixture_state(
        base_input=base,
        locked_forecast=forecast,
        fixture_revision_log=_revision_log(),
        gameweeks=[2, 3, 4],
        feature_state_sha256="a" * 64,
        config=_config(),
    )
    assert [row["players"][0]["fixture_count"] for row in horizon] == [0, 2, 0]
    assert horizon[1]["players"][0]["expected_points"] == pytest.approx(5.3333)

    missing = deepcopy(forecast)
    missing["players"][0].pop("expected_minutes_per_fixture")
    missing["content_sha256"] = artifact_hash(missing)
    with pytest.raises(MultiweekChallengerError, match="lacks per-fixture minutes"):
        build_same_cutoff_horizon_from_fixture_state(
            base_input=base,
            locked_forecast=missing,
            fixture_revision_log=_revision_log(),
            gameweeks=[2, 3, 4],
            feature_state_sha256="a" * 64,
            config=_config(),
        )


def test_chip_future_projection_uses_the_same_fixture_state_contract() -> None:
    chip_config = json.loads(
        (ROOT / "control/policies/chip-v1.json").read_text(encoding="utf-8")
    )["future_projection"]
    horizon = build_same_cutoff_horizon_from_fixture_state(
        base_input=_base_input(),
        locked_forecast=_forecast(),
        fixture_revision_log=_revision_log(),
        gameweeks=[1, 2, 3],
        feature_state_sha256="a" * 64,
        config=chip_config,
    )

    assert [week["players"][0]["fixture_count"] for week in horizon] == [1, 0, 2]
    assert horizon[2]["players"][0]["expected_points"] > horizon[0]["players"][0][
        "expected_points"
    ]


def test_bound_horizon_refuses_count_or_component_mismatch() -> None:
    horizon = build_same_cutoff_horizon_from_fixture_state(
        base_input=_base_input(),
        locked_forecast=_forecast(),
        fixture_revision_log=_revision_log(),
        gameweeks=[1, 2, 3],
        feature_state_sha256="a" * 64,
        config=_config(),
    )
    tampered = deepcopy(horizon)
    tampered[2]["players"][0]["fixture_count"] = 1
    with pytest.raises(MultiweekPlanningError, match="count differs"):
        validate_horizon(
            tampered,
            base_input=SolverInput.from_dict(_base_input()),
        )

    fixture_weeks = [
        {
            "gameweek": week,
            "fixtures": [],
            "fixture_state_sha256": "b" * 64,
            "fixture_count_table_sha256": "c" * 64,
            "team_fixture_counts": {f"team:{SEASON}:1": 1},
            "schedule_provenance": {"source": "test"},
        }
        for week in (1, 2, 3)
    ]
    with pytest.raises(MultiweekChallengerError, match="fixture count mismatch"):
        build_same_cutoff_horizon(
            base_input=_base_input(),
            locked_forecast=_forecast(),
            fixture_weeks=fixture_weeks,
            feature_state_sha256="a" * 64,
            config=_config(),
        )
