"""Offline contracts for capture freshness monitoring and alerting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.orchestration.freshness_monitor import (
    FreshnessMonitorError,
    NullNotifier,
    RecordingNotifier,
    evaluate_capture_freshness,
    parse_max_staleness,
    apply_freshness_to_decision_record,
)


REPO = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (REPO / "config" / "data_sources" / "2026-27-capture-scheduler.json").read_text(
        encoding="utf-8"
    )
)
BOOTSTRAP = {
    "events": [
        {"id": 1, "deadline_time": "2026-08-21T17:30:00Z"},
        {"id": 2, "deadline_time": "2026-08-28T17:30:00Z"},
    ]
}


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_parse_max_staleness_units_and_non_enforceable() -> None:
    assert parse_max_staleness("6h").total_seconds() == 6 * 3600
    assert parse_max_staleness("24h").total_seconds() == 24 * 3600
    assert parse_max_staleness("7d").total_seconds() == 7 * 86400
    assert parse_max_staleness("1h").total_seconds() == 3600
    assert parse_max_staleness("n/a") is None
    assert parse_max_staleness("pending") is None
    assert parse_max_staleness("slot-specific") is None
    with pytest.raises(FreshnessMonitorError):
        parse_max_staleness("weird")


def test_missed_t2h_produces_alert_and_degraded_reasons() -> None:
    report = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": [], "updated_at": "2026-08-21T16:01:00Z"},
        now=at("2026-08-21T16:01:00Z"),
    )

    assert report["status"] == "degraded"
    missed = [job for job in report["missed_jobs"] if job["checkpoint"] == "T-2h"]
    assert len(missed) == 2
    assert any(alert["code"] == "missed_checkpoint" for alert in report["alerts"])
    assert any(reason.startswith("capture_missed:T-2h") for reason in report["degraded_reasons"])


def test_stale_source_against_registry_max_staleness() -> None:
    report = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": []},
        now=at("2026-08-20T12:00:00Z"),
        registry_sources=[
            {
                "source_id": "fpl-official-endpoints",
                "max_staleness": "6h",
                "enabled": True,
            }
        ],
        source_observations=[
            {
                "source_id": "fpl-official-endpoints",
                "observed_at": "2026-08-20T01:00:00Z",
            }
        ],
    )

    assert report["status"] == "degraded"
    assert report["stale_sources"][0]["source_id"] == "fpl-official-endpoints"
    assert "source_stale:fpl-official-endpoints" in report["degraded_reasons"]


def test_duplicate_terminal_job_ids_are_flagged() -> None:
    job_id = "2026-27:gw1:T-2h:official:2026-08-21T15:30:00Z"
    with pytest.raises(FreshnessMonitorError, match="duplicate"):
        evaluate_capture_freshness(
            policy=POLICY,
            bootstrap=BOOTSTRAP,
            scheduler_state={"terminal_job_ids": [job_id, job_id]},
            now=at("2026-08-21T16:01:00Z"),
        )


def test_recovered_checkpoint_clears_prior_miss_alert() -> None:
    job_id = "2026-27:gw1:T-2h:official:2026-08-21T15:30:00Z"
    report = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": [job_id]},
        now=at("2026-08-21T16:01:00Z"),
        prior_alerts=[
            {
                "code": "missed_checkpoint",
                "job_id": job_id,
                "checkpoint": "T-2h",
            }
        ],
    )

    assert job_id in report["recovered_job_ids"]
    assert not any(
        job["job_id"] == job_id for job in report["missed_jobs"]
    )


def test_notifier_is_invoked_for_degraded_report_without_network() -> None:
    notifier = RecordingNotifier()
    report = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": []},
        now=at("2026-08-21T16:01:00Z"),
        notifier=notifier,
    )
    assert report["status"] == "degraded"
    assert len(notifier.reports) == 1
    assert notifier.reports[0]["content_sha256"] == report["content_sha256"]


def test_null_notifier_is_safe_default() -> None:
    report = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": []},
        now=at("2026-08-20T07:00:00Z"),
        notifier=NullNotifier(),
    )
    assert "content_sha256" in report


def test_apply_freshness_marks_gdr_degraded() -> None:
    record: dict[str, Any] = {
        "data_quality": "complete",
        "degraded": False,
        "degraded_reasons": [],
        "freshness": {"point_in_time_ok": True},
    }
    freshness = evaluate_capture_freshness(
        policy=POLICY,
        bootstrap=BOOTSTRAP,
        scheduler_state={"terminal_job_ids": []},
        now=at("2026-08-21T16:01:00Z"),
    )
    updated = apply_freshness_to_decision_record(record, freshness)
    assert updated["degraded"] is True
    assert updated["data_quality"] == "degraded"
    assert any(r.startswith("capture_missed:T-2h") for r in updated["degraded_reasons"])
    assert updated["freshness"]["capture"]["status"] == "degraded"
