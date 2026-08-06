"""Bounded Wildcard / Free Hit full-squad rebuild enumeration (ADR-0022)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from src.optimisation.transfers import _ep, _forecast_fields
from src.scoring.validator import selling_price

POSITIONS = ("GKP", "DEF", "MID", "FWD")


def _chip_kind(active_chip: str | None) -> str | None:
    if not active_chip:
        return None
    token = str(active_chip).lower()
    if "wildcard" in token:
        return "wildcard"
    if "free_hit" in token:
        return "free_hit"
    return None


def rebuild_budget(
    owned: Sequence[Mapping[str, Any]],
    *,
    bank: float,
) -> float:
    """Cash available for a full rebuild: bank plus selling prices of the current squad."""

    return round(float(bank) + sum(float(row["selling_price"]) for row in owned), 1)


def build_rebuild_pools(
    owned: Sequence[Mapping[str, Any]],
    market: Mapping[str, Mapping[str, Any]],
    *,
    position_counts: Mapping[str, int],
    candidate_limit_per_position: int,
    availability_policy: str,
) -> dict[str, list[dict[str, Any]]]:
    """Per-position shortlists: keep owned + top market by expected points."""

    if candidate_limit_per_position < 1:
        raise ValueError("rebuild candidate_limit_per_position must be positive")

    owned_ids = {str(row["player_id"]) for row in owned}
    pools: dict[str, list[dict[str, Any]]] = {pos: [] for pos in POSITIONS}

    for row in owned:
        pos = str(row["position"])
        pools.setdefault(pos, []).append(dict(row))

    for player in market.values():
        pid = str(player["player_id"])
        if pid in owned_ids:
            continue
        if availability_policy == "available_only" and player.get("status") != "a":
            continue
        pos = str(player["position"])
        pools.setdefault(pos, []).append(
            {
                "player_id": pid,
                "position": pos,
                "club_id": str(player["club_id"]),
                "now_cost": float(player["now_cost"]),
                "purchase_price": float(player["now_cost"]),
                "selling_price": float(player["now_cost"]),
                "expected_points": _ep(dict(player)),
                "web_name": player.get("web_name", ""),
                "status": player.get("status", "a"),
                **_forecast_fields(player),
            }
        )

    for pos, required in position_counts.items():
        rows = pools.get(str(pos), [])
        rows.sort(
            key=lambda row: (
                -float(row["expected_points"]),
                float(row["now_cost"]),
                str(row["player_id"]),
            )
        )
        # Always retain owned players for the position even if outside the EP shortlist.
        owned_here = [row for row in rows if str(row["player_id"]) in owned_ids]
        others = [row for row in rows if str(row["player_id"]) not in owned_ids]
        limit = max(int(required), int(candidate_limit_per_position))
        shortlisted = owned_here + others[: max(0, limit - len(owned_here))]
        # De-duplicate while preserving order
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for row in shortlisted:
            pid = str(row["player_id"])
            if pid in seen:
                continue
            seen.add(pid)
            deduped.append(row)
        pools[str(pos)] = deduped
        if len(deduped) < int(required):
            raise ValueError(
                f"rebuild pool for {pos} has {len(deduped)} players; need {required}"
            )
    return pools


def enumerate_bounded_rebuild_squads(
    owned: Sequence[Mapping[str, Any]],
    market: Mapping[str, Mapping[str, Any]],
    *,
    bank: float,
    position_counts: Mapping[str, int],
    max_per_club: int,
    candidate_limit_per_position: int,
    beam_width: int,
    max_expanded_nodes: int,
    availability_policy: str,
    rules: Mapping[str, Any],
) -> Iterator[dict[str, Any]]:
    """Yield bounded rebuild squads as transfer payloads (hit_cost always 0)."""

    if beam_width < 1 or max_expanded_nodes < 1:
        raise ValueError("rebuild beam_width and max_expanded_nodes must be positive")

    pools = build_rebuild_pools(
        owned,
        market,
        position_counts=position_counts,
        candidate_limit_per_position=candidate_limit_per_position,
        availability_policy=availability_policy,
    )
    budget = rebuild_budget(owned, bank=bank)
    budget_tenths = int(round(budget * 10))
    owned_by_id = {str(row["player_id"]): dict(row) for row in owned}
    slots = [
        position
        for position in POSITIONS
        for _ in range(int(position_counts.get(position, 0)))
    ]

    frontier: list[dict[str, Any]] = [
        {
            "chosen": [],
            "cost_tenths": 0,
            "clubs": {},
            "ep": 0.0,
            "last_indices": {},
            "position_selected": {},
        }
    ]
    expanded = 0
    emitted = 0

    for position in slots:
        next_states: list[dict[str, Any]] = []
        for state in frontier:
            expanded += 1
            if expanded > max_expanded_nodes:
                return
            last = int(state["last_indices"].get(position, -1))
            selected_here = int(state["position_selected"].get(position, 0))
            remaining_here = int(position_counts[position]) - selected_here
            stop = len(pools[position]) - remaining_here + 1
            for index in range(last + 1, stop):
                row = pools[position][index]
                club_id = str(row["club_id"])
                club_count = int(state["clubs"].get(club_id, 0)) + 1
                if club_count > max_per_club:
                    continue
                cost = int(state["cost_tenths"]) + int(
                    round(float(row["now_cost"]) * 10)
                )
                if cost > budget_tenths:
                    continue
                clubs = dict(state["clubs"])
                clubs[club_id] = club_count
                last_indices = dict(state["last_indices"])
                last_indices[position] = index
                position_selected = dict(state["position_selected"])
                position_selected[position] = selected_here + 1
                next_states.append(
                    {
                        "chosen": [*state["chosen"], row],
                        "cost_tenths": cost,
                        "clubs": clubs,
                        "ep": round(
                            float(state["ep"]) + float(row["expected_points"]), 6
                        ),
                        "last_indices": last_indices,
                        "position_selected": position_selected,
                    }
                )
        if not next_states:
            return
        next_states.sort(
            key=lambda item: (
                -float(item["ep"]),
                int(item["cost_tenths"]),
                tuple(str(row["player_id"]) for row in item["chosen"]),
            )
        )
        frontier = next_states[:beam_width]

    for state in frontier:
        squad = [dict(row) for row in state["chosen"]]
        new_ids = {str(row["player_id"]) for row in squad}
        old_ids = set(owned_by_id)
        outs = sorted(old_ids - new_ids)
        ins = sorted(new_ids - old_ids)
        # Pair same-position outs/ins deterministically; leftover outs/ins imply
        # a structural change that must still be expressible as same-position moves.
        out_by_pos: dict[str, list[str]] = {}
        in_by_pos: dict[str, list[str]] = {}
        for out_id in outs:
            out_by_pos.setdefault(owned_by_id[out_id]["position"], []).append(out_id)
        market_rows = {str(p["player_id"]): p for p in market.values()}
        for in_id in ins:
            pos = str(
                next(row["position"] for row in squad if str(row["player_id"]) == in_id)
            )
            in_by_pos.setdefault(pos, []).append(in_id)
        moves: list[tuple[str, str]] = []
        ok = True
        for pos in sorted(set(out_by_pos) | set(in_by_pos)):
            left = out_by_pos.get(pos, [])
            right = in_by_pos.get(pos, [])
            if len(left) != len(right):
                ok = False
                break
            for out_id, in_id in zip(sorted(left), sorted(right), strict=True):
                moves.append((out_id, in_id))
        if not ok:
            continue
        moves.sort(key=lambda item: (item[0], item[1]))
        # Rebuild squad rows with purchase/selling semantics for kept vs bought.
        rebuilt: list[dict[str, Any]] = []
        for row in squad:
            pid = str(row["player_id"])
            if pid in owned_by_id:
                rebuilt.append(dict(owned_by_id[pid]))
                continue
            src = market_rows[pid]
            buy = float(src["now_cost"])
            rebuilt.append(
                {
                    "player_id": pid,
                    "position": src["position"],
                    "club_id": str(src["club_id"]),
                    "purchase_price": buy,
                    "now_cost": buy,
                    "selling_price": selling_price(buy, buy, dict(rules)),
                    "expected_points": _ep(dict(src)),
                    "web_name": src.get("web_name", ""),
                    "status": src.get("status", "a"),
                    **_forecast_fields(src),
                }
            )
        spent = sum(float(row["now_cost"]) for row in rebuilt)
        new_bank = round(budget - spent, 1)
        if new_bank < -1e-9:
            continue
        clubs = Counter(str(row["club_id"]) for row in rebuilt)
        if any(count > max_per_club for count in clubs.values()):
            continue
        emitted += 1
        yield {
            "squad": rebuilt,
            "bank": new_bank,
            "hit_cost": 0,
            "transfers": [
                {"player_out_id": out_id, "player_in_id": in_id}
                for out_id, in_id in moves
            ],
            "rebuild_expanded_nodes": expanded,
            "rebuild_emitted_index": emitted,
        }
