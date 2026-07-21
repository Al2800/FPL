"""Transparent single-Gameweek optimiser (WP-07)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.optimisation.io import fingerprint
from src.optimisation.simple_plan import choose_starting_xi
from src.optimisation.transfers import (
    apply_transfers,
    enumerate_transfer_sets,
    index_players,
    owned_records,
)
from src.optimisation.types import SOLVER_VERSION, SolverInput
from src.scoring.rules_loader import load_rules
from src.scoring.validator import validate_chips, validate_lineup, validate_squad


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
    gameweek: int,
    rules: dict[str, Any],
) -> dict[str, Any] | None:
    # Skip initial-budget trap for in-season squads
    for row in squad_rows:
        row.setdefault("selling_price", row.get("now_cost", row["purchase_price"]))

    squad_val = validate_squad(squad_rows, bank=bank, rules=rules)
    hard = [e for e in squad_val.errors if "initial_budget" not in e]
    if hard:
        return None

    chip_val = validate_chips([active_chip] if active_chip else [], gameweek=gameweek, rules=rules)
    if not chip_val.ok:
        return None

    df = pd.DataFrame(squad_rows)
    try:
        lineup = choose_starting_xi(df)
    except ValueError:
        return None

    lineup_val = validate_lineup(
        lineup["starting_xi"],
        lineup["bench"],
        captain_id=lineup["captain_id"],
        vice_captain_id=lineup["vice_captain_id"],
        rules=rules,
    )
    if not lineup_val.ok:
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
            "chips_ok": chip_val.ok,
        },
    }


def solve(solver_input: SolverInput) -> dict[str, Any]:
    """Return candidate plans and a selected highest-EV plan. Deterministic."""
    rules = load_rules()
    if solver_input.ruleset_id and solver_input.ruleset_id != rules["meta"]["ruleset_id"]:
        # Soft warning only — still solve under loaded rules
        ruleset_note = (
            f"input ruleset_id={solver_input.ruleset_id} "
            f"differs from loaded {rules['meta']['ruleset_id']}"
        )
    else:
        ruleset_note = None

    market = index_players(solver_input.players)
    for pid in solver_input.squad_player_ids:
        if pid not in market:
            raise KeyError(f"squad player {pid} missing from market")

    owned = owned_records(solver_input.squad_player_ids, market)
    # Attach purchase prices from input players when present
    for row in owned:
        src = market[row["player_id"]]
        if src.get("purchase_price") is not None:
            row["purchase_price"] = float(src["purchase_price"])

    candidates: list[dict[str, Any]] = []

    # --- no_transfer / bank_transfer ---
    base = _evaluate_squad(
        [dict(r) for r in owned],
        transfers=[],
        hit_cost=0,
        bank=solver_input.bank,
        strategy="no_transfer",
        active_chip=solver_input.active_chip,
        gameweek=solver_input.gameweek,
        rules=rules,
    )
    if base:
        candidates.append(base)
        if solver_input.free_transfers > 0:
            banked = dict(base)
            banked["strategy"] = "bank_transfer"
            candidates.append(banked)

    max_t = min(solver_input.max_transfers, 3)
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
        )
        for moves in move_sets:
            applied = apply_transfers(
                owned,
                moves,
                market,
                bank=solver_input.bank,
                free_transfers=effective_free,
                rules=rules,
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
                gameweek=solver_input.gameweek,
                rules=rules,
            )
            if plan:
                candidates.append(plan)

    # Deduplicate by (transfers tuple, chip) keeping first (deterministic order)
    uniq: dict[tuple[Any, ...], dict[str, Any]] = {}
    for c in candidates:
        key = (
            tuple((t["player_out_id"], t["player_in_id"]) for t in c["transfers"]),
            c["strategy"] if c["strategy"] in {"no_transfer", "bank_transfer"} else "xfer",
            c["hit_cost"],
        )
        # Prefer richer strategy labels on identical transfer sets
        if key not in uniq:
            uniq[key] = c
        elif c["strategy"] == "bank_transfer" and uniq[key]["strategy"] == "no_transfer":
            # keep both via different keys — already handled
            pass

    # Stable sort: objective desc, fewer transfers, strategy name, transfer ids
    ranked = sorted(
        candidates,
        key=lambda c: (
            -c["objective"],
            len(c["transfers"]),
            c["strategy"],
            tuple((t["player_out_id"], t["player_in_id"]) for t in c["transfers"]),
        ),
    )

    by_strategy: dict[str, dict[str, Any]] = {}
    for c in ranked:
        by_strategy.setdefault(c["strategy"], c)

    selected = ranked[0] if ranked else None
    highest = dict(selected) if selected else None
    if highest:
        highest["strategy"] = "highest_ev"

    output = {
        "solver_version": SOLVER_VERSION,
        "ruleset_id": rules["meta"]["ruleset_id"],
        "horizon_gameweeks": solver_input.horizon_gameweeks,
        "input_fingerprint": fingerprint(solver_input.as_dict()),
        "ruleset_note": ruleset_note,
        "n_candidates": len(candidates),
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
        "all_candidates": ranked[:50],  # cap for artefact size
    }
    output["output_fingerprint"] = fingerprint(
        {k: output[k] for k in ("solver_version", "selected", "plans") if k in output}
    )
    return output
