from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.orchestration.genuine_replay as replay_module
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.genuine_replay import (
    GenuineReplayError,
    prepare_historical_gameweek,
)
from src.orchestration.policy_state import POLICY_ARMS


REPO = Path(__file__).resolve().parents[2]
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
GW1 = REPO / "reports" / "benchmarks" / "2025-26" / "gw-01"


def _require_local_data() -> None:
    if not (EPISODES / "gw-02" / "episode-manifest.json").exists():
        pytest.skip("local immutable GW2 episode is unavailable")


def _prepare(output_root: Path) -> dict:
    return prepare_historical_gameweek(
        season="2025-26",
        gameweek=2,
        episode_root=EPISODES,
        previous_checkpoint_dir=GW1,
        output_root=output_root,
        code_commit="b" * 40,
    )


def test_gw2_setup_is_shared_sealed_and_not_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_local_data()
    requested_paths: list[Path] = []
    original_read = replay_module._read_json

    def audited_read(path: Path) -> dict:
        requested_paths.append(path)
        return original_read(path)

    monkeypatch.setattr(replay_module, "_read_json", audited_read)

    summary = _prepare(tmp_path)
    setup = tmp_path / "gw-02" / "setup"

    assert summary["status"] == "prepared_review_blocked"
    assert summary["outcome_access"] == "sealed_not_loaded"
    assert summary["contains_hidden_outcome"] is False
    assert summary["contains_validated_plan"] is False
    assert summary["contains_state_transition"] is False
    assert summary["shared_engine_input"] is True
    assert summary["candidate_count"] > 0
    assert summary["projection_diagnostics"] == {
        "model_version": "historical-rolling-v1",
        "completed_history_gameweeks": [1],
        "history_gameweek_count": 1,
        "configured_rolling_window": 3,
        "maximum_player_expected_points": 17.0,
        "cold_start_risk": "severe_single_gameweek_outcome_chasing",
        "freeze_recommendation": "blocked_pending_prior_or_shrinkage_policy",
    }
    assert not [
        path for path in requested_paths if path.name == "hidden-outcome.json"
    ]
    assert not (tmp_path / "gw-02" / "hidden-outcome.json").exists()
    assert not list(setup.rglob("realised-outcome.json"))
    assert not list(setup.rglob("validated-plan.json"))
    assert not list(setup.rglob("state-transition.json"))

    state_hashes = set()
    engine_hashes = set()
    for arm in POLICY_ARMS:
        arm_dir = setup / "arms" / arm
        state = json.loads(
            (arm_dir / "starting-policy-state.json").read_text(encoding="utf-8")
        )
        brief = json.loads(
            (arm_dir / "decision-brief.json").read_text(encoding="utf-8")
        )
        assert state["policy_arm"] == arm
        assert state["gameweek"] == 2
        assert brief["proposal_frozen"] is False
        assert brief["outcome_access"] == "sealed_not_loaded"
        state_hashes.add(state["content_sha256"])
        engine_hashes.add(brief["solver_input_sha256"])

    assert len(state_hashes) == len(POLICY_ARMS)
    assert len(engine_hashes) == 1


def test_gw2_setup_reproduces(tmp_path: Path) -> None:
    _require_local_data()

    assert _prepare(tmp_path / "one") == _prepare(tmp_path / "two")


def test_setup_refuses_unreviewed_gw3(tmp_path: Path) -> None:
    with pytest.raises(GenuineReplayError, match="Gameweek 2 only"):
        prepare_historical_gameweek(
            season="2025-26",
            gameweek=3,
            episode_root=EPISODES,
            previous_checkpoint_dir=GW1,
            output_root=tmp_path,
            code_commit="b" * 40,
        )


def test_checked_in_reliability_comparison_remains_sealed_and_unfrozen() -> None:
    setup = REPO / "reports" / "benchmarks" / "2025-26" / "gw-02" / "setup"
    comparison_path = setup / "forecast-reliability-comparison.json"
    review_path = setup / "reliability-review.json"
    if not comparison_path.exists():
        pytest.skip("checked-in reliability comparison is unavailable")
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert comparison["content_sha256"] == artifact_hash(comparison)
    assert review["content_sha256"] == artifact_hash(review)
    for artifact in (comparison, review):
        assert artifact["contains_hidden_outcome"] is False
        assert artifact["contains_validated_plan"] is False
        assert artifact["contains_state_transition"] is False
    assert review["reliability_calibrated"]["maximum_expected_points"] < 17
    assert review["reliability_calibrated"]["hit_cost"] == 0
    assert review["assessment"]["freeze_recommendation"].startswith("remain_unfrozen")


def test_feature_complete_comparison_resets_all_promoted_teams_and_stays_sealed() -> None:
    setup = REPO / "reports" / "benchmarks" / "2025-26" / "gw-02" / "setup"
    comparison = json.loads(
        (setup / "forecast-feature-complete-comparison.json").read_text(
            encoding="utf-8"
        )
    )
    review = json.loads(
        (setup / "feature-complete-review.json").read_text(encoding="utf-8")
    )
    assert comparison["content_sha256"] == artifact_hash(comparison)
    assert review["content_sha256"] == artifact_hash(review)
    assert comparison["forecast_diagnostics"]["team_fallbacks"] == [
        "team:2025-26:11",
        "team:2025-26:17",
        "team:2025-26:3",
    ]
    assert review["sealed_gw2"]["promoted_fallback_teams"] == [
        "Burnley",
        "Leeds",
        "Sunderland",
    ]
    assert comparison["forecast_diagnostics"]["event_model_weight"] == 0
    assert comparison["forecast_diagnostics"]["recent_minutes_weight"] == 0.5
    assert review["contains_hidden_outcome"] is False
    assert review["contains_validated_plan"] is False
    assert review["contains_state_transition"] is False
