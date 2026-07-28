from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import yaml

from src.evidence.candidate_boundary_retrieval import (
    build_candidate_boundary_packet,
    discover_candidate_boundaries,
)
from src.forecasting.live_faithful import artifact_hash
from src.ingestion.evidence_source_orchestrator import (
    build_evidence_acquisition_plan,
    execute_evidence_acquisition_plan,
)
from src.orchestration.live_evidence_arm import freeze_live_evidence_arm
from tests.evidence.test_candidate_boundary_retrieval import (
    claim,
    engine,
    evidence_view,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence-coverage.json").read_text()
)
REGISTRY = yaml.safe_load(
    (ROOT / "control/sources/source-registry.yaml").read_text()
)
EVIDENCE_CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence.json").read_text()
)


def test_plan_runs_only_rights_resolved_automated_source_and_exposes_manual_paths() -> None:
    plan = build_evidence_acquisition_plan(
        checkpoint_id="T-48h",
        observed_at="2026-08-14T08:00:00Z",
        config=CONFIG,
        source_registry=REGISTRY,
    )
    actions = {row["family_id"]: row for row in plan["actions"]}

    assert actions["official_fpl_state"]["action"] == "run_automated_adapter"
    assert actions["official_club_news"]["action"] == "manual_citation_required"
    assert actions["press_conferences"]["action"] == "manual_citation_required"
    assert actions["training_and_injury"]["action"] == (
        "manual_citation_required"
    )
    assert all(
        row["action"] != "run_automated_adapter"
        for key, row in actions.items()
        if key != "official_fpl_state"
    )
    assert plan["content_sha256"] == artifact_hash(plan)


def test_disabled_automated_source_is_refused_before_adapter_call() -> None:
    config = deepcopy(CONFIG)
    family = next(
        row
        for row in config["source_families"]
        if row["family_id"] == "official_club_news"
    )
    family["collection_mode"] = "automated_snapshot"
    plan = build_evidence_acquisition_plan(
        checkpoint_id="T-48h",
        observed_at="2026-08-14T08:00:00Z",
        config=config,
        source_registry=REGISTRY,
    )
    called = False

    def forbidden() -> dict:
        nonlocal called
        called = True
        return {"status": "complete"}

    result = execute_evidence_acquisition_plan(
        plan=plan,
        automated_adapters={
            "fpl-official-endpoints": lambda: {
                "status": "complete",
                "observed_at": "2026-08-14T08:00:00Z",
                "document_count": 1,
                "raw_claim_count": 1,
                "claim_count_added": 1,
            },
            "official-club-communications": forbidden,
        },
        manual_observations={},
    )

    assert called is False
    refused = next(
        row
        for row in result["observations"]
        if row["family_id"] == "official_club_news"
    )
    assert refused["status"] == "blocked"
    assert "registry_disabled" in refused["reasons"]


def test_funnel_degrades_on_missing_manual_coverage_without_blocking_control() -> None:
    plan = build_evidence_acquisition_plan(
        checkpoint_id="T-48h",
        observed_at="2026-08-14T08:00:00Z",
        config=CONFIG,
        source_registry=REGISTRY,
    )
    result = execute_evidence_acquisition_plan(
        plan=plan,
        automated_adapters={
            "fpl-official-endpoints": lambda: {
                "status": "complete",
                "observed_at": "2026-08-14T08:00:00Z",
                "document_count": 1,
                "raw_claim_count": 2,
                "claim_count_added": 2,
                "observed_club_ids": ["club:a"],
                "observed_player_ids": ["p1", "p2"],
            }
        },
        manual_observations={
            "official_club_news": [
                {
                    "document_id": "club-a-news",
                    "observed_at": "2026-08-14T07:30:00Z",
                    "observed_club_ids": ["club:a"],
                    "observed_player_ids": ["p1"],
                    "claim_count": 1,
                }
            ]
        },
    )

    assert result["status"] == "degraded"
    assert any("press_conferences" in gap for gap in result["gaps"])
    assert result["frozen_no_evidence_control_preserved"] is True
    assert result["account_writes"] is False

def test_success_payload_without_observation_time_is_not_counted_as_fresh() -> None:
    plan = build_evidence_acquisition_plan(
        checkpoint_id="T-48h",
        observed_at="2026-08-14T08:00:00Z",
        config=CONFIG,
        source_registry=REGISTRY,
    )
    result = execute_evidence_acquisition_plan(
        plan=plan,
        automated_adapters={
            "fpl-official-endpoints": lambda: {
                "status": "complete",
                "document_count": 1,
            }
        },
        manual_observations={},
    )
    official = next(
        row
        for row in result["observations"]
        if row["family_id"] == "official_fpl_state"
    )
    assert official["status"] == "degraded"
    assert official["fresh"] is False
    assert official["reasons"] == ["observation_timestamp_missing"]

def test_candidate_packet_preserves_exact_frozen_no_evidence_shadow() -> None:
    solver_input, solver_output = engine()
    discovery = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=CONFIG,
    )
    packet = build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=evidence_view(
            claim("shadow-relevant", player_id="q1")
        ),
        config=CONFIG,
    )
    baseline = deepcopy(solver_output["selected"])
    frozen = freeze_live_evidence_arm(
        engine_output=solver_output,
        no_evidence_candidate=baseline,
        evidence_packet=packet,
        agent_run=None,
        challenger_run=None,
        frozen_at="2026-08-14T09:59:00Z",
        config=EVIDENCE_CONFIG,
    )

    assert frozen["plans"]["frozen_no_evidence_control"]["candidate"] == baseline
    assert frozen["plans"]["evidence_actual"]["candidate"] == baseline
    assert frozen["effect_before_outcome"]["plan_changed"] is False
    assert frozen["agent_gate"]["reason"] == "agent_run_missing"
