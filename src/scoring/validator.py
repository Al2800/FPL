"""Deterministic squad, lineup, transfer and price validation against versioned rules."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from math import floor
from typing import Any

from src.scoring.rules_loader import get_rule, load_rules


POSITIONS = ("GKP", "DEF", "MID", "FWD")


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hit_cost: int = 0
    ruleset_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "hit_cost": self.hit_cost,
            "ruleset_id": self.ruleset_id,
        }


def club_limit_exceptions(
    players: list[dict[str, Any]],
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Describe club-limit overflow caused by an in-season player club change."""

    rules = rules or load_rules()
    maximum = int(get_rule(rules, "squad.max_per_club")["value"])
    clubs = Counter(str(player["club_id"]) for player in players)
    return [
        {
            "club_id": club_id,
            "player_count": count,
            "maximum": maximum,
            "reason": "player_transferred_between_premier_league_clubs",
            "must_resolve_when_next_transfer_made": True,
        }
        for club_id, count in sorted(clubs.items())
        if count > maximum
    ]


def legal_formations(rules: dict[str, Any] | None = None) -> list[dict[str, int]]:
    """Enumerate every legal outfield formation from the active ruleset."""
    rules = rules or load_rules()
    xi_size = int(get_rule(rules, "lineup.starting_xi_size")["value"])
    constraints = get_rule(rules, "lineup.formation_constraints")["value"]
    goalkeeper = constraints["GKP"]
    if goalkeeper["min"] != goalkeeper["max"]:
        raise ValueError("lineup.formation_constraints: goalkeeper count must be fixed")
    outfield_size = xi_size - int(goalkeeper["min"])

    formations: list[dict[str, int]] = []
    for defenders in range(constraints["DEF"]["min"], constraints["DEF"]["max"] + 1):
        for midfielders in range(constraints["MID"]["min"], constraints["MID"]["max"] + 1):
            for forwards in range(constraints["FWD"]["min"], constraints["FWD"]["max"] + 1):
                if defenders + midfielders + forwards == outfield_size:
                    formations.append(
                        {"DEF": defenders, "MID": midfielders, "FWD": forwards}
                    )
    return formations


def selling_price(purchase: float, current: float, rules: dict[str, Any] | None = None) -> float:
    """Half-profit selling price, rounded down to 0.1."""
    rules = rules or load_rules()
    rule = get_rule(rules, "prices.selling_half_profit")
    rise_share = float(rule["value"]["rise_share_kept"])
    step = float(rule["value"]["round_down_to"])
    if current <= purchase:
        return round(current, 1)
    rise = current - purchase
    kept = floor((rise * rise_share) / step + 1e-9) * step
    return round(purchase + kept, 1)


