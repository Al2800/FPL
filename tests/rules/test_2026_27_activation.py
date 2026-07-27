"""Owner-ready activation contracts for the official 2026/27 ruleset."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.build_rules_owner_review import (
    artifact_hash,
    build_owner_review,
)
from src.scoring.rules_loader import (
    build_ruleset_activation,
    index_rules,
    load_rules,
    ruleset_sha256,
)


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = ROOT / "control" / "rules" / "2025-26.yaml"
LIVE = ROOT / "control" / "rules" / "2026-27.yaml"
REPORT = ROOT / "reports" / "rules" / "2026-27-activation.json"


def test_every_live_rule_has_dated_official_evidence() -> None:
    rules = load_rules(LIVE)
    indexed = index_rules(rules)
    assert len(indexed) == 39
    assert rules["meta"]["ruleset_id"] == "2026-27-v1.0"
    assert rules["launch_verification_checklist"] == []
    for rule_id, rule in indexed.items():
        assert rule["status"] == "confirmed", rule_id
        assert rule["source_url"].startswith(
            "https://www.premierleague.com/"
        ), rule_id
        assert rule["source_published_at"] <= "2026-07-27", rule_id
        assert rule["verified_at"] == "2026-07-27", rule_id
        assert rule.get("launch_verification_required") is not True, rule_id


def test_live_activation_has_zero_blockers_and_exact_boundaries() -> None:
    report = build_ruleset_activation(
        load_rules(LIVE),
        ruleset_sha256(LIVE),
        mode="live",
    )
    assert report["activatable"] is True
    assert report["blockers"] == []
    profile = report["transition_profile"]
    assert profile["chip_boundary_restrictions"] == {
        "wildcard_unavailable_gameweeks": [1],
        "free_hit_unavailable_gameweeks": [1],
        "free_hit_cannot_span_adjacent_gameweeks": [19, 20],
    }
    assert profile["chip_sets"][0]["end_gameweek"] == 19
    assert profile["chip_sets"][1]["start_gameweek"] == 20
    assert profile["regular_gameweeks"] == 38
    assert profile["terminal_state_gameweek"] == 39
    assert profile["exceptional_transfer_events"] == []


def test_boundary_mutation_fails_closed() -> None:
    rules = load_rules(LIVE)
    boundary = next(
        row
        for row in rules["chips"]
        if row["rule_id"] == "chips.boundary_restrictions"
    )
    boundary["value"]["free_hit_cannot_span_adjacent_gameweeks"] = [18, 19]
    report = build_ruleset_activation(rules, ruleset_sha256(LIVE), mode="live")
    assert report["activatable"] is False
    assert any(
        blocker["code"] == "inconsistent_rules"
        and blocker["rule_id"] == "chips.boundary_restrictions"
        for blocker in report["blockers"]
    )


def test_approved_owner_packet_is_reproducible_and_separate_from_execution() -> None:
    stored = json.loads(REPORT.read_text(encoding="utf-8"))
    rebuilt = build_owner_review(
        historical_path=HISTORICAL,
        live_path=LIVE,
        reviewed_at=stored["reviewed_at"],
        status="approved",
        approved_by=stored["owner_review"]["approved_by"],
        approved_at=stored["owner_review"]["approved_at"],
    )
    assert stored == rebuilt
    assert stored["content_sha256"] == artifact_hash(stored)
    assert stored["ruleset_activation"]["blockers"] == []
    assert stored["source_audit"]["rule_count"] == 39
    assert stored["source_audit"]["confirmed_rule_count"] == 39
    assert stored["source_audit"]["unresolved_rule_ids"] == []
    assert stored["source_audit"]["missing_source_date_rule_ids"] == []
    assert stored["owner_review"]["status"] == "approved"
    assert stored["owner_review"]["approved_by"] == "Alastair"
    assert stored["owner_review"]["approved_at"] == "2026-07-27T19:01:48Z"
    assert stored["advisory_use"] == "approved"
    assert stored["browser_execution_authorized"] is False
    assert stored["fpl_account_writes_authorized"] is False
    changed = {
        row["rule_id"] for row in stored["semantic_diff_from_2025_26"]["changes"]
    }
    assert changed == {
        "transfers.afcon_exceptional_topup",
        "chips.first_half_expiry",
    }


def test_owner_approval_requires_identity_and_never_grants_account_writes() -> None:
    with pytest.raises(ValueError, match="require approver"):
        build_owner_review(
            reviewed_at="2026-07-27T18:00:00Z",
            status="approved",
        )

    approved = build_owner_review(
        reviewed_at="2026-07-27T18:00:00Z",
        status="approved",
        approved_by="Alastair",
        approved_at="2026-07-27T18:05:00Z",
    )
    assert approved["owner_review"]["status"] == "approved"
    assert approved["advisory_use"] == "approved"
    assert approved["browser_execution_authorized"] is False
    assert approved["fpl_account_writes_authorized"] is False


def test_source_or_ruleset_tamper_breaks_stored_packet_identity() -> None:
    stored = json.loads(REPORT.read_text(encoding="utf-8"))
    tampered = deepcopy(stored)
    tampered["source_audit"]["confirmed_rule_count"] = 38
    assert artifact_hash(tampered) != stored["content_sha256"]
