"""Transparent single-Gameweek optimiser (WP-07)."""

from __future__ import annotations

from bisect import insort
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
import time
from typing import Any

from src.optimisation.io import fingerprint
from src.optimisation.simple_plan import choose_starting_xi_rows
from src.optimisation.squad_contingency import (
    SquadContingencyError,
    choose_contingency_lineup,
)
from src.optimisation.rebuild import _chip_kind, enumerate_bounded_rebuild_squads
from src.optimisation.transfers import (
    apply_transfers,
    enumerate_transfer_sets,
    index_players,
    owned_records,
)
from src.optimisation.types import SOLVER_VERSION, SolverInput
from src.scoring.rules_loader import get_rule
from src.scoring.validator import legal_formations, validate_chips


def _objective(
    lineup: dict[str, Any],
    *,
    hit_cost: int,
    active_chip: str | None,
) -> float:
    """Single-GW objective: XI EP with captaincy (− hits) (+ bench if Bench Boost)."""
    xi = lineup["starting_xi"]
    by_id = {str(p["player_id"]): float(p["expected_points"]) for p in xi}
    base = sum(by_id.values())
    cap = by_id.get(str(lineup["captain_id"]), 0.0)
    # Default captain already doubles in choose_starting_xi expected_xi_points;
    # recompute explicitly for chip modifiers.
    if active_chip and "triple_captain" in active_chip:
        points = base + 2.0 * cap  # total captain multiplier 3×
    else:
        points = base + cap  # 2× captain
    if active_chip and "bench_boost" in active_chip:
        points += sum(float(p["expected_points"]) for p in lineup["bench"])
    return round(points - float(hit_cost), 4)


