"""Canonical rules-validated Gameweek plan contracts."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.orchestration.validated_plan import (
    ValidatedPlanError,
    validate_and_freeze_plan,
    validate_plan_integrity,
    validated_plan_hash,
)
from src.reporting.decision_record import validate_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
PLAN_SCHEMA = ROOT / "control/schemas/benchmark/validated-plan.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def player_rows() -> list[dict[str, object]]:
    spec = (
        [(i, "GKP", 4.5) for i in (1, 2)]
        + [(i, "DEF", 4.5) for i in range(3, 8)]
        + [(i, "MID", 7.0) for i in range(8, 13)]
        + [(i, "FWD", 11.0) for i in range(13, 16)]
    )
    rows = []
    for player_id, position, purchase in spec:
        rows.append(
            {
                "player_id": str(player_id),
                "position": position,
                "club_id": str(player_id),
                "purchase_price": purchase,
                "current_price": purchase,
                "selling_price": selling_price(purchase, purchase, RULES),
            }
        )
    return rows


def policy_state() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "state_id": "policy-state:test:forecast_optimizer:gw02",
        "status": "active",
        "origin": {
            "type": "controlled_shared_seed",
            "seed_id": "test-seed",
            "seed_sha256": "b" * 64,
        },
        "policy_arm": "forecast_optimizer",
        "season": "2025-26",
        "gameweek": 2,
        "ruleset_id": RULES["meta"]["ruleset_id"],
        "ruleset_sha256": RULES_HASH,
        "previous_state_sha256": "c" * 64,
        "transition_id": "transition:test:gw01",
        "squad": player_rows(),
        "bank": 0.5,
        "free_transfers": 1,
        "chips_available": [
            "wildcard_fh",
            "free_hit_fh",
            "triple_captain_fh",
            "bench_boost_fh",
        ],
        "chip_history": [],
        "cumulative_points": 50,
        "content_sha256": "a" * 64,
    }


def decision_market() -> dict[str, dict[str, object]]:
    market = {}
    for row in player_rows():
        market[str(row["player_id"])] = {
            "player_id": str(row["player_id"]),
            "position": row["position"],
            "club_id": row["club_id"],
            "now_cost": row["current_price"],
        }
    market["16"] = {
        "player_id": "16",
        "position": "DEF",
        "club_id": "16",
        "now_cost": 4.8,
    }
    return market


def candidate(*, bank_after: float = 0.2, hit_cost: int = 0) -> dict[str, object]:
    return {
        "strategy": "highest_ev",
        "transfers": [{"player_out_id": "3", "player_in_id": "16"}],
        "bank_after": bank_after,
        "hit_cost": hit_cost,
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


def frozen_plan(*, active_chip: str | None = None) -> dict[str, object]:
    return validate_and_freeze_plan(
        episode_id="benchmark-v0:2025-26:gw02:manager-neutral",
        policy_arm="forecast_optimizer",
        state=policy_state(),
        candidate=candidate(),
        decision_market=decision_market(),
        active_chip=active_chip,
        frozen_at="2025-08-22T17:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def test_plan_is_schema_valid_complete_deterministic_and_order_stable() -> None:
    plan = frozen_plan()
    reversed_market = dict(reversed(list(decision_market().items())))
    again = validate_and_freeze_plan(
        episode_id=plan["episode_id"],
        policy_arm="forecast_optimizer",
        state=policy_state(),
        candidate=candidate(),
        decision_market=reversed_market,
        active_chip=None,
        frozen_at=plan["frozen_at"],
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )

    assert again == plan
    assert plan["previous_state_sha256"] == policy_state()["content_sha256"]
    assert plan["ruleset"] == {
        "ruleset_id": "2025-26-v1.0",
        "content_sha256": RULES_HASH,
    }
    assert plan["transfers"] == [
        {
            "player_out_id": "3",
            "player_in_id": "16",
            "position": "DEF",
            "selling_price": 4.5,
            "purchase_price": 4.8,
        }
    ]
    assert plan["finance"] == {
        "bank_before": 0.5,
        "bank_after": 0.2,
        "free_transfers_before": 1,
        "transfer_count": 1,
        "hit_cost": 0,
    }
    assert plan["lineup"]["bench_ids"] == ["2", "6", "7", "12"]
    assert plan["content_sha256"] == validated_plan_hash(plan)
    assert plan["validation"]["status"] == "passed"
    assert len(plan["validation"]["content_sha256"]) == 64
    Draft202012Validator(
        json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    ).validate(plan)


def test_affordable_transfer_batch_is_independent_of_move_order() -> None:
    market = decision_market()
    market["17"] = {
        "player_id": "17",
        "position": "MID",
        "club_id": "17",
        "now_cost": 8.0,
    }
    market["18"] = {
        "player_id": "18",
        "position": "FWD",
        "club_id": "18",
        "now_cost": 10.0,
    }
    transfers = [
        {"player_out_id": "8", "player_in_id": "17"},
        {"player_out_id": "13", "player_in_id": "18"},
    ]
    batch_candidate = {
        "strategy": "highest_ev",
        "transfers": transfers,
        "bank_after": 0.5,
        "hit_cost": 4,
        "lineup": {
            "formation": {"DEF": 3, "MID": 4, "FWD": 3},
            "starting_xi_ids": [
                "1",
                "3",
                "4",
                "5",
                "17",
                "9",
                "10",
                "11",
                "18",
                "14",
                "15",
            ],
            "bench_ids": ["2", "6", "7", "12"],
            "captain_id": "17",
            "vice_captain_id": "9",
        },
    }

    def freeze(candidate_transfers: list[dict[str, str]]) -> dict[str, object]:
        proposal = deepcopy(batch_candidate)
        proposal["transfers"] = candidate_transfers
        return validate_and_freeze_plan(
            episode_id="benchmark-v0:2025-26:gw02:manager-neutral",
            policy_arm="forecast_optimizer",
            state=policy_state(),
            candidate=proposal,
            decision_market=market,
            active_chip=None,
            frozen_at="2025-08-22T17:00:00Z",
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )

    upgrade_first = freeze(transfers)
    downgrade_first = freeze(list(reversed(transfers)))

    assert upgrade_first["finance"]["bank_after"] == 0.5
    assert downgrade_first["finance"]["bank_after"] == 0.5
    assert {
        (move["player_out_id"], move["player_in_id"])
        for move in upgrade_first["transfers"]
    } == {
        (move["player_out_id"], move["player_in_id"])
        for move in downgrade_first["transfers"]
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "transfer",
        "xi_order",
        "bench_order",
        "captain",
        "finance",
        "chip",
        "predecessor",
        "rules",
        "validation_hash",
        "content_hash",
    ],
)
def test_integrity_rejects_every_tampered_action_or_binding(mutation: str) -> None:
    plan = deepcopy(frozen_plan())
    if mutation == "transfer":
        plan["transfers"][0]["player_in_id"] = "17"
    elif mutation == "xi_order":
        plan["lineup"]["starting_xi_ids"][0:2] = reversed(
            plan["lineup"]["starting_xi_ids"][0:2]
        )
    elif mutation == "bench_order":
        plan["lineup"]["bench_ids"][1:3] = reversed(plan["lineup"]["bench_ids"][1:3])
    elif mutation == "captain":
        plan["lineup"]["captain_id"] = "10"
    elif mutation == "finance":
        plan["finance"]["bank_after"] = 9.9
    elif mutation == "chip":
        plan["active_chip"] = "bench_boost_fh"
    elif mutation == "predecessor":
        plan["previous_state_sha256"] = "d" * 64
    elif mutation == "rules":
        plan["ruleset"]["content_sha256"] = "e" * 64
    elif mutation == "validation_hash":
        plan["validation"]["content_sha256"] = "f" * 64
    else:
        plan["content_sha256"] = "0" * 64

    with pytest.raises(ValidatedPlanError):
        validate_plan_integrity(
            plan,
            expected_state=policy_state(),
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )


@pytest.mark.parametrize(
    ("bad_candidate", "message"),
    [
        (candidate(bank_after=9.9), "bank_after"),
        (candidate(hit_cost=4), "hit_cost"),
    ],
)
def test_candidate_cannot_self_authorise_finance(
    bad_candidate: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidatedPlanError, match=message):
        validate_and_freeze_plan(
            episode_id="benchmark-v0:2025-26:gw02:manager-neutral",
            policy_arm="forecast_optimizer",
            state=policy_state(),
            candidate=bad_candidate,
            decision_market=decision_market(),
            active_chip=None,
            frozen_at="2025-08-22T17:00:00Z",
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )


def test_illegal_lineup_never_receives_a_plan_hash() -> None:
    bad = candidate()
    bad["lineup"]["captain_id"] = "2"
    with pytest.raises(ValidatedPlanError, match="line-up"):
        validate_and_freeze_plan(
            episode_id="benchmark-v0:2025-26:gw02:manager-neutral",
            policy_arm="forecast_optimizer",
            state=policy_state(),
            candidate=bad,
            decision_market=decision_market(),
            active_chip=None,
            frozen_at="2025-08-22T17:00:00Z",
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )


def test_gdr_rejects_a_second_arbitrary_action_representation() -> None:
    record = json.loads(
        (
            ROOT
            / "control/schemas/examples/gameweek_decision_records.json"
        ).read_text(encoding="utf-8")
    )
    record["recommendation"]["lineup"] = {"captain_id": "someone-else"}
    with pytest.raises(Exception, match="Additional properties"):
        validate_decision_record(record)


def test_gdr_display_metadata_must_reference_the_embedded_plan() -> None:
    record = json.loads(
        (
            ROOT
            / "control/schemas/examples/gameweek_decision_records.json"
        ).read_text(encoding="utf-8")
    )
    record["recommendation"]["validated_plan_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not match plan"):
        validate_decision_record(record)