def validate_squad(
    players: list[dict[str, Any]],
    *,
    bank: float = 0.0,
    rules: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate a 15-player squad.

    Each player dict needs: player_id, position (GKP|DEF|MID|FWD), club_id, purchase_price.
    """
    rules = rules or load_rules()
    result = ValidationResult(ok=True, ruleset_id=rules["meta"]["ruleset_id"])
    size = get_rule(rules, "squad.size")["value"]
    positions = get_rule(rules, "squad.position_counts")["value"]
    max_club = get_rule(rules, "squad.max_per_club")["value"]
    budget = get_rule(rules, "squad.initial_budget")["value"]

    if len(players) != size:
        result.errors.append(f"squad.size: expected {size}, got {len(players)}")

    player_ids = [str(p["player_id"]) for p in players]
    if len(set(player_ids)) != len(player_ids):
        result.errors.append("squad.player_unique: player IDs must be unique")

    counts = Counter(p["position"] for p in players)
    for pos, expected in positions.items():
        if counts.get(pos, 0) != expected:
            result.errors.append(
                f"squad.position_counts: {pos} expected {expected}, got {counts.get(pos, 0)}"
            )

    clubs = Counter(p["club_id"] for p in players)
    for club, n in clubs.items():
        if n > max_club:
            result.errors.append(f"squad.max_per_club: club {club} has {n} > {max_club}")

    spent = sum(float(p["purchase_price"]) for p in players)
    if spent + bank > budget + 1e-9 and bank == 0.0:
        # For initial squad construction only; in-season squads use selling prices.
        pass
    if spent > budget + 1e-9 and all("selling_price" not in p for p in players):
        result.errors.append(f"squad.initial_budget: spent {spent:.1f} > budget {budget}")

    result.ok = not result.errors
    return result


def validate_lineup(
    starting_xi: list[dict[str, Any]],
    bench: list[dict[str, Any]],
    *,
    captain_id: str | None,
    vice_captain_id: str | None,
    rules: dict[str, Any] | None = None,
) -> ValidationResult:
    rules = rules or load_rules()
    result = ValidationResult(ok=True, ruleset_id=rules["meta"]["ruleset_id"])
    xi_size = get_rule(rules, "lineup.starting_xi_size")["value"]
    constraints = get_rule(rules, "lineup.formation_constraints")["value"]
    bench_rule = get_rule(rules, "lineup.bench_order")["value"]

    if len(starting_xi) != xi_size:
        result.errors.append(f"lineup.starting_xi_size: expected {xi_size}, got {len(starting_xi)}")

    counts = Counter(p["position"] for p in starting_xi)
    for pos, bounds in constraints.items():
        n = counts.get(pos, 0)
        if n < bounds["min"] or n > bounds["max"]:
            result.errors.append(
                f"lineup.formation_constraints: {pos}={n} outside [{bounds['min']},{bounds['max']}]"
            )

    if get_rule(rules, "lineup.captain_required")["value"] and not captain_id:
        result.errors.append("lineup.captain_required: captain missing")
    if get_rule(rules, "lineup.vice_captain_required")["value"] and not vice_captain_id:
        result.errors.append("lineup.vice_captain_required: vice-captain missing")

    start_id_list = [str(p["player_id"]) for p in starting_xi]
    bench_id_list = [str(p["player_id"]) for p in bench]
    start_ids = set(start_id_list)
    bench_ids = set(bench_id_list)
    if len(start_ids) != len(start_id_list):
        result.errors.append("lineup.player_unique: starting XI player IDs must be unique")
    if len(bench_ids) != len(bench_id_list):
        result.errors.append("lineup.player_unique: bench player IDs must be unique")
    if start_ids & bench_ids:
        result.errors.append("lineup.xi_bench_disjoint: starting XI and bench must be disjoint")

    captain_id = str(captain_id) if captain_id is not None else None
    vice_captain_id = str(vice_captain_id) if vice_captain_id is not None else None
    if captain_id and captain_id not in start_ids:
        result.errors.append("lineup.captain_required: captain must be in starting XI")
    if vice_captain_id and vice_captain_id not in start_ids:
        result.errors.append("lineup.vice_captain_required: vice-captain must be in starting XI")
    if captain_id and vice_captain_id and captain_id == vice_captain_id:
        result.errors.append("lineup: captain and vice-captain must differ")

    if len(bench) != bench_rule["bench_size"]:
        result.errors.append(
            f"lineup.bench_order: expected bench size {bench_rule['bench_size']}, got {len(bench)}"
        )

    full_position_counts = get_rule(rules, "squad.position_counts")["value"]
    selected_counts = Counter(p["position"] for p in starting_xi + bench)
    for pos, expected in full_position_counts.items():
        if selected_counts.get(pos, 0) != expected:
            result.errors.append(
                "lineup.bench_composition: "
                f"XI plus bench {pos} expected {expected}, got {selected_counts.get(pos, 0)}"
            )

    result.ok = not result.errors
    return result


def transfer_hit_cost(n_transfers: int, free_available: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    hit = int(get_rule(rules, "transfers.hit_cost")["value"])
    extras = max(0, n_transfers - free_available)
    return extras * hit


def banked_transfers(previous_banked: int, used: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    free_per = int(get_rule(rules, "transfers.free_per_gameweek")["value"])
    max_banked = int(get_rule(rules, "transfers.max_banked")["value"])
    available = min(max_banked, previous_banked + free_per)
    remaining = max(0, available - used)
    return min(max_banked, remaining)


def defensive_contribution_points(position: str, actions: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    thresholds = get_rule(rules, "defensive_contributions.thresholds")["value"]
    if position == "GKP" or not thresholds.get("goalkeepers_eligible", False) and position == "GKP":
        return 0
    pos_rule = thresholds.get(position)
    if not pos_rule:
        return 0
    if actions >= pos_rule["threshold"]:
        return int(min(pos_rule["points"], thresholds["max_points_per_match"]))
    return 0


def validate_chips(active_chips: list[str], *, gameweek: int, rules: dict[str, Any] | None = None) -> ValidationResult:
    rules = rules or load_rules()
    result = ValidationResult(ok=True, ruleset_id=rules["meta"]["ruleset_id"])
    if get_rule(rules, "chips.one_per_gameweek")["value"] and len(active_chips) > 1:
        result.errors.append("chips.one_per_gameweek: more than one chip active")
    expiry_gw = get_rule(rules, "chips.first_half_expiry")["value"]["expires_at_gameweek"]
    first_half_chips = {"wildcard_fh", "free_hit_fh", "triple_captain_fh", "bench_boost_fh"}
    if gameweek > expiry_gw and any(c in first_half_chips for c in active_chips):
        result.errors.append("chips.first_half_expiry: first-half chip used after expiry")
    result.ok = not result.errors
    return result