def apply_transfer_hit_gate(
    solver_output: Mapping[str, Any],
    gate_artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a copied solver output whose selection passed the sealed hit gate."""

    from src.evaluation.transfer_counterfactual import (
        validate_transfer_counterfactual_ladder,
    )

    base_input = SolverInput.from_dict(dict(gate_artifact["solver_input"]))
    validate_transfer_counterfactual_ladder(
        gate_artifact,
        solver_input=base_input,
        solver_output=solver_output,
    )
    result = deepcopy(dict(solver_output))
    result["ungated_selected"] = deepcopy(result.get("selected"))
    result["selected"] = deepcopy(
        dict(gate_artifact["selected"]["candidate"])
    )
    if isinstance(result.get("plans"), dict):
        result["plans"]["highest_ev"] = deepcopy(result["selected"])
    result["transfer_hit_gate"] = {
        "policy_id": str(gate_artifact["policy_id"]),
        "artifact_sha256": str(gate_artifact["content_sha256"]),
        "selected_candidate_id": str(
            gate_artifact["selected"]["candidate_id"]
        ),
        "active_chip": gate_artifact["selected"].get("active_chip"),
        "risk_premium_points_per_paid_transfer": float(
            gate_artifact["verdict"][
                "risk_premium_points_per_paid_transfer"
            ]
        ),
        "forecast_uncertainty_points_per_paid_transfer": float(
            gate_artifact["verdict"][
                "forecast_uncertainty_points_per_paid_transfer"
            ]
        ),
    }
    result["output_fingerprint"] = fingerprint(
        {
            key: result[key]
            for key in ("solver_version", "selected", "plans")
            if key in result
        }
    )
    return result


def _evaluate_squad(
    squad_rows: list[dict[str, Any]],
    *,
    transfers: list[dict[str, str]],
    hit_cost: int,
    bank: float,
    strategy: str,
    active_chip: str | None,
    formations: Sequence[Mapping[str, int]],
    position_counts: Mapping[str, int],
    max_per_club: int,
    chip_ok: bool,
    squad_contingency_policy: str = "none",
    appearance_calibration: Mapping[str, Any] | None = None,
    formation_constraints: Mapping[str, Any] | None = None,
    allow_club_limit_exception: bool = False,
    contingency_lineup_cache: dict[tuple[Any, ...], dict[str, Any]] | None = None,
    contingency_evaluation_cache: dict[tuple[Any, ...], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if len(squad_rows) != 15 or len({str(row["player_id"]) for row in squad_rows}) != 15:
        return None
    positions = Counter(str(row["position"]) for row in squad_rows)
    if any(positions.get(position, 0) != expected for position, expected in position_counts.items()):
        return None
    clubs = Counter(str(row["club_id"]) for row in squad_rows)
    club_limit_exceeded = any(
        count > max_per_club for count in clubs.values()
    )
    if (
        club_limit_exceeded
        and not allow_club_limit_exception
    ) or not chip_ok:
        return None

    try:
        if squad_contingency_policy == "probabilistic_v1":
            if appearance_calibration is None or formation_constraints is None:
                raise SquadContingencyError(
                    "Contingency planning requires calibration and constraints"
                )
            lineup = choose_contingency_lineup(
                squad_rows,
                formations=formations,
                calibration=appearance_calibration,
                constraints=formation_constraints,
                active_chip=active_chip,
                lineup_cache=contingency_lineup_cache,
                evaluation_cache=contingency_evaluation_cache,
            )
        else:
            lineup = choose_starting_xi_rows(squad_rows, formations=formations)
    except (ValueError, SquadContingencyError):
        return None

    if squad_contingency_policy == "probabilistic_v1":
        obj = round(
            float(lineup["contingency"]["planning_value"]) - float(hit_cost), 4
        )
    else:
        obj = _objective(lineup, hit_cost=hit_cost, active_chip=active_chip)
    result = {
        "strategy": strategy,
        "transfers": transfers,
        "hit_cost": hit_cost,
        "bank_after": bank,
        "objective": obj,
        "lineup": {
            "formation": lineup["formation"],
            "starting_xi_ids": [str(p["player_id"]) for p in lineup["starting_xi"]],
            "bench_ids": [str(p["player_id"]) for p in lineup["bench"]],
            "captain_id": str(lineup["captain_id"]),
            "vice_captain_id": str(lineup["vice_captain_id"]),
        },
        "validation": {
            "squad_ok": True,
            "lineup_ok": True,
            "chips_ok": chip_ok,
        },
    }
    if squad_contingency_policy == "probabilistic_v1":
        result["contingency"] = lineup["contingency"]
        result["objective_without_hits"] = round(
            float(lineup["contingency"]["planning_value"]), 4
        )
    return result


def solve(
    solver_input: SolverInput,
    *,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Return candidate plans and a selected highest-EV plan. Deterministic."""
    rules_dict = dict(rules)
    if len(ruleset_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in ruleset_sha256
    ):
        raise ValueError("ruleset_sha256 must be a lower-case SHA-256")
    if solver_input.ruleset_mismatch_policy not in {"fail_closed", "allow_loaded"}:
        raise ValueError(
            "ruleset_mismatch_policy must be 'fail_closed' or 'allow_loaded'"
        )
    if solver_input.availability_policy not in {"available_only", "include_all"}:
        raise ValueError("availability_policy must be 'available_only' or 'include_all'")
    if solver_input.transfer_value_policy not in {
        "none",
        "expected_hit_avoidance_v1",
    }:
        raise ValueError(
            "transfer_value_policy must be 'none' or 'expected_hit_avoidance_v1'"
        )
    if solver_input.squad_contingency_policy not in {
        "none",
        "probabilistic_v1",
    }:
        raise ValueError(
            "squad_contingency_policy must be 'none' or 'probabilistic_v1'"
        )
    contingency_policy_active = (
        solver_input.squad_contingency_policy == "probabilistic_v1"
    )
    if contingency_policy_active and solver_input.appearance_calibration is None:
        raise ValueError("probabilistic_v1 requires an appearance_calibration")
    if (
        solver_input.search_candidate_budget is not None
        and (
            isinstance(solver_input.search_candidate_budget, bool)
            or solver_input.search_candidate_budget < 1
        )
    ):
        raise ValueError("search_candidate_budget must be a positive integer when set")
    if (
        solver_input.search_deadline_ms is not None
        and (
            isinstance(solver_input.search_deadline_ms, bool)
            or solver_input.search_deadline_ms < 1
        )
    ):
        raise ValueError("search_deadline_ms must be a positive integer when set")
    if not 0.0 <= solver_input.probability_extra_transfer_needed <= 1.0:
        raise ValueError("probability_extra_transfer_needed must be between 0 and 1")
    if not 0.0 <= solver_input.future_transfer_discount <= 1.0:
        raise ValueError("future_transfer_discount must be between 0 and 1")
    if solver_input.horizon_gameweeks != 1 or solver_input.discount_factors != [1.0]:
        raise ValueError(
            "This solver supports only horizon_gameweeks=1 with discount_factors=[1.0]; "
            "destination_horizon_gameweeks records the ADR-0023 target until multi-GW "
            "forecasts exist"
        )
    if solver_input.destination_horizon_gameweeks < 1:
        raise ValueError("destination_horizon_gameweeks must be positive")
    if not 0.0 <= solver_input.destination_discount_factor <= 1.0:
        raise ValueError("destination_discount_factor must be between 0 and 1")
    if solver_input.rebuild_beam_width < 1:
        raise ValueError("rebuild_beam_width must be positive")
    if solver_input.rebuild_max_expanded_nodes < 1:
        raise ValueError("rebuild_max_expanded_nodes must be positive")
    if (
        solver_input.rebuild_candidate_limit_per_position is not None
        and solver_input.rebuild_candidate_limit_per_position < 1
    ):
        raise ValueError("rebuild_candidate_limit_per_position must be positive")
    if not 0 <= solver_input.max_transfers <= 3:
        raise ValueError("max_transfers must be between 0 and 3 for this solver")
    if solver_input.sell_pool_per_pos < 1 or solver_input.buy_pool_per_pos < 1:
        raise ValueError("candidate pool limits must be positive")
    if solver_input.solver_version != SOLVER_VERSION:
        raise ValueError(
            f"input solver_version={solver_input.solver_version} differs from {SOLVER_VERSION}"
        )
    if solver_input.active_chip and solver_input.active_chip not in solver_input.chips_available:
        raise ValueError("active_chip must be present in chips_available")

    if solver_input.ruleset_id and solver_input.ruleset_id != rules_dict["meta"]["ruleset_id"]:
        if solver_input.ruleset_mismatch_policy == "fail_closed":
            raise ValueError(
                f"input ruleset_id={solver_input.ruleset_id} "
                f"differs from loaded {rules_dict['meta']['ruleset_id']}"
            )
        ruleset_note = (
            f"input ruleset_id={solver_input.ruleset_id} "
            f"differs from loaded {rules_dict['meta']['ruleset_id']}; "
            "explicit allow_loaded policy applied"
        )
    else:
        ruleset_note = None

    market = index_players(solver_input.players)
    for pid in solver_input.squad_player_ids:
        if pid not in market:
            raise KeyError(f"squad player {pid} missing from market")

    owned = owned_records(
        solver_input.squad_player_ids, market, rules=rules_dict
    )
    # Attach purchase prices from input players when present
    for row in owned:
        src = market[row["player_id"]]
        if src.get("purchase_price") is not None:
            row["purchase_price"] = float(src["purchase_price"])

    formations = legal_formations(rules_dict)
    formation_constraints = get_rule(
        rules_dict, "lineup.formation_constraints"
    )["value"]
    position_counts = get_rule(rules_dict, "squad.position_counts")["value"]
    max_per_club = int(get_rule(rules_dict, "squad.max_per_club")["value"])
    hit_cost_per_transfer = int(get_rule(rules_dict, "transfers.hit_cost")["value"])
    free_per_gameweek = int(
        get_rule(rules_dict, "transfers.free_per_gameweek")["value"]
    )
    max_banked = int(get_rule(rules_dict, "transfers.max_banked")["value"])
    option_policy_active = (
        solver_input.transfer_value_policy == "expected_hit_avoidance_v1"
    )
    option_unit_value = round(
        hit_cost_per_transfer
        * solver_input.probability_extra_transfer_needed
        * solver_input.future_transfer_discount,
        4,
    )
    chip_validation = validate_chips(
        [solver_input.active_chip] if solver_input.active_chip else [],
        gameweek=solver_input.gameweek,
        rules=rules_dict,
    )
    top_ranked: list[tuple[tuple[Any, ...], int, dict[str, Any]]] = []
    by_strategy: dict[str, dict[str, Any]] = {}
    by_transfer_count: dict[int, dict[str, Any]] = {}
    candidate_count = 0
    contingency_lineup_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    contingency_evaluation_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    search_started = time.perf_counter()
    deadline_seconds = (
        None
        if solver_input.search_deadline_ms is None
        else solver_input.search_deadline_ms / 1000.0
    )
    search_degraded = False
    search_degraded_reason: str | None = None
    searched_transfer_widths: list[int] = []
    incomplete_transfer_width: int | None = None
    baseline_state: tuple[
        list[tuple[tuple[Any, ...], int, dict[str, Any]]],
        dict[str, dict[str, Any]],
        dict[int, dict[str, Any]],
        int,
        dict[tuple[Any, ...], dict[str, Any]],
        dict[tuple[Any, ...], dict[str, Any]],
    ] | None = None

    def deadline_exceeded() -> bool:
        return (
            deadline_seconds is not None
            and (time.perf_counter() - search_started) >= deadline_seconds
        )

    def rank_key(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
        return (
            -float(candidate["objective"]),
            len(candidate["transfers"]),
            str(candidate["strategy"]),
            tuple(
                (transfer["player_out_id"], transfer["player_in_id"])
                for transfer in candidate["transfers"]
            ),
        )

    def consider(candidate: dict[str, Any] | None) -> None:
        nonlocal candidate_count
        if candidate is None:
            return
        if option_policy_active:
            transfer_count = len(candidate["transfers"])
            if solver_input.active_chip and (
                "wildcard" in solver_input.active_chip
                or "free_hit" in solver_input.active_chip
            ):
                next_free_transfers = solver_input.free_transfers
            else:
                next_free_transfers = min(
                    max_banked,
                    max(0, solver_input.free_transfers - transfer_count)
                    + free_per_gameweek,
                )
            banked_option_units = max(
                0, next_free_transfers - free_per_gameweek
            )
            immediate = float(
                candidate.get("immediate_objective", candidate["objective"])
            )
            transfer_option_value = round(
                banked_option_units * option_unit_value, 4
            )
            candidate.update(
                {
                    "immediate_objective": immediate,
                    "next_gameweek_free_transfers": next_free_transfers,
                    "banked_option_units": banked_option_units,
                    "transfer_option_value": transfer_option_value,
                    "objective": round(immediate + transfer_option_value, 4),
                }
            )
        candidate_count += 1
        strategy = str(candidate["strategy"])
        if strategy not in by_strategy or rank_key(candidate) < rank_key(
            by_strategy[strategy]
        ):
            by_strategy[strategy] = candidate
        transfer_count = len(candidate["transfers"])
        if transfer_count not in by_transfer_count or rank_key(
            candidate
        ) < rank_key(by_transfer_count[transfer_count]):
            by_transfer_count[transfer_count] = candidate
        insort(top_ranked, (rank_key(candidate), candidate_count, candidate))
        if len(top_ranked) > 50:
            top_ranked.pop()

    # --- no_transfer / bank_transfer ---
    base = _evaluate_squad(
        [dict(r) for r in owned],
        transfers=[],
        hit_cost=0,
        bank=solver_input.bank,
        strategy="no_transfer",
        active_chip=solver_input.active_chip,
        formations=formations,
        position_counts=position_counts,
        max_per_club=max_per_club,
        chip_ok=chip_validation.ok,
        squad_contingency_policy=solver_input.squad_contingency_policy,
        appearance_calibration=solver_input.appearance_calibration,
        formation_constraints=formation_constraints,
        allow_club_limit_exception=True,
        contingency_lineup_cache=contingency_lineup_cache,
        contingency_evaluation_cache=contingency_evaluation_cache,
    )
    if base:
        consider(base)
        if solver_input.free_transfers > 0:
            banked = dict(base)
            banked["strategy"] = "bank_transfer"
            consider(banked)

    baseline_state = (
        deepcopy(top_ranked),
        deepcopy(by_strategy),
        deepcopy(by_transfer_count),
        candidate_count,
        deepcopy(contingency_lineup_cache),
        deepcopy(contingency_evaluation_cache),
    )

    max_t = solver_input.max_transfers
    free = solver_input.free_transfers

    for n in range(1, max_t + 1):
        if not solver_input.allow_hits and n > free:
            break
        if (
            solver_input.search_candidate_budget is not None
            and candidate_count >= solver_input.search_candidate_budget
        ):
            search_degraded = True
            search_degraded_reason = "candidate_budget"
            incomplete_transfer_width = n
            break
        if deadline_exceeded():
            search_degraded = True
            search_degraded_reason = "operational_deadline"
            incomplete_transfer_width = n
            break
        # Wildcard / Free Hit: treat as unlimited free transfers for hit accounting
        effective_free = free
        if solver_input.active_chip and (
            "wildcard" in solver_input.active_chip or "free_hit" in solver_input.active_chip
        ):
            effective_free = max(effective_free, n)

        move_sets = enumerate_transfer_sets(
            owned,
            market,
            n_transfers=n,
            sell_pool_per_pos=solver_input.sell_pool_per_pos,
            buy_pool_per_pos=solver_input.buy_pool_per_pos,
            bank=solver_input.bank,
            availability_policy=solver_input.availability_policy,
            rules=rules_dict,
        )
        width_complete = True
        for moves in move_sets:
            if (
                solver_input.search_candidate_budget is not None
                and candidate_count >= solver_input.search_candidate_budget
            ):
                search_degraded = True
                search_degraded_reason = "candidate_budget"
                incomplete_transfer_width = n
                width_complete = False
                break
            if deadline_exceeded():
                search_degraded = True
                search_degraded_reason = "operational_deadline"
                incomplete_transfer_width = n
                width_complete = False
                break
            applied = apply_transfers(
                owned,
                moves,
                market,
                bank=solver_input.bank,
                free_transfers=effective_free,
                max_per_club=max_per_club,
                hit_cost_per_transfer=hit_cost_per_transfer,
            )
            if not applied:
                continue
            strategy = "no_hit" if applied["hit_cost"] == 0 else "hit"
            if n <= free and applied["hit_cost"] == 0:
                strategy = "free_transfer"
            plan = _evaluate_squad(
                [dict(r) for r in applied["squad"]],
                transfers=applied["transfers"],
                hit_cost=applied["hit_cost"],
                bank=applied["bank"],
                strategy=strategy,
                active_chip=solver_input.active_chip,
                formations=formations,
                position_counts=position_counts,
                max_per_club=max_per_club,
                chip_ok=chip_validation.ok,
                squad_contingency_policy=solver_input.squad_contingency_policy,
                appearance_calibration=solver_input.appearance_calibration,
                formation_constraints=formation_constraints,
                contingency_lineup_cache=contingency_lineup_cache,
                contingency_evaluation_cache=contingency_evaluation_cache,
            )
            consider(plan)
        if width_complete:
            searched_transfer_widths.append(n)
        else:
            break

    rebuild_kind = _chip_kind(solver_input.active_chip)
    rebuild_candidates = 0
    rebuild_fallback_used = False
    rebuild_degraded_reason: str | None = None
    if rebuild_kind is not None and not search_degraded:
        rebuild_limit = (
            solver_input.rebuild_candidate_limit_per_position
            if solver_input.rebuild_candidate_limit_per_position is not None
            else solver_input.buy_pool_per_pos
        )
        try:
            for applied in enumerate_bounded_rebuild_squads(
                owned,
                market,
                bank=solver_input.bank,
                position_counts=position_counts,
                max_per_club=max_per_club,
                candidate_limit_per_position=rebuild_limit,
                beam_width=solver_input.rebuild_beam_width,
                max_expanded_nodes=solver_input.rebuild_max_expanded_nodes,
                availability_policy=solver_input.availability_policy,
                rules=rules_dict,
            ):
                if (
                    solver_input.search_candidate_budget is not None
                    and candidate_count >= solver_input.search_candidate_budget
                ):
                    search_degraded = True
                    search_degraded_reason = "candidate_budget"
                    rebuild_degraded_reason = "candidate_budget"
                    break
                if deadline_exceeded():
                    search_degraded = True
                    search_degraded_reason = "operational_deadline"
                    rebuild_degraded_reason = "operational_deadline"
                    break
                strategy = f"{rebuild_kind}_rebuild"
                plan = _evaluate_squad(
                    [dict(r) for r in applied["squad"]],
                    transfers=applied["transfers"],
                    hit_cost=0,
                    bank=applied["bank"],
                    strategy=strategy,
                    active_chip=solver_input.active_chip,
                    formations=formations,
                    position_counts=position_counts,
                    max_per_club=max_per_club,
                    chip_ok=chip_validation.ok,
                    squad_contingency_policy=solver_input.squad_contingency_policy,
                    appearance_calibration=solver_input.appearance_calibration,
                    formation_constraints=formation_constraints,
                    contingency_lineup_cache=contingency_lineup_cache,
                    contingency_evaluation_cache=contingency_evaluation_cache,
                )
                if plan is not None:
                    rebuild_candidates += 1
                    consider(plan)
        except ValueError as exc:
            rebuild_fallback_used = True
            rebuild_degraded_reason = str(exc)
        if rebuild_candidates == 0:
            rebuild_fallback_used = True
            if rebuild_degraded_reason is None:
                rebuild_degraded_reason = "no_feasible_rebuild_in_bounds"

    if search_degraded_reason == "operational_deadline":
        if baseline_state is None:
            raise RuntimeError("deadline fallback baseline was not captured")
        (
            top_ranked,
            by_strategy,
            by_transfer_count,
            candidate_count,
            contingency_lineup_cache,
            contingency_evaluation_cache,
        ) = deepcopy(baseline_state)
        searched_transfer_widths = []
        rebuild_fallback_used = True

    top_candidates = [entry[2] for entry in top_ranked]
    selected = top_candidates[0] if top_candidates else None
    highest = dict(selected) if selected else None
    if search_degraded_reason == "candidate_budget":
        optimality = "highest_ev_in_deterministic_candidate_budget"
    elif search_degraded_reason == "operational_deadline":
        optimality = "deterministic_no_transfer_deadline_fallback"
    else:
        optimality = "highest_ev_in_declared_candidate_pool"
    if highest:
        highest["strategy"] = "highest_ev"

        highest["optimality"] = optimality
    output = {
        "solver_version": SOLVER_VERSION,
        "ruleset_id": rules_dict["meta"]["ruleset_id"],
        "ruleset_sha256": ruleset_sha256,
        "horizon_gameweeks": solver_input.horizon_gameweeks,
        "destination_horizon": {
            "horizon_gameweeks": solver_input.destination_horizon_gameweeks,
            "discount_factor": solver_input.destination_discount_factor,
            "live_active": False,
            "policy_alignment": "transfer-horizon-v1",
            "note": (
                "ADR-0023 destination; live objective remains single-GW until "
                "cutoff-safe multi-GW forecasts exist"
            ),
        },
        "input_fingerprint": fingerprint(solver_input.as_dict()),
        "ruleset_note": ruleset_note,
        "n_candidates": candidate_count,
        "search_scope": {
            "optimality": optimality,
            "global_optimality_guaranteed": False,
            "max_transfers": solver_input.max_transfers,
            "sell_pool_per_pos": solver_input.sell_pool_per_pos,
            "buy_pool_per_pos": solver_input.buy_pool_per_pos,
            "affordability_filter_before_ranking": True,
            "ruleset_mismatch_policy": solver_input.ruleset_mismatch_policy,
            "availability_policy": solver_input.availability_policy,
            "candidate_generation": "lazy",
            "retained_ranked_candidates": len(top_candidates),
            "full_rebuild_search": rebuild_kind is not None,
            "rebuild_kind": rebuild_kind,
            "rebuild_candidates": rebuild_candidates,
            "rebuild_fallback_used": rebuild_fallback_used,
            "rebuild_degraded_reason": rebuild_degraded_reason,
            "rebuild_beam_width": solver_input.rebuild_beam_width,
            "rebuild_max_expanded_nodes": solver_input.rebuild_max_expanded_nodes,
            "rebuild_candidate_limit_per_position": (
                solver_input.rebuild_candidate_limit_per_position
                if solver_input.rebuild_candidate_limit_per_position is not None
                else solver_input.buy_pool_per_pos
            ),
            "wildcard_free_hit_hit_accounting": True,
            "searched_transfer_widths": searched_transfer_widths,
            "search_degraded": search_degraded,
            "search_degraded_reason": search_degraded_reason,
            "search_candidate_budget": solver_input.search_candidate_budget,
            "search_deadline_ms": solver_input.search_deadline_ms,
            "incomplete_transfer_width": incomplete_transfer_width,
            "contingency_lineup_cache_entries": len(contingency_lineup_cache),
            "contingency_evaluation_cache_entries": len(contingency_evaluation_cache),
        },
        "selected": highest,
        "plans": {
            "highest_ev": highest,
            "no_transfer": by_strategy.get("no_transfer"),
            "bank_transfer": by_strategy.get("bank_transfer"),
            "no_hit": by_strategy.get("no_hit")
            or by_strategy.get("free_transfer")
            or by_strategy.get("no_transfer"),
            "free_transfer": by_strategy.get("free_transfer"),
            "hit": by_strategy.get("hit"),
            "wildcard_rebuild": by_strategy.get("wildcard_rebuild"),
            "free_hit_rebuild": by_strategy.get("free_hit_rebuild"),
        },
        "all_candidates": top_candidates,
    }
    if option_policy_active:
        output["transfer_value_policy"] = {
            "policy": solver_input.transfer_value_policy,
            "hit_cost_per_transfer": hit_cost_per_transfer,
            "probability_extra_transfer_needed": (
                solver_input.probability_extra_transfer_needed
            ),
            "future_transfer_discount": solver_input.future_transfer_discount,
            "option_unit_value": option_unit_value,
            "free_per_gameweek": free_per_gameweek,
            "max_banked": max_banked,
            "interpretation": (
                "expected discounted hit avoided per retained transfer; "
                "not a multi-Gameweek player forecast"
            ),
        }
        output["best_by_transfer_count"] = {
            str(count): candidate
            for count, candidate in sorted(by_transfer_count.items())
        }
    if contingency_policy_active:
        assert solver_input.appearance_calibration is not None
        output["squad_contingency_policy"] = {
            "policy": solver_input.squad_contingency_policy,
            "appearance_model_version": solver_input.appearance_calibration[
                "model_version"
            ],
            "appearance_calibration_sha256": solver_input.appearance_calibration[
                "content_sha256"
            ],
            "states": ["zero", "under_60", "60_plus"],
            "realised_scorer_changed": False,
            "interpretation": (
                "planning-time expected legal auto-substitution, goalkeeper, "
                "bench-order and vice-captain fallback value"
            ),
        }
    output["output_fingerprint"] = fingerprint(
        {k: output[k] for k in ("solver_version", "selected", "plans") if k in output}
    )
    return output
