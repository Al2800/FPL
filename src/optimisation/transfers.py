"""Same-position transfer enumeration under budget and club constraints."""

from __future__ import annotations

from collections import Counter
from itertools import combinations, product
from typing import Any

from src.scoring.rules_loader import get_rule, load_rules
from src.scoring.validator import selling_price, transfer_hit_cost, validate_squad


def _ep(p: dict[str, Any]) -> float:
    if "expected_points" in p and p["expected_points"] is not None:
        return float(p["expected_points"])
    if "ep_next" in p and p["ep_next"] is not None:
        return float(p["ep_next"])
    return 0.0


def index_players(players: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(p["player_id"]): p for p in players}


def owned_records(
    squad_ids: list[str],
    market: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for pid in squad_ids:
        p = market[pid]
        rows.append(
            {
                "player_id": str(p["player_id"]),
                "position": p["position"],
                "club_id": str(p["club_id"]),
                "purchase_price": float(p.get("purchase_price", p["now_cost"])),
                "now_cost": float(p["now_cost"]),
                "expected_points": _ep(p),
                "web_name": p.get("web_name", ""),
                "status": p.get("status", "a"),
            }
        )
    return rows


def apply_transfers(
    owned: list[dict[str, Any]],
    moves: list[tuple[str, str]],
    market: dict[str, dict[str, Any]],
    *,
    bank: float,
    free_transfers: int,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Apply same-position swaps. Returns new squad payload or None if illegal."""
    rules = rules or load_rules()
    by_id = {r["player_id"]: dict(r) for r in owned}
    proceeds = 0.0
    spend = 0.0

    for out_id, in_id in moves:
        if out_id not in by_id or in_id in by_id:
            return None
        if in_id not in market:
            return None
        out_p = by_id[out_id]
        in_p = market[in_id]
        if out_p["position"] != in_p["position"]:
            return None
        sell = selling_price(float(out_p["purchase_price"]), float(out_p["now_cost"]), rules)
        buy = float(in_p["now_cost"])
        proceeds += sell
        spend += buy
        del by_id[out_id]
        by_id[in_id] = {
            "player_id": str(in_p["player_id"]),
            "position": in_p["position"],
            "club_id": str(in_p["club_id"]),
            "purchase_price": buy,
            "now_cost": buy,
            "expected_points": _ep(in_p),
            "web_name": in_p.get("web_name", ""),
            "status": in_p.get("status", "a"),
        }

    new_bank = bank + proceeds - spend
    if new_bank < -1e-9:
        return None

    squad_list = list(by_id.values())
    # validate_squad budget check uses purchase_price + bank vs initial_budget —
    # for mid-season we only enforce club/position/size here and bank non-negative.
    result = validate_squad(squad_list, bank=max(new_bank, 0.0), rules=rules)
    # Mid-season squads routinely exceed initial 100m TV; strip that specific error.
    filtered = [
        e
        for e in result.errors
        if not e.startswith("squad.initial_budget") and "budget" not in e.lower()
    ]
    # Re-check club/position manually already in validate_squad — keep non-budget errors
    hard_errors = [e for e in result.errors if "budget" not in e.lower() and "initial_budget" not in e]
    # Actually validate_squad message uses spent+bank > budget — always filter budget-related
    hard_errors = [
        e
        for e in result.errors
        if "squad.size" in e
        or "squad.position_counts" in e
        or "squad.max_per_club" in e
    ]
    if hard_errors:
        return None

    # Explicit club cap (validator already does this)
    max_club = get_rule(rules, "squad.max_per_club")["value"]
    clubs = Counter(p["club_id"] for p in squad_list)
    if any(n > max_club for n in clubs.values()):
        return None

    hit = transfer_hit_cost(len(moves), free_transfers, rules)
    return {
        "squad": squad_list,
        "bank": round(new_bank, 1),
        "hit_cost": hit,
        "transfers": [{"player_out_id": a, "player_in_id": b} for a, b in moves],
        "validation_errors": filtered,
    }


def enumerate_transfer_sets(
    owned: list[dict[str, Any]],
    market: dict[str, dict[str, Any]],
    *,
    n_transfers: int,
    sell_pool_per_pos: int,
    buy_pool_per_pos: int,
) -> list[list[tuple[str, str]]]:
    """Deterministic list of same-position transfer combinations of size n."""
    if n_transfers <= 0:
        return [[]]

    owned_ids = {p["player_id"] for p in owned}
    by_pos: dict[str, list[dict[str, Any]]] = {}
    for p in owned:
        by_pos.setdefault(p["position"], []).append(p)
    for pos in by_pos:
        by_pos[pos].sort(key=lambda r: (_ep(r), r["player_id"]))  # weakest first
        by_pos[pos] = by_pos[pos][:sell_pool_per_pos]

    buy_by_pos: dict[str, list[dict[str, Any]]] = {}
    for p in market.values():
        pid = str(p["player_id"])
        if pid in owned_ids:
            continue
        pos = p["position"]
        buy_by_pos.setdefault(pos, []).append(p)
    for pos in buy_by_pos:
        buy_by_pos[pos].sort(key=lambda r: (-_ep(r), str(r["player_id"])))
        buy_by_pos[pos] = buy_by_pos[pos][:buy_pool_per_pos]

    # Choose which owned players to sell (across positions), then match buys per position counts
    sell_candidates = [p for plist in by_pos.values() for p in plist]
    sell_candidates.sort(key=lambda r: (_ep(r), r["player_id"]))

    results: list[list[tuple[str, str]]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()

    for outs in combinations(sell_candidates, n_transfers):
        out_ids = [o["player_id"] for o in outs]
        if len(set(out_ids)) != n_transfers:
            continue
        pos_counts = Counter(o["position"] for o in outs)
        # For each position, choose that many buys
        pos_options: list[list[tuple[str, str]]] = []
        ok = True
        # Pair by position: for each pos, match outs to buys
        for pos, n in sorted(pos_counts.items()):
            buys = buy_by_pos.get(pos, [])
            if len(buys) < n:
                ok = False
                break
            pos_outs = sorted([o["player_id"] for o in outs if o["position"] == pos])
            buy_combos = []
            for buy_set in combinations(buys, n):
                buy_ids = sorted(str(b["player_id"]) for b in buy_set)
                # pair sorted out ids with sorted buy ids for determinism
                pairs = list(zip(pos_outs, buy_ids, strict=True))
                buy_combos.append(pairs)
            pos_options.append(buy_combos)
        if not ok:
            continue
        for combo in product(*pos_options):
            moves = [pair for group in combo for pair in group]
            moves.sort(key=lambda t: (t[0], t[1]))
            key = tuple(moves)
            if key in seen:
                continue
            seen.add(key)
            results.append(moves)

    results.sort(key=lambda m: tuple(m))
    return results
