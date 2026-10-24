"""Spend leftover initial-squad budget without changing a path's 15-slot shape."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

from src.optimisation.five_path_squads import path_player_ids
from src.optimisation.initial_squad import (
    InitialSquadError,
    score_declared_initial_squad,
)
from src.scoring.rules_loader import get_rule
from src.scoring.validator import POSITIONS, validate_squad

BUDGET = 100.0


def discounted_ep(row: Mapping[str, Any], discounts: Sequence[float]) -> float:
    return sum(
        float(discount) * float(points)
        for discount, points in zip(discounts, row["expected_points"], strict=True)
    )


def squad_cost(ids: Sequence[str], by_id: Mapping[str, Mapping[str, Any]]) -> float:
    return round(sum(float(by_id[str(player_id)]["now_cost"]) for player_id in ids), 1)


def _legal_ids(
    ids: Sequence[str],
    *,
    by_id: Mapping[str, Mapping[str, Any]],
    rules: Mapping[str, Any],
    max_per_club: int,
) -> bool:
    if len(ids) != 15 or len(set(ids)) != 15:
        return False
    unknown = [player_id for player_id in ids if str(player_id) not in by_id]
    if unknown:
        return False
    clubs: dict[str, int] = {}
    counts = {position: 0 for position in POSITIONS}
    rows = []
    for player_id in ids:
        row = by_id[str(player_id)]
        club = str(row["club_id"])
        clubs[club] = clubs.get(club, 0) + 1
        if clubs[club] > max_per_club:
            return False
        counts[str(row["position"])] += 1
        rows.append(
            {
                "player_id": str(row["player_id"]),
                "position": row["position"],
                "club_id": str(row["club_id"]),
                "purchase_price": float(row["now_cost"]),
                "now_cost": float(row["now_cost"]),
            }
        )
    if counts != {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}:
        return False
    spent = squad_cost(ids, by_id)
    if spent > BUDGET + 1e-9:
        return False
    bank = round(BUDGET - spent, 1)
    return validate_squad(rows, bank=bank, rules=rules).ok


def _replacements(
    outgoing: Mapping[str, Any],
    *,
    by_id: Mapping[str, Mapping[str, Any]],
    owned: set[str],
    min_extra: float,
    max_extra: float,
    discounts: Sequence[float],
    limit: int,
) -> list[dict[str, Any]]:
    position = str(outgoing["position"])
    old_cost = float(outgoing["now_cost"])
    old_ep = discounted_ep(outgoing, discounts)
    ranked: list[dict[str, Any]] = []
    for row in by_id.values():
        if str(row["player_id"]) in owned:
            continue
        if str(row["position"]) != position:
            continue
        extra = round(float(row["now_cost"]) - old_cost, 1)
        if extra < min_extra - 1e-9 or extra > max_extra + 1e-9:
            continue
        gain = discounted_ep(row, discounts) - old_ep
        ranked.append(
            {
                "in_id": str(row["player_id"]),
                "in_name": str(row["web_name"]),
                "out_id": str(outgoing["player_id"]),
                "out_name": str(outgoing["web_name"]),
                "extra": extra,
                "ep_gain": round(gain, 4),
                "in_cost": float(row["now_cost"]),
            }
        )
    ranked.sort(key=lambda item: (-item["ep_gain"], item["extra"], item["in_id"]))
    return ranked[:limit]


def spend_remaining_candidates(
    path: Mapping[str, Any],
    packet: Mapping[str, Any],
    *,
    rules: Mapping[str, Any],
    one_for_one_limit: int = 8,
    two_for_two_limit: int = 5,
) -> dict[str, Any]:
    """Propose legal upgrades that spend leftover bank, ranked by EP gain."""

    by_id = {str(row["player_id"]): row for row in packet["players"]}
    discounts = [float(item) for item in packet["discount_factors"]]
    max_per_club = int(get_rule(dict(rules), "squad.max_per_club")["value"])
    base_ids = path_player_ids(path)
    owned = set(base_ids)
    spent = squad_cost(base_ids, by_id)
    bank = round(BUDGET - spent, 1)
    result: dict[str, Any] = {
        "path_id": path["path_id"],
        "spent": spent,
        "bank": bank,
        "candidates": [],
    }
    if any(player_id not in by_id for player_id in base_ids):
        result["error"] = "path references players absent from the packet"
        return result
    if bank <= 0:
        return result

    seen: set[tuple[str, ...]] = set()

    def consider(ids: list[str], moves: list[dict[str, Any]]) -> None:
        key = tuple(sorted(ids))
        if key in seen:
            return
        if not _legal_ids(
            ids, by_id=by_id, rules=rules, max_per_club=max_per_club
        ):
            return
        seen.add(key)
        extra = round(squad_cost(ids, by_id) - spent, 1)
        ep_gain = round(sum(float(move["ep_gain"]) for move in moves), 4)
        leftover = round(BUDGET - squad_cost(ids, by_id), 1)
        result["candidates"].append(
            {
                "squad_player_ids": ids,
                "moves": moves,
                "extra_spend": extra,
                "bank_after": leftover,
                "ep_gain": ep_gain,
                "exhausts_budget": leftover == 0.0,
            }
        )

    for outgoing_id in base_ids:
        outgoing = by_id[outgoing_id]
        for move in _replacements(
            outgoing,
            by_id=by_id,
            owned=owned,
            min_extra=0.1,
            max_extra=bank,
            discounts=discounts,
            limit=one_for_one_limit,
        ):
            ids = [move["in_id"] if item == outgoing_id else item for item in base_ids]
            consider(ids, [move])

    if bank >= 1.0:
        for out_a, out_b in combinations(base_ids, 2):
            if by_id[out_a]["position"] == by_id[out_b]["position"]:
                owned_pair = owned
            else:
                owned_pair = owned
            options_a = _replacements(
                by_id[out_a],
                by_id=by_id,
                owned=owned_pair,
                min_extra=0.1,
                max_extra=bank,
                discounts=discounts,
                limit=two_for_two_limit,
            )
            options_b = _replacements(
                by_id[out_b],
                by_id=by_id,
                owned=owned_pair,
                min_extra=0.1,
                max_extra=bank,
                discounts=discounts,
                limit=two_for_two_limit,
            )
            for move_a in options_a:
                for move_b in options_b:
                    if move_a["in_id"] == move_b["in_id"]:
                        continue
                    extra = round(float(move_a["extra"]) + float(move_b["extra"]), 1)
                    if extra > bank + 1e-9:
                        continue
                    ids = []
                    for item in base_ids:
                        if item == out_a:
                            ids.append(move_a["in_id"])
                        elif item == out_b:
                            ids.append(move_b["in_id"])
                        else:
                            ids.append(item)
                    consider(ids, [move_a, move_b])

    result["candidates"].sort(
        key=lambda item: (
            -int(item["exhausts_budget"]),
            -item["ep_gain"],
            -item["extra_spend"],
            item["squad_player_ids"][0],
        )
    )
    return result


def score_spend_candidates(
    packet: Mapping[str, Any],
    path: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    *,
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    arm_mode: str = "robust",
    limit: int = 8,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for candidate in list(candidates)[:limit]:
        try:
            result = score_declared_initial_squad(
                packet,
                candidate["squad_player_ids"],
                policy=policy,
                arm_mode=arm_mode,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
        except InitialSquadError as exc:
            scored.append({**dict(candidate), "ok": False, "error": str(exc)})
            continue
        first = result["weekly_plans"][0]["lineup"]
        by_id = {str(row["player_id"]): str(row["web_name"]) for row in result["squad"]}
        scored.append(
            {
                **dict(candidate),
                "ok": True,
                "objective": result["objective"],
                "bank": result["bank"],
                "proposal_sha256": result["proposal_sha256"],
                "captain": by_id[str(first["captain_id"])],
                "vice": by_id[str(first["vice_captain_id"])],
                "xi": [by_id[str(player_id)] for player_id in first["starting_xi"]],
                "bench": [by_id[str(player_id)] for player_id in first["bench"]],
            }
        )
    return scored
