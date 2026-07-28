from __future__ import annotations

from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.enhanced_season_replay import (
    ARM_IDS,
    _effects,
    _later_artifact_version,
    run_enhanced_season_replay,
)
from src.orchestration.evidence_fork import EvidenceForkError, _read


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "reports/benchmarks/2025-26-enhanced"
FIRST_CHECKPOINT_SHA256 = (
    "21a8f0fc8e426b55466b58eeffbe8ec09a7056247b68a91ab829534b0ae172e0"
)
SECOND_CHECKPOINT_SHA256 = (
    "58401799c19936939aff66caf5f332b29bb0c6bd339e353547f255ab08ea7846"
)
THIRD_CHECKPOINT_SHA256 = (
    "be2e5d45d4f7db41e5f7b71e077b57334f9406b066eff98849f359033f9e2d16"
)
FOURTH_CHECKPOINT_SHA256 = (
    "f69e3890193899634c74051706b3e4baf94bdf95c1eeb15ffd576387bc6ce5a7"
)


def _runner_kwargs() -> dict:
    return {
        "repo_root": ROOT,
        "canonical_root": ROOT / "reports/benchmarks/2025-26",
        "optimized_seed_root": (
            ROOT / "reports/benchmarks/2025-26-gw1-seed-counterfactual"
        ),
        "scout_evidence_root": (
            ROOT / "reports/benchmarks/2025-26-early-evidence"
        ),
        "enhanced_input_root": ROOT / "evals/episodes/enhanced/2025-26",
        "episode_root": ROOT / "data/benchmark-v0/episodes/v2/2025-26",
        "evidence_bundle_root": ROOT / "evals/evidence-forks/2025-26",
        "later_evidence_root": (
            ROOT / "reports/benchmarks/2025-26-agent-forks"
        ),
        "output_root": REPORT_ROOT,
    }


def test_gw1_gw5_checkpoint_remains_sealed_and_paused() -> None:
    checkpoint = _read(REPORT_ROOT / "checkpoints/gw-01-gw-05.json")
    assert checkpoint["content_sha256"] == artifact_hash(checkpoint)
    assert checkpoint["content_sha256"] == FIRST_CHECKPOINT_SHA256
    assert checkpoint["start_gameweek"] == 1
    assert checkpoint["stop_gameweek"] == 5
    assert checkpoint["next_gameweek"] == 6
    assert checkpoint["status"] == "paused_for_review"
    assert checkpoint["review_required_before_continuation"] is True
    assert checkpoint["arms"] == list(ARM_IDS)
    assert checkpoint["canonical_artifacts"]["unchanged"] is True
    assert (
        checkpoint["canonical_artifacts"]["tree_sha256_before"]
        == checkpoint["canonical_artifacts"]["tree_sha256_after"]
    )


def test_gw6_gw10_checkpoint_binds_predecessor_and_pauses() -> None:
    checkpoint = _read(REPORT_ROOT / "checkpoints/gw-06-gw-10.json")
    assert checkpoint["content_sha256"] == artifact_hash(checkpoint)
    assert checkpoint["start_gameweek"] == 6
    assert checkpoint["stop_gameweek"] == 10
    assert checkpoint["next_gameweek"] == 11
    assert checkpoint["status"] == "paused_for_review"
    assert checkpoint["predecessor_checkpoint"]["content_sha256"] == (
        FIRST_CHECKPOINT_SHA256
    )
    assert checkpoint["canonical_artifacts"]["unchanged"] is True
    assert (
        checkpoint["canonical_artifacts"]["tree_sha256_before"]
        == checkpoint["canonical_artifacts"]["tree_sha256_after"]
    )
    terminal = _read(REPORT_ROOT / "weeks/gw-10/comparison.json")
    for arm_id in ARM_IDS:
        assert checkpoint["season_to_date_totals"][arm_id][
            "terminal_cumulative_points"
        ] == terminal["arms"][arm_id]["cumulative_points"]


