"""Season-aware FPL points from match events/stats using versioned rules."""

from __future__ import annotations

from typing import Any

from src.scoring.rules_loader import get_rule, load_rules
from src.scoring.validator import defensive_contribution_points


def appearance_points(minutes: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    table = get_rule(rules, "scoring.minutes")["value"]
    if minutes <= 0:
        return 0
    if minutes >= 60:
        return int(table["at_least_60"])
    return int(table["under_60"])


def goal_points(position: str, goals: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    return int(get_rule(rules, "scoring.goals")["value"][position]) * goals


def assist_points(assists: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    return int(get_rule(rules, "scoring.assists")["value"]) * assists


def clean_sheet_points(position: str, minutes: int, clean_sheet: bool, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    if not clean_sheet or minutes < 60:
        return 0
    return int(get_rule(rules, "scoring.clean_sheet")["value"].get(position, 0))


def save_points(saves: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    cfg = get_rule(rules, "scoring.saves")["value"]
    return (saves // int(cfg["n_saves"])) * int(cfg["points_per_n_saves"])


def goals_conceded_points(position: str, conceded: int, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    cfg = get_rule(rules, "scoring.goals_conceded")["value"]
    if position not in cfg["applies_to"]:
        return 0
    return (conceded // int(cfg["n_conceded"])) * int(cfg["points_per_n_conceded"])


def card_and_og_points(yellow: int = 0, red: int = 0, own_goals: int = 0, penalty_misses: int = 0, rules: dict[str, Any] | None = None) -> int:
    rules = rules or load_rules()
    cards = get_rule(rules, "scoring.cards_and_own_goals")["value"]
    miss = int(get_rule(rules, "scoring.penalty_miss")["value"])
    return (
        yellow * int(cards["yellow_card"])
        + red * int(cards["red_card"])
        + own_goals * int(cards["own_goal"])
        + penalty_misses * miss
    )


def score_match_stats(stats: dict[str, Any], rules: dict[str, Any] | None = None) -> dict[str, int]:
    """Return component and total points for one player-match stats row (excludes bonus)."""
    rules = rules or load_rules()
    position = stats["position"]
    minutes = int(stats.get("minutes", 0))
    components = {
        "appearance": appearance_points(minutes, rules),
        "goals": goal_points(position, int(stats.get("goals", 0)), rules),
        "assists": assist_points(int(stats.get("assists", 0)), rules),
        "clean_sheet": clean_sheet_points(position, minutes, bool(stats.get("clean_sheet")), rules),
        "saves": save_points(int(stats.get("saves", 0)), rules) if position == "GKP" else 0,
        "penalty_saves": int(get_rule(rules, "scoring.penalty_save")["value"]) * int(stats.get("penalty_saves", 0)),
        "goals_conceded": goals_conceded_points(position, int(stats.get("goals_conceded", 0)), rules),
        "defensive_contribution": defensive_contribution_points(
            position, int(stats.get("defensive_actions", 0)), rules
        ),
        "cards_og_misses": card_and_og_points(
            yellow=int(stats.get("yellow_cards", 0)),
            red=int(stats.get("red_cards", 0)),
            own_goals=int(stats.get("own_goals", 0)),
            penalty_misses=int(stats.get("penalty_misses", 0)),
            rules=rules,
        ),
        "bonus": int(stats.get("bonus", 0)),
    }
    components["total"] = sum(v for k, v in components.items() if k != "total")
    return components


def award_bonus_from_bps(bps_by_player: dict[str, int], rules: dict[str, Any] | None = None) -> dict[str, int]:
    """Assign 3/2/1 bonus with official tie rules (plan / scoring guidance)."""
    rules = rules or load_rules()
    _ = get_rule(rules, "bonus.award")  # ensure rule present
    if not bps_by_player:
        return {}
    # Sort unique BPS descending
    ranked = sorted(bps_by_player.items(), key=lambda kv: (-kv[1], kv[0]))
    awards: dict[str, int] = {pid: 0 for pid in bps_by_player}

    # Group by score
    from itertools import groupby

    groups = [(score, [pid for pid, s in group]) for score, group in groupby(ranked, key=lambda kv: kv[1])]
    # groups already ordered by descending score because ranked is
    place_points = [3, 2, 1]
    place_idx = 0
    for score, pids in groups:
        if place_idx >= len(place_points):
            break
        pts = place_points[place_idx]
        for pid in pids:
            awards[pid] = pts
        # Advance place index by group size (ties consume subsequent places)
        place_idx += len(pids)
    return awards


def captain_points(
    captain_raw: int,
    captain_minutes: int,
    vice_raw: int,
    *,
    triple: bool = False,
    rules: dict[str, Any] | None = None,
) -> tuple[int, str]:
    """Apply captain multiplier with vice-captain fallback on zero minutes."""
    rules = rules or load_rules()
    mult = get_rule(rules, "scoring.captain_multiplier")["value"]
    factor = int(mult["triple_captain"] if triple else mult["normal"])
    if captain_minutes == 0 and get_rule(rules, "captain_fallback.vice_on_zero_minutes")["value"]:
        return vice_raw * factor, "vice_captain"
    return captain_raw * factor, "captain"


def apply_automatic_substitutions(
    starting_xi: list[dict[str, Any]],
    bench: list[dict[str, Any]],
    *,
    played_minutes: dict[str, int],
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Formation-preserving autosubs: replace non-playing starters from ordered bench.

    Goalkeepers only replace goalkeepers. Outfield replacements must keep formation legal
    (at least 3 DEF, 2 MID, 1 FWD after each swap).
    """
    rules = rules or load_rules()
    _ = get_rule(rules, "automatic_substitutions.formation_preserving")
    constraints = get_rule(rules, "lineup.formation_constraints")["value"]

    xi = [dict(p) for p in starting_xi]
    remaining_bench = [dict(p) for p in bench]

    def counts(players: list[dict[str, Any]]) -> dict[str, int]:
        from collections import Counter

        return Counter(p["position"] for p in players)

    def legal(players: list[dict[str, Any]]) -> bool:
        c = counts(players)
        for pos, bounds in constraints.items():
            n = c.get(pos, 0)
            if n < bounds["min"] or n > bounds["max"]:
                return False
        return len(players) == 11

    for i, starter in enumerate(list(xi)):
        sid = str(starter["player_id"])
        if played_minutes.get(sid, 0) > 0:
            continue
        for j, cand in enumerate(remaining_bench):
            if played_minutes.get(str(cand["player_id"]), 0) <= 0:
                continue
            if starter["position"] == "GKP" and cand["position"] != "GKP":
                continue
            if starter["position"] != "GKP" and cand["position"] == "GKP":
                continue
            trial = list(xi)
            trial[i] = cand
            if legal(trial):
                xi[i] = cand
                remaining_bench.pop(j)
                break
    return xi
