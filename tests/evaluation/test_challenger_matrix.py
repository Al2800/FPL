from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.challenger_matrix import (
    ChallengerMatrixError,
    PROMOTION_RULE,
    apply_promotion_rule,
    build_live_shadow_candidate,
    validate_matrix_rows,
)
from src.forecasting.live_faithful import artifact_hash


def _row(challenger_id: str, *, score: float = 0.0) -> dict:
    return {
        "challenger_id": challenger_id,
        "configuration_sha256": "a" * 64,
        "episode_bindings": [
            {
                "episode_manifest_sha256": "b" * 64,
                "observed_sha256": "c" * 64,
                "hidden_outcome_sha256": "d" * 64,
            }
        ],
        "gates": {gate: True for gate in PROMOTION_RULE["required_gates"]},
        "disqualifiers": [],
        "selection_metrics": {
            "held_out_decision_quality": score,
            "full_replay_realised_net_points": score,
            "calibration": score,
            "operational_cost": 1.0,
        },
    }


def test_rejected_challenger_cannot_be_rescued_by_final_points() -> None:
    rejected = _row("rejected", score=1000)
    rejected["gates"]["locked_held_out_gate"] = False
    rejected["disqualifiers"] = ["failed_locked_gate"]
    eligible = _row("eligible", score=1)

    assert apply_promotion_rule([rejected, eligible]) == "eligible"
    assert PROMOTION_RULE["final_season_points_can_override_failed_gate"] is False


def test_every_matrix_row_binds_configuration_and_episode_hashes() -> None:
    row = _row("valid")
    validate_matrix_rows([row])
    missing = deepcopy(row)
    del missing["episode_bindings"][0]["observed_sha256"]
    with pytest.raises(ChallengerMatrixError, match="observed_sha256"):
        validate_matrix_rows([missing])


def test_live_shadow_candidate_keeps_control_executable() -> None:
    row = _row("robust-selection-v2")
    candidate = build_live_shadow_candidate(
        nominee="robust-selection-v2",
        rows=[row],
        control_model_sha256="e" * 64,
    )
    assert candidate["mode"] == "observation_only_no_fpl_execution"
    assert candidate["executable_policy"]["model_config_sha256"] == "e" * 64
    assert candidate["shadow_policy"]["configuration_sha256"] == "a" * 64
    assert candidate["fallback"]["on_validation_failure"] is True
    assert candidate["agent_completion_gate"] == {
        "required_status": "completed",
        "requires_validated_output": True,
        "on_failure": "refuse_agent_scoring_use_control_only",
    }
    assert candidate["paired_trajectory"]["attribution_bridge"] == (
        "evidence_state_no_evidence"
    )
    assert candidate["unstructured_evidence"]["missing_feed"] == (
        "degrade_to_control_policy"
    )
    assert candidate["content_sha256"] == artifact_hash(candidate)


def test_committed_matrix_preserves_rejections_and_control_tree() -> None:
    root = Path(__file__).resolve().parents[2]
    matrix = json.loads(
        (
            root / "reports/benchmarks/2025-26-challenger-matrix/matrix.json"
        ).read_text(encoding="utf-8")
    )
    decisions = {row["challenger_id"]: row["decision"] for row in matrix["rows"]}
    assert decisions["captain-v1"] == "rejected"
    assert decisions["team-context-v2"] == "rejected"
    assert decisions["top-bin-recalibration-v2"] == "rejected"
    assert matrix["nomination"]["challenger_id"] == "robust-selection-v2"
    assert matrix["nomination"]["control_remains_executable"] is True
    candidate = json.loads(
        (root / "control/policies/live-shadow-candidate.json").read_text(
            encoding="utf-8"
        )
    )
    assert matrix["nomination"]["candidate_config_sha256"] == (
        candidate["content_sha256"]
    )
    assert (
        matrix["control"]["canonical_tree_sha256_before"]
        == matrix["control"]["canonical_tree_sha256_after"]
    )
    assert matrix["content_sha256"] == artifact_hash(matrix)
