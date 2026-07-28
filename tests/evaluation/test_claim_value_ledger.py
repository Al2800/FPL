from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.evaluation.claim_value_ledger import (
    ClaimValueLedgerError,
    ClaimValueRun,
    build_agent_fork_ledger,
    build_claim_value_ledger,
    build_enhanced_factorial_ledger,
    claim_value_report_bytes,
    write_claim_value_report,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]


def _seal(value: dict) -> dict:
    result = deepcopy(value)
    result["content_sha256"] = artifact_hash(result)
    return result


def _write(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(_seal(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _synthetic_run(root: Path) -> ClaimValueRun:
    root.mkdir(parents=True)
    _write(
        root / "host-bundle.json",
        {
            "episode": {"decision_at": "2025-08-22T17:30:00Z"},
            "evidence_mode": "retrospective_published_before_deadline",
            "evidence_documents": [
                {
                    "document_id": "document:club-news",
                    "source_id": "club-news",
                    "published_at": "2025-08-22T12:30:00Z",
                    "observed_at": "2026-07-28T10:00:00Z",
                    "available_at": "2026-07-28T10:00:00Z",
                }
            ],
        },
    )
    _write(
        root / "evidence-run.json",
        {
            "status": "completed",
            "trace": {
                "decision_cutoff": "2025-08-22T17:30:00Z",
                "run_mode": "retrospective",
            },
            "artifacts": {
                "response": {
                    "payload": {
                        "structured_output": {
                            "claims": [
                                {
                                    "claim_id": "claim:absence",
                                    "claim_text": "Player is unavailable.",
                                    "document_id": "document:club-news",
                                    "source_id": "club-news",
                                    "passage_id": "passage:absence",
                                    "citation_excerpt": "Player is out.",
                                    "citation_excerpt_sha256": "a" * 64,
                                    "player_uid": "player:2025-26:1",
                                    "confidence": 0.99,
                                    "published_at": "2025-08-22T12:30:00Z",
                                }
                            ],
                            "proposed_adjustments": [
                                {
                                    "adjustment_id": "adjustment:absence",
                                    "claim_ids": ["claim:absence"],
                                    "target": "expected_minutes",
                                    "after_value": 0,
                                }
                            ],
                        }
                    }
                }
            },
            "validated_output": {
                "evidence_mode": "retrospective_published_before_deadline",
                "production_eligible": False,
                "claims": [
                    {
                        "claim_id": "claim:absence",
                        "claim_text": "Player is unavailable.",
                        "document_id": "document:club-news",
                        "confidence": 0.99,
                        "published_at": "2025-08-22T12:30:00Z",
                        "observed_at": "2026-07-28T10:00:00Z",
                        "available_at": "2026-07-28T10:00:00Z",
                        "expires_at": "2025-08-25T23:59:59Z",
                        "decision_eligibility": {
                            "production_eligible": False,
                        },
                        "provenance": {"source_ids": ["club-news"]},
                    }
                ],
                "claim_entities": [
                    {
                        "claim_id": "claim:absence",
                        "entity_uid": "player:2025-26:1",
                    }
                ],
                "signals": [
                    {
                        "signal_id": "signal:absence",
                        "claim_ids": ["claim:absence"],
                    }
                ],
                "proposed_adjustments": [
                    {
                        "adjustment_id": "adjustment:absence",
                        "signal_ids": ["signal:absence"],
                        "target": "expected_minutes",
                        "after_value": 0,
                    }
                ],
            },
        },
    )
    _write(
        root / "adapter-audit.json",
        {
            "applied": True,
            "fallback_reason": None,
            "adjustments": [
                {
                    "adjustment_id": "adjustment:absence",
                    "claim_ids": ["signal:absence"],
                    "target": "expected_minutes",
                    "after": {"expected_minutes": 0},
                }
            ],
        },
    )
    _write(root / "comparison.json", {"gameweek": 2})
    _write(
        root / "same-state-attribution.json",
        {
            "gameweek": 2,
            "agent_plan_sha256": "agent",
            "control_plan_sha256": "control",
            "agent_evidence_delta": -2,
        },
    )
    _write(
        root / "realised-outcome.json",
        {
            "gameweek": 2,
            "aggregated_players": [
                {
                    "player_id": "player:2025-26:1",
                    "minutes": 0,
                    "total_points": 0,
                }
            ],
        },
    )
    return ClaimValueRun(
        arm="evidence",
        gameweek=2,
        root=root,
        source_ref="fixture/evidence/gw-02",
        namespace="fixture",
    )


def test_claim_join_resolves_signal_application_and_preserves_causal_scope(
    tmp_path: Path,
) -> None:
    report = build_claim_value_ledger(
        report_id="claim-value:test",
        season="2025-26",
        mode="fixture",
        runs=[_synthetic_run(tmp_path / "run")],
        expected_gameweeks={"evidence": [1, 2]},
        zero_statuses={("evidence", 1): "not_applicable_seed"},
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["gameweeks"][0]["run_status"] == "not_applicable_seed"
    assert report["gameweeks"][0]["claim_count"] == 0
    claim = report["claims"][0]
    assert claim["claim_class"] == {
        "value": "player_availability",
        "basis": "derived_from_adjustment_target",
    }
    assert claim["retrieval"]["retrieved_into_host_bundle"] is True
    assert claim["citation"]["cited_by_agent"] is True
    assert claim["application"]["applied"] is True
    assert claim["application"]["adjustment_ids"] == ["adjustment:absence"]
    assert "paired_same_state_delta" not in claim["application"]
    assert claim["age_at_deadline_hours"] == 5.0
    assert claim["source"]["source_family_status"] == "not_recorded"
    assert claim["source"]["authority_status"] == "not_recorded"
    assert claim["verification"]["status"] == "verified"
    assert report["application_groups"][0]["paired_same_state_delta"] == -2
    assert report["rollups"]["arms"][0]["paired_same_state_sum"] == -2

def test_sealed_episode_minutes_are_manifest_bound_and_preferred(
    tmp_path: Path,
) -> None:
    episode = tmp_path / "episode"
    episode.mkdir()
    hidden = {
        "player_outcomes": [
            {
                "element": 1,
                "minutes": 0,
                "total_points": 0,
            }
        ]
    }
    hidden_hash = artifact_hash(hidden)
    (episode / "hidden-outcome.json").write_text(
        json.dumps(hidden), encoding="utf-8"
    )
    (episode / "episode-manifest.json").write_text(
        json.dumps(
            {
                "hidden_outcome_ref": {
                    "content_sha256": hidden_hash,
                }
            }
        ),
        encoding="utf-8",
    )
    run = replace(
        _synthetic_run(tmp_path / "run"),
        verification_root=episode,
        verification_source_ref="episode/gw-02",
    )
    report = build_claim_value_ledger(
        report_id="claim-value:test:sealed",
        season="2025-26",
        mode="fixture",
        runs=[run],
        expected_gameweeks={"evidence": [2]},
    )

    assert report["claims"][0]["verification"]["minutes_source"] == (
        "sealed_all_player_hidden_outcome"
    )
    assert any(
        row["source_ref"] == "episode/gw-02/hidden-outcome.json"
        and row["content_sha256"] == hidden_hash
        for row in report["input_bindings"]
    )



def test_report_bytes_and_write_are_idempotent(tmp_path: Path) -> None:
    report = build_claim_value_ledger(
        report_id="claim-value:test",
        season="2025-26",
        mode="fixture",
        runs=[_synthetic_run(tmp_path / "run")],
        expected_gameweeks={"evidence": [2]},
    )
    first = claim_value_report_bytes(report)
    second = claim_value_report_bytes(deepcopy(report))
    assert first == second

    output = tmp_path / "report.json"
    assert write_claim_value_report(output, report) is True
    assert write_claim_value_report(output, report) is False
    changed = deepcopy(report)
    changed["mode"] = "changed"
    changed["content_sha256"] = artifact_hash(changed)
    with pytest.raises(ClaimValueLedgerError, match="Refusing to overwrite"):
        write_claim_value_report(output, changed)


def test_input_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    run = _synthetic_run(tmp_path / "run")
    evidence_path = run.root / "evidence-run.json"
    value = json.loads(evidence_path.read_text(encoding="utf-8"))
    value["status"] = "tampered"
    evidence_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ClaimValueLedgerError, match="hash mismatch"):
        build_claim_value_ledger(
            report_id="claim-value:test",
            season="2025-26",
            mode="fixture",
            runs=[run],
            expected_gameweeks={"evidence": [2]},
        )


def test_enhanced_factorial_reproduces_published_artifact_oracle() -> None:
    report = build_enhanced_factorial_ledger(
        enhanced_root=ROOT / "reports/benchmarks/2025-26-enhanced",
        early_evidence_root=ROOT / "reports/benchmarks/2025-26-early-evidence",
    )
    summaries = {
        row["arm"]: row for row in report["rollups"]["arms"]
    }

    assert summaries["scout_evidence"]["gameweek_count"] == 38
    assert summaries["scout_evidence"]["applied_week_count"] == 17
    assert summaries["scout_evidence"]["paired_same_state_sum"] == 0
    assert summaries["scout_evidence"]["nonzero_paired_gameweeks"] == [
        7,
        12,
        17,
        18,
        22,
    ]
    assert summaries["optimized_evidence"]["gameweek_count"] == 38
    assert summaries["optimized_evidence"]["applied_week_count"] == 17
    assert summaries["optimized_evidence"]["paired_same_state_sum"] == 11
    assert summaries["optimized_evidence"]["nonzero_paired_gameweeks"] == [
        12,
        17,
        18,
    ]
    assert report["rollups"]["nonzero_paired_gameweeks_union"] == [
        7,
        12,
        17,
        18,
        22,
    ]


def test_agent_fork_is_reported_as_separate_plus_sixteen_mode() -> None:
    report = build_agent_fork_ledger(
        agent_fork_root=ROOT / "reports/benchmarks/2025-26-agent-forks",
    )
    summary = report["rollups"]["arms"][0]
    selected = {
        row["gameweek"]: row["namespace"] for row in report["gameweeks"]
    }

    assert report["mode"] == "accepted_agent_fork"
    assert summary["gameweek_count"] == 27
    assert summary["paired_week_count"] == 26
    assert summary["paired_same_state_sum"] == 16
    assert summary["nonzero_paired_gameweeks"] == [14, 16, 17, 22]
    assert selected[20] == "sol-v3"
    assert selected[30] == "sol-v5"
    assert report["rollups"]["nonzero_paired_gameweeks_union"] == [
        14,
        16,
        17,
        22,
    ]
