"""Immutable counterfactual ladders and risk gates for paid transfers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import yaml

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint
from src.optimisation.types import SolverInput


class TransferCounterfactualError(ValueError):
    """Raised when a paid-transfer comparison is incomplete or unbound."""


def _validate_config(config: Mapping[str, Any]) -> None:
    if config.get("content_sha256") != artifact_hash(config):
        raise TransferCounterfactualError("transfer policy config hash mismatch")
    if config.get("policy_version") != "transfer-horizon-v1":
        raise TransferCounterfactualError("unsupported transfer policy version")
    gate = config.get("hit_gate")
    if not isinstance(gate, Mapping):
        raise TransferCounterfactualError("transfer policy requires a hit gate")
    required = [int(value) for value in gate.get("required_transfer_counts", [])]
    if required != list(range(max(required, default=-1) + 1)) or not required:
        raise TransferCounterfactualError(
            "required transfer counts must be consecutive from zero"
        )
    nominal = float(gate.get("nominal_hit_cost_per_paid_transfer", -1))
    premium = float(gate.get("risk_premium_points_per_paid_transfer", -1))
    uncertainty = float(
        gate.get("forecast_uncertainty_points_per_paid_transfer", -1)
    )
    if nominal <= 0 or premium <= 0 or uncertainty < 0:
        raise TransferCounterfactualError(
            "hit cost, positive premium and non-negative uncertainty are required"
        )
    if int(config.get("horizon_gameweeks", 0)) < 1:
        raise TransferCounterfactualError("hit gate requires a horizon")


def _discounted(values: Sequence[float], discount: float) -> float:
    return round(
        sum(float(value) * discount**index for index, value in enumerate(values)),
        6,
    )


def _payback_gameweek(
    candidate: Sequence[float],
    control: Sequence[float],
    *,
    gameweek: int,
    hit_cost: float,
    hurdle: float,
    discount: float,
) -> int | None:
    candidate_total = hit_cost
    control_total = 0.0
    for index, (candidate_week, control_week) in enumerate(
        zip(candidate, control, strict=True)
    ):
        factor = discount**index
        candidate_total += float(candidate_week) * factor
        control_total += float(control_week) * factor
        if candidate_total - control_total >= hurdle:
            return gameweek + index
    return None


def build_transfer_counterfactual_ladder(
    *,
    solver_input: SolverInput,
    solver_output: Mapping[str, Any],
    config: Mapping[str, Any],
    horizon_weekly_values: Mapping[str, Sequence[float]],
    eligible_chip_ids: Sequence[str] = (),
    chip_alternatives: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Compare every lower-transfer and chip alternative before selecting a hit."""

    _validate_config(config)
    gate = config["hit_gate"]
    required_counts = [int(value) for value in gate["required_transfer_counts"]]
    by_count = solver_output.get("best_by_transfer_count")
    if not isinstance(by_count, Mapping) or set(by_count) != {
        str(value) for value in required_counts
    }:
        raise TransferCounterfactualError(
            "paid plans require a complete transfer-count ladder"
        )
    chips = [deepcopy(dict(row)) for row in chip_alternatives]
    chip_ids = [str(row.get("candidate_id")) for row in chips]
    if set(chip_ids) != {str(value) for value in eligible_chip_ids}:
        raise TransferCounterfactualError(
            "ladder does not cover every eligible chip alternatives set"
        )
    if len(chip_ids) != len(set(chip_ids)):
        raise TransferCounterfactualError("chip candidate IDs must be unique")

    transfer_ids = [f"transfer_count:{value}" for value in required_counts]
    expected_ids = set(transfer_ids) | set(chip_ids)
    if set(horizon_weekly_values) != expected_ids:
        raise TransferCounterfactualError(
            "weekly horizon values must cover the complete counterfactual ladder"
        )
    horizon_length = int(config["horizon_gameweeks"])
    weekly = {
        str(key): [float(value) for value in values]
        for key, values in horizon_weekly_values.items()
    }
    if any(len(values) != horizon_length for values in weekly.values()):
        raise TransferCounterfactualError(
            "every counterfactual must cover the configured horizon"
        )

    nominal_per_paid = float(gate["nominal_hit_cost_per_paid_transfer"])
    premium_per_paid = float(gate["risk_premium_points_per_paid_transfer"])
    uncertainty_per_paid = float(
        gate["forecast_uncertainty_points_per_paid_transfer"]
    )
    discount = float(config["discount_factor"])
    if not 0 < discount <= 1:
        raise TransferCounterfactualError("discount factor must be in (0, 1]")

    rows: list[dict[str, Any]] = []
    for count in required_counts:
        candidate_id = f"transfer_count:{count}"
        candidate = deepcopy(dict(by_count[str(count)]))
        if len(candidate.get("transfers", [])) != count:
            raise TransferCounterfactualError(
                "transfer-count candidate does not match its ladder position"
            )
        hit_cost = float(candidate.get("hit_cost", 0))
        paid_transfers = max(0, count - int(solver_input.free_transfers))
        if hit_cost != paid_transfers * nominal_per_paid:
            raise TransferCounterfactualError(
                "candidate hit cost differs from configured nominal arithmetic"
            )
        values = weekly[candidate_id]
        immediate_net = float(
            candidate.get("immediate_objective", candidate["objective"])
        )
        if abs(values[0] - immediate_net) > 1e-6:
            raise TransferCounterfactualError(
                "first horizon value must equal immediate net objective"
            )
        rows.append(
            {
                "candidate_id": candidate_id,
                "transfer_count": count,
                "paid_transfer_count": paid_transfers,
                "candidate": candidate,
                "immediate_pre_hit_points": round(immediate_net + hit_cost, 6),
                "immediate_net_points": round(immediate_net, 6),
                "nominal_hit_cost": int(hit_cost),
                "future_free_transfer_option_value": round(
                    float(candidate.get("transfer_option_value", 0.0)), 6
                ),
                "horizon_weekly_net_values": values,
                "horizon_net_value": _discounted(values, discount),
            }
        )

    no_hit = [row for row in rows if row["nominal_hit_cost"] == 0]
    if not no_hit:
        raise TransferCounterfactualError("ladder requires a no-hit control")
    control = min(
        no_hit,
        key=lambda row: (
            -float(row["horizon_net_value"]),
            int(row["transfer_count"]),
            str(row["candidate_id"]),
        ),
    )
    control_values = control["horizon_weekly_net_values"]
    control_horizon = float(control["horizon_net_value"])
    for row in rows:
        paid = int(row["paid_transfer_count"])
        premium = premium_per_paid * paid
        uncertainty = uncertainty_per_paid * paid
        hit_cost = float(row["nominal_hit_cost"])
        pre_hit_advantage = (
            float(row["horizon_net_value"]) + hit_cost - control_horizon
        )
        hurdle = hit_cost + premium + uncertainty
        row.update(
            {
                "risk_premium_points": round(premium, 6),
                "forecast_uncertainty_points": round(uncertainty, 6),
                "pre_hit_horizon_advantage": round(pre_hit_advantage, 6),
                "required_pre_hit_advantage": round(hurdle, 6),
                "risk_adjusted_net_advantage": round(
                    pre_hit_advantage - hurdle, 6
                ),
                "clears_hit_gate": paid == 0 or pre_hit_advantage >= hurdle,
                "payback_gameweek": (
                    solver_input.gameweek
                    if paid == 0
                    else _payback_gameweek(
                        row["horizon_weekly_net_values"],
                        control_values,
                        gameweek=solver_input.gameweek,
                        hit_cost=hit_cost,
                        hurdle=hurdle,
                        discount=discount,
                    )
                ),
                "selection_value": round(
                    float(row["horizon_net_value"]) - premium - uncertainty,
                    6,
                ),
            }
        )

    chip_rows: list[dict[str, Any]] = []
    for source in chips:
        candidate_id = str(source["candidate_id"])
        values = weekly[candidate_id]
        candidate = deepcopy(dict(source["candidate"]))
        immediate = float(
            candidate.get("immediate_objective", candidate["objective"])
        )
        if abs(values[0] - immediate) > 1e-6:
            raise TransferCounterfactualError(
                "chip first horizon value must equal immediate net objective"
            )
        uncertainty = float(source.get("uncertainty_penalty_points", 0.0))
        if uncertainty < 0:
            raise TransferCounterfactualError(
                "chip uncertainty penalty cannot be negative"
            )
        policy_value = float(
            source.get(
                "policy_value",
                _discounted(values, discount) - uncertainty,
            )
        )
        chip_rows.append(
            {
                "candidate_id": candidate_id,
                "active_chip": str(source["active_chip"]),
                "candidate": candidate,
                "horizon_weekly_net_values": values,
                "horizon_net_value": _discounted(values, discount),
                "forecast_uncertainty_points": round(uncertainty, 6),
                "selection_value": round(policy_value, 6),
                "policy_eligible": bool(source.get("policy_eligible", True)),
            }
        )

    eligible: list[dict[str, Any]] = [
        {**row, "active_chip": None}
        for row in rows
        if row["clears_hit_gate"]
    ] + [row for row in chip_rows if row["policy_eligible"]]
    selected = min(
        eligible,
        key=lambda row: (
            -float(row["selection_value"]),
            row.get("active_chip") is not None,
            int(row.get("paid_transfer_count", 0)) > 0,
            int(row.get("transfer_count", 99)),
            str(row["candidate_id"]),
        ),
    )
    ungated = solver_output.get("selected")
    ungated_count = (
        len(ungated.get("transfers", []))
        if isinstance(ungated, Mapping)
        else None
    )
    artifact = {
        "schema_version": "1.0",
        "policy_id": "transfer-hit-gate-v1",
        "season": solver_input.season,
        "gameweek": solver_input.gameweek,
        "solver_input": deepcopy(solver_input.as_dict()),
        "solver_input_sha256": fingerprint(solver_input.as_dict()),
        "solver_output_sha256": fingerprint(solver_output),
        "policy_config": deepcopy(dict(config)),
        "horizon_weekly_values": weekly,
        "eligible_chip_ids": sorted(str(value) for value in eligible_chip_ids),
        "chip_alternative_inputs": chips,
        "no_hit_control_id": control["candidate_id"],
        "ungated_selected_id": (
            f"transfer_count:{ungated_count}"
            if ungated_count is not None
            else None
        ),
        "transfer_ladder": rows,
        "chip_alternatives": chip_rows,
        "selected": {
            "candidate_id": str(selected["candidate_id"]),
            "active_chip": selected.get("active_chip"),
            "candidate": deepcopy(dict(selected["candidate"])),
            "selection_value": float(selected["selection_value"]),
        },
        "verdict": {
            "ungated_paid_plan_selected": bool(
                ungated_count is not None
                and ungated_count > int(solver_input.free_transfers)
            ),
            "ungated_plan_survives_gate": (
                f"transfer_count:{ungated_count}"
                == str(selected["candidate_id"])
            ),
            "risk_premium_points_per_paid_transfer": premium_per_paid,
            "forecast_uncertainty_points_per_paid_transfer": (
                uncertainty_per_paid
            ),
        },
    }
    artifact["content_sha256"] = artifact_hash(artifact)
    return artifact


