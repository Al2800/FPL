from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.prepare_replay_gameweek as replay_setup
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.policy_state import POLICY_ARMS
from scripts.prepare_replay_gameweek import prepare


REPO = Path(__file__).resolve().parents[2]
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
GW2 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-02"
GW3 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-03"


def _require_local_data() -> None:
    required = [
        EPISODES / "gw-03" / "episode-manifest.json",
        REPO
        / "data"
        / "raw"
        / "vaastav"
        / "Fantasy-Premier-League"
        / "data"
        / "2024-25"
        / "players_raw.csv",
    ]
    if not all(path.exists() for path in required):
        pytest.skip("local replay/training data is unavailable")


def test_gw3_locked_forecast_setup_is_sealed_state_bound_and_reproducible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_local_data()
    requested: list[Path] = []
    original_read = replay_setup._read

    def audited_read(path: Path) -> dict:
        requested.append(path)
        return original_read(path)

    monkeypatch.setattr(replay_setup, "_read", audited_read)
    summary = prepare(
        season="2025-26",
        gameweek=3,
        episode_root=EPISODES,
        output_root=tmp_path,
        previous_checkpoint_dir=GW2,
        code_commit="c" * 40,
    )

    assert summary["content_sha256"] == artifact_hash(summary)
    assert summary["status"] == "sealed_setup_awaiting_human_review"
    assert summary["contains_hidden_outcome"] is False
    assert summary["contains_validated_plan"] is False
    assert summary["contains_state_transition"] is False
    assert summary["shared_forecast"] is True
    assert summary["shared_solver_input"] is True
    assert summary["shared_solver_output"] is True
    assert summary["forecast_diagnostics"]["maximum_expected_points"] == 8.71
    assert "historical_player_availability_status_unavailable" in summary[
        "limitations"
    ]
    assert not [path for path in requested if path.name == "hidden-outcome.json"]
    assert set(summary["arms"]) == set(POLICY_ARMS)
    assert len(
        {row["state_sha256"] for row in summary["arms"].values()}
    ) == len(POLICY_ARMS)
    assert len(
        {row["solver_input_sha256"] for row in summary["arms"].values()}
    ) == 1
    for arm, row in summary["arms"].items():
        assert row["selected"]["transfer_count"] == 0
        assert row["selected"]["captain_name"] == "Mohamed Salah"
        assert row["selected"]["next_gameweek_free_transfers"] == 4
        review = json.loads(
            (
                tmp_path
                / "gw-03"
                / "setup"
                / "arms"
                / arm
                / "forecast-plan-review.json"
            ).read_text(encoding="utf-8")
        )
        assert review["content_sha256"] == artifact_hash(review)
        assert review["state_sha256"] == row["state_sha256"]


def test_gw4_review_records_the_policy_candidate_each_arm_will_freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_local_data()
    requested: list[Path] = []
    original_read = replay_setup._read

    def audited_read(path: Path) -> dict:
        requested.append(path)
        return original_read(path)

    monkeypatch.setattr(replay_setup, "_read", audited_read)
    summary = prepare(
        season="2025-26",
        gameweek=4,
        episode_root=EPISODES,
        output_root=tmp_path,
        previous_checkpoint_dir=GW3,
        code_commit="d" * 40,
    )

    naive = summary["arms"]["naive_baseline"]["selected"]
    optimizer = summary["arms"]["forecast_optimizer"]["selected"]
    assert naive["transfer_count"] == 0
    assert naive["next_gameweek_free_transfers"] == 5
    assert optimizer["transfer_count"] == 2
    assert optimizer["next_gameweek_free_transfers"] == 3
    assert {
        (move["player_out_name"], move["player_in_name"])
        for move in optimizer["transfers"]
    } == {
        ("Cole Palmer", "Cody Gakpo"),
        ("Elliot Anderson", "Dominik Szoboszlai"),
    }
    assert not [path for path in requested if path.name == "hidden-outcome.json"]
