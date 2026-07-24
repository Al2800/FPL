from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

import src.orchestration.genuine_replay as replay_module
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


def _run_through_gw2(output_root: Path) -> dict:
    _run(output_root)
    return run_historical_replay(
        season="2025-26",
        episode_root=EPISODES,
        output_root=output_root,
        start_gameweek=2,
        stop_after_gameweek=2,
        code_commit="a" * 40,
    )


def _run_through_gw3(output_root: Path) -> dict:
    _run_through_gw2(output_root)
    return run_historical_replay(
        season="2025-26",
        episode_root=EPISODES,
        output_root=output_root,
        start_gameweek=3,
        stop_after_gameweek=3,
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
        assert state["free_transfers"] == 0
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
        assert successor["free_transfers"] == 1
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
        match="exactly one Gameweek at a time",
    ):
        run_historical_replay(
            season="2025-26",
            episode_root=EPISODES,
            output_root=tmp_path / "run",
            start_gameweek=1,
            stop_after_gameweek=2,
            code_commit="a" * 40,
        )


def test_gw2_checkpoint_freezes_then_reveals_and_advances_independent_states(
    tmp_path: Path,
) -> None:
    _require_local_episodes()

    summary = _run_through_gw2(tmp_path / "run")

    assert summary["decisions_completed_through_gameweek"] == 2
    assert summary["next_state_gameweek"] == 3
    assert summary["contains_next_gameweek_decision"] is False
    assert summary["shared_action_count"] == 1
    assert set(summary["arms"]) == set(POLICY_ARMS)
    assert {row["gross_points"] for row in summary["arms"].values()} == {59}
    assert {row["cumulative_points"] for row in summary["arms"].values()} == {
        115
    }
    assert {row["free_transfers"] for row in summary["arms"].values()} == {2}
    assert len(
        {row["next_state_sha256"] for row in summary["arms"].values()}
    ) == len(POLICY_ARMS)
    assert not (tmp_path / "run" / "gw-03").exists()

    for arm in POLICY_ARMS:
        arm_dir = tmp_path / "run" / "gw-02" / arm
        state = json.loads(
            (arm_dir / "policy-state-before.json").read_text(encoding="utf-8")
        )
        plan = json.loads(
            (arm_dir / "validated-plan.json").read_text(encoding="utf-8")
        )
        outcome = json.loads(
            (arm_dir / "realised-outcome.json").read_text(encoding="utf-8")
        )
        successor = json.loads(
            (arm_dir / "next-policy-state.json").read_text(encoding="utf-8")
        )
        assert plan["previous_state_sha256"] == state["content_sha256"]
        assert plan["transfers"] == []
        assert plan["lineup"]["captain_id"] == "player:2025-26:381"
        assert plan["frozen_at"] < outcome["revealed_at"]
        assert outcome["plan_sha256"] == plan["content_sha256"]
        assert successor["previous_state_sha256"] == state["content_sha256"]
        assert successor["policy_arm"] == arm
        assert successor["gameweek"] == 3
        assert successor["free_transfers"] == 2


def test_gw2_hidden_partition_cannot_open_until_every_arm_is_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened = False

    def forbidden_load(_: Path) -> dict:
        nonlocal opened
        opened = True
        return {}

    monkeypatch.setattr(replay_module, "_load_episode", forbidden_load)
    with pytest.raises(GenuineReplayError, match="every policy arm"):
        replay_module._load_outcomes_after_all_plans_freeze(
            tmp_path,
            frozen_plans={},
        )
    assert opened is False


def test_gw2_persists_every_frozen_plan_before_hidden_outcome_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_local_episodes()
    output_root = tmp_path / "run"
    _run(output_root)
    original_read = replay_module._read_json
    audited = False

    def audited_read(path: Path) -> dict:
        nonlocal audited
        if path.name == "hidden-outcome.json" and path.parent.name == "gw-02":
            audited = True
            for arm in POLICY_ARMS:
                assert (
                    output_root / "gw-02" / arm / "validated-plan.json"
                ).exists()
        return original_read(path)

    monkeypatch.setattr(replay_module, "_read_json", audited_read)
    run_historical_replay(
        season="2025-26",
        episode_root=EPISODES,
        output_root=output_root,
        start_gameweek=2,
        stop_after_gameweek=2,
        code_commit="a" * 40,
    )

    assert audited is True