def test_gw11_gw15_checkpoint_binds_predecessor_and_pauses() -> None:
    checkpoint = _read(REPORT_ROOT / "checkpoints/gw-11-gw-15.json")
    assert checkpoint["content_sha256"] == artifact_hash(checkpoint)
    assert checkpoint["start_gameweek"] == 11
    assert checkpoint["stop_gameweek"] == 15
    assert checkpoint["next_gameweek"] == 16
    assert checkpoint["status"] == "paused_for_review"
    assert checkpoint["predecessor_checkpoint"]["content_sha256"] == (
        SECOND_CHECKPOINT_SHA256
    )
    assert checkpoint["canonical_artifacts"]["unchanged"] is True
    assert (
        checkpoint["canonical_artifacts"]["tree_sha256_before"]
        == checkpoint["canonical_artifacts"]["tree_sha256_after"]
    )
    terminal = _read(REPORT_ROOT / "weeks/gw-15/comparison.json")
    for arm_id in ARM_IDS:
        assert checkpoint["season_to_date_totals"][arm_id][
            "terminal_cumulative_points"
        ] == terminal["arms"][arm_id]["cumulative_points"]

def test_gw16_gw20_checkpoint_binds_predecessor_and_pauses() -> None:
    checkpoint = _read(REPORT_ROOT / "checkpoints/gw-16-gw-20.json")
    assert checkpoint["content_sha256"] == artifact_hash(checkpoint)
    assert checkpoint["start_gameweek"] == 16
    assert checkpoint["stop_gameweek"] == 20
    assert checkpoint["next_gameweek"] == 21
    assert checkpoint["status"] == "paused_for_review"
    assert checkpoint["predecessor_checkpoint"]["content_sha256"] == (
        THIRD_CHECKPOINT_SHA256
    )
    assert checkpoint["canonical_artifacts"]["unchanged"] is True
    assert (
        checkpoint["canonical_artifacts"]["tree_sha256_before"]
        == checkpoint["canonical_artifacts"]["tree_sha256_after"]
    )
    terminal = _read(REPORT_ROOT / "weeks/gw-20/comparison.json")
    for arm_id in ARM_IDS:
        assert checkpoint["season_to_date_totals"][arm_id][
            "terminal_cumulative_points"
        ] == terminal["arms"][arm_id]["cumulative_points"]


def test_gw21_gw25_checkpoint_binds_predecessor_and_pauses() -> None:
    checkpoint = _read(REPORT_ROOT / "checkpoints/gw-21-gw-25.json")
    assert checkpoint["content_sha256"] == artifact_hash(checkpoint)
    assert checkpoint["start_gameweek"] == 21
    assert checkpoint["stop_gameweek"] == 25
    assert checkpoint["next_gameweek"] == 26
    assert checkpoint["status"] == "paused_for_review"
    assert checkpoint["predecessor_checkpoint"]["content_sha256"] == (
        FOURTH_CHECKPOINT_SHA256
    )
    assert checkpoint["canonical_artifacts"]["unchanged"] is True
    terminal = _read(REPORT_ROOT / "weeks/gw-25/comparison.json")
    for arm_id in ARM_IDS:
        assert checkpoint["season_to_date_totals"][arm_id][
            "terminal_cumulative_points"
        ] == terminal["arms"][arm_id]["cumulative_points"]


def test_later_artifact_version_uses_only_accepted_namespaces() -> None:
    assert _later_artifact_version(19) == "sol-v1"
    assert _later_artifact_version(20) == "sol-v3"
    assert _later_artifact_version(21) == "sol-v3"
    assert _later_artifact_version(22) == "sol-v3"
    assert _later_artifact_version(23) == "sol-v2"
    assert _later_artifact_version(24) == "sol-v1"
    assert _later_artifact_version(25) == "sol-v3"

