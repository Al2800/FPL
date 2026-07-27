from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.optimisation.initial_squad import validate_initial_squad_packet
from src.orchestration.live_seed_selection import (
    LiveSeedSelectionError,
    run_live_seed_selection,
    write_live_seed_artifact,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256
from tests.optimisation.test_initial_squad import packet, policy


REPO = Path(__file__).resolve().parents[2]
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def test_all_arms_bind_the_same_base_packet_and_missing_external_arms_are_visible() -> None:
    output = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    base_hash = output["base_packet_sha256"]
    assert output["arms"]["deterministic"]["base_packet_sha256"] == base_hash
    assert output["arms"]["robust"]["base_packet_sha256"] == base_hash
    assert output["arms"]["evidence_agent"] == {
        "status": "not_run",
        "reason": "external_arm_missing",
        "base_packet_sha256": base_hash,
    }
    assert output["selection"]["selected_arm"] == "robust"
    assert output["selection"]["alternatives"]
    assert len(output["sensitivity"]) == 3
    assert output["approval_gate"]["status"] == "blocked"
    assert "rules_activation_missing" in output["approval_gate"]["blockers"]
    assert "owner_approval_missing" in output["approval_gate"]["blockers"]
    assert output["account_writes"] is False
    assert output["browser_actions"] is False


def test_external_adjustment_arm_is_bounded_host_validated_and_base_scored() -> None:
    validated = validate_initial_squad_packet(
        packet(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    external = {
        "evidence_agent": {
            "completion": {
                "status": "completed",
                "base_packet_sha256": validated["content_sha256"],
                "validated_output": {"schema": "initial-adjustments-v1"},
            },
            "adjustments": [
                {
                    "player_id": "p11",
                    "expected_points_delta": [-1.0] * 6,
                    "available_at": "2026-08-14T17:00:00Z",
                    "evidence_ids": ["official-club-availability-1"],
                    "rationale": "Official managed-minutes statement.",
                }
            ],
        }
    }
    output = run_live_seed_selection(
        packet=validated,
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        external_arms=external,
        selected_arm="evidence_agent",
    )
    arm = output["arms"]["evidence_agent"]
    assert arm["status"] == "complete"
    assert arm["base_packet_sha256"] == validated["content_sha256"]
    assert arm["adjusted_packet_sha256"] != validated["content_sha256"]
    assert arm["adjustment_ledger"][0]["evidence_ids"] == [
        "official-club-availability-1"
    ]
    assert arm["base_packet_evaluation"]["validation"]["squad"]["ok"] is True
    assert output["selection"]["selected_arm"] == "evidence_agent"


def test_incomplete_external_arm_falls_back_to_robust() -> None:
    validated = validate_initial_squad_packet(
        packet(), rules=RULES, ruleset_sha256=RULES_HASH
    )
    output = run_live_seed_selection(
        packet=validated,
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        external_arms={
            "challenger": {
                "completion": {
                    "status": "completed",
                    "base_packet_sha256": "0" * 64,
                    "validated_output": {},
                },
                "squad_player_ids": ["p01"] * 15,
            }
        },
        selected_arm="challenger",
    )
    assert output["arms"]["challenger"]["status"] == "rejected"
    assert output["selection"]["selected_arm"] == "robust"
    assert (
        output["selection"]["reason"]
        == "requested_arm_incomplete_fallback_to_robust"
    )


def test_active_rules_and_exact_owner_binding_make_manual_entry_ready() -> None:
    first = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    proposal = first["selection"]["proposal"]
    output = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        rules_activation={"status": "active", "ruleset_sha256": RULES_HASH},
        approval={
            "status": "approved",
            "approved_by": "Alastair",
            "approved_at": "2026-08-14T17:20:00Z",
            "selected_arm": "robust",
            "proposal_sha256": proposal["proposal_sha256"],
            "base_packet_sha256": first["base_packet_sha256"],
        },
    )
    assert output["approval_gate"]["status"] == "ready_for_manual_entry"
    assert output["approval_gate"]["blockers"] == []
    assert output["approval_gate"]["manual_entry_only"] is True
    assert output["approval_gate"]["account_write_authorised"] is False


def test_owner_cannot_override_inactive_rules_or_mismatched_proposal() -> None:
    first = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    output = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        rules_activation={"status": "pending", "ruleset_sha256": RULES_HASH},
        approval={
            "status": "approved",
            "approved_by": "Alastair",
            "approved_at": "2026-08-14T17:20:00Z",
            "selected_arm": "robust",
            "proposal_sha256": "f" * 64,
            "base_packet_sha256": first["base_packet_sha256"],
        },
    )
    assert output["approval_gate"]["status"] == "blocked"
    assert "ruleset_not_active" in output["approval_gate"]["blockers"]
    assert (
        "owner_approval_proposal_hash_mismatch"
        in output["approval_gate"]["blockers"]
    )


def test_live_seed_artifact_is_immutable(tmp_path: Path) -> None:
    output = run_live_seed_selection(
        packet=packet(),
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    path = tmp_path / "seed.json"
    write_live_seed_artifact(path, output)
    write_live_seed_artifact(path, output)
    changed = deepcopy(output)
    changed["selection"]["selected_arm"] = "deterministic"
    with pytest.raises(LiveSeedSelectionError, match="Refusing to overwrite"):
        write_live_seed_artifact(path, changed)

    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["content_sha256"] == output["content_sha256"]
