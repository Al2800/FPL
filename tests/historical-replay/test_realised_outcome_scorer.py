"""Reveal-gated official FPL outcome scoring for frozen plans."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.evaluation.outcome_scorer import (
    OutcomeScoringError,
    realised_outcome_hash,
    score_revealed_outcome,
)
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import load_rules, ruleset_sha256


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)
GOLDEN = ROOT / "evals/golden-cases/outcomes"
OUTCOME_SCHEMA = ROOT / "control/schemas/benchmark/realised-outcome.json"


def _state() -> dict[str, object]:
    positions = {
        **{str(i): "GKP" for i in (1, 2)},
        **{str(i): "DEF" for i in (3, 4, 5, 6, 7)},
        **{str(i): "MID" for i in (8, 9, 10, 11, 12)},
        **{str(i): "FWD" for i in (13, 14, 15)},
    }
    costs = {"GKP": 4.5, "DEF": 4.5, "MID": 7.0, "FWD": 11.0}
    squad = [
        {
            "player_id": player_id,
            "position": position,
            "club_id": player_id,
            "purchase_price": costs[position],
            "current_price": costs[position],
            "selling_price": costs[position],
        }
        for player_id, position in positions.items()
    ]
    return {
        "policy_arm": "forecast_optimizer",
        "season": "2025-26",
        "gameweek": 2,
        "ruleset_id": "2025-26-v1.0",
        "ruleset_sha256": RULES_HASH,
        "squad": squad,
        "bank": 0.5,
        "free_transfers": 1,
        "chips_available": [
            "wildcard_fh",
            "free_hit_fh",
            "triple_captain_fh",
            "bench_boost_fh",
        ],
        "content_sha256": "a" * 64,
    }


def _market() -> dict[str, dict[str, object]]:
    rows = {
        row["player_id"]: {
            "player_id": row["player_id"],
            "position": row["position"],
            "club_id": row["club_id"],
            "now_cost": row["current_price"],
        }
        for row in _state()["squad"]
    }
    rows["16"] = {
        "player_id": "16",
        "position": "DEF",
        "club_id": "16",
        "now_cost": 4.8,
    }
    return rows


def _candidate() -> dict[str, object]:
    return {
        "transfers": [{"player_out_id": "3", "player_in_id": "16"}],
        "bank_after": 0.2,
        "hit_cost": 0,
        "lineup": {
            "formation": {"DEF": 3, "MID": 4, "FWD": 3},
            "starting_xi_ids": [
                "1",
                "4",
                "5",
                "16",
                "8",
                "9",
                "10",
                "11",
                "13",
                "14",
                "15",
            ],
            "bench_ids": ["2", "6", "7", "12"],
            "captain_id": "8",
            "vice_captain_id": "9",
        },
    }


def _plan(active_chip: str | None) -> dict[str, object]:
    return validate_and_freeze_plan(
        episode_id="benchmark-v0:2025-26:gw02:manager-neutral",
        policy_arm="forecast_optimizer",
        state=_state(),
        candidate=_candidate(),
        decision_market=_market(),
        active_chip=active_chip,
        frozen_at="2025-08-22T17:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def _hidden(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "hidden_outcome_version": "1.0",
        "episode_id": "benchmark-v0:2025-26:gw02:manager-neutral",
        "season": "2025-26",
        "gameweek": 2,
        "reveal_after": "proposal_frozen",
        "player_outcomes": rows,
        "fixtures": [],
        "match_results": [],
    }


@pytest.mark.parametrize(
    "case_path", sorted(GOLDEN.glob("*.json")), ids=lambda path: path.stem
)
def test_golden_realised_outcomes(case_path: Path) -> None:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    result = score_revealed_outcome(
        _plan(case["active_chip"]),
        _hidden(case["player_outcomes"]),
        revealed_at="2025-08-25T09:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    expected = case["expected"]
    assert result["gross_points"] == expected["gross_points"]
    assert result["captain"]["player_id"] == expected["captain_player_id"]
    assert result["captain"]["multiplier"] == expected["captain_multiplier"]
    assert result["substitutions"] == expected["substitutions"]
    if "captain_total_minutes" in expected:
        assert result["captain"]["total_minutes"] == expected["captain_total_minutes"]
    if "bench_points" in expected:
        assert result["bench_points"] == expected["bench_points"]
    assert result["content_sha256"] == realised_outcome_hash(result)
    Draft202012Validator(
        json.loads(OUTCOME_SCHEMA.read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    ).validate(result)


def test_zero_total_gameweek_minutes_falls_back_to_vice() -> None:
    rows = [
        {"element": player_id, "fixture": 400 + int(player_id), "position": position, "minutes": 90, "total_points": 1}
        for player_id, position in {
            "1": "GK",
            "4": "DEF",
            "5": "DEF",
            "16": "DEF",
            "10": "MID",
            "11": "MID",
            "13": "FWD",
            "14": "FWD",
            "15": "FWD",
        }.items()
    ]
    rows.extend(
        [
            {"element": 8, "fixture": 408, "position": "MID", "minutes": 0, "total_points": 0},
            {"element": 9, "fixture": 409, "position": "MID", "minutes": 90, "total_points": 4},
            {"element": 9, "fixture": 499, "position": "MID", "minutes": 90, "total_points": 0},
            {"element": 12, "fixture": 412, "position": "MID", "minutes": 90, "total_points": 2},
        ]
    )
    result = score_revealed_outcome(
        _plan(None),
        _hidden(rows),
        revealed_at="2025-08-25T09:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    assert result["captain"]["source"] == "vice_captain"
    assert result["captain"]["player_id"] == "9"
    assert result["captain"]["total_minutes"] == 180


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("early_reveal", "after plan freeze"),
        ("episode", "episode"),
        ("duplicate", "Duplicate"),
        ("position", "position"),
        ("tampered_plan", "hash"),
    ],
)
def test_outcome_boundary_fails_closed(mutation: str, message: str) -> None:
    case = json.loads((GOLDEN / "normal-autosub.json").read_text(encoding="utf-8"))
    plan = _plan(None)
    hidden = _hidden(case["player_outcomes"])
    revealed_at = "2025-08-25T09:00:00Z"
    if mutation == "early_reveal":
        revealed_at = plan["frozen_at"]
    elif mutation == "episode":
        hidden["episode_id"] = "benchmark-v0:2025-26:gw03:manager-neutral"
    elif mutation == "duplicate":
        hidden["player_outcomes"].append(deepcopy(hidden["player_outcomes"][0]))
    elif mutation == "position":
        hidden["player_outcomes"][0]["position"] = "MID"
    else:
        plan["lineup"]["captain_id"] = "10"

    with pytest.raises(OutcomeScoringError, match=message):
        score_revealed_outcome(
            plan,
            hidden,
            revealed_at=revealed_at,
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )
