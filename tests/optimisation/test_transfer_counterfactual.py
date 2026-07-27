"""Contracts for complete, risk-adjusted transfer-hit ladders."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.transfer_counterfactual import (
    TransferCounterfactualError,
    build_transfer_counterfactual_ladder,
    validate_transfer_counterfactual_ladder,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.solver import apply_transfer_hit_gate
from src.optimisation.types import SolverInput


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (ROOT / "control/policies/transfer-horizon-v1.json").read_text(
        encoding="utf-8"
    )
)
GW34_REPORT = (
    ROOT
    / "reports/benchmarks/2025-26-counterfactuals"
    / "gw-34/transfer-hit-evaluation.json"
)


def _input() -> SolverInput:
    return SolverInput(
        season="2025-26",
        gameweek=34,
        ruleset_id="2025-26-v1.0",
        bank=0.3,
        free_transfers=1,
        squad_player_ids=[str(value) for value in range(1, 16)],
        players=[],
        chips_available=["free_hit_sh"],
        max_transfers=3,
        transfer_value_policy="expected_hit_avoidance_v1",
    )


def _candidate(count: int, net: float) -> dict:
    hit = max(0, count - 1) * 4
    return {
        "strategy": "hit" if hit else "free_transfer",
        "transfers": [
            {"player_out_id": str(index), "player_in_id": str(20 + index)}
            for index in range(count)
        ],
        "hit_cost": hit,
        "bank_after": 0.0,
        "objective": net,
        "immediate_objective": net,
        "transfer_option_value": 0.0,
        "lineup": {"captain_id": "1"},
    }


def _output(*, three_transfer_net: float = 35.5) -> dict:
    rows = {
        "0": _candidate(0, 30.0),
        "1": _candidate(1, 34.0),
        "2": _candidate(2, 34.8),
        "3": _candidate(3, three_transfer_net),
    }
    return {
        "solver_version": "test",
        "selected": deepcopy(rows["3"]),
        "plans": {"highest_ev": deepcopy(rows["3"])},
        "best_by_transfer_count": rows,
    }


def _weekly(*, strong_hit: bool = False) -> dict[str, list[float]]:
    return {
        "transfer_count:0": [30.0, 30.0, 30.0, 30.0],
        "transfer_count:1": [34.0, 30.0, 30.0, 30.0],
        "transfer_count:2": [34.8, 31.0, 31.0, 31.0],
        "transfer_count:3": (
            [42.0, 34.0, 34.0, 34.0]
            if strong_hit
            else [35.5, 30.5, 30.5, 30.5]
        ),
        "free_hit_sh": [36.0, 30.0, 30.0, 30.0],
    }


def _chip() -> dict:
    return {
        "candidate_id": "free_hit_sh",
        "active_chip": "free_hit_sh",
        "candidate": _candidate(3, 36.0),
        "policy_value": 111.0,
        "uncertainty_penalty_points": 1.0,
    }


def test_incomplete_transfer_or_chip_ladder_is_refused() -> None:
    output = _output()
    output["best_by_transfer_count"].pop("2")
    weekly = _weekly()
    weekly.pop("transfer_count:2")
    with pytest.raises(
        TransferCounterfactualError,
        match="complete transfer-count ladder",
    ):
        build_transfer_counterfactual_ladder(
            solver_input=_input(),
            solver_output=output,
            config=CONFIG,
            horizon_weekly_values=weekly,
            eligible_chip_ids=["free_hit_sh"],
            chip_alternatives=[_chip()],
        )

    with pytest.raises(
        TransferCounterfactualError,
        match="eligible chip alternatives",
    ):
        build_transfer_counterfactual_ladder(
            solver_input=_input(),
            solver_output=_output(),
            config=CONFIG,
            horizon_weekly_values={
                key: value
                for key, value in _weekly().items()
                if key != "free_hit_sh"
            },
            eligible_chip_ids=["free_hit_sh"],
            chip_alternatives=[],
        )


def test_marginal_eight_point_hit_is_rejected_with_explicit_hurdle() -> None:
    artifact = build_transfer_counterfactual_ladder(
        solver_input=_input(),
        solver_output=_output(),
        config=CONFIG,
        horizon_weekly_values=_weekly(),
        eligible_chip_ids=["free_hit_sh"],
        chip_alternatives=[_chip()],
    )
    row = next(
        item
        for item in artifact["transfer_ladder"]
        if item["transfer_count"] == 3
    )

    assert row["nominal_hit_cost"] == 8
    assert row["risk_premium_points"] > 0
    assert row["required_pre_hit_advantage"] > 8
    assert row["clears_hit_gate"] is False
    assert row["payback_gameweek"] is None
    assert artifact["selected"]["candidate_id"] != "transfer_count:3"


def test_strong_hit_clears_and_gate_replaces_ungated_solver_selection() -> None:
    output = _output(three_transfer_net=42.0)
    weekly = _weekly(strong_hit=True)
    weekly.pop("free_hit_sh")
    artifact = build_transfer_counterfactual_ladder(
        solver_input=_input(),
        solver_output=output,
        config=CONFIG,
        horizon_weekly_values=weekly,
        eligible_chip_ids=[],
        chip_alternatives=[],
    )
    gated = apply_transfer_hit_gate(output, artifact)
    row = next(
        item
        for item in artifact["transfer_ladder"]
        if item["transfer_count"] == 3
    )

    assert row["clears_hit_gate"] is True
    assert row["payback_gameweek"] is not None
    assert artifact["selected"]["candidate_id"] == "transfer_count:3"
    assert gated["selected"] == artifact["selected"]["candidate"]
    assert gated["ungated_selected"] == output["selected"]
    assert gated["transfer_hit_gate"]["artifact_sha256"] == artifact[
        "content_sha256"
    ]


def test_artifact_is_immutable_and_bound_to_exact_solver_output() -> None:
    output = _output()
    artifact = build_transfer_counterfactual_ladder(
        solver_input=_input(),
        solver_output=output,
        config=CONFIG,
        horizon_weekly_values=_weekly(),
        eligible_chip_ids=["free_hit_sh"],
        chip_alternatives=[_chip()],
    )
    validate_transfer_counterfactual_ladder(
        artifact,
        solver_input=_input(),
        solver_output=output,
    )

    tampered = deepcopy(artifact)
    tampered["transfer_ladder"][0]["horizon_net_value"] += 1
    tampered["content_sha256"] = artifact_hash(tampered)
    with pytest.raises(
        TransferCounterfactualError,
        match="does not reproduce",
    ):
        validate_transfer_counterfactual_ladder(
            tampered,
            solver_input=_input(),
            solver_output=output,
        )

    changed_output = deepcopy(output)
    changed_output["selected"]["objective"] += 1
    with pytest.raises(
        TransferCounterfactualError,
        match="solver output binding",
    ):
        validate_transfer_counterfactual_ladder(
            artifact,
            solver_input=_input(),
            solver_output=changed_output,
        )


def test_sealed_gw34_report_is_complete_outcome_blind_and_canonical_safe() -> None:
    report = json.loads(GW34_REPORT.read_text(encoding="utf-8"))
    assert report["content_sha256"] == artifact_hash(report)
    assert report["outcome_access"] == "sealed_not_loaded"
    assert report["canonical_artifacts"]["unchanged"] is True
    assert (
        report["canonical_artifacts"]["tree_sha256_before"]
        == report["canonical_artifacts"]["tree_sha256_after"]
    )
    ladder = report["transfer_hit_ladder"]
    assert {row["transfer_count"] for row in ladder["transfer_ladder"]} == {
        0,
        1,
        2,
        3,
    }
    assert {row["active_chip"] for row in ladder["chip_alternatives"]} == {
        "wildcard_sh",
        "free_hit_sh",
        "triple_captain_sh",
        "bench_boost_sh",
    }
    eight_point = next(
        row for row in ladder["transfer_ladder"] if row["nominal_hit_cost"] == 8
    )
    assert eight_point["required_pre_hit_advantage"] > 8
    assert isinstance(
        ladder["verdict"]["ungated_plan_survives_gate"], bool
    )
    assert (
        report["gated_solver_selection"]["selected"]
        == ladder["selected"]["candidate"]
    )
