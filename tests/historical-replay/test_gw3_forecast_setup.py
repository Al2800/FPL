from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.prepare_replay_gameweek as replay_setup
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint
from src.orchestration.genuine_replay import (
    GenuineReplayError,
    _load_reviewed_gameweek_setup,
)
from src.orchestration.policy_state import POLICY_ARMS
from src.orchestration.replay_payload_store import (
    is_payload_ref,
    payload_path,
    resolve_reviewed_payload,
)
from scripts.prepare_replay_gameweek import prepare


REPO = Path(__file__).resolve().parents[2]
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
GW2 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-02"
GW3 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-03"
GW4 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-04"


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


def test_terminal_gameweek_zeroes_future_transfer_probability() -> None:
    assert replay_setup._extra_transfer_probability_for_gameweek(37) == (
        replay_setup.PROBABILITY_EXTRA_TRANSFER_NEEDED
    )
    assert (
        replay_setup._extra_transfer_probability_for_gameweek(38) == 0.0
    )


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
        assert row["selected"]["next_gameweek_free_transfers"] == 3
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


def test_gw3_checked_in_legacy_inline_payloads_still_load() -> None:
    setup = GW3 / "setup"
    previous_summary = json.loads(
        (GW2 / "run-summary.json").read_text(encoding="utf-8")
    )
    feature_state, states, solver_inputs, solver_outputs = (
        _load_reviewed_gameweek_setup(
            setup,
            season="2025-26",
            gameweek=3,
            previous_summary=previous_summary,
        )
    )
    assert set(states) == set(POLICY_ARMS)
    shared_input_hash = fingerprint(next(iter(solver_inputs.values())))
    assert all(
        fingerprint(value) == shared_input_hash for value in solver_inputs.values()
    )
    for arm in POLICY_ARMS:
        arm_dir = setup / "arms" / arm
        inline = json.loads(
            (arm_dir / "reviewed-engine-input.json").read_text(encoding="utf-8")
        )
        assert not is_payload_ref(inline)
        assert resolve_reviewed_payload(arm_dir, "solver_input") == inline


def test_prepare_writes_content_addressed_payload_store_once_per_hash(
    tmp_path: Path,
) -> None:
    _require_local_data()
    summary = prepare(
        season="2025-26",
        gameweek=3,
        episode_root=EPISODES,
        output_root=tmp_path,
        previous_checkpoint_dir=GW2,
        code_commit="e" * 40,
    )
    setup = tmp_path / "gw-03" / "setup"
    manifest = summary["payload_store"]
    assert manifest["unique_solver_inputs"] == 1
    assert manifest["unique_solver_outputs"] == 1
    assert manifest["content_sha256"] == artifact_hash(manifest)
    assert len(list((setup / "payloads" / "solver-input").glob("*.json"))) == 1
    assert len(list((setup / "payloads" / "solver-output").glob("*.json"))) == 1
    for arm in POLICY_ARMS:
        arm_dir = setup / "arms" / arm
        input_ref = json.loads(
            (arm_dir / "reviewed-engine-input.json").read_text(encoding="utf-8")
        )
        output_ref = json.loads(
            (arm_dir / "reviewed-engine-output.json").read_text(encoding="utf-8")
        )
        assert is_payload_ref(input_ref)
        assert is_payload_ref(output_ref)
        assert input_ref["payload_sha256"] == manifest["solver_inputs"][0]
        assert output_ref["payload_sha256"] == manifest["solver_outputs"][0]
        assert input_ref["content_sha256"] != input_ref["payload_sha256"]
        assert output_ref["content_sha256"] != output_ref["payload_sha256"]
        assert payload_path(
            setup, "solver_input", input_ref["payload_sha256"]
        ).exists()
        assert resolve_reviewed_payload(arm_dir, "solver_input")["gameweek"] == 3


def test_payload_store_rejects_hash_mismatch(tmp_path: Path) -> None:
    from src.orchestration.replay_payload_store import ReplayPayloadStoreError

    _require_local_data()
    prepare(
        season="2025-26",
        gameweek=3,
        episode_root=EPISODES,
        output_root=tmp_path,
        previous_checkpoint_dir=GW2,
        code_commit="f" * 40,
    )
    setup = tmp_path / "gw-03" / "setup"
    arm_dir = setup / "arms" / "naive_baseline"
    input_ref = json.loads(
        (arm_dir / "reviewed-engine-input.json").read_text(encoding="utf-8")
    )
    stored_path = payload_path(setup, "solver_input", input_ref["payload_sha256"])
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    stored["bank"] = round(float(stored["bank"]) + 0.1, 1)
    stored_path.write_text(json.dumps(stored, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ReplayPayloadStoreError, match="hash mismatch"):
        _load_reviewed_gameweek_setup(
            setup,
            season="2025-26",
            gameweek=3,
            previous_summary=json.loads(
                (GW2 / "run-summary.json").read_text(encoding="utf-8")
            ),
        )


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
    assert naive["next_gameweek_free_transfers"] == 4
    assert optimizer["transfer_count"] == 2
    assert optimizer["next_gameweek_free_transfers"] == 2
    assert {
        (move["player_out_name"], move["player_in_name"])
        for move in optimizer["transfers"]
    } == {
        ("Cole Palmer", "Cody Gakpo"),
        ("Elliot Anderson", "Dominik Szoboszlai"),
    }
    assert summary["payload_store"]["unique_solver_inputs"] == 1
    assert summary["payload_store"]["unique_solver_outputs"] == 1
    assert not [path for path in requested if path.name == "hidden-outcome.json"]
