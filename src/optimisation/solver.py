"""Transparent single-Gameweek optimiser (WP-07)."""

from __future__ import annotations

from bisect import insort
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from src.optimisation.io import fingerprint
from src.optimisation.simple_plan import choose_starting_xi_rows
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
    allow_club_limit_exception: bool = False,
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
        lineup = choose_starting_xi_rows(squad_rows, formations=formations)
    except ValueError:
        return None

    obj = _objective(lineup, hit_cost=hit_cost, active_chip=active_chip)
    return {
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
    if not 0.0 <= solver_input.probability_extra_transfer_needed <= 1.0:
        raise ValueError("probability_extra_transfer_needed must be between 0 and 1")
    if not 0.0 <= solver_input.future_transfer_discount <= 1.0:
        raise ValueError("future_transfer_discount must be between 0 and 1")
    if solver_input.horizon_gameweeks != 1 or solver_input.discount_factors != [1.0]:
        raise ValueError(
            "This solver supports only horizon_gameweeks=1 with discount_factors=[1.0]"
        )
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
        allow_club_limit_exception=True,
    )
    if base:
        consider(base)
        if solver_input.free_transfers > 0:
            banked = dict(base)
            banked["strategy"] = "bank_transfer"
            consider(banked)

    max_t = solver_input.max_transfers
    free = solver_input.free_transfers

    for n in range(1, max_t + 1):
        if not solver_input.allow_hits and n > free:
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
        for moves in move_sets:
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
            )
            consider(plan)

    top_candidates = [entry[2] for entry in top_ranked]
    selected = top_candidates[0] if top_candidates else None
    highest = dict(selected) if selected else None
    if highest:
        highest["strategy"] = "highest_ev"

        highest["optimality"] = "highest_ev_in_declared_candidate_pool"
    output = {
        "solver_version": SOLVER_VERSION,
        "ruleset_id": rules_dict["meta"]["ruleset_id"],
        "ruleset_sha256": ruleset_sha256,
        "horizon_gameweeks": solver_input.horizon_gameweeks,
        "input_fingerprint": fingerprint(solver_input.as_dict()),
        "ruleset_note": ruleset_note,
        "n_candidates": candidate_count,
        "search_scope": {
            "optimality": "highest_ev_in_declared_candidate_pool",
            "global_optimality_guaranteed": False,
            "max_transfers": solver_input.max_transfers,
            "sell_pool_per_pos": solver_input.sell_pool_per_pos,
            "buy_pool_per_pos": solver_input.buy_pool_per_pos,
            "affordability_filter_before_ranking": True,
            "ruleset_mismatch_policy": solver_input.ruleset_mismatch_policy,
            "availability_policy": solver_input.availability_policy,
            "candidate_generation": "lazy",
            "retained_ranked_candidates": len(top_candidates),
            "full_rebuild_search": False,
            "wildcard_free_hit_hit_accounting": True,
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
    output["output_fingerprint"] = fingerprint(
        {k: output[k] for k in ("solver_version", "selected", "plans") if k in output}
    )
    return output
