"""Pure planning and state helpers for local deadline-aware FPL capture."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SCHEDULER_VERSION = "1.0"
TERMINAL_STATUSES = frozenset({"complete", "degraded", "missed", "refused"})


class DeadlineCaptureSchedulerError(ValueError):
    """Raised when scheduler input cannot produce a safe capture plan."""


def utc_timestamp(value: str | datetime) -> datetime:
    """Return a timezone-aware UTC timestamp, refusing ambiguous values."""

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DeadlineCaptureSchedulerError(
                f"Invalid ISO-8601 timestamp: {value!r}"
            ) from exc
    else:
        raise DeadlineCaptureSchedulerError("Timestamp must be an ISO string or datetime")
    if parsed.tzinfo is None:
        raise DeadlineCaptureSchedulerError("Timestamp must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    """Render a validated timestamp in canonical UTC form."""

    return utc_timestamp(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash a JSON object deterministically for report and state lineage."""

    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object or raise a scheduler-specific error."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeadlineCaptureSchedulerError(f"Cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DeadlineCaptureSchedulerError(f"Expected JSON object at {path}")
    return value


def validate_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the small scheduler policy surface before planning."""

    required = (
        "season",
        "time_zone",
        "daily_checkpoints",
        "deadline_checkpoints",
        "active_event_grace_hours",
    )
    missing = [name for name in required if name not in policy]
    if missing:
        raise DeadlineCaptureSchedulerError(f"Scheduler policy is missing {missing}")
    try:
        ZoneInfo(str(policy["time_zone"]))
    except ZoneInfoNotFoundError as exc:
        raise DeadlineCaptureSchedulerError(
            f"Unknown scheduler time zone: {policy['time_zone']!r}"
        ) from exc
    if not isinstance(policy["daily_checkpoints"], list) or not isinstance(
        policy["deadline_checkpoints"], list
    ):
        raise DeadlineCaptureSchedulerError("Scheduler checkpoint collections must be lists")
    seen: set[str] = set()
    for row in [*policy["daily_checkpoints"], *policy["deadline_checkpoints"]]:
        if not isinstance(row, Mapping):
            raise DeadlineCaptureSchedulerError("Each checkpoint policy row must be an object")
        checkpoint = str(row.get("checkpoint", "")).strip()
        if not checkpoint or checkpoint in seen:
            raise DeadlineCaptureSchedulerError(
                f"Checkpoint identifiers must be unique and non-empty: {checkpoint!r}"
            )
        seen.add(checkpoint)
        window = row.get("window_minutes")
        if not isinstance(window, int) or window < 1:
            raise DeadlineCaptureSchedulerError(
                f"Checkpoint {checkpoint} has an invalid window_minutes"
            )
    for row in policy["daily_checkpoints"]:
        local_time = str(row.get("local_time", ""))
        try:
            datetime.strptime(local_time, "%H:%M")
        except ValueError as exc:
            raise DeadlineCaptureSchedulerError(
                f"Daily checkpoint {row['checkpoint']} requires HH:MM local_time"
            ) from exc
    for row in policy["deadline_checkpoints"]:
        if not isinstance(row.get("offset_minutes"), int) or row["offset_minutes"] < 1:
            raise DeadlineCaptureSchedulerError(
                f"Deadline checkpoint {row['checkpoint']} requires a positive offset_minutes"
            )
    return dict(policy)


def _event_rows(
    bootstrap: Mapping[str, Any], *, now: datetime, grace_hours: int | float
) -> list[dict[str, Any]]:
    events = bootstrap.get("events")
    if not isinstance(events, list):
        raise DeadlineCaptureSchedulerError("Official bootstrap has no events list")
    minimum = now - timedelta(hours=float(grace_hours))
    rows: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, Mapping):
            continue
        event_id = event.get("id")
        deadline = event.get("deadline_time")
        if not isinstance(event_id, int) or not isinstance(deadline, str):
            continue
        deadline_at = utc_timestamp(deadline)
        if deadline_at >= minimum:
            rows.append({"gameweek": event_id, "deadline_at": deadline_at})
    if not rows:
        raise DeadlineCaptureSchedulerError(
            "Official bootstrap has no deadline inside the active scheduler horizon"
        )
    return sorted(rows, key=lambda row: (row["deadline_at"], row["gameweek"]))


def _window_status(now: datetime, target: datetime, window_minutes: int) -> str | None:
    if now < target:
        return None
    if now <= target + timedelta(minutes=window_minutes):
        return "due"
    return "missed"


def _job_id(
    *, season: str, gameweek: int, checkpoint: str, kind: str, target_at: datetime
) -> str:
    return ":".join((season, f"gw{gameweek}", checkpoint, kind, iso_utc(target_at)))


def plan_due_jobs(
    *,
    bootstrap: Mapping[str, Any],
    now: datetime,
    policy: Mapping[str, Any],
    completed_job_ids: Collection[str],
) -> list[dict[str, Any]]:
    """Produce ordered jobs without reading the clock, network, or filesystem.

    A job outside its intended window becomes missed rather than due. Callers
    persist either result as terminal so a restart cannot backfill it.
    """

    configured = validate_policy(policy)
    current = utc_timestamp(now)
    completed = set(completed_job_ids)
    zone = ZoneInfo(str(configured["time_zone"]))
    active_events = _event_rows(
        bootstrap,
        now=current,
        grace_hours=configured["active_event_grace_hours"],
    )
    next_gameweek = next(
        (row["gameweek"] for row in active_events if row["deadline_at"] >= current),
        active_events[0]["gameweek"],
    )
    planned: list[dict[str, Any]] = []

    local_now = current.astimezone(zone)
    for row in configured["daily_checkpoints"]:
        hour, minute = (int(part) for part in str(row["local_time"]).split(":"))
        target = datetime(
            local_now.year,
            local_now.month,
            local_now.day,
            hour,
            minute,
            tzinfo=zone,
        ).astimezone(timezone.utc)
        status = _window_status(current, target, int(row["window_minutes"]))
        if status is None:
            continue
        job_id = _job_id(
            season=str(configured["season"]),
            gameweek=next_gameweek,
            checkpoint=str(row["checkpoint"]),
            kind="official",
            target_at=target,
        )
        if job_id not in completed:
            planned.append(
                {
                    "job_id": job_id,
                    "kind": "official",
                    "status": status,
                    "gameweek": next_gameweek,
                    "checkpoint": str(row["checkpoint"]),
                    "target_at": iso_utc(target),
                    "deadline_at": None,
                    "odds_slot": None,
                    "late_by_seconds": max(0, int((current - target).total_seconds())),
                }
            )

    for event in active_events:
        deadline = event["deadline_at"]
        for row in configured["deadline_checkpoints"]:
            target = deadline - timedelta(minutes=int(row["offset_minutes"]))
            status = _window_status(current, target, int(row["window_minutes"]))
            if status is None:
                continue
            base = {
                "gameweek": event["gameweek"],
                "checkpoint": str(row["checkpoint"]),
                "target_at": iso_utc(target),
                "deadline_at": iso_utc(deadline),
                "odds_slot": row.get("odds_slot"),
                "late_by_seconds": max(0, int((current - target).total_seconds())),
            }
            odds_slot = row.get("odds_slot")
            if odds_slot:
                odds_id = _job_id(
                    season=str(configured["season"]),
                    gameweek=event["gameweek"],
                    checkpoint=str(row["checkpoint"]),
                    kind="odds",
                    target_at=target,
                )
                if odds_id not in completed:
                    planned.append(
                        {
                            **base,
                            "job_id": odds_id,
                            "kind": "odds",
                            "status": status,
                        }
                    )
            official_id = _job_id(
                season=str(configured["season"]),
                gameweek=event["gameweek"],
                checkpoint=str(row["checkpoint"]),
                kind="official",
                target_at=target,
            )
            if official_id not in completed:
                planned.append(
                    {
                        **base,
                        "job_id": official_id,
                        "kind": "official",
                        "status": status,
                    }
                )

    rank = {"odds": 0, "official": 1}
    return sorted(
        planned,
        key=lambda job: (
            job["target_at"],
            rank[job["kind"]],
            job["gameweek"],
            job["checkpoint"],
        ),
    )


def new_scheduler_state(*, now: datetime) -> dict[str, Any]:
    """Return initial local operational state."""

    current = iso_utc(now)
    state = {
        "scheduler_version": SCHEDULER_VERSION,
        "created_at": current,
        "updated_at": current,
        "terminal_job_ids": [],
        "latest_bootstrap": None,
    }
    state["content_sha256"] = artifact_hash(state)
    return state


def validate_scheduler_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate state loaded from disk before it influences deduplication."""

    terminal = state.get("terminal_job_ids")
    if not isinstance(terminal, list) or not all(isinstance(item, str) for item in terminal):
        raise DeadlineCaptureSchedulerError("Scheduler state terminal_job_ids must be strings")
    if len(set(terminal)) != len(terminal):
        raise DeadlineCaptureSchedulerError("Scheduler state contains duplicate terminal job IDs")
    return dict(state)


def record_terminal_job(
    state: Mapping[str, Any], *, job_id: str, status: str, now: datetime
) -> dict[str, Any]:
    """Return a new state after one terminal job result."""

    if status not in TERMINAL_STATUSES:
        raise DeadlineCaptureSchedulerError(f"Non-terminal scheduler status: {status}")
    result = validate_scheduler_state(state)
    terminal = list(result["terminal_job_ids"])
    if job_id not in terminal:
        terminal.append(job_id)
    result["terminal_job_ids"] = sorted(terminal)
    result["updated_at"] = iso_utc(now)
    result.pop("content_sha256", None)
    result["content_sha256"] = artifact_hash(result)
    return result


def scheduler_report(
    *, now: datetime, policy: Mapping[str, Any], jobs: list[Mapping[str, Any]]
) -> dict[str, Any]:
    """Produce a report envelope with explicit advisory-only safety fields."""

    body = {
        "scheduler_version": SCHEDULER_VERSION,
        "observed_at": iso_utc(now),
        "season": str(policy["season"]),
        "account_writes": False,
        "browser_actions": False,
        "jobs": [dict(job) for job in jobs],
    }
    body["content_sha256"] = artifact_hash(body)
    return body