def test_each_week_has_identical_inputs_and_independent_continuous_state() -> None:
    previous = None
    state_paths: set[str] = set()
    for gameweek in range(1, 26):
        week = _read(
            REPORT_ROOT / f"weeks/gw-{gameweek:02d}/comparison.json"
        )
        assert week["content_sha256"] == artifact_hash(week)
        assert set(week["arms"]) == set(ARM_IDS)
        assert len(set(week["identical_input_binding"].values())) == 1
        assert (
            next(iter(week["identical_input_binding"].values()))
            == week["enhanced_input"]["content_sha256"]
        )
        for arm_id, arm in week["arms"].items():
            state_paths.add(arm["artifacts"]["next_state"]["path"])
            assert arm["transfer_count"] == len(arm["transfers"])
            assert arm["hit_cost"] >= 0
            if previous is not None:
                assert (
                    previous[arm_id]["next_state_sha256"]
                    == arm["starting_state_sha256"]
                )
        previous = week["arms"]
    assert len(state_paths) == len(ARM_IDS) * 25


def test_reported_factorial_effects_are_exact() -> None:
    for gameweek in range(1, 26):
        week = _read(
            REPORT_ROOT / f"weeks/gw-{gameweek:02d}/comparison.json"
        )
        assert week["weekly_effects"] == _effects(
            week["arms"], "weekly_net_points"
        )
        assert week["cumulative_effects"] == _effects(
            week["arms"], "cumulative_points"
        )
        interaction = week["cumulative_effects"]["seed_evidence_interaction"]
        expected = (
            week["cumulative_effects"]["evidence_effect_with_optimized_seed"]
            - week["cumulative_effects"]["evidence_effect_with_scout_seed"]
        )
        assert interaction == expected


def test_first_tranche_refuses_to_cross_gw5_review_boundary() -> None:
    with pytest.raises(EvidenceForkError, match="hard review stop at GW5"):
        run_enhanced_season_replay(
            start_gameweek=1,
            stop_gameweek=6,
            **_runner_kwargs(),
        )


def test_second_tranche_refuses_to_cross_gw10_or_skip_boundary() -> None:
    with pytest.raises(EvidenceForkError, match="hard review stop at GW10"):
        run_enhanced_season_replay(
            start_gameweek=6,
            stop_gameweek=11,
            **_runner_kwargs(),
        )
    with pytest.raises(EvidenceForkError, match="approved review boundary"):
        run_enhanced_season_replay(
            start_gameweek=7,
            stop_gameweek=10,
            **_runner_kwargs(),
        )


def test_third_tranche_refuses_to_cross_gw15_or_skip_boundary() -> None:
    with pytest.raises(EvidenceForkError, match="hard review stop at GW15"):
        run_enhanced_season_replay(
            start_gameweek=11,
            stop_gameweek=16,
            **_runner_kwargs(),
        )
    with pytest.raises(EvidenceForkError, match="approved review boundary"):
        run_enhanced_season_replay(
            start_gameweek=12,
            stop_gameweek=15,
            **_runner_kwargs(),
        )

def test_fourth_tranche_refuses_to_cross_gw20_or_skip_boundary() -> None:
    with pytest.raises(EvidenceForkError, match="hard review stop at GW20"):
        run_enhanced_season_replay(
            start_gameweek=16,
            stop_gameweek=21,
            **_runner_kwargs(),
        )
    with pytest.raises(EvidenceForkError, match="approved review boundary"):
        run_enhanced_season_replay(
            start_gameweek=17,
            stop_gameweek=20,
            **_runner_kwargs(),
        )

def test_fifth_tranche_refuses_to_cross_gw25_or_skip_boundary() -> None:
    with pytest.raises(EvidenceForkError, match="hard review stop at GW25"):
        run_enhanced_season_replay(
            start_gameweek=21,
            stop_gameweek=26,
            **_runner_kwargs(),
        )
    with pytest.raises(EvidenceForkError, match="approved review boundary"):
        run_enhanced_season_replay(
            start_gameweek=22,
            stop_gameweek=25,
            **_runner_kwargs(),
        )
