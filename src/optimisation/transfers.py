"""Same-position transfer enumeration under budget and club constraints."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping
from itertools import combinations, product
from typing import Any

from src.scoring.validator import selling_price


def _ep(p: dict[str, Any]) -> float:
    if "expected_points" in p and p["expected_points"] is not None:
        return float(p["expected_points"])
    if "ep_next" in p and p["ep_next"] is not None:
        return float(p["ep_next"])
    return 0.0


def _forecast_fields(player: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve optional planning forecast fields through squad transitions."""

    return {
        key: player[key]
        for key in (
            "expected_minutes",
            "start_probability",
            "fixture_count",
            "appearance_distribution",
        )
        if player.get(key) is not None
    }


def index_players(players: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(p["player_id"]): p for p in players}


def owned_records(
    squad_ids: list[str],
    market: dict[str, dict[str, Any]],
    *,
    rules: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for pid in squad_ids:
        p = market[pid]
        purchase = float(p.get("purchase_price", p["now_cost"]))
        current = float(p["now_cost"])
        rows.append(
            {
                "player_id": str(p["player_id"]),
                "position": p["position"],
                "club_id": str(p["club_id"]),
                "purchase_price": purchase,
                "now_cost": current,
                "selling_price": selling_price(purchase, current, dict(rules)),
                "expected_points": _ep(p),
                "web_name": p.get("web_name", ""),
                "status": p.get("status", "a"),
                **_forecast_fields(p),
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
    max_per_club: int,
    hit_cost_per_transfer: int,
) -> dict[str, Any] | None:
    """Apply same-position swaps. Returns new squad payload or None if illegal."""
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
        sell = float(out_p["selling_price"])
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
            "selling_price": buy,
            "expected_points": _ep(in_p),
            "web_name": in_p.get("web_name", ""),
            "status": in_p.get("status", "a"),
            **_forecast_fields(in_p),
        }

    new_bank = bank + proceeds - spend
    if new_bank < -1e-9:
        return None

    squad_list = list(by_id.values())
    clubs = Counter(p["club_id"] for p in squad_list)
    if any(n > max_per_club for n in clubs.values()):
        return None

    hit = max(0, len(moves) - free_transfers) * hit_cost_per_transfer
    return {
        "squad": squad_list,
        "bank": round(new_bank, 1),
        "hit_cost": hit,
        "transfers": [{"player_out_id": a, "player_in_id": b} for a, b in moves],
        "validation_errors": [],
    }


def enumerate_transfer_sets(
    owned: list[dict[str, Any]],
    market: dict[str, dict[str, Any]],
    *,
    n_transfers: int,
    sell_pool_per_pos: int,
    buy_pool_per_pos: int,
    bank: float,
    availability_policy: str,
    rules: Mapping[str, Any] | None = None,
) -> Iterator[list[tuple[str, str]]]:
    """Deterministic transfer combinations from a finance-safe declared pool.

    Market rows are filtered by a conservative affordability upper bound before
    expected-points truncation. This prevents an unaffordable headline player
    from occupying a limited pool slot while a lower-ranked feasible player is
    silently discarded.
    """
    if n_transfers <= 0:
        yield []
        return

    owned_ids = {p["player_id"] for p in owned}
    by_pos: dict[str, list[dict[str, Any]]] = {}
    for p in owned:
        by_pos.setdefault(p["position"], []).append(p)
    for pos in by_pos:
        by_pos[pos].sort(key=lambda r: (_ep(r), r["player_id"]))  # weakest first
        by_pos[pos] = by_pos[pos][:sell_pool_per_pos]

    buy_by_pos: dict[str, list[dict[str, Any]]] = {}
    sale_values = sorted(
        (
            float(p["selling_price"])
            for p in owned
        ),
        reverse=True,
    )
    # Safe upper bound: no single incoming player in a feasible n-transfer set
    # can cost more than bank plus all sale proceeds available to that set.
    affordability_upper_bound = float(bank) + sum(sale_values[:n_transfers])
    for p in market.values():
        pid = str(p["player_id"])
        if pid in owned_ids:
            continue
        if availability_policy == "available_only" and p.get("status") != "a":
            continue
        if float(p["now_cost"]) > affordability_upper_bound + 1e-9:
            continue
        pos = p["position"]
        buy_by_pos.setdefault(pos, []).append(p)
    for pos in buy_by_pos:
        buy_by_pos[pos].sort(key=lambda r: (-_ep(r), str(r["player_id"])))
        buy_by_pos[pos] = buy_by_pos[pos][:buy_pool_per_pos]

    # Choose which owned players to sell (across positions), then match buys per position counts
    sell_candidates = [p for plist in by_pos.values() for p in plist]
    sell_candidates.sort(key=lambda r: (_ep(r), r["player_id"]))

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
            yield moves
