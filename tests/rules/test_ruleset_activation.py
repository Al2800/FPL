"""Typed activation gates raw rules before they can drive season state."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.scoring.rules_loader import (
    RulesetActivationError,
    assert_ruleset_activatable,
    build_ruleset_activation,
    get_rule,
    load_rules,
    ruleset_semantic_diff,
)


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_PATH = ROOT / "control/rules/2025-26.yaml"
LIVE_PATH = ROOT / "control/rules/2026-27.yaml"
SCHEMA_PATH = ROOT / "control/schemas/rules/ruleset-activation.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approval(rule_id: str) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "status": "inherited",
        "rationale": "Reviewed carry-forward pending the official launch page.",
        "approved_by": "Alastair",
        "approved_at": "2026-07-22T20:00:00Z",
    }


def test_historical_rules_compile_to_schema_valid_transition_profile():
    rules = load_rules(HISTORICAL_PATH)
    report = build_ruleset_activation(
        rules, _sha(HISTORICAL_PATH), mode="historical_replay"
    )

    Draft202012Validator(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    ).validate(report)
    assert report["activatable"] is True
    assert report["blockers"] == []
    profile = report["transition_profile"]
    assert profile["regular_gameweeks"] == 38
    assert profile["terminal_state_gameweek"] == 39
    assert profile["exceptional_transfer_events"] == [
        {"kind": "free_transfer_top_up", "gameweek": 16, "top_up_to": 5}
    ]
    assert [row["suffix"] for row in profile["chip_sets"]] == ["fh", "sh"]
    assert profile["chip_sets"][0]["end_gameweek"] == 19
    assert profile["chip_sets"][1]["start_gameweek"] == 20


def test_current_live_rules_fail_closed_with_complete_named_blockers():
    rules = load_rules(LIVE_PATH)
    report = build_ruleset_activation(rules, _sha(LIVE_PATH), mode="live")

    assert report["activatable"] is False
    assert report["transition_profile"] is None
    blockers = {(row["code"], row["rule_id"]) for row in report["blockers"]}
    assert ("unconfirmed_rule", "squad.initial_budget") in blockers
    assert ("unconfirmed_rule", "transfers.hit_cost") in blockers
    assert ("unconfirmed_rule", "chips.boundary_restrictions") in blockers
    assert ("malformed_rule_value", "chips.boundary_restrictions") in blockers
    assert not any(
        row["rule_id"] == "transfers.afcon_exceptional_topup"
        and row["code"] == "malformed_rule_value"
        for row in report["blockers"]
    )
    with pytest.raises(RulesetActivationError, match="chips.boundary_restrictions"):
        assert_ruleset_activatable(rules, _sha(LIVE_PATH), mode="live")


def test_reviewed_compatibility_can_allow_inherited_but_never_provisional():
    rules = load_rules(HISTORICAL_PATH)
    get_rule(rules, "transfers.hit_cost")["status"] = "inherited"

    blocked = build_ruleset_activation(rules, _sha(HISTORICAL_PATH), mode="live")
    assert any(row["rule_id"] == "transfers.hit_cost" for row in blocked["blockers"])

    allowed = build_ruleset_activation(
        rules,
        _sha(HISTORICAL_PATH),
        mode="live",
        compatibility_policy=[_approval("transfers.hit_cost")],
    )
    assert allowed["activatable"] is True
    assert allowed["compatibility_policy"] == [_approval("transfers.hit_cost")]

    get_rule(rules, "transfers.hit_cost")["status"] = "provisional"
    denied = build_ruleset_activation(
        rules,
        _sha(HISTORICAL_PATH),
        mode="live",
        compatibility_policy=[_approval("transfers.hit_cost")],
    )
    assert denied["activatable"] is False
    assert any(row["code"] == "invalid_compatibility_policy" for row in denied["blockers"])


@pytest.mark.parametrize(
    ("mutation", "code", "rule_id"),
    [
        ("missing", "missing_rule", "transfers.hit_cost"),
        ("bad_afcon", "malformed_rule_value", "transfers.afcon_exceptional_topup"),
        ("bad_expiry", "malformed_rule_value", "chips.first_half_expiry"),
        ("bad_hash", "invalid_ruleset_identity", None),
    ],
)
def test_missing_malformed_and_identity_errors_are_structured(
    mutation: str, code: str, rule_id: str | None
):
    rules = load_rules(HISTORICAL_PATH)
    digest = _sha(HISTORICAL_PATH)
    if mutation == "missing":
        rules["transfers"] = [
            row for row in rules["transfers"] if row["rule_id"] != "transfers.hit_cost"
        ]
    elif mutation == "bad_afcon":
        get_rule(rules, "transfers.afcon_exceptional_topup")["value"] = {"gameweek": 16}
    elif mutation == "bad_expiry":
        get_rule(rules, "chips.first_half_expiry")["value"] = {"expires_at_gameweek": 0}
    else:
        digest = "not-a-sha"

    report = build_ruleset_activation(rules, digest, mode="historical_replay")
    assert any(row["code"] == code and row["rule_id"] == rule_id for row in report["blockers"])
    assert report["activatable"] is False


def test_semantic_diff_ignores_metadata_and_exposes_behavioral_deltas():
    historical = load_rules(HISTORICAL_PATH)
    live = load_rules(LIVE_PATH)
    metadata_only = deepcopy(historical)
    metadata_only["meta"]["verified_at"] = "2099-01-01"
    for rows in metadata_only.values():
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    row["description"] = "rewritten wording"

    assert ruleset_semantic_diff(
        historical, _sha(HISTORICAL_PATH), metadata_only, _sha(HISTORICAL_PATH)
    )["changes"] == []

    diff = ruleset_semantic_diff(
        historical, _sha(HISTORICAL_PATH), live, _sha(LIVE_PATH)
    )
    changed = {row["rule_id"]: row for row in diff["changes"]}
    assert changed["transfers.afcon_exceptional_topup"]["left"] == {
        "gameweek": 16,
        "top_up_to": 5,
    }
    assert changed["transfers.afcon_exceptional_topup"]["right"] is False
    assert "chips.boundary_restrictions" in changed
    assert diff["left_ruleset_id"] == "2025-26-v1.0"
    assert diff["right_ruleset_id"] == "2026-27-v0.1"


def test_activation_cli_emits_reviewable_report_and_exit_status(capsys):
    from scripts.verify_ruleset_activation import main

    assert main([str(HISTORICAL_PATH)]) == 0
    historical = json.loads(capsys.readouterr().out)
    assert historical["activations"][0]["activatable"] is True
    assert historical["semantic_diff"] is None

    assert main([str(HISTORICAL_PATH), str(LIVE_PATH)]) == 1
    compared = json.loads(capsys.readouterr().out)
    assert [row["ruleset_id"] for row in compared["activations"]] == [
        "2025-26-v1.0",
        "2026-27-v0.1",
    ]
    assert compared["activations"][1]["activatable"] is False
    assert {
        row["rule_id"] for row in compared["semantic_diff"]["changes"]
    } >= {
        "transfers.afcon_exceptional_topup",
        "chips.boundary_restrictions",
    }
