from __future__ import annotations

from tests.optimisation.test_five_path_host_rescore import PATHS, packet_for_paths, RULES
from src.optimisation.spend_remaining import spend_remaining_candidates


def test_spend_remaining_is_empty_when_budget_already_spent() -> None:
    path_a = next(path for path in PATHS if path["path_id"] == "A-tight-ep-robust")
    result = spend_remaining_candidates(path_a, packet_for_paths(), rules=RULES)
    assert result["bank"] == 0.0
    assert result["candidates"] == []


def test_spend_remaining_finds_half_million_goalkeeper_upgrade_for_path_c() -> None:
    path_c = next(
        path for path in PATHS if path["path_id"] == "C-premium-override-advisory"
    )
    result = spend_remaining_candidates(path_c, packet_for_paths(), rules=RULES)
    assert result["bank"] == 0.5
    moves = [
        (move["out_name"], move["in_name"], move["extra"])
        for candidate in result["candidates"]
        for move in candidate["moves"]
    ]
    assert ("Dubravka", "Kinsky", 0.5) in moves
    exhausted = [row for row in result["candidates"] if row["exhausts_budget"]]
    assert exhausted
    assert all(row["bank_after"] == 0.0 for row in exhausted)
