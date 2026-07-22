"""Deterministic validator behaviour for key golden cases."""

from copy import deepcopy

import pandas as pd
import pytest

from src.optimisation.simple_plan import choose_starting_xi
from src.scoring.rules_loader import load_rules
from src.scoring.validator import (
    banked_transfers,
    defensive_contribution_points,
    legal_formations,
    selling_price,
    transfer_hit_cost,
    validate_chips,
    validate_lineup,
    validate_squad,
)


def _player(pid, pos, club, price):
    return {
        "player_id": str(pid),
        "position": pos,
        "club_id": str(club),
        "purchase_price": price,
    }


def _legal_squad():
    return (
        [_player(i, "GKP", i, 4.5) for i in (1, 2)]
        + [_player(i, "DEF", i, 4.5) for i in range(3, 8)]
        + [_player(i, "MID", i, 6.0) for i in range(8, 13)]
        + [_player(i, "FWD", i, 7.0) for i in range(13, 16)]
    )


def _lineup_for(formation):
    squad = _legal_squad()
    by_position = {
        position: [player for player in squad if player["position"] == position]
        for position in ("GKP", "DEF", "MID", "FWD")
    }
    xi = [by_position["GKP"][0]]
    for position in ("DEF", "MID", "FWD"):
        xi.extend(by_position[position][: formation[position]])
    xi_ids = {player["player_id"] for player in xi}
    bench = [player for player in squad if player["player_id"] not in xi_ids]
    return xi, bench


def test_selling_half_profit_cases():
    assert selling_price(10.0, 10.5) == 10.2
    assert selling_price(10.0, 9.5) == 9.5


def test_transfer_hit_and_bank_cap():
    assert transfer_hit_cost(2, 1) == 4
    assert banked_transfers(5, 0) == 5
    assert banked_transfers(4, 0) == 5


def test_defensive_contribution_thresholds():
    assert defensive_contribution_points("DEF", 10) == 2
    assert defensive_contribution_points("DEF", 20) == 2
    assert defensive_contribution_points("MID", 11) == 0
    assert defensive_contribution_points("MID", 12) == 2


def test_valid_squad_and_lineup():
    squad = _legal_squad()
    assert validate_squad(squad).ok

    xi = squad[0:1] + squad[2:5] + squad[7:11] + squad[12:15]  # 1 GKP + 3 DEF + 4 MID + 3 FWD = 11
    bench = [squad[1], squad[5], squad[6], squad[11]]  # GKP + 2 DEF + 1 MID
    result = validate_lineup(xi, bench, captain_id="1", vice_captain_id="3")
    assert result.ok, result.errors


@pytest.mark.parametrize("formation", legal_formations())
def test_every_legal_formation_passes(formation):
    xi, bench = _lineup_for(formation)
    result = validate_lineup(
        xi,
        bench,
        captain_id=xi[0]["player_id"],
        vice_captain_id=xi[1]["player_id"],
    )
    assert result.ok, (formation, result.errors)


def test_legal_formations_include_previous_gaps():
    shapes = {tuple(f[pos] for pos in ("DEF", "MID", "FWD")) for f in legal_formations()}
    assert (4, 5, 1) in shapes
    assert (5, 2, 3) in shapes
    assert len(shapes) == 8


def test_lineup_rejects_duplicate_overlap_and_bad_bench_composition():
    xi, bench = _lineup_for({"DEF": 3, "MID": 4, "FWD": 3})

    duplicate_xi = [dict(player) for player in xi]
    duplicate_xi[-1]["player_id"] = duplicate_xi[-2]["player_id"]
    duplicate = validate_lineup(
        duplicate_xi,
        bench,
        captain_id=duplicate_xi[0]["player_id"],
        vice_captain_id=duplicate_xi[1]["player_id"],
    )
    assert not duplicate.ok
    assert any("unique" in error for error in duplicate.errors)

    overlapping_bench = [dict(player) for player in bench]
    overlapping_bench[0]["player_id"] = xi[0]["player_id"]
    overlap = validate_lineup(
        xi,
        overlapping_bench,
        captain_id=xi[0]["player_id"],
        vice_captain_id=xi[1]["player_id"],
    )
    assert not overlap.ok
    assert any("disjoint" in error for error in overlap.errors)

    bad_bench = [dict(player) for player in bench]
    bad_bench[0]["position"] = "MID"
    composition = validate_lineup(
        xi,
        bad_bench,
        captain_id=xi[0]["player_id"],
        vice_captain_id=xi[1]["player_id"],
    )
    assert not composition.ok
    assert any("bench_composition" in error for error in composition.errors)


def test_squad_rejects_duplicate_player_ids():
    squad = _legal_squad()
    squad[-1]["player_id"] = squad[-2]["player_id"]
    result = validate_squad(squad)
    assert not result.ok
    assert any("unique" in error for error in result.errors)


def test_formation_generation_uses_active_ruleset():
    rules = deepcopy(load_rules())
    for rule in rules["lineup"]:
        if rule["rule_id"] == "lineup.formation_constraints":
            rule["value"]["DEF"]["min"] = 4
    assert all(formation["DEF"] >= 4 for formation in legal_formations(rules))


@pytest.mark.parametrize(
    ("position_points", "expected"),
    [
        ({"GKP": 1, "DEF": 10, "MID": 100, "FWD": [20, -100, -100]}, {"DEF": 4, "MID": 5, "FWD": 1}),
        ({"GKP": 1, "DEF": 20, "MID": 1, "FWD": 100}, {"DEF": 5, "MID": 2, "FWD": 3}),
    ],
)
def test_plan_generator_can_select_previously_missing_formations(position_points, expected):
    squad = _legal_squad()
    rows = []
    position_seen = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
    for player in squad:
        pos = player["position"]
        value = position_points[pos]
        if isinstance(value, list):
            value = value[position_seen[pos]]
        position_seen[pos] += 1
        rows.append({**player, "expected_points": value})
    assert choose_starting_xi(pd.DataFrame(rows))["formation"] == expected


def test_club_limit_and_chip_rules():
    squad = (
        [_player(i, "GKP", 1 if i == 1 else 2, 4.5) for i in (1, 2)]
        + [_player(i, "DEF", 1, 4.5) for i in range(3, 8)]  # 5 DEF from club 1 + GKP = 6
        + [_player(i, "MID", i, 6.0) for i in range(8, 13)]
        + [_player(i, "FWD", i, 7.0) for i in range(13, 16)]
    )
    assert not validate_squad(squad).ok

    assert not validate_chips(["bench_boost_fh", "triple_captain_fh"], gameweek=5).ok
    assert not validate_chips(["wildcard_fh"], gameweek=20).ok
    assert validate_chips(["wildcard_fh"], gameweek=10).ok
