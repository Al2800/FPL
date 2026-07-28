from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.evidence_coverage import (
    build_evidence_coverage_report,
    evaluate_retrieval_golden,
)
from src.evidence.live_evidence_ledger import live_evidence_hash
from src.forecasting.live_faithful import artifact_hash
from scripts.audit_live_evidence_coverage import run_audit


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence-coverage.json").read_text()
)


def test_coverage_keeps_silence_unknown_and_separates_pipeline_planes() -> None:
    funnel = {
        "content_sha256": "a" * 64,
        "observations": [
            {
                "family_id": "official_fpl_state",
                "status": "complete",
                "automated": True,
                "document_count": 1,
                "raw_claim_count": 4,
                "claim_count_added": 3,
                "observed_club_ids": ["club:a"],
                "observed_player_ids": ["p1"],
                "fresh": True,
            },
            {
                "family_id": "official_club_news",
                "status": "manual_required",
                "automated": False,
                "document_count": 0,
                "raw_claim_count": 0,
                "claim_count_added": 0,
                "observed_club_ids": [],
                "observed_player_ids": [],
                "fresh": False,
            },
        ],
        "gaps": ["official_club_news:manual_citation_missing"],
    }
    funnel["content_sha256"] = artifact_hash(funnel)
    view = {
        "accepted": [{"claim_id": "c1"}],
        "conflicts": [{"subject_key": "player:p2"}],
        "excluded": {
            "future": [],
            "expired": [{"claim_id": "old"}],
            "superseded": [],
            "quarantined": [],
        },
    }
    view["content_sha256"] = live_evidence_hash(view)
    packet = {
        "evidence": [{"claim": {"claim_id": "c1"}}],
        "omitted": {
            "irrelevant_claim_ids": [],
            "claim_budget_claim_ids": [],
            "character_budget_claim_ids": [],
        },
        "limits": {"selected_claims": 1},
    }
    packet["content_sha256"] = artifact_hash(packet)
    report = build_evidence_coverage_report(
        checkpoint_id="T-48h",
        decision_at="2026-08-14T10:00:00Z",
        config=CONFIG,
        acquisition_funnel=funnel,
        evidence_view=view,
        packet=packet,
        expected_club_ids=["club:a", "club:b"],
        expected_player_ids=["p1", "p2"],
        accepted_adjustments=[],
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["planes"] == {
        "raw_acquisitions": 1,
        "raw_documents": 1,
        "raw_claims": 4,
        "deduplicated_claims_added": 3,
        "active_claims": 1,
        "retrieved_claims": 1,
        "accepted_adjustments": 0,
    }
    assert report["entity_coverage"]["club_rate"] == 0.5
    assert report["entity_coverage"]["player_rate"] == 0.5
    assert report["silence_interpretation"] == "unknown_not_available"
    assert "club:b" in report["entity_coverage"]["unobserved_club_ids"]
    assert report["status"] == "degraded"


def test_golden_metrics_measure_recall_precision_latency_and_omissions() -> None:
    packet = {
        "evidence": [
            {"claim": {"claim_id": "relevant-a"}},
            {"claim": {"claim_id": "irrelevant-a"}},
        ]
    }
    result = evaluate_retrieval_golden(
        packet=packet,
        relevant_claim_ids=["relevant-a", "relevant-b"],
        irrelevant_claim_ids=["irrelevant-a", "irrelevant-b"],
        latency_ms=25.0,
        maximum_latency_ms=250.0,
    )

    assert result["relevant_claim_recall"] == 0.5
    assert result["selected_claim_precision"] == 0.5
    assert result["irrelevant_claim_rejection_rate"] == 0.5
    assert result["latency_within_budget"] is True
    assert result["missed_relevant_claim_ids"] == ["relevant-b"]

def test_offline_audit_runner_adds_golden_metrics_and_reseals_report() -> None:
    funnel = {"observations": [], "gaps": []}
    funnel["content_sha256"] = artifact_hash(funnel)
    view = {
        "accepted": [],
        "conflicts": [],
        "excluded": {
            "future": [],
            "expired": [],
            "superseded": [],
            "quarantined": [],
        },
    }
    view["content_sha256"] = live_evidence_hash(view)
    packet = {
        "evidence": [],
        "omitted": {
            "irrelevant_claim_ids": [],
            "claim_budget_claim_ids": [],
            "character_budget_claim_ids": [],
        },
    }
    packet["content_sha256"] = artifact_hash(packet)
    report = run_audit(
        checkpoint_id="T-48h",
        decision_at="2026-08-14T10:00:00Z",
        config=CONFIG,
        acquisition_funnel=funnel,
        evidence_view=view,
        packet=packet,
        expected_entities={"club_ids": [], "player_ids": []},
        golden={
            "relevant_claim_ids": [],
            "irrelevant_claim_ids": [],
            "latency_ms": 1.0,
        },
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["golden_retrieval"]["latency_within_budget"] is True
