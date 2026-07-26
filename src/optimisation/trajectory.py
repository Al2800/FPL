"""Pure planning-state transitions for multi-Gameweek transfer search."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from typing import Any

from src.optimisation.transfers import apply_transfers, index_players, owned_records
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import get_rule
from src.scoring.validator import selling_price


class TrajectoryError(ValueError):
    """Raised when a projected state transition is illegal or inconsistent."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def trajectory_state_hash(state: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(dict(state))).hexdigest()


def initial_trajectory_state(
    solver_input: SolverInput,
    *,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    market = index_players(solver_input.players)
    squad = owned_records(solver_input.squad_player_ids, market, rules=rules)
    state = {
        "gameweek": int(solver_input.gameweek),
        "squad": sorted(squad, key=lambda row: str(row["player_id"])),
        "bank": round(float(solver_input.bank), 1),
        "free_transfers": int(solver_input.free_transfers),
    }
    validate_trajectory_state(state, rules=rules)
    return state


def validate_trajectory_state(
    state: Mapping[str, Any],
    *,
    rules: Mapping[str, Any],
) -> None:
    squad = list(state.get("squad", []))
    counts = Counter(str(row["position"]) for row in squad)
    expected = get_rule(dict(rules), "squad.position_counts")["value"]
    if len(squad) != 15 or counts != Counter(expected):
        raise TrajectoryError("planning squad has illegal size or positions")
    ids = [str(row["player_id"]) for row in squad]
    if len(set(ids)) != len(ids):
        raise TrajectoryError("planning squad player IDs must be unique")
    max_per_club = int(get_rule(dict(rules), "squad.max_per_club")["value"])
    if any(value > max_per_club for value in Counter(
        str(row["club_id"]) for row in squad
    ).values()):
        raise TrajectoryError("planning squad exceeds club limit")
    if round(float(state["bank"]), 1) < 0:
        raise TrajectoryError("planning bank cannot be negative")
    maximum = int(get_rule(dict(rules), "transfers.max_banked")["value"])
    if not 0 <= int(state["free_transfers"]) <= maximum:
        raise TrajectoryError("planning free transfers outside rule bounds")


def market_for_state(
    state: Mapping[str, Any],
    players: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Attach carried purchase prices to one projected market."""
    owned = {str(row["player_id"]): row for row in state["squad"]}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in players:
        row = deepcopy(dict(source))
        player_id = str(row["player_id"])
        if player_id in seen:
            raise TrajectoryError(f"duplicate projected player {player_id}")
        seen.add(player_id)
        if player_id in owned:
            row["purchase_price"] = float(owned[player_id]["purchase_price"])
        else:
            row["purchase_price"] = None
        result.append(row)
    missing = sorted(set(owned) - seen)
    if missing:
        raise TrajectoryError(f"projected market missing owned players: {missing}")
    return result


def _next_free_transfers(
    *,
    available: int,
    used: int,
    next_gameweek: int,
    rules: Mapping[str, Any],
) -> int:
    per_week = int(get_rule(dict(rules), "transfers.free_per_gameweek")["value"])
    maximum = int(get_rule(dict(rules), "transfers.max_banked")["value"])
    result = min(maximum, max(0, available - used) + per_week)
    exceptional = get_rule(
        dict(rules), "transfers.afcon_exceptional_topup"
    )["value"]
    if int(exceptional["gameweek"]) == next_gameweek:
        result = int(exceptional["top_up_to"])
    return result


def advance_trajectory_state(
    state: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    current_players: Sequence[Mapping[str, Any]],
    next_players: Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply one planned action and refresh quotes for the following week."""
    validate_trajectory_state(state, rules=rules)
    current_market = index_players(market_for_state(state, current_players))
    moves = [
        (str(move["player_out_id"]), str(move["player_in_id"]))
        for move in candidate.get("transfers", [])
    ]
    max_per_club = int(get_rule(dict(rules), "squad.max_per_club")["value"])
    hit_cost = int(get_rule(dict(rules), "transfers.hit_cost")["value"])
    applied = apply_transfers(
        [deepcopy(dict(row)) for row in state["squad"]],
        moves,
        current_market,
        bank=float(state["bank"]),
        free_transfers=int(state["free_transfers"]),
        max_per_club=max_per_club,
        hit_cost_per_transfer=hit_cost,
    )
    if applied is None:
        raise TrajectoryError("candidate transfer set is illegal in planning state")
    if int(candidate["hit_cost"]) != int(applied["hit_cost"]):
        raise TrajectoryError("candidate hit cost differs from state transition")
    if round(float(candidate["bank_after"]), 1) != round(float(applied["bank"]), 1):
        raise TrajectoryError("candidate bank differs from state transition")

    next_market = index_players([deepcopy(dict(row)) for row in next_players])
    refreshed: list[dict[str, Any]] = []
    for player in applied["squad"]:
        player_id = str(player["player_id"])
        if player_id not in next_market:
            raise TrajectoryError(f"next projected market missing {player_id}")
        quote = next_market[player_id]
        if str(quote["position"]) != str(player["position"]):
            raise TrajectoryError(f"position changed for {player_id}")
        purchase = round(float(player["purchase_price"]), 1)
        current = round(float(quote["now_cost"]), 1)
        refreshed.append(
            {
                **deepcopy(dict(player)),
                "club_id": str(quote["club_id"]),
                "purchase_price": purchase,
                "now_cost": current,
                "selling_price": selling_price(purchase, current, dict(rules)),
                "expected_points": float(quote["expected_points"]),
                "status": str(quote.get("status", "a")),
            }
        )
    result = {
        "gameweek": int(state["gameweek"]) + 1,
        "squad": sorted(refreshed, key=lambda row: str(row["player_id"])),
        "bank": round(float(applied["bank"]), 1),
        "free_transfers": _next_free_transfers(
            available=int(state["free_transfers"]),
            used=len(moves),
            next_gameweek=int(state["gameweek"]) + 1,
            rules=rules,
        ),
    }
    validate_trajectory_state(result, rules=rules)
    return result
