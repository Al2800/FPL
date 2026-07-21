"""Deterministic validator behaviour for key golden cases."""

from src.scoring.rules_loader import load_rules
from src.scoring.validator import (
    banked_transfers,
    defensive_contribution_points,
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
    squad = (
        [_player(i, "GKP", i, 4.5) for i in (1, 2)]
        + [_player(i, "DEF", i, 4.5) for i in range(3, 8)]
        + [_player(i, "MID", i, 6.0) for i in range(8, 13)]
        + [_player(i, "FWD", i, 7.0) for i in range(13, 16)]
    )
    assert validate_squad(squad).ok

    xi = squad[0:1] + squad[2:5] + squad[7:11] + squad[12:15]  # 1 GKP + 3 DEF + 4 MID + 3 FWD = 11
    bench = [squad[1], squad[5], squad[6], squad[11]]  # GKP + 2 DEF + 1 MID
    result = validate_lineup(xi, bench, captain_id="1", vice_captain_id="3")
    assert result.ok, result.errors


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