def test_gw2_checkpoint_is_reproducible(tmp_path: Path) -> None:
    _require_local_episodes()

    first = _run_through_gw2(tmp_path / "first")
    second = _run_through_gw2(tmp_path / "second")

    assert second == first


def test_gw3_checkpoint_consumes_reviewed_arm_setups_and_stops_before_gw4(
    tmp_path: Path,
) -> None:
    _require_local_episodes()

    summary = _run_through_gw3(tmp_path / "run")

    assert summary["decisions_completed_through_gameweek"] == 3
    assert summary["next_state_gameweek"] == 4
    assert summary["contains_next_gameweek_decision"] is False
    assert summary["shared_action_count"] == 1
    assert set(summary["arms"]) == set(POLICY_ARMS)
    assert len(
        {row["next_state_sha256"] for row in summary["arms"].values()}
    ) == len(POLICY_ARMS)
    assert set(summary["reviewed_solver_input_sha256_by_arm"]) == set(
        POLICY_ARMS
    )
    assert set(summary["reviewed_solver_output_sha256_by_arm"]) == set(
        POLICY_ARMS
    )
    assert not (tmp_path / "run" / "gw-04").exists()

    for arm in POLICY_ARMS:
        arm_dir = tmp_path / "run" / "gw-03" / arm
        state = json.loads(
            (arm_dir / "policy-state-before.json").read_text(encoding="utf-8")
        )
        plan = json.loads(
            (arm_dir / "validated-plan.json").read_text(encoding="utf-8")
        )
        outcome = json.loads(
            (arm_dir / "realised-outcome.json").read_text(encoding="utf-8")
        )
        successor = json.loads(
            (arm_dir / "next-policy-state.json").read_text(encoding="utf-8")
        )
        assert plan["previous_state_sha256"] == state["content_sha256"]
        assert plan["transfers"] == []
        assert plan["lineup"]["captain_id"] == "player:2025-26:381"
        assert plan["lineup"]["vice_captain_id"] == "player:2025-26:249"
        assert plan["frozen_at"] < outcome["revealed_at"]
        assert outcome["plan_sha256"] == plan["content_sha256"]
        assert successor["previous_state_sha256"] == state["content_sha256"]
        assert successor["policy_arm"] == arm
        assert successor["gameweek"] == 4
        assert successor["free_transfers"] == 3


def test_gw3_persists_every_frozen_plan_before_hidden_outcome_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_local_episodes()
    output_root = tmp_path / "run"
    _run_through_gw2(output_root)
    original_read = replay_module._read_json
    audited = False

    def audited_read(path: Path) -> dict:
        nonlocal audited
        if path.name == "hidden-outcome.json" and path.parent.name == "gw-03":
            audited = True
            for arm in POLICY_ARMS:
                assert (
                    output_root / "gw-03" / arm / "validated-plan.json"
                ).exists()
        return original_read(path)

    monkeypatch.setattr(replay_module, "_read_json", audited_read)
    run_historical_replay(
        season="2025-26",
        episode_root=EPISODES,
        output_root=output_root,
        start_gameweek=3,
        stop_after_gameweek=3,
        code_commit="a" * 40,
    )

    assert audited is True


def test_gw3_checkpoint_is_reproducible(tmp_path: Path) -> None:
    _require_local_episodes()

    first = _run_through_gw3(tmp_path / "first")
    second = _run_through_gw3(tmp_path / "second")

    assert second == first


def test_gw3_refuses_to_run_without_the_gw2_handoff(tmp_path: Path) -> None:
    _require_local_episodes()

    with pytest.raises(
        GenuineReplayError,
        match="Required replay artefact is missing",
    ):
        run_historical_replay(
            season="2025-26",
            episode_root=EPISODES,
            output_root=tmp_path / "run",
            start_gameweek=3,
            stop_after_gameweek=3,
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