def validate_transfer_counterfactual_ladder(
    artifact: Mapping[str, Any],
    *,
    solver_input: SolverInput,
    solver_output: Mapping[str, Any],
) -> None:
    """Rebuild a ladder from sealed inputs and reject any changed conclusion."""

    if artifact.get("content_sha256") != artifact_hash(artifact):
        raise TransferCounterfactualError("counterfactual ladder hash mismatch")
    if artifact.get("solver_input_sha256") != fingerprint(solver_input.as_dict()):
        raise TransferCounterfactualError("counterfactual solver input binding mismatch")
    if artifact.get("solver_output_sha256") != fingerprint(solver_output):
        raise TransferCounterfactualError(
            "counterfactual solver output binding mismatch"
        )
    rebuilt = build_transfer_counterfactual_ladder(
        solver_input=solver_input,
        solver_output=solver_output,
        config=dict(artifact["policy_config"]),
        horizon_weekly_values=dict(artifact["horizon_weekly_values"]),
        eligible_chip_ids=list(artifact["eligible_chip_ids"]),
        chip_alternatives=list(artifact["chip_alternative_inputs"]),
    )
    if dict(artifact) != rebuilt:
        raise TransferCounterfactualError(
            "counterfactual ladder does not reproduce"
        )


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_gw34_transfer_hit(
    *,
    canonical_root: Path,
    episode_root: Path,
    transfer_config_path: Path,
    chip_config_path: Path,
) -> dict[str, Any]:
    """Rebuild the GW34 ladder from sealed cutoff inputs without outcome access."""

    from src.evaluation.chip_counterfactual import (
        _advance_candidate_for_projection,
        _canonical_tree_hash,
        _future_solver_input,
    )
    from src.optimisation.chips import (
        generate_chip_candidates,
        select_chip_candidate,
    )
    from src.optimisation.solver import apply_transfer_hit_gate, solve
    from src.optimisation.trajectory import (
        advance_trajectory_state,
        trajectory_state_hash,
    )
    from src.orchestration.multiweek_challenger import (
        build_same_cutoff_horizon,
    )

    before_hash, before_count = _canonical_tree_hash(
        canonical_root, through_gameweek=34
    )
    setup = canonical_root / "gw-34/setup"
    arm = setup / "arms/forecast_optimizer"
    episode = episode_root / "gw-34"
    state = _read(arm / "starting-policy-state.json")
    base_value = _read(arm / "reviewed-engine-input.json")
    base_input = SolverInput.from_dict(base_value)
    solver_output = _read(arm / "reviewed-engine-output.json")
    locked_forecast = _read(setup / "shared-locked-forecast.json")
    feature_state = _read(setup / "shared-feature-state.json")
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    transfer_config = _read(transfer_config_path)
    chip_config = _read(chip_config_path)
    _validate_config(transfer_config)

    horizon_length = int(transfer_config["horizon_gameweeks"])
    fixture_weeks: list[dict[str, Any]] = []
    for gameweek in range(34, 34 + horizon_length):
        observed_path = episode_root / f"gw-{gameweek:02d}/observed.json"
        observed = _read(observed_path)
        fixture_weeks.append(
            {
                "gameweek": gameweek,
                "fixtures": observed["fixtures"],
                "schedule_provenance": {
                    "source_path": observed_path.as_posix(),
                    "observed_dataset_hash": observed["dataset_hash"],
                    "historical_point_in_time_snapshot_available": False,
                },
            }
        )
    horizon = build_same_cutoff_horizon(
        base_input=base_value,
        locked_forecast=locked_forecast,
        fixture_weeks=fixture_weeks,
        feature_state_sha256=str(feature_state["content_sha256"]),
        config=transfer_config,
    )
    eligible_chips = [
        str(chip)
        for chip in base_input.chips_available
        if str(chip).endswith("_sh")
    ]
    candidates = generate_chip_candidates(
        base_input,
        solver_output,
        config=chip_config,
        rules=rules,
        ruleset_sha256=rules_hash,
        eligible_chips=eligible_chips,
    )
    projection_config = {
        "content_sha256": str(transfer_config["content_sha256"]),
        "future_projection": {
            key: deepcopy(transfer_config[key])
            for key in (
                "allow_hits",
                "beam_width",
                "branch_width",
                "buy_pool_per_pos",
                "discount_factor",
                "fixture_projection",
                "max_expanded_nodes",
                "max_transfers_per_week",
                "sell_pool_per_pos",
            )
        },
    }
    no_transfer = next(
        row["candidate"]
        for row in candidates
        if row["candidate_id"] == "no_chip_0_transfers"
    )
    future_values: dict[str, float] = {}
    future_lineage: dict[str, dict[str, Any]] = {}
    discount = float(transfer_config["discount_factor"])
    for record in candidates:
        projected_state = _advance_candidate_for_projection(
            base_input=base_input,
            record=record,
            no_transfer=no_transfer,
            horizon=horizon,
            rules=rules,
        )
        opening_state_sha256 = trajectory_state_hash(projected_state)
        weekly_tail: list[float] = []
        weekly_plan_sha256: list[str] = []
        for index in range(1, len(horizon)):
            future_input = _future_solver_input(
                base_input=base_input,
                state=projected_state,
                first_future_week=horizon[index],
                config=projection_config,
            )
            future_input.max_transfers = 0
            future_input.allow_hits = False
            output = solve(
                future_input,
                rules=rules,
                ruleset_sha256=rules_hash,
            )
            candidate = deepcopy(dict(output["selected"]))
            weekly_tail.append(
                float(
                    candidate.get(
                        "immediate_objective", candidate["objective"]
                    )
                )
            )
            weekly_plan_sha256.append(fingerprint(output))
            if index < len(horizon) - 1:
                projected_state = advance_trajectory_state(
                    projected_state,
                    candidate,
                    current_players=horizon[index]["players"],
                    next_players=horizon[index + 1]["players"],
                    rules=rules,
                )
        candidate_id = str(record["candidate_id"])
        future_values[candidate_id] = round(
            sum(
                value * discount**offset
                for offset, value in enumerate(weekly_tail, start=1)
            ),
            6,
        )
        future_lineage[candidate_id] = {
            "projected_state_sha256": opening_state_sha256,
            "future_policy": "hold_initial_squad_zero_future_transfers",
            "future_weekly_net_values": weekly_tail,
            "future_weekly_solver_output_sha256": weekly_plan_sha256,
            "discounted_future_value": future_values[candidate_id],
        }
    chip_selection = select_chip_candidate(
        candidates,
        config=chip_config,
        future_trajectory_values=future_values,
        current_gameweek=34,
        chip_expiry_gameweeks={chip: 38 for chip in eligible_chips},
    )
    evaluated = {
        str(row["candidate_id"]): row
        for row in chip_selection["candidates"]
    }
    weekly_values: dict[str, list[float]] = {}
    for count in range(4):
        candidate_id = f"no_chip_{count}_transfers"
        weekly_values[f"transfer_count:{count}"] = [
            float(evaluated[candidate_id]["expected"]["immediate_net_points"]),
            *future_lineage[candidate_id]["future_weekly_net_values"],
        ]
    chip_inputs: list[dict[str, Any]] = []
    for chip in eligible_chips:
        row = evaluated[chip]
        weekly_values[chip] = [
            float(row["expected"]["immediate_net_points"]),
            *future_lineage[chip]["future_weekly_net_values"],
        ]
        chip_inputs.append(
            {
                "candidate_id": chip,
                "active_chip": chip,
                "candidate": deepcopy(row["candidate"]),
                "policy_value": float(row["expected"]["policy_value"]),
                "uncertainty_penalty_points": float(
                    row["expected"]["uncertainty_penalty_points"]
                ),
                "policy_eligible": (
                    chip_selection["selected_active_chip"] == chip
                    or float(row["expected"]["policy_value"])
                    >= float(
                        chip_selection["no_chip_control_policy_value"]
                    )
                    + float(
                        chip_selection[
                            "minimum_policy_gain_to_deploy_chip"
                        ]
                    )
                ),
            }
        )
    ladder = build_transfer_counterfactual_ladder(
        solver_input=base_input,
        solver_output=solver_output,
        config=transfer_config,
        horizon_weekly_values=weekly_values,
        eligible_chip_ids=eligible_chips,
        chip_alternatives=chip_inputs,
    )
    gated_output = apply_transfer_hit_gate(solver_output, ladder)
    after_hash, after_count = _canonical_tree_hash(
        canonical_root, through_gameweek=34
    )
    if (before_hash, before_count) != (after_hash, after_count):
        raise TransferCounterfactualError(
            "canonical replay changed during GW34 counterfactual"
        )
    report = {
        "schema_version": "1.0",
        "report_id": "transfer-hit-counterfactual:2025-26:gw34",
        "season": "2025-26",
        "gameweek": 34,
        "exploratory_only": True,
        "promotion_eligible": False,
        "outcome_access": "sealed_not_loaded",
        "state_sha256": str(state["content_sha256"]),
        "solver_input_sha256": fingerprint(base_value),
        "solver_output_sha256": fingerprint(solver_output),
        "forecast_sha256": str(locked_forecast["content_sha256"]),
        "feature_state_sha256": str(feature_state["content_sha256"]),
        "ruleset_sha256": rules_hash,
        "transfer_policy_sha256": str(
            transfer_config["content_sha256"]
        ),
        "chip_policy_sha256": str(chip_config["content_sha256"]),
        "horizon_gameweeks": [int(row["gameweek"]) for row in horizon],
        "horizon_sha256": fingerprint(horizon),
        "future_projection_lineage": future_lineage,
        "chip_policy_selection": {
            key: deepcopy(value)
            for key, value in chip_selection.items()
            if key != "candidates"
        },
        "transfer_hit_ladder": ladder,
        "gated_solver_selection": {
            "selected": deepcopy(gated_output["selected"]),
            "ungated_selected": deepcopy(gated_output["ungated_selected"]),
            "transfer_hit_gate": deepcopy(
                gated_output["transfer_hit_gate"]
            ),
            "output_fingerprint": str(
                gated_output["output_fingerprint"]
            ),
        },
        "canonical_artifacts": {
            "tree_sha256_before": before_hash,
            "tree_sha256_after": after_hash,
            "file_count": before_count,
            "unchanged": True,
        },
        "limitations": [
            "historical full-schedule point-in-time snapshots are unavailable",
            "future fixtures use outcome-stripped reconstructed schedules",
            "future player rates and prices remain frozen at the GW34 cutoff",
        ],
    }
    report["content_sha256"] = artifact_hash(report)
    return report
