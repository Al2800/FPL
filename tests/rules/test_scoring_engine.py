"""WP-06 scoring engine and expanded golden-case coverage."""

from src.scoring.engine import (
    apply_automatic_substitutions,
    award_bonus_from_bps,
    captain_points,
    score_match_stats,
)
from src.quality.point_in_time import assert_no_lookahead, filter_by_deadline, usable_in_decision


def test_scoring_minutes_goal_assist_mid():
    stats = {
        "position": "MID",
        "minutes": 90,
        "goals": 1,
        "assists": 1,
        "clean_sheet": False,
        "defensive_actions": 0,
    }
    parts = score_match_stats(stats)
    assert parts["appearance"] == 2
    assert parts["goals"] == 5
    assert parts["assists"] == 3
    assert parts["total"] == 10


def test_defensive_contribution_scoring_cases():
    assert score_match_stats({"position": "DEF", "minutes": 90, "defensive_actions": 10})[
        "defensive_contribution"
    ] == 2
    assert score_match_stats({"position": "DEF", "minutes": 90, "defensive_actions": 20})[
        "defensive_contribution"
    ] == 2
    assert score_match_stats({"position": "MID", "minutes": 90, "defensive_actions": 11})[
        "defensive_contribution"
    ] == 0


def test_bonus_tie_for_first():
    awards = award_bonus_from_bps({"a": 40, "b": 40, "c": 30})
    assert awards == {"a": 3, "b": 3, "c": 1}


def test_bonus_tie_for_second():
    awards = award_bonus_from_bps({"a": 40, "b": 30, "c": 30})
    assert awards == {"a": 3, "b": 2, "c": 2}


def test_captain_fallback():
    pts, who = captain_points(0, 0, 8)
    assert pts == 16 and who == "vice_captain"
    pts, who = captain_points(5, 1, 8)
    assert pts == 10 and who == "captain"


def test_autosub_formation_preserving():
    xi = [
        {"player_id": "g1", "position": "GKP"},
        {"player_id": "d1", "position": "DEF"},
        {"player_id": "d2", "position": "DEF"},
        {"player_id": "d3", "position": "DEF"},
        {"player_id": "m1", "position": "MID"},
        {"player_id": "m2", "position": "MID"},
        {"player_id": "m3", "position": "MID"},
        {"player_id": "m4", "position": "MID"},
        {"player_id": "f1", "position": "FWD"},
        {"player_id": "f2", "position": "FWD"},
        {"player_id": "f3", "position": "FWD"},
    ]
    bench = [
        {"player_id": "g2", "position": "GKP"},
        {"player_id": "d4", "position": "DEF"},
        {"player_id": "m5", "position": "MID"},
        {"player_id": "f4", "position": "FWD"},
    ]
    # d3 did not play; d4 on bench did — swap in
    minutes = {p["player_id"]: 90 for p in xi}
    minutes["d3"] = 0
    minutes["d4"] = 90
    minutes["g2"] = 0
    minutes["m5"] = 90
    minutes["f4"] = 90
    out = apply_automatic_substitutions(xi, bench, played_minutes=minutes)
    ids = [p["player_id"] for p in out]
    assert "d3" not in ids
    assert "d4" in ids


def test_point_in_time_filter():
    deadline = "2024-08-30T11:00:00Z"
    records = [
        {"id": 1, "available_at": "2024-08-30T10:00:00Z"},
        {"id": 2, "available_at": "2024-08-30T12:00:00Z"},
    ]
    assert usable_in_decision(records[0], deadline)
    assert not usable_in_decision(records[1], deadline)
    assert [r["id"] for r in filter_by_deadline(records, deadline)] == [1]
    try:
        assert_no_lookahead(records, deadline)
        assert False, "expected leak detection"
    except ValueError:
        pass
