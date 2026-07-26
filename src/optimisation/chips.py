"""Deadline-safe chip candidate generation and declared policy selection."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput


class ChipPolicyError(ValueError):
    """Raised when a chip policy input is incomplete or internally unsafe."""


CHIP_BASES = ("wildcard", "free_hit", "triple_captain", "bench_boost")


def _chip_base(chip: str | None) -> str:
    return "no_chip" if chip is None else str(chip).rsplit("_", 1)[0]


def validate_chip_policy_config(config: Mapping[str, Any]) -> None:
    """Fail closed when the versioned policy cannot be reproduced."""

    if config.get("content_sha256") != artifact_hash(config):
        raise ChipPolicyError("chip policy config hash mismatch")
    if config.get("policy_version") != "chip-policy-v1":
        raise ChipPolicyError("unsupported chip policy version")
    reserves = config.get("chip_reserve_points", {})
    if set(reserves) != set(CHIP_BASES):
        raise ChipPolicyError("chip reserve policy must cover all four chips")
    if any(float(value) < 0 for value in reserves.values()):
        raise ChipPolicyError("chip reserve points cannot be negative")
    if int(config.get("candidate_max_transfers", -1)) not in range(4):
        raise ChipPolicyError("candidate_max_transfers must be between zero and three")
    if not 3 <= int(config.get("planning_horizon_gameweeks", 0)) <= 6:
        raise ChipPolicyError("planning horizon must contain three to six Gameweeks")


def _candidate_record(
    *,
    candidate_id: str,
    active_chip: str | None,
    candidate: Mapping[str, Any],
    solver_output_sha256: str,
) -> dict[str, Any]:
    value = deepcopy(dict(candidate))
    immediate = float(value.get("immediate_objective", value["objective"]))
    return {
        "candidate_id": candidate_id,
        "active_chip": active_chip,
        "chip_base": _chip_base(active_chip),
        "candidate": value,
        "expected": {
            "immediate_net_points": round(immediate, 6),
            "one_week_planning_value": round(float(value["objective"]), 6),
            "future_trajectory_value": None,
            "chip_reserve_points": 0.0,
            "policy_value": None,
        },
        "lineage": {
            "solver_output_sha256": solver_output_sha256,
        },
    }


def generate_chip_candidates(
    base_input: SolverInput,
    canonical_output: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> list[dict[str, Any]]:
    """Generate legal no-chip and four-chip alternatives before outcome reveal."""

    validate_chip_policy_config(config)
    if base_input.active_chip is not None:
        raise ChipPolicyError("base solver input must not have an active chip")
    configured_max = int(config["candidate_max_transfers"])
    if int(base_input.max_transfers) != configured_max:
        raise ChipPolicyError("solver input transfer bound differs from chip policy")
    available = {str(value) for value in base_input.chips_available}
    selected_chips: dict[str, str] = {}
    for chip in available:
        base = _chip_base(chip)
        if base in CHIP_BASES:
            if base in selected_chips:
                raise ChipPolicyError(f"more than one available {base} chip")
            selected_chips[base] = chip
    missing = sorted(set(CHIP_BASES) - set(selected_chips))
    if missing:
        raise ChipPolicyError(f"missing available chip candidates: {missing}")

    expected_counts = {str(value) for value in range(configured_max + 1)}
    by_count = canonical_output.get("best_by_transfer_count", {})
    if set(by_count) != expected_counts:
        raise ChipPolicyError("canonical output lacks a complete transfer-count matrix")
    canonical_hash = fingerprint(canonical_output)
    records = [
        _candidate_record(
            candidate_id=f"no_chip_{count}_transfers",
            active_chip=None,
            candidate=by_count[str(count)],
            solver_output_sha256=canonical_hash,
        )
        for count in range(configured_max + 1)
    ]

    for base in CHIP_BASES:
        chip = selected_chips[base]
        payload = deepcopy(base_input.as_dict())
        payload["active_chip"] = chip
        chip_output = solve(
            SolverInput.from_dict(payload),
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
        selected = chip_output.get("selected")
        if selected is None:
            raise ChipPolicyError(f"{chip} produced no legal candidate")
        records.append(
            _candidate_record(
                candidate_id=chip,
                active_chip=chip,
                candidate=selected,
                solver_output_sha256=fingerprint(chip_output),
            )
        )
    return records


def select_chip_candidate(
    candidates: list[Mapping[str, Any]],
    *,
    config: Mapping[str, Any],
    future_trajectory_values: Mapping[str, float],
) -> dict[str, Any]:
    """Select on forecast value and chip reserve, never on realised points."""

    validate_chip_policy_config(config)
    identifiers = [str(row["candidate_id"]) for row in candidates]
    if len(identifiers) != len(set(identifiers)):
        raise ChipPolicyError("chip candidate IDs must be unique")
    if set(identifiers) != set(future_trajectory_values):
        raise ChipPolicyError("future trajectory values do not cover every candidate")

    reserves = config["chip_reserve_points"]
    threshold = float(config["minimum_policy_gain_to_deploy_chip"])
    evaluated: list[dict[str, Any]] = []
    for source in candidates:
        row = deepcopy(dict(source))
        future = float(future_trajectory_values[row["candidate_id"]])
        reserve = (
            0.0
            if row["active_chip"] is None
            else float(reserves[row["chip_base"]])
        )
        policy_value = (
            float(row["expected"]["immediate_net_points"]) + future - reserve
        )
        row["expected"].update(
            {
                "future_trajectory_value": round(future, 6),
                "chip_reserve_points": round(reserve, 6),
                "policy_value": round(policy_value, 6),
            }
        )
        evaluated.append(row)

    no_chip = [row for row in evaluated if row["active_chip"] is None]
    if not no_chip:
        raise ChipPolicyError("policy requires a no-chip control")
    control = min(
        no_chip,
        key=lambda row: (
            -float(row["expected"]["policy_value"]),
            len(row["candidate"]["transfers"]),
            str(row["candidate_id"]),
        ),
    )
    control_value = float(control["expected"]["policy_value"])
    eligible = [
        row
        for row in evaluated
        if row["active_chip"] is None
        or float(row["expected"]["policy_value"]) >= control_value + threshold
    ]
    selected = min(
        eligible,
        key=lambda row: (
            -float(row["expected"]["policy_value"]),
            row["active_chip"] is not None,
            len(row["candidate"]["transfers"]),
            str(row["candidate_id"]),
        ),
    )
    return {
        "selection_basis": (
            "immediate expected net points plus same-cutoff discounted future "
            "trajectory value minus declared chip reserve"
        ),
        "minimum_policy_gain_to_deploy_chip": threshold,
        "no_chip_control_id": control["candidate_id"],
        "no_chip_control_policy_value": control_value,
        "selected_candidate_id": selected["candidate_id"],
        "selected_active_chip": selected["active_chip"],
        "candidates": evaluated,
    }
