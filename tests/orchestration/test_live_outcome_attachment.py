"""Contracts for live post-GW outcome attachment and revision discipline."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.paired_metrics import paired_summary
from src.orchestration.live_outcome_attachment import (
    LiveOutcomeAttachmentError,
    assert_outcome_revision_allowed,
    attach_live_outcome,
    event_live_to_player_outcomes,
)
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[2]
RULES_PATH = REPO / "control" / "rules" / "2025-26.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _state() -> dict:
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
        "policy_arm": "live_forecast_optimizer",
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


def _market() -> dict[str, dict]:
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


def _plan(
    *,
    transfers: list[dict] | None = None,
    captain_id: str = "8",
    vice_id: str = "9",
) -> dict:
    moves = (
        [{"player_out_id": "3", "player_in_id": "16"}]
        if transfers is None
        else list(transfers)
    )
    starting = [
        "1",
        "4",
        "5",
        "16" if moves else "3",
        "8",
        "9",
        "10",
        "11",
        "13",
        "14",
        "15",
    ]
    candidate = {
        "transfers": moves,
        "bank_after": 0.2 if moves else 0.5,
        "hit_cost": 0,
        "lineup": {
            "formation": {"DEF": 3, "MID": 4, "FWD": 3},
            "starting_xi_ids": starting,
            "bench_ids": ["2", "6", "7", "12"],
            "captain_id": captain_id,
            "vice_captain_id": vice_id,
        },
    }
    return validate_and_freeze_plan(
        episode_id="live-shadow:2025-26:gw02:lab-manager",
        policy_arm="live_forecast_optimizer",
        state=_state(),
        candidate=candidate,
        decision_market=_market(),
        active_chip=None,
        frozen_at="2025-08-22T17:00:00Z",
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def _bootstrap() -> dict:
    elements = []
    for player_id in list(range(1, 17)):
        if player_id <= 2:
            element_type = 1
        elif player_id <= 7 or player_id == 16:
            element_type = 2
        elif player_id <= 12:
            element_type = 3
        else:
            element_type = 4
        elements.append({"id": player_id, "element_type": element_type, "web_name": f"P{player_id}"})
    return {"elements": elements}


def _live_from_points(points_by_id: dict[str, tuple[int, int]]) -> dict:
    return {
        "elements": [
            {
                "id": int(player_id),
                "stats": {"minutes": minutes, "total_points": points},
            }
            for player_id, (minutes, points) in points_by_id.items()
        ]
    }


def _gdr(plan: dict) -> dict:
    return {
        "record_id": "gdr_live_lab_gw2",
        "gameweek": 2,
        "season": "2025-26",
        "decision_cutoff": "2025-08-22T16:00:00Z",
        "deadline": "2025-08-22T17:30:00Z",
        "observed_at": "2025-08-22T10:00:00Z",
        "available_at": "2025-08-22T10:00:00Z",
        "ruleset_id": "2025-26-v1.0",
        "validated_plan": plan,
        "recommendation": {
            "strategy": "highest_ev",
            "objective": 50.0,
            "validated_plan_sha256": plan["content_sha256"],
        },
        "baseline_comparison": {
            "do_nothing_objective": 45.0,
            "recommended_objective": 50.0,
            "expected_advantage": 5.0,
        },
        "validation": {"squad": {"ok": True}, "lineup": {"ok": True}},
        "outcome": None,
        "retrospective": None,
    }


def test_event_live_flattens_with_bootstrap_positions() -> None:
    rows = event_live_to_player_outcomes(
        _live_from_points({"8": (90, 6), "9": (90, 4)}),
        bootstrap=_bootstrap(),
    )
    assert {row["element"]: row["total_points"] for row in rows} == {8: 6, 9: 4}
    assert all(row["position"] in {"GKP", "DEF", "MID", "FWD"} for row in rows)


def test_attach_live_outcome_scores_and_accepts_paired_metrics() -> None:
    recommended = _plan()
    do_nothing = _plan(transfers=[])
    points = {
        str(player_id): (90, 2)
        for player_id in range(1, 17)
    }
    points["8"] = (90, 10)
    points["9"] = (90, 4)
    points["16"] = (90, 5)
    points["3"] = (90, 1)
    live = _live_from_points(points)
    record = _gdr(recommended)
    updated = attach_live_outcome(
        record,
        live=live,
        bootstrap=_bootstrap(),
        revealed_at="2025-08-25T09:00:00Z",
        rules_path=RULES_PATH,
        status="final",
        do_nothing_plan=do_nothing,
        alternate_captain_plan=_plan(captain_id="9", vice_id="8"),
    )
    assert updated["outcome"]["status"] == "final"
    assert updated["outcome"]["points"] == updated["retrospective"]["metrics"]["gross_points"]
    assert "transfer_gain_vs_do_nothing" in updated["retrospective"]["metrics"]
    assert "captaincy_gain_vs_alternate" in updated["retrospective"]["metrics"]
    assert "bench_points" in updated["retrospective"]["metrics"]
    assert "hit_recovery" in updated["retrospective"]["metrics"]

    paired = updated["retrospective"]["metrics"]["paired_do_nothing"]
    summary = paired_summary(
        [
            {
                "episode_id": paired["episode_id"],
                "cluster_id": paired["season"],
                "evaluated_value": paired["evaluated"]["points"],
                "baseline_value": paired["baseline"]["points"],
            }
        ]
    )
    assert summary["n_pairs"] == 1
    assert summary["total_difference"] == paired["realised_gain"]


def test_provisional_cannot_overwrite_final() -> None:
    assert_outcome_revision_allowed(
        None, incoming_status="provisional", incoming_points=10.0
    )
    with pytest.raises(LiveOutcomeAttachmentError, match="final outcome"):
        assert_outcome_revision_allowed(
            {"points": 12.0, "status": "final", "finalised_at": "2025-08-25T09:00:00Z"},
            incoming_status="provisional",
            incoming_points=11.0,
        )


def test_final_may_replace_provisional_and_identical_final_is_ok() -> None:
    recommended = _plan()
    points = {str(player_id): (90, 2) for player_id in range(1, 17)}
    points["8"] = (90, 6)
    live = _live_from_points(points)
    provisional = attach_live_outcome(
        _gdr(recommended),
        live=live,
        bootstrap=_bootstrap(),
        revealed_at="2025-08-24T20:00:00Z",
        rules_path=RULES_PATH,
        status="provisional",
    )
    assert provisional["outcome"]["status"] == "provisional"
    assert provisional["outcome"]["finalised_at"] is None

    finalised = attach_live_outcome(
        provisional,
        live=live,
        bootstrap=_bootstrap(),
        revealed_at="2025-08-25T09:00:00Z",
        rules_path=RULES_PATH,
        status="final",
    )
    assert finalised["outcome"]["status"] == "final"
    assert finalised["finalised_at"] == "2025-08-25T09:00:00Z"

    again = attach_live_outcome(
        finalised,
        live=live,
        bootstrap=_bootstrap(),
        revealed_at="2025-08-25T09:00:00Z",
        rules_path=RULES_PATH,
        status="final",
    )
    assert again["outcome"]["realised_outcome_sha256"] == (
        finalised["outcome"]["realised_outcome_sha256"]
    )

    conflicting_live = _live_from_points({**points, "8": (90, 99)})
    with pytest.raises(LiveOutcomeAttachmentError, match="different points"):
        attach_live_outcome(
            finalised,
            live=conflicting_live,
            bootstrap=_bootstrap(),
            revealed_at="2025-08-25T09:00:00Z",
            rules_path=RULES_PATH,
            status="final",
        )
