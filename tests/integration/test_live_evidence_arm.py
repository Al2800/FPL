from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    build_live_evidence_packet,
    new_live_evidence_ledger,
    project_live_evidence,
)
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.live_evidence_arm import (
    LiveEvidenceArmError,
    freeze_live_evidence_arm,
    write_live_evidence_arm_artifact,
)
from tests.evidence.test_live_evidence_ledger import claim


REPO = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (REPO / "config/data_sources/2026-27-evidence.json").read_text(
        encoding="utf-8"
    )
)
REGISTRY = yaml.safe_load(
    (REPO / "control/sources/source-registry.yaml").read_text(encoding="utf-8")
)


def packet() -> tuple[dict, dict]:
    engine = {"engine_id": "fixture-engine", "margin": 2.0}
    engine["content_sha256"] = artifact_hash(engine)
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    ledger = append_live_evidence_claim(
        ledger,
        claim("l-active"),
        source_registry=REGISTRY,
        config=CONFIG,
    )
    view = project_live_evidence(
        ledger, decision_at="2026-08-14T10:00:00Z"
    )
    evidence = build_live_evidence_packet(
        evidence_view=view,
        engine_output_sha256=engine["content_sha256"],
        boundaries=[
            {
                "boundary_id": "availability:player:2026-27:1",
                "margin_points": 2.0,
            }
        ],
        config=CONFIG,
    )
    return engine, evidence


def baseline() -> dict:
    return {
        "transfers": [],
        "lineup": {"captain_id": "1"},
    }


def proposal() -> dict:
    return {
        "transfers": [{"player_out_id": "1", "player_in_id": "2"}],
        "lineup": {"captain_id": "2"},
    }


def agent(engine: dict, evidence: dict, proposed: dict) -> dict:
    proposal_hash = artifact_hash(proposed)
    return {
        "status": "completed",
        "engine_output_sha256": engine["content_sha256"],
        "evidence_packet_sha256": evidence["content_sha256"],
        "validated_output": {
            "schema_version": "1.0",
            "action": "propose",
            "accepted_claim_ids": ["l-active"],
            "proposal": deepcopy(proposed),
            "proposal_sha256": proposal_hash,
            "confidence": 0.8,
            "rationale": "Availability changes the close transfer boundary.",
        },
        "content_sha256": "a" * 64,
    }


def challenger(proposed: dict, *, verdict: str = "accept") -> dict:
    return {
        "status": "completed",
        "proposal_sha256": artifact_hash(proposed),
        "validated_output": {
            "schema_version": "1.0",
            "verdict": verdict,
            "rationale": "Proposal is grounded and bounded.",
        },
        "content_sha256": "b" * 64,
    }


def test_evidence_arm_freezes_byte_stable_control_and_admits_reviewed_proposal() -> None:
    engine, evidence = packet()
    proposed = proposal()
    output = freeze_live_evidence_arm(
        engine_output=engine,
        no_evidence_candidate=baseline(),
        evidence_packet=evidence,
        agent_run=agent(engine, evidence, proposed),
        challenger_run=challenger(proposed),
        frozen_at="2026-08-14T09:55:00Z",
        config=CONFIG,
    )
    assert output["plans"]["frozen_no_evidence_control"]["candidate"] == baseline()
    assert output["plans"]["evidence_actual"]["candidate"] == proposed
    assert output["effect_before_outcome"]["plan_changed"] is True
    assert output["effect_before_outcome"]["accepted_claim_ids"] == ["l-active"]
    assert output["agent_gate"]["status"] == "completed"
    assert output["challenger_gate"]["verdict"] == "accept"
    assert output["account_writes"] is False
    assert output["browser_actions"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing_agent", "agent_run_missing"),
        ("outside_claim", "agent_used_claim_outside_packet"),
        ("challenger_reject", "Proposal is grounded and bounded."),
    ],
)
def test_invalid_or_rejected_agent_path_degrades_to_exact_control(
    mutation: str, reason: str
) -> None:
    engine, evidence = packet()
    proposed = proposal()
    agent_run = agent(engine, evidence, proposed)
    challenger_run = challenger(proposed)
    if mutation == "missing_agent":
        agent_run = None
    elif mutation == "outside_claim":
        agent_run["validated_output"]["accepted_claim_ids"] = ["not-in-packet"]
    else:
        challenger_run = challenger(proposed, verdict="reject")
    output = freeze_live_evidence_arm(
        engine_output=engine,
        no_evidence_candidate=baseline(),
        evidence_packet=evidence,
        agent_run=agent_run,
        challenger_run=challenger_run,
        frozen_at="2026-08-14T09:55:00Z",
        config=CONFIG,
    )
    assert (
        output["plans"]["evidence_actual"]["candidate"]
        == output["plans"]["frozen_no_evidence_control"]["candidate"]
    )
    assert output["effect_before_outcome"]["plan_changed"] is False
    if mutation != "challenger_reject":
        assert output["agent_gate"]["reason"] == reason
    else:
        assert output["challenger_gate"]["reason"] == reason


def test_post_cutoff_freeze_and_hash_changed_packet_are_refused() -> None:
    engine, evidence = packet()
    with pytest.raises(LiveEvidenceArmError, match="freeze by"):
        freeze_live_evidence_arm(
            engine_output=engine,
            no_evidence_candidate=baseline(),
            evidence_packet=evidence,
            agent_run=None,
            challenger_run=None,
            frozen_at="2026-08-14T10:00:01Z",
            config=CONFIG,
        )
    changed = deepcopy(evidence)
    changed["status"] = "degraded"
    with pytest.raises(LiveEvidenceArmError, match="hash mismatch"):
        freeze_live_evidence_arm(
            engine_output=engine,
            no_evidence_candidate=baseline(),
            evidence_packet=changed,
            agent_run=None,
            challenger_run=None,
            frozen_at="2026-08-14T09:55:00Z",
            config=CONFIG,
        )


def test_evidence_arm_artifact_is_immutable(tmp_path: Path) -> None:
    engine, evidence = packet()
    output = freeze_live_evidence_arm(
        engine_output=engine,
        no_evidence_candidate=baseline(),
        evidence_packet=evidence,
        agent_run=None,
        challenger_run=None,
        frozen_at="2026-08-14T09:55:00Z",
        config=CONFIG,
    )
    path = tmp_path / "arm.json"
    write_live_evidence_arm_artifact(path, output)
    write_live_evidence_arm_artifact(path, output)
    changed = deepcopy(output)
    changed["mode"] = "changed"
    with pytest.raises(LiveEvidenceArmError, match="Refusing to overwrite"):
        write_live_evidence_arm_artifact(path, changed)
