"""Historical 2025/26 rules are explicit, executable and content-addressed."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from src.orchestration.historical_episode_builder import HistoricalEpisodeError, _validated_ruleset

from src.scoring.engine import score_match_stats
from src.scoring.rules_loader import get_rule, index_rules, load_rules, required_categories
from src.scoring.validator import (
    banked_transfers,
    defensive_contribution_points,
    selling_price,
    transfer_hit_cost,
    validate_chips,
    validate_lineup,
    validate_squad,
)


REPO = Path(__file__).resolve().parents[2]
RULES_PATH = REPO / "control" / "rules" / "2025-26.yaml"
GOLDEN_PATH = REPO / "evals" / "golden-cases" / "rules-2025-26.yaml"


def _player(pid: int, position: str, club: int, price: float) -> dict[str, object]:
    return {
        "player_id": str(pid),
        "position": position,
        "club_id": str(club),
        "purchase_price": price,
    }


def _legal_squad() -> list[dict[str, object]]:
    return (
        [_player(i, "GKP", i, 4.5) for i in (1, 2)]
        + [_player(i, "DEF", i, 4.5) for i in range(3, 8)]
        + [_player(i, "MID", i, 6.0) for i in range(8, 13)]
        + [_player(i, "FWD", i, 7.0) for i in range(13, 16)]
    )


def test_catalogue_is_complete_source_backed_and_resolved_for_replay():
    rules = load_rules(RULES_PATH)
    assert rules["meta"]["season"] == "2025-26"
    assert rules["meta"]["ruleset_id"] == "2025-26-v1.0"
    assert rules["meta"]["replay_status"] == "validated"
    assert set(required_categories()) <= set(rules)

    indexed = index_rules(rules)
    assert indexed
    for rule_id, rule in indexed.items():
        assert rule["status"] == "confirmed", rule_id
        assert rule["source_url"].startswith("https://www.premierleague.com/"), rule_id
        assert rule["source_published_at"] <= "2026-05-31", rule_id
        assert rule["verified_at"] == "2026-07-22", rule_id
        assert "value" in rule, rule_id


def test_catalogue_records_2025_26_specific_differences():
    rules = load_rules(RULES_PATH)
    assert get_rule(rules, "transfers.afcon_exceptional_topup")["value"] == {
        "gameweek": 16,
        "top_up_to": 5,
    }
    assert get_rule(rules, "chips.sets_per_season")["value"]["sets"] == 2
    assert get_rule(rules, "chips.assistant_manager_available")["value"] is False
    assert get_rule(rules, "corrections.gameweek_lock")["value"] == {
        "minutes_after_final_whistle": 60,
    }
    bps = get_rule(rules, "bonus.bps_2025_26_changes")["value"]
    assert bps["penalty_goal_bps"] == 12
    assert bps["goal_line_clearance_bps"] == 9
    assert bps["tackle_won_bps"] == 2


def test_historical_rules_execute_through_existing_engines():
    rules = load_rules(RULES_PATH)
    squad = _legal_squad()
    assert validate_squad(squad, rules=rules).ok

    xi = [squad[0], *squad[2:5], *squad[7:11], *squad[12:15]]
    bench = [squad[1], squad[5], squad[6], squad[11]]
    lineup = validate_lineup(
        xi,
        bench,
        captain_id="1",
        vice_captain_id="3",
        rules=rules,
    )
    assert lineup.ok, lineup.errors
    assert lineup.ruleset_id == "2025-26-v1.0"
    assert transfer_hit_cost(2, 1, rules) == 4
    assert banked_transfers(5, 0, rules) == 5
    assert selling_price(10.0, 10.5, rules) == 10.2
    assert defensive_contribution_points("DEF", 10, rules) == 2
    assert defensive_contribution_points("MID", 11, rules) == 0
    assert not validate_chips(["wildcard_fh"], gameweek=20, rules=rules).ok
    assert score_match_stats(
        {"position": "MID", "minutes": 90, "goals": 1, "assists": 1},
        rules,
    )["total"] == 10


def test_golden_cases_cover_every_required_family_and_historical_delta():
    golden = yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert golden["meta"]["ruleset_id"] == "2025-26-v1.0"
    cases = golden["cases"]
    families = {case["family"] for case in cases}
    assert set(required_categories()) - {"exceptional_events"} <= families
    assert "exceptional_events" in families
    ids = {case["case_id"] for case in cases}
    assert {
        "transfers.afcon_top_up_gw16",
        "corrections.one_hour_after_final_whistle",
        "assists.single_deflection_inside_box",
        "bonus.penalty_goal_twelve_bps",
    } <= ids


def test_rules_file_digest_is_exact_and_stable():
    digest = hashlib.sha256(RULES_PATH.read_bytes()).hexdigest()
    assert len(digest) == 64
    assert digest == hashlib.sha256(RULES_PATH.read_bytes()).hexdigest()


@pytest.mark.parametrize("mutation", ["wrong_season", "unresolved_rule"])
def test_episode_ruleset_validation_fails_closed(tmp_path: Path, mutation: str):
    rules = load_rules(RULES_PATH)
    if mutation == "wrong_season":
        rules["meta"]["season"] = "2026-27"
        message = "does not match dataset season"
    else:
        rules["squad"][0]["status"] = "provisional"
        message = "unresolved entries"

    candidate = tmp_path / "rules.yaml"
    candidate.write_text(
        yaml.safe_dump(rules, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(HistoricalEpisodeError, match=message):
        _validated_ruleset(candidate, "2025-26")
