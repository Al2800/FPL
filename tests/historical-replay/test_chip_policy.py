from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.chip_counterfactual import _canonical_tree_hash
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.chips import (
    ChipPolicyError,
    select_chip_candidate,
    validate_chip_policy_config,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "control/policies/chip-v1.json"
REPORT_PATH = (
    ROOT
    / "reports/benchmarks/2025-26-counterfactuals/gw-31/evaluation.json"
)
CANONICAL_ROOT = ROOT / "reports/benchmarks/2025-26"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate(candidate_id: str, chip: str | None, immediate: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "active_chip": chip,
        "chip_base": "no_chip" if chip is None else chip.rsplit("_", 1)[0],
        "candidate": {
            "transfers": [],
            "lineup": {},
            "objective": immediate,
        },
        "expected": {
            "immediate_net_points": immediate,
            "one_week_planning_value": immediate,
            "future_trajectory_value": None,
            "chip_reserve_points": 0.0,
            "policy_value": None,
        },
        "lineage": {"solver_output_sha256": "a" * 64},
    }


def test_chip_policy_reserve_prevents_marginal_deployment():
    config = _read(CONFIG_PATH)
    candidates = [
        _candidate("no_chip", None, 50.0),
        _candidate("triple_captain_sh", "triple_captain_sh", 57.0),
    ]
    result = select_chip_candidate(
        candidates,
        config=config,
        future_trajectory_values={
            "no_chip": 200.0,
            "triple_captain_sh": 200.0,
        },
    )
    assert result["selected_candidate_id"] == "no_chip"
    assert result["selected_active_chip"] is None


def test_chip_policy_fails_closed_on_tampered_config():
    config = _read(CONFIG_PATH)
    validate_chip_policy_config(config)
    tampered = deepcopy(config)
    tampered["chip_reserve_points"]["free_hit"] = 0.0
    with pytest.raises(ChipPolicyError, match="hash mismatch"):
        validate_chip_policy_config(tampered)


def test_sealed_gw31_matrix_is_legal_restorative_and_canonical_safe():
    report = _read(REPORT_PATH)
    assert report["content_sha256"] == artifact_hash(report)
    assert report["outcome_opened_after_all_plans_frozen"] is True
    assert report["promotion_eligible"] is False
    assert report["selection"]["selected_candidate_id"] == "no_chip_3_transfers"
    assert report["selection"]["selected_active_chip"] is None
    assert "candidate_matrix" not in report["selection"]

    matrix = {row["candidate_id"]: row for row in report["candidate_matrix"]}
    assert {
        "no_chip_0_transfers",
        "no_chip_1_transfers",
        "no_chip_2_transfers",
        "no_chip_3_transfers",
        "wildcard_sh",
        "free_hit_sh",
        "triple_captain_sh",
        "bench_boost_sh",
    } == set(matrix)
    assert {
        matrix[f"no_chip_{count}_transfers"]["transfer_count"]
        for count in range(4)
    } == {0, 1, 2, 3}
    assert all(
        row["lineage"]["validation_status"] == "passed"
        for row in matrix.values()
    )
    assert (
        matrix["no_chip_3_transfers"]["lineage"]["plan_sha256"]
        == report["canonical_artifacts"]["gw31_plan_sha256"]
    )

    state = _read(
        CANONICAL_ROOT
        / "gw-31/setup/arms/forecast_optimizer/starting-policy-state.json"
    )
    free_hit = matrix["free_hit_sh"]["next_state"]
    assert free_hit["bank"] == state["bank"] == 0.3
    assert free_hit["free_transfers"] == state["free_transfers"] == 5
    assert free_hit["squad_player_ids"] == sorted(
        row["player_id"] for row in state["squad"]
    )
    assert free_hit["purchase_prices"] == {
        row["player_id"]: row["purchase_price"] for row in state["squad"]
    }
    assert report["free_hit_restoration"] == {
        **report["free_hit_restoration"],
        "squad_and_purchase_prices_restored": True,
        "bank_restored": True,
        "free_transfers_retained": True,
    }

    # The tempting hindsight result remains evaluation-only.
    assert matrix["triple_captain_sh"]["realised"]["net_points"] == 76
    assert matrix["no_chip_3_transfers"]["realised"]["net_points"] == 63
    assert report["longitudinal_free_hit"]["net_points_delta"] == 28
    assert report["uncertainty"]["classification"] == "high"

    tree_hash, file_count = _canonical_tree_hash(
        CANONICAL_ROOT, through_gameweek=31
    )
    canonical = report["canonical_artifacts"]
    assert canonical["unchanged"] is True
    assert tree_hash == canonical["tree_sha256_before"]
    assert tree_hash == canonical["tree_sha256_after"]
    assert file_count == canonical["file_count"]
