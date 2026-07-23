from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.orchestration.genuine_replay import (
    GenuineReplayError,
    run_historical_replay,
)
from src.orchestration.policy_state import POLICY_ARMS


REPO = Path(__file__).resolve().parents[2]
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"


def _run(output_root: Path) -> dict:
    return run_historical_replay(
        season="2025-26",
        episode_root=EPISODES,
        output_root=output_root,
        start_gameweek=1,
        stop_after_gameweek=1,
        code_commit="a" * 40,
    )


def _require_local_episodes() -> None:
    if not (EPISODES / "gw-01" / "episode-manifest.json").exists():
        pytest.skip("immutable benchmark-v0 episode bundle is not present")


def test_gw1_checkpoint_is_shared_real_and_stops_before_gw2(
    tmp_path: Path,
) -> None:
    _require_local_episodes()

    summary = _run(tmp_path / "run")

    assert summary["run_mode"] == "genuine_historical_checkpoint"
    assert summary["decisions_completed_through_gameweek"] == 1
    assert summary["next_state_gameweek"] == 2
    assert summary["contains_next_gameweek_decision"] is False
    assert summary["shared_action_count"] == 1
    assert set(summary["arms"]) == set(POLICY_ARMS)
    assert not (tmp_path / "run" / "gw-02").exists()

    points = {
        (
            arm["gross_points"],
            arm["net_points"],
            arm["cumulative_points"],
        )
        for arm in summary["arms"].values()
    }
    assert len(points) == 1

    for arm in POLICY_ARMS:
        arm_dir = tmp_path / "run" / "gw-01" / arm
        state = json.loads(
            (arm_dir / "policy-state-before.json").read_text(encoding="utf-8")
        )
        plan = json.loads(
            (arm_dir / "validated-plan.json").read_text(encoding="utf-8")
        )
        outcome = json.loads(
            (arm_dir / "realised-outcome.json").read_text(encoding="utf-8")
        )
        transition = json.loads(
            (arm_dir / "state-transition.json").read_text(encoding="utf-8")
        )
        successor = json.loads(
            (arm_dir / "next-policy-state.json").read_text(encoding="utf-8")
        )

        assert state["policy_arm"] == arm
        assert plan["previous_state_sha256"] == state["content_sha256"]
        assert plan["lineup"]["captain_id"] == "player:2025-26:235"
        assert plan["lineup"]["vice_captain_id"] == "player:2025-26:381"
        assert outcome["plan_sha256"] == plan["content_sha256"]
        assert outcome["source_outcome_sha256"] == summary["hidden_outcome_sha256"]
        assert outcome["identity_map_sha256"] == summary["identity_map_sha256"]
        assert transition["proposal_sha256"] == plan["content_sha256"]
        assert transition["outcome_id"] == outcome["outcome_id"]
        assert transition["next_state_sha256"] == successor["content_sha256"]
        assert successor["policy_arm"] == arm
        assert successor["gameweek"] == 2
        assert successor["cumulative_points"] == transition["net_points"]


def test_gw1_checkpoint_is_reproducible(tmp_path: Path) -> None:
    _require_local_episodes()

    first = _run(tmp_path / "first")
    second = _run(tmp_path / "second")

    assert second == first


def test_checkpoint_refuses_to_cross_unreviewed_gameweek_boundary(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        GenuineReplayError,
        match="implements Gameweek 1 only",
    ):
        run_historical_replay(
            season="2025-26",
            episode_root=EPISODES,
            output_root=tmp_path / "run",
            start_gameweek=1,
            stop_after_gameweek=2,
            code_commit="a" * 40,
        )


def test_documented_module_cli_writes_the_gw1_checkpoint(
    tmp_path: Path,
) -> None:
    _require_local_episodes()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.run_replay",
            "--season",
            "2025-26",
            "--start-gameweek",
            "1",
            "--stop-after-gameweek",
            "1",
            "--episode-root",
            str(EPISODES),
            "--out",
            str(tmp_path / "cli-run"),
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(completed.stdout)
    assert summary["decisions_completed_through_gameweek"] == 1
    assert (tmp_path / "cli-run" / "gw-01" / "run-summary.json").exists()
    assert not (tmp_path / "cli-run" / "gw-02").exists()
