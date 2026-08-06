"""Tests for scheduled evidence/challenger overlay (ticket 11)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.agent_arm import build_hosted_request
from src.orchestration.agent_trace import write_agent_trace
from src.orchestration.scheduled_agent_overlay import (
    attach_overlay_to_decision_record,
    build_forced_timeout_hosted_response,
    load_overlay_policy,
    past_t90m_cutoff,
    plan_due_overlay_stages,
    run_overlay_arm,
    run_scheduled_overlay,
)


ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "evals" / "golden-cases" / "agents"
CODE_COMMIT = "a" * 40


def _candidate() -> dict:
    value = {
        "schema_version": "1.0",
        "candidate_id": "forecast-optimizer:gw08",
        "transfers": [],
        "captain": "player:salah",
    }
    value["content_sha256"] = artifact_hash(value)
    return value


def _budget() -> dict:
    return {
        "wall_clock_ms": 60_000,
        "tool_calls": 1,
        "input_tokens": 20_000,
        "output_tokens": 4_000,
        "total_tokens": 24_000,
        "cost": {"currency": "GBP", "amount": 0.0},
    }


def _request(*, run_id: str = "agent-gw08-evidence-overlay") -> dict:
    candidate = _candidate()
    evidence_document = {
        "document_id": "document:club-update",
        "source_id": "official-club-update",
        "published_at": "2025-10-18T08:45:00Z",
        "observed_at": "2025-10-18T09:00:00Z",
        "available_at": "2025-10-18T09:00:00Z",
        "passages": {
            "passage:palmer-training": (
                "Palmer did not train fully and will be assessed."
            )
        },
    }
    evidence_document["content_sha256"] = artifact_hash(evidence_document)
    return build_hosted_request(
        arm="evidence_agent",
        run_id=run_id,
        episode_id="episode:2025-26:gw08",
        observed_episode_sha256="b" * 64,
        snapshot_ids=["snapshot:gw08:deadline"],
        decision_at="2025-10-18T10:00:00Z",
        ruleset_id="fpl-2025-26",
        player_ids=["player:palmer", "player:salah"],
        player_baselines={
            "player:palmer": {
                "expected_minutes": 80.0,
                "start_probability": 0.9,
            },
            "player:salah": {
                "expected_minutes": 90.0,
                "start_probability": 1.0,
            },
        },
        evidence_documents=[evidence_document],
        deterministic_candidate_sha256=artifact_hash(candidate),
        budget=_budget(),
    )


def test_policy_loads_and_plans_t2h_window() -> None:
    policy = load_overlay_policy()
    due = plan_due_overlay_stages(
        policy,
        deadline="2026-08-15T10:00:00Z",
        now="2026-08-15T08:10:00Z",
    )
    assert [row["checkpoint"] for row in due] == ["T-2h"]
    assert "evidence_challenger" in due[0]["arms"]


def test_past_t90m_cutoff_blocks_stages() -> None:
    assert past_t90m_cutoff("2026-08-15T10:00:00Z", "2026-08-15T08:40:00Z") is True
    policy = load_overlay_policy()
    assert (
        plan_due_overlay_stages(
            policy,
            deadline="2026-08-15T10:00:00Z",
            now="2026-08-15T08:40:00Z",
        )
        == []
    )


def test_forced_timeout_degrades_to_deterministic_and_writes_trace(
    tmp_path: Path,
) -> None:
    request = _request()
    candidate = _candidate()
    result = run_overlay_arm(
        request=request,
        deterministic_candidate=candidate,
        code_commit=CODE_COMMIT,
        force_timeout=True,
        completed_at="2026-08-06T08:00:00Z",
        traces_dir=tmp_path,
    )
    assert result["status"] == "degraded"
    assert result["selected_candidate"] == candidate
    assert result["trace"]["failure"]["category"] == "timeout"
    trace_path = tmp_path / f"{request['run_id']}.jsonl"
    assert trace_path.is_file()
    event = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
    assert event["status"] == "degraded"
    assert event["trace"]["failure"]["category"] == "timeout"


def test_run_scheduled_overlay_force_timeout_at_t2h(tmp_path: Path) -> None:
    overlay = run_scheduled_overlay(
        deadline="2026-08-15T10:00:00Z",
        now="2026-08-15T08:10:00Z",
        evidence_request=_request(run_id="overlay-evidence-timeout"),
        challenger_request=None,
        deterministic_candidate=_candidate(),
        code_commit=CODE_COMMIT,
        force_timeout=True,
        checkpoint="T-2h",
        traces_dir=tmp_path,
    )
    assert overlay["status"] == "timeout"
    assert "evidence_timeout" in overlay["degraded_reasons"]
    assert overlay["accepted_adjustment_ids"] == []
    gdr = attach_overlay_to_decision_record(
        {"gameweek": 1, "degraded": False, "degraded_reasons": [], "evidence": {}},
        overlay,
    )
    assert gdr["degraded"] is True
    assert gdr["agent_overlay"]["status"] == "timeout"
    assert "agent_overlay" in gdr


def test_t90m_cutoff_overlay_result() -> None:
    overlay = run_scheduled_overlay(
        deadline="2026-08-15T10:00:00Z",
        now="2026-08-15T08:45:00Z",
        evidence_request=_request(),
        challenger_request=None,
        deterministic_candidate=_candidate(),
        code_commit=CODE_COMMIT,
    )
    assert overlay["status"] == "t90m_cutoff"
    assert "agent_t90m_fallback_deterministic" in overlay["degraded_reasons"]


def test_forced_timeout_envelope_matches_request_hash() -> None:
    request = _request()
    hosted = build_forced_timeout_hosted_response(
        request,
        completed_at="2026-08-06T08:00:00Z",
    )
    assert hosted["failure"]["category"] == "timeout"
    assert hosted["request_sha256"] == request["rendered_input_sha256"]


def test_write_agent_trace_rejects_unsafe_run_id(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="run_id"):
        write_agent_trace({"run_id": "../escape", "status": "degraded"}, traces_dir=tmp_path)
