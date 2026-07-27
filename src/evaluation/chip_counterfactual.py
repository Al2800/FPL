"""Sealed GW31 chip counterfactual and longitudinal Free Hit evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.replay_adapter import build_replay_solver_input
from src.optimisation.chips import (
    generate_chip_candidates,
    select_chip_candidate,
    validate_chip_policy_config,
)
from src.optimisation.io import fingerprint
from src.optimisation.multiweek import plan_multiweek
from src.optimisation.solver import solve
from src.optimisation.trajectory import (
    advance_trajectory_state,
    initial_trajectory_state,
    market_for_state,
    trajectory_state_hash,
)
from src.optimisation.types import SolverInput
from src.orchestration.multiweek_challenger import build_same_cutoff_horizon
from src.orchestration.policy_state import transition_policy_state
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import get_rule


class ChipCounterfactualError(ValueError):
    """Raised when the chip counterfactual cannot preserve its seals."""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_tree_hash(root: Path, *, through_gameweek: int) -> tuple[str, int]:
    """Hash every canonical file through the declared Gameweek without writing."""

    digest = hashlib.sha256()
    count = 0
    for gameweek in range(1, through_gameweek + 1):
        directory = root / f"gw-{gameweek:02d}"
        if not directory.is_dir():
            raise ChipCounterfactualError(f"missing canonical GW{gameweek} directory")
        for path in sorted(item for item in directory.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            body_hash = hashlib.sha256(path.read_bytes()).digest()
            digest.update(body_hash)
            count += 1
    return digest.hexdigest(), count


def _identity_index(value: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(row["fpl_player_id"]): str(row["canonical_id"])
        for row in value["players"]
    }


def _market_from_feature_state(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "player_id": str(row["player_id"]),
            "position": str(row["position"]),
            "club_id": str(row["club_id"]),
            "now_cost": float(row["quote"]["now_cost"]),
        }
        for row in value["players"]
    ]


def _future_config(config: Mapping[str, Any], horizon_length: int) -> dict[str, Any]:
    projection = config["future_projection"]
    return {
        "horizon_gameweeks": horizon_length,
        "discount_factor": float(projection["discount_factor"]),
        "beam_width": int(projection["beam_width"]),
        "branch_width": int(projection["branch_width"]),
        "max_expanded_nodes": int(projection["max_expanded_nodes"]),
        "max_transfers_per_week": int(projection["max_transfers_per_week"]),
        "sell_pool_per_pos": int(projection["sell_pool_per_pos"]),
        "buy_pool_per_pos": int(projection["buy_pool_per_pos"]),
        "allow_hits": bool(projection["allow_hits"]),
        "fixture_projection": deepcopy(projection["fixture_projection"]),
        "content_sha256": str(config["content_sha256"]),
    }


def _build_horizon(
    *,
    base_input: Mapping[str, Any],
    locked_forecast: Mapping[str, Any],
    episode_root: Path,
    feature_state_sha256: str,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    start = int(base_input["gameweek"])
    count = int(config["planning_horizon_gameweeks"])
    fixture_weeks: list[dict[str, Any]] = []
    for gameweek in range(start, start + count):
        path = episode_root / f"gw-{gameweek:02d}" / "observed.json"
        observed = _read(path)
        fixture_weeks.append(
            {
                "gameweek": gameweek,
                "fixtures": observed["fixtures"],
                "schedule_provenance": {
                    "source_path": path.as_posix(),
                    "observed_dataset_hash": observed["dataset_hash"],
                    "historical_point_in_time_snapshot_available": False,
                },
            }
        )
    projection_config = _future_config(config, count)
    return build_same_cutoff_horizon(
        base_input=base_input,
        locked_forecast=locked_forecast,
        fixture_weeks=fixture_weeks,
        feature_state_sha256=feature_state_sha256,
        config=projection_config,
    )


def _normal_hit_cost(
    candidate: Mapping[str, Any],
    base_input: SolverInput,
    rules: Mapping[str, Any],
) -> int:
    count = len(candidate["transfers"])
    return max(0, count - int(base_input.free_transfers)) * int(
        get_rule(dict(rules), "transfers.hit_cost")["value"]
    )


def _advance_candidate_for_projection(
    *,
    base_input: SolverInput,
    record: Mapping[str, Any],
    no_transfer: Mapping[str, Any],
    horizon: Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    state = initial_trajectory_state(base_input, rules=rules)
    chip_base = str(record["chip_base"])
    candidate = deepcopy(dict(record["candidate"]))
    if chip_base == "free_hit":
        projected = deepcopy(dict(no_transfer))
    else:
        projected = candidate
        projected["hit_cost"] = _normal_hit_cost(candidate, base_input, rules)
    successor = advance_trajectory_state(
        state,
        projected,
        current_players=horizon[0]["players"],
        next_players=horizon[1]["players"],
        rules=rules,
    )
    if chip_base in {"wildcard", "free_hit"}:
        successor["free_transfers"] = int(base_input.free_transfers)
    return successor


def _future_solver_input(
    *,
    base_input: SolverInput,
    state: Mapping[str, Any],
    first_future_week: Mapping[str, Any],
    config: Mapping[str, Any],
) -> SolverInput:
    projection = config["future_projection"]
    return SolverInput(
        season=base_input.season,
        gameweek=int(state["gameweek"]),
        ruleset_id=base_input.ruleset_id,
        bank=float(state["bank"]),
        free_transfers=int(state["free_transfers"]),
        squad_player_ids=[str(row["player_id"]) for row in state["squad"]],
        players=market_for_state(state, first_future_week["players"]),
        active_chip=None,
        chips_available=[],
        max_transfers=int(projection["max_transfers_per_week"]),
        sell_pool_per_pos=int(projection["sell_pool_per_pos"]),
        buy_pool_per_pos=int(projection["buy_pool_per_pos"]),
        allow_hits=bool(projection["allow_hits"]),
        transfer_value_policy="none",
        squad_contingency_policy=base_input.squad_contingency_policy,
        appearance_calibration=deepcopy(base_input.appearance_calibration),
        ruleset_mismatch_policy=base_input.ruleset_mismatch_policy,
        availability_policy=base_input.availability_policy,
    )


def _project_future_values(
    *,
    candidates: Sequence[Mapping[str, Any]],
    base_input: SolverInput,
    horizon: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
    no_transfer = next(
        row["candidate"]
        for row in candidates
        if row["candidate_id"] == "no_chip_0_transfers"
    )
    values: dict[str, float] = {}
    plans_by_state: dict[str, dict[str, Any]] = {}
    lineage: dict[str, dict[str, Any]] = {}
    future_horizon = list(horizon[1:])
    projection = config["future_projection"]
    discount = float(projection["discount_factor"])
    for record in candidates:
        state = _advance_candidate_for_projection(
            base_input=base_input,
            record=record,
            no_transfer=no_transfer,
            horizon=horizon,
            rules=rules,
        )
        state_key = trajectory_state_hash(state)
        if state_key not in plans_by_state:
            future_input = _future_solver_input(
                base_input=base_input,
                state=state,
                first_future_week=future_horizon[0],
                config=config,
            )
            plans_by_state[state_key] = plan_multiweek(
                future_input,
                future_horizon,
                config=_future_config(config, len(future_horizon)),
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
        plan = plans_by_state[state_key]
        value = round(discount * float(plan["value"]["total"]), 6)
        candidate_id = str(record["candidate_id"])
        values[candidate_id] = value
        lineage[candidate_id] = {
            "projected_state_sha256": state_key,
            "future_plan_sha256": plan["content_sha256"],
            "future_plan_status": plan["status"],
            "global_optimality_guaranteed": bool(
                plan.get("search", {}).get("global_optimality_guaranteed", False)
            ),
            "discounted_future_value": value,
            "future_weekly_net_values": (
                [
                    float(plan["value"]["immediate"]),
                    *[
                        float(row["candidate"]["objective"])
                        for row in plan["advisory_trajectory"]
                    ],
                ]
                if plan["status"] == "complete"
                else [float(plan["value"]["immediate"])]
            ),
        }
    return values, lineage


def _freeze_all(
    candidates: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any],
    state: Mapping[str, Any],
    decision_market: Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, dict[str, Any]]:
    plans: dict[str, dict[str, Any]] = {}
    for record in candidates:
        candidate_id = str(record["candidate_id"])
        plans[candidate_id] = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=record["candidate"],
            decision_market=decision_market,
            active_chip=record["active_chip"],
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
    if any(
        plan["validation"]["status"] != "passed" or not plan["content_sha256"]
        for plan in plans.values()
    ):
        raise ChipCounterfactualError("all plans must freeze before outcome access")
    return plans


def _score_and_transition_all(
    plans: Mapping[str, Mapping[str, Any]],
    *,
    state: Mapping[str, Any],
    hidden: Mapping[str, Any],
    identity: Mapping[str, Any],
    identity_hash: str,
    revealed_at: str,
    decision_market: Sequence[Mapping[str, Any]],
    next_market: Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for candidate_id, plan in plans.items():
        outcome = score_revealed_outcome(
            plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
            player_identity_map=_identity_index(identity),
            identity_map_sha256=identity_hash,
        )
        successor, transition = transition_policy_state(
            state,
            plan,
            outcome,
            decision_market=decision_market,
            next_market=next_market,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
        )
        result[candidate_id] = {
            "plan": deepcopy(dict(plan)),
            "outcome": outcome,
            "successor": successor,
            "transition": transition,
        }
    return result


def _assert_free_hit_restoration(
    state: Mapping[str, Any],
    branch: Mapping[str, Any],
) -> None:
    successor = branch["successor"]
    transition = branch["transition"]
    before = {
        str(row["player_id"]): float(row["purchase_price"])
        for row in state["squad"]
    }
    after = {
        str(row["player_id"]): float(row["purchase_price"])
        for row in successor["squad"]
    }
    if before != after:
        raise ChipCounterfactualError("Free Hit did not restore squad and purchases")
    if float(successor["bank"]) != float(state["bank"]):
        raise ChipCounterfactualError("Free Hit did not restore bank")
    if int(successor["free_transfers"]) != int(state["free_transfers"]):
        raise ChipCounterfactualError("Free Hit did not retain transfer bank")
    if not transition.get("temporary_squad_sha256"):
        raise ChipCounterfactualError("Free Hit transition lacks temporary squad hash")


def _run_tail(
    *,
    start_state: Mapping[str, Any],
    canonical_root: Path,
    episode_root: Path,
) -> dict[str, Any]:
    """Replan GW32-GW38 from the restored state using each week's sealed input."""

    state = deepcopy(dict(start_state))
    weeks: list[dict[str, Any]] = []
    for gameweek in range(int(state["gameweek"]), 39):
        canonical_week = canonical_root / f"gw-{gameweek:02d}"
        setup = canonical_week / "setup"
        episode = episode_root / f"gw-{gameweek:02d}"
        feature = _read(setup / "shared-feature-state.json")
        forecast = _read(setup / "shared-locked-forecast.json")
        manifest = _read(episode / "episode-manifest.json")
        rules = yaml.safe_load(
            (episode / "ruleset.yaml").read_text(encoding="utf-8")
        )
        rules_hash = str(manifest["ruleset"]["content_sha256"])
        solver_input = build_replay_solver_input(
            feature_state=feature,
            policy_state=state,
            forecast_view=forecast,
            max_transfers=3,
            transfer_value_policy="expected_hit_avoidance_v1",
            probability_extra_transfer_needed=0.0 if gameweek == 38 else 0.5,
            future_transfer_discount=0.9,
        )
        output = solve(
            solver_input,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        candidate = output["selected"]
        plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=candidate,
            decision_market=solver_input.players,
            active_chip=None,
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        hidden = _read(episode / "hidden-outcome.json")
        identity = _read(episode / "identity-map.json")
        shared = _read(canonical_week / "shared-context.json")
        canonical_outcome = _read(
            canonical_week / "forecast_optimizer" / "realised-outcome.json"
        )
        outcome = score_revealed_outcome(
            plan,
            hidden,
            revealed_at=str(canonical_outcome["revealed_at"]),
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=_identity_index(identity),
            identity_map_sha256=str(shared["identity_map_sha256"]),
        )
        if gameweek == 38:
            next_market = _market_from_feature_state(feature)
        else:
            next_feature = _read(
                canonical_root
                / f"gw-{gameweek + 1:02d}"
                / "setup"
                / "shared-feature-state.json"
            )
            next_market = _market_from_feature_state(next_feature)
        successor, transition = transition_policy_state(
            state,
            plan,
            outcome,
            decision_market=solver_input.players,
            next_market=next_market,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        weeks.append(
            {
                "gameweek": gameweek,
                "starting_state_sha256": state["content_sha256"],
                "solver_input_sha256": fingerprint(solver_input.as_dict()),
                "solver_output_sha256": fingerprint(output),
                "plan_sha256": plan["content_sha256"],
                "outcome_sha256": outcome["content_sha256"],
                "transition_sha256": transition["content_sha256"],
                "next_state_sha256": successor["content_sha256"],
                "transfers": len(plan["transfers"]),
                "hit_cost": int(plan["finance"]["hit_cost"]),
                "gross_points": int(outcome["gross_points"]),
                "net_points": int(transition["net_points"]),
            }
        )
        state = successor
    return {
        "weeks": weeks,
        "net_points": sum(int(row["net_points"]) for row in weeks),
        "terminal_state_sha256": state["content_sha256"],
        "terminal_cumulative_points": int(state["cumulative_points"]),
    }


def _canonical_tail(canonical_root: Path) -> dict[str, Any]:
    weeks: list[dict[str, Any]] = []
    for gameweek in range(32, 39):
        directory = canonical_root / f"gw-{gameweek:02d}" / "forecast_optimizer"
        plan = _read(directory / "validated-plan.json")
        outcome = _read(directory / "realised-outcome.json")
        transition = _read(directory / "state-transition.json")
        successor = _read(directory / "next-policy-state.json")
        weeks.append(
            {
                "gameweek": gameweek,
                "plan_sha256": plan["content_sha256"],
                "outcome_sha256": outcome["content_sha256"],
                "transition_sha256": transition["content_sha256"],
                "next_state_sha256": successor["content_sha256"],
                "transfers": int(plan["finance"]["transfer_count"]),
                "hit_cost": int(plan["finance"]["hit_cost"]),
                "gross_points": int(outcome["gross_points"]),
                "net_points": int(transition["net_points"]),
            }
        )
    return {
        "weeks": weeks,
        "net_points": sum(int(row["net_points"]) for row in weeks),
    }


def evaluate_gw31_chip_policy(
    *,
    canonical_root: Path,
    episode_root: Path,
    config_path: Path,
) -> dict[str, Any]:
    """Return the sealed GW31 matrix and a longitudinal Free Hit branch."""

    before_hash, before_count = _canonical_tree_hash(
        canonical_root, through_gameweek=31
    )
    config = _read(config_path)
    validate_chip_policy_config(config)
    gameweek = 31
    canonical_week = canonical_root / "gw-31"
    setup = canonical_week / "setup"
    arm_setup = setup / "arms" / "forecast_optimizer"
    episode = episode_root / "gw-31"
    state = _read(arm_setup / "starting-policy-state.json")
    base_input_value = _read(arm_setup / "reviewed-engine-input.json")
    base_input = SolverInput.from_dict(base_input_value)
    canonical_output = _read(arm_setup / "reviewed-engine-output.json")
    locked_forecast = _read(setup / "shared-locked-forecast.json")
    feature_state = _read(setup / "shared-feature-state.json")
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])

    candidates = generate_chip_candidates(
        base_input,
        canonical_output,
        config=config,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    horizon = _build_horizon(
        base_input=base_input_value,
        locked_forecast=locked_forecast,
        episode_root=episode_root,
        feature_state_sha256=str(feature_state["content_sha256"]),
        config=config,
    )
    future_values, future_lineage = _project_future_values(
        candidates=candidates,
        base_input=base_input,
        horizon=horizon,
        config=config,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    selection = select_chip_candidate(
        candidates,
        config=config,
        future_trajectory_values=future_values,
    )
    selected_candidates = selection.pop("candidates")
    plans = _freeze_all(
        selected_candidates,
        manifest=manifest,
        state=state,
        decision_market=base_input.players,
        rules=rules,
        ruleset_sha256=rules_hash,
    )

    # The hidden outcome is first opened only after every alternative is frozen.
    hidden = _read(episode / "hidden-outcome.json")
    identity = _read(episode / "identity-map.json")
    shared = _read(canonical_week / "shared-context.json")
    canonical_outcome = _read(
        canonical_week / "forecast_optimizer" / "realised-outcome.json"
    )
    next_feature = _read(
        canonical_root / "gw-32" / "setup" / "shared-feature-state.json"
    )
    branches = _score_and_transition_all(
        plans,
        state=state,
        hidden=hidden,
        identity=identity,
        identity_hash=str(shared["identity_map_sha256"]),
        revealed_at=str(canonical_outcome["revealed_at"]),
        decision_market=base_input.players,
        next_market=_market_from_feature_state(next_feature),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    free_hit_id = next(
        row["candidate_id"]
        for row in selected_candidates
        if row["chip_base"] == "free_hit"
    )
    _assert_free_hit_restoration(state, branches[free_hit_id])
    free_hit_tail = _run_tail(
        start_state=branches[free_hit_id]["successor"],
        canonical_root=canonical_root,
        episode_root=episode_root,
    )
    canonical_tail = _canonical_tail(canonical_root)

    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in base_input.players
    }
    matrix: list[dict[str, Any]] = []
    for record in selected_candidates:
        candidate_id = str(record["candidate_id"])
        branch = branches[candidate_id]
        plan = branch["plan"]
        outcome = branch["outcome"]
        successor = branch["successor"]
        transition = branch["transition"]
        expected = record["expected"]
        matrix.append(
            {
                "candidate_id": candidate_id,
                "active_chip": record["active_chip"],
                "transfer_count": int(plan["finance"]["transfer_count"]),
                "transfers": [
                    {
                        **deepcopy(move),
                        "player_out_name": names[move["player_out_id"]],
                        "player_in_name": names[move["player_in_id"]],
                    }
                    for move in plan["transfers"]
                ],
                "expected": expected,
                "future_lineage": future_lineage[candidate_id],
                "realised": {
                    "gross_points": int(outcome["gross_points"]),
                    "hit_cost": int(plan["finance"]["hit_cost"]),
                    "net_points": int(transition["net_points"]),
                    "bench_points": int(outcome["bench_points"]),
                    "captain_extra_points": int(
                        outcome["captain"]["extra_points"]
                    ),
                },
                "next_state": {
                    "bank": float(successor["bank"]),
                    "free_transfers": int(successor["free_transfers"]),
                    "squad_player_ids": sorted(
                        str(row["player_id"]) for row in successor["squad"]
                    ),
                    "purchase_prices": {
                        str(row["player_id"]): float(row["purchase_price"])
                        for row in successor["squad"]
                    },
                    "chips_available": list(successor["chips_available"]),
                    "content_sha256": successor["content_sha256"],
                },
                "lineage": {
                    "plan_sha256": plan["content_sha256"],
                    "outcome_sha256": outcome["content_sha256"],
                    "transition_sha256": transition["content_sha256"],
                    "validation_status": plan["validation"]["status"],
                },
            }
        )

    after_hash, after_count = _canonical_tree_hash(
        canonical_root, through_gameweek=31
    )
    if (before_hash, before_count) != (after_hash, after_count):
        raise ChipCounterfactualError("canonical GW1-GW31 artifacts changed")
    canonical_gw31_net = int(
        _read(
            canonical_week / "forecast_optimizer" / "state-transition.json"
        )["net_points"]
    )
    free_hit_gw31_net = int(branches[free_hit_id]["transition"]["net_points"])
    report = {
        "schema_version": "1.0",
        "report_id": "chip-policy:2025-26:gw31",
        "season": "2025-26",
        "gameweek": gameweek,
        "comparison_type": "sealed_chip_matrix_and_longitudinal_free_hit",
        "promotion_eligible": False,
        "reason_not_promotion_eligible": (
            "historical full fixture schedule snapshots at the GW31 cutoff are "
            "unavailable; the stripped schedule projection is exploratory"
        ),
        "decision_cutoff": manifest["deadline"],
        "outcome_opened_after_all_plans_frozen": True,
        "policy_config_sha256": config["content_sha256"],
        "episode_id": manifest["episode_id"],
        "observed_sha256": shared["observed_sha256"],
        "hidden_outcome_sha256": shared["hidden_outcome_sha256"],
        "feature_state_sha256": feature_state["content_sha256"],
        "forecast_sha256": locked_forecast["content_sha256"],
        "selection": selection,
        "candidate_matrix": matrix,
        "free_hit_restoration": {
            "candidate_id": free_hit_id,
            "squad_and_purchase_prices_restored": True,
            "bank_restored": True,
            "free_transfers_retained": True,
            "temporary_squad_sha256": branches[free_hit_id]["transition"][
                "temporary_squad_sha256"
            ],
        },
        "longitudinal_free_hit": {
            "canonical_gw31_to_gw38_net_points": (
                canonical_gw31_net + canonical_tail["net_points"]
            ),
            "free_hit_gw31_to_gw38_net_points": (
                free_hit_gw31_net + free_hit_tail["net_points"]
            ),
            "net_points_delta": (
                free_hit_gw31_net
                + free_hit_tail["net_points"]
                - canonical_gw31_net
                - canonical_tail["net_points"]
            ),
            "canonical_tail": canonical_tail,
            "free_hit_tail": free_hit_tail,
        },
        "uncertainty": {
            "classification": "high",
            "historical_point_in_time_full_fixture_schedule_available": False,
            "future_player_rates_frozen_at_gw31_cutoff": True,
            "future_prices_frozen_at_gw31_cutoff": True,
            "candidate_search_global_optimality_guaranteed": False,
            "maximum_first_week_transfers": int(
                config["candidate_max_transfers"]
            ),
            "interpretation": (
                "The matrix is a legality and process evaluation. Realised gains "
                "describe this branch but cannot promote the policy or tune reserves."
            ),
        },
        "canonical_artifacts": {
            "through_gameweek": 31,
            "file_count": before_count,
            "tree_sha256_before": before_hash,
            "tree_sha256_after": after_hash,
            "unchanged": True,
            "gw31_plan_sha256": _read(
                canonical_week / "forecast_optimizer" / "validated-plan.json"
            )["content_sha256"],
            "gw31_outcome_sha256": canonical_outcome["content_sha256"],
        },
        "limitations": [
            "historical_point_in_time_full_fixture_schedule_snapshot_unavailable",
            "chip_candidate_transfer_search_is_bounded_to_zero_through_three_moves",
            "future_projection_freezes_player_rates_and_prices_at_the_gw31_cutoff",
            "longitudinal_free_hit_tail_uses_no_further_chips_to_isolate_the_branch",
            "realised_results_are_evaluation_only_and_never_enter_policy_selection",
        ],
    }
    report["content_sha256"] = artifact_hash(report)
    return report
