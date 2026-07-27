"""Contracts for prospective launch classification and World Cup priors."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.forecasting.launch_context import (
    LaunchContextError,
    apply_launch_context,
    artifact_hash,
    load_launch_context,
)


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_HASH = "a" * 64
WORLD_CUP_HASH = "b" * 64


def _bootstrap() -> dict:
    return {
        "teams": [
            {"id": 1, "code": 101, "name": "Promoted"},
            {"id": 2, "code": 202, "name": "Incumbent"},
        ],
        "elements": [
            {"id": 1, "code": 10, "team": 1},
            {"id": 2, "code": 20, "team": 2},
            {"id": 3, "code": 30, "team": 2},
            {"id": 4, "code": 40, "team": 2},
        ],
    }


def _context() -> dict:
    return {
        "season": "2026-27",
        "source_bindings": {
            "official_bootstrap": {
                "observed_at": "2026-07-20T08:00:00Z",
                "sha256": BOOTSTRAP_HASH,
            },
            "world_cup_priors": {"sha256": WORLD_CUP_HASH},
        },
        "promoted_teams": [{"team_id": 1, "team_code": 101, "name": "Promoted"}],
        "new_player_codes": [10, 20],
        "transferred_player_codes": [10, 30],
        "classification_policy": {
            "precedence": [
                "promoted_team",
                "new_to_fpl",
                "transferred_player",
                "established",
            ],
            "expected_class_counts": {
                "promoted_team": 1,
                "new_to_fpl": 1,
                "transferred_player": 1,
                "established": 1,
            },
        },
        "cold_start_risk": {
            "promoted_team": 0.1,
            "new_to_fpl": 0.08,
            "transferred_player": 0.08,
            "established": 0.0,
        },
        "world_cup_policy": {
            "fatigue_tier_score": {
                "none": 0.0,
                "moderate": 0.35,
                "high": 0.7,
                "extreme": 1.0,
            },
            "gameweek_fade": [1.0, 1.0, 0.5, 0.5, 0.25, 0.0],
        },
    }


def _world_rows() -> list[dict[str, str]]:
    return [
        {
            "fpl_code": "10",
            "fatigue_prior": "high",
            "wc_minutes": "420",
            "elimination_date": "2026-07-15",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
        {
            "fpl_code": "999",
            "fatigue_prior": "moderate",
            "wc_minutes": "180",
            "elimination_date": "2026-07-01",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
        {
            "fpl_code": "",
            "fatigue_prior": "none",
            "wc_minutes": "",
            "elimination_date": "",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
    ]


def _apply(
    *,
    context: dict | None = None,
    world_rows: list[dict[str, str]] | None = None,
    cutoff: str = "2026-08-14T17:30:00Z",
    gameweek: int = 3,
) -> dict:
    return apply_launch_context(
        bootstrap=_bootstrap(),
        context=context or _context(),
        world_cup_rows=world_rows or _world_rows(),
        official_bootstrap_source_sha256=BOOTSTRAP_HASH,
        world_cup_source_sha256=WORLD_CUP_HASH,
        decision_cutoff=cutoff,
        gameweek=gameweek,
    )


def test_classifies_every_player_once_and_keeps_orthogonal_flags() -> None:
    result = _apply()
    assert result["class_counts"] == {
        "promoted_team": 1,
        "new_to_fpl": 1,
        "transferred_player": 1,
        "established": 1,
    }
    players = {row["fpl_code"]: row for row in result["players"]}
    assert players[10]["cold_start_class"] == "promoted_team"
    assert players[10]["is_new_to_fpl"] is True
    assert players[10]["changed_club"] is True
    assert players[20]["cold_start_class"] == "new_to_fpl"
    assert players[30]["cold_start_class"] == "transferred_player"
    assert players[40]["cold_start_class"] == "established"


def test_world_cup_prior_joins_by_code_fades_and_reports_unknowns() -> None:
    result = _apply(gameweek=3)
    players = {row["fpl_code"]: row for row in result["players"]}
    assert players[10]["world_cup"]["effective_fatigue"] == 0.35
    assert players[10]["world_cup"]["return_to_training_date"] is None
    assert players[20]["world_cup"]["status"] == "not_in_admitted_ledger"
    assert result["world_cup_coverage"] == {
        "ledger_rows": 3,
        "matched_rows": 1,
        "blank_code_rows": 1,
        "non_current_code_rows": 1,
        "late_rows": 0,
        "missing_return_to_training_rows": 1,
    }
    assert {row["reason"] for row in result["degraded_features"]} == {
        "blank_stable_fpl_code_no_name_join",
        "stable_code_not_in_current_official_universe",
    }


def test_late_world_cup_row_degrades_but_late_official_context_blocks() -> None:
    rows = _world_rows()
    rows[0]["observed_at"] = "2026-08-14T17:30:00Z"
    result = _apply(world_rows=rows)
    assert result["world_cup_coverage"]["late_rows"] == 1
    assert next(
        row for row in result["players"] if row["fpl_code"] == 10
    )["world_cup"]["status"] == "not_in_admitted_ledger"

    context = _context()
    context["source_bindings"]["official_bootstrap"]["observed_at"] = (
        "2026-08-14T17:30:00Z"
    )
    with pytest.raises(LaunchContextError, match="strictly before decision cutoff"):
        _apply(context=context)


def test_unknown_identity_duplicate_world_code_and_source_hash_fail_closed() -> None:
    context = _context()
    context["promoted_teams"][0]["team_code"] = 999
    with pytest.raises(LaunchContextError, match="stable code does not match"):
        _apply(context=context)

    context = _context()
    context["transferred_player_codes"].append(999)
    with pytest.raises(LaunchContextError, match="empty or unknown"):
        _apply(context=context)

    duplicate = _world_rows()
    duplicate.append(deepcopy(duplicate[1]))
    with pytest.raises(LaunchContextError, match="Duplicate World Cup stable code"):
        _apply(world_rows=duplicate)

    with pytest.raises(LaunchContextError, match="source hash mismatch"):
        apply_launch_context(
            bootstrap=_bootstrap(),
            context=_context(),
            world_cup_rows=_world_rows(),
            official_bootstrap_source_sha256="c" * 64,
            world_cup_source_sha256=WORLD_CUP_HASH,
            decision_cutoff="2026-08-14T17:30:00Z",
            gameweek=1,
        )


def test_committed_context_is_self_hashed_and_non_empty() -> None:
    path = ROOT / "control" / "identities" / "2026-27-launch-context.json"
    context = load_launch_context(path)
    assert context["content_sha256"] == artifact_hash(context)
    assert len(context["promoted_teams"]) == 3
    assert context["new_player_codes"]
    assert context["transferred_player_codes"]
    assert sum(context["classification_policy"]["expected_class_counts"].values()) == 558


def test_hash_tamper_is_rejected(tmp_path: Path) -> None:
    context = _context()
    context["content_sha256"] = artifact_hash(context)
    context["season"] = "tampered"
    path = tmp_path / "context.json"
    path.write_text(json.dumps(context), encoding="utf-8")
    with pytest.raises(LaunchContextError, match="content hash mismatch"):
        load_launch_context(path)
