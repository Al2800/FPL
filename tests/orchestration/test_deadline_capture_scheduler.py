"""Offline contracts for the deadline-aware capture planner."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.orchestration.deadline_capture_scheduler import (
    DeadlineCaptureSchedulerError,
    new_scheduler_state,
    plan_due_jobs,
    record_terminal_job,
    validate_policy,
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


def test_t24_plans_ordered_odds_then_official_without_fixed_gw_date() -> None:
    jobs = plan_due_jobs(
        bootstrap=BOOTSTRAP,
        now=at("2026-08-20T17:30:00Z"),
        policy=POLICY,
        completed_job_ids=[],
    )
    selected = [
        job
        for job in jobs
        if job["gameweek"] == 1 and job["checkpoint"] == "T-24h"
    ]

    assert [(job["kind"], job["status"], job["odds_slot"]) for job in selected] == [
        ("odds", "due", "T-24h"),
        ("official", "due", "T-24h"),
    ]
    assert all(job["deadline_at"] == "2026-08-21T17:30:00Z" for job in selected)


def test_final_checkpoint_is_due_at_t15_and_stays_predeadline() -> None:
    jobs = plan_due_jobs(
        bootstrap=BOOTSTRAP,
        now=at("2026-08-21T17:15:00Z"),
        policy=POLICY,
        completed_job_ids=[],
    )
    final_jobs = [job for job in jobs if job["checkpoint"] == "final"]

    assert [(job["kind"], job["status"]) for job in final_jobs] == [
        ("odds", "due"),
        ("official", "due"),
    ]
    assert {job["target_at"] for job in final_jobs} == {"2026-08-21T17:15:00Z"}
    assert {job["late_by_seconds"] for job in final_jobs} == {0}


def test_expired_window_is_missed_and_not_issued_as_due() -> None:
    jobs = plan_due_jobs(
        bootstrap=BOOTSTRAP,
        now=at("2026-08-21T16:01:00Z"),
        policy=POLICY,
        completed_job_ids=[],
    )
    t2 = [job for job in jobs if job["checkpoint"] == "T-2h"]

    assert [(job["kind"], job["status"]) for job in t2] == [
        ("odds", "missed"),
        ("official", "missed"),
    ]
    assert all(job["late_by_seconds"] == 1860 for job in t2)


def test_terminal_state_prevents_duplicate_dispatch_and_state_is_deterministic() -> None:
    now = at("2026-08-20T17:30:00Z")
    first = plan_due_jobs(
        bootstrap=BOOTSTRAP, now=now, policy=POLICY, completed_job_ids=[]
    )
    state = new_scheduler_state(now=now)
    for job in first:
        state = record_terminal_job(
            state, job_id=job["job_id"], status="missed", now=now
        )
    second = plan_due_jobs(
        bootstrap=BOOTSTRAP,
        now=now,
        policy=POLICY,
        completed_job_ids=state["terminal_job_ids"],
    )

    assert not [
        job
        for job in second
        if job["gameweek"] == 1 and job["checkpoint"] in {"T-48h", "T-24h"}
    ]
    assert state["terminal_job_ids"] == sorted(state["terminal_job_ids"])
    assert len(set(state["terminal_job_ids"])) == len(state["terminal_job_ids"])


def test_daily_london_checkpoint_handles_bst_as_utc() -> None:
    jobs = plan_due_jobs(
        bootstrap=BOOTSTRAP,
        now=at("2026-07-30T06:00:00Z"),
        policy=POLICY,
        completed_job_ids=[],
    )
    daily = [job for job in jobs if job["checkpoint"] == "daily_am"]

    assert len(daily) == 1
    assert daily[0]["status"] == "due"
    assert daily[0]["target_at"] == "2026-07-30T06:00:00Z"


def test_bad_policy_and_naive_deadline_fail_closed() -> None:
    policy = dict(POLICY)
    policy["time_zone"] = "Mars/Olympus"
    with pytest.raises(DeadlineCaptureSchedulerError, match="Unknown scheduler time zone"):
        validate_policy(policy)

    with pytest.raises(DeadlineCaptureSchedulerError, match="explicit timezone"):
        plan_due_jobs(
            bootstrap={"events": [{"id": 1, "deadline_time": "2026-08-21T17:30:00"}]},
            now=at("2026-08-20T17:30:00Z"),
            policy=POLICY,
            completed_job_ids=[],
        )
