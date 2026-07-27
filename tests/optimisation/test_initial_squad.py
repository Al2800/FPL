from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.optimisation.initial_squad import (
    InitialSquadError,
    apply_initial_squad_adjustments,
    optimise_initial_squad,
    score_declared_initial_squad,
    validate_initial_squad_packet,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[2]
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
POLICY_PATH = REPO / "control" / "policies" / "initial-squad-2026-27.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def policy() -> dict:
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    value["search"].update(
        {
            "beam_width": 500,
            "candidate_limit_per_position": 12,
            "cheapest_per_position": 4,
            "retained_squads": 4,
        }
    )
    return value


def packet() -> dict:
    positions = [
        *(["GKP"] * 3),
        *(["DEF"] * 7),
        *(["MID"] * 7),
        *(["FWD"] * 5),
    ]
    players = []
    for index, position in enumerate(positions, start=1):
        within_position = sum(1 for item in positions[:index] if item == position)
        base = {
            "GKP": 3.6,
            "DEF": 4.7,
            "MID": 6.2,
            "FWD": 5.8,
        }[position] - 0.18 * (within_position - 1)
        players.append(
            {
                "player_id": f"p{index:02d}",
                "web_name": f"Player {index}",
                "position": position,
                "club_id": f"club-{(index - 1) % 10}",
                "now_cost": 5.0,
                "available_at": "2026-08-14T10:00:00Z",
                "expected_points": [
                    round(base + 0.05 * week, 3) for week in range(6)
                ],
                "start_probability": [0.9] * 6,
                "uncertainty": [0.4] * 6,
                "transfer_optionality": round(0.8 - 0.02 * within_position, 3),
                "early_wildcard_risk": round(0.03 * within_position, 3),
            }
        )
    # The top raw midfielder is materially uncertain. Robust selection should
    # expose a larger penalty than the point-estimate arm.
    players[10]["expected_points"] = [7.0] * 6
    players[10]["uncertainty"] = [3.0] * 6
    players[11]["promoted_team"] = True
    players[17]["new_signing"] = True
    players[18]["world_cup_fatigue"] = 0.7
    return {
        "schema_version": "1.0",
        "decision_id": "seed:2026-27:launch",
        "season": "2026-27",
        "decision_cutoff": "2026-08-14T17:30:00Z",
        "captured_at": "2026-08-14T16:30:00Z",
        "ruleset_id": RULES["meta"]["ruleset_id"],
        "ruleset_sha256": RULES_HASH,
        "feature_state_sha256": "a" * 64,
        "forecast_model_version": "test-forecast-v1",
        "horizon_gameweeks": [1, 2, 3, 4, 5, 6],
        "discount_factors": [1.0, 0.9, 0.81, 0.729, 0.6561, 0.59049],
        "players": players,
    }


def test_initial_squad_is_reproducible_legal_and_decomposed() -> None:
    first = optimise_initial_squad(
        packet(),
        policy=policy(),
        arm_mode="robust",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    second = optimise_initial_squad(
        packet(),
        policy=policy(),
        arm_mode="robust",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )

    assert first == second
    assert first["content_sha256"] == second["content_sha256"]
    assert first["selected"]["validation"]["squad"]["ok"] is True
    assert first["selected"]["validation"]["first_lineup"]["ok"] is True
    assert len(first["selected"]["squad_player_ids"]) == 15
    assert first["selected"]["bank"] == 25.0
    assert first["search"]["global_optimality_guaranteed"] is False
    assert first["alternatives"]
    assert set(first["selected"]["decomposition"]) == {
        "discounted_lineup_captain_bench_autosub",
        "context_shrinkage_loss",
        "uncertainty_penalty",
        "transfer_optionality_bonus",
        "early_wildcard_risk_penalty",
    }
    assert len(first["selected"]["weekly_plans"]) == 6


def test_robust_arm_applies_more_uncertainty_penalty() -> None:
    point = optimise_initial_squad(
        packet(),
        policy=policy(),
        arm_mode="deterministic",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    robust = optimise_initial_squad(
        packet(),
        policy=policy(),
        arm_mode="robust",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )

    assert point["selected"]["decomposition"]["uncertainty_penalty"] == 0
    assert robust["selected"]["decomposition"]["uncertainty_penalty"] > 0


def test_packet_rejects_post_cutoff_and_incomplete_vectors() -> None:
    leaked = packet()
    leaked["players"][0]["available_at"] = "2026-08-14T18:00:00Z"
    with pytest.raises(InitialSquadError, match="after decision_cutoff"):
        validate_initial_squad_packet(
            leaked, rules=RULES, ruleset_sha256=RULES_HASH
        )

    incomplete = packet()
    incomplete["players"][0]["expected_points"] = [1.0]
    with pytest.raises(InitialSquadError, match="must contain 6 values"):
        validate_initial_squad_packet(
            incomplete, rules=RULES, ruleset_sha256=RULES_HASH
        )


def test_search_uses_budget_from_supplied_rules() -> None:
    lower_budget_rules = deepcopy(RULES)
    next(
        row
        for row in lower_budget_rules["squad"]
        if row["rule_id"] == "squad.initial_budget"
    )["value"] = 70.0
    with pytest.raises(InitialSquadError, match="no feasible state"):
        optimise_initial_squad(
            packet(),
            policy=policy(),
            arm_mode="deterministic",
            rules=lower_budget_rules,
            ruleset_sha256=RULES_HASH,
        )


def test_bounded_adjustments_require_evidence_and_respect_cutoff() -> None:
    validated = validate_initial_squad_packet(
        packet(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    adjustment = {
        "player_id": "p11",
        "expected_points_delta": [-1.5] * 6,
        "available_at": "2026-08-14T17:00:00Z",
        "evidence_ids": ["club-presser-1"],
        "rationale": "Managed return to training.",
    }
    adjusted = apply_initial_squad_adjustments(
        validated, [adjustment], maximum_absolute_delta=2.0
    )
    assert adjusted["players"][10]["expected_points"] == [5.5] * 6
    assert adjusted["content_sha256"] != validated["content_sha256"]

    too_large = deepcopy(adjustment)
    too_large["expected_points_delta"] = [-2.1] * 6
    with pytest.raises(InitialSquadError, match="exceeds maximum"):
        apply_initial_squad_adjustments(
            validated, [too_large], maximum_absolute_delta=2.0
        )


def test_declared_squad_is_deterministically_validated() -> None:
    output = optimise_initial_squad(
        packet(),
        policy=policy(),
        arm_mode="deterministic",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    scored = score_declared_initial_squad(
        packet(),
        output["selected"]["squad_player_ids"],
        policy=policy(),
        arm_mode="human_reference",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    assert scored["validation"]["squad"]["ok"] is True
    with pytest.raises(InitialSquadError, match="must be unique"):
        score_declared_initial_squad(
            packet(),
            ["p01"] * 15,
            policy=policy(),
            arm_mode="human_reference",
            rules=RULES,
            ruleset_sha256=RULES_HASH,
        )
