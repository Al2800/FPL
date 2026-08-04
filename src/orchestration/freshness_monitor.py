"""Capture freshness monitoring and pluggable alerting (ticket 04).

Reports missed scheduler jobs, stale registry sources, recovered checkpoints and
duplicate terminal state. Transport is pluggable and secret-free in Git: webhook
URLs come from the environment at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any, Protocol
from urllib import error, request

from src.orchestration.deadline_capture_scheduler import (
    DeadlineCaptureSchedulerError,
    plan_due_jobs,
    utc_timestamp,
    validate_scheduler_state,
)


FRESHNESS_MONITOR_VERSION = "1.0"
_STALENESS_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[hd])$", re.IGNORECASE)
_NON_ENFORCEABLE = frozenset({"n/a", "pending", "slot-specific", ""})


class FreshnessMonitorError(ValueError):
    """Raised when freshness inputs cannot be evaluated safely."""


class Notifier(Protocol):
    """Secret-free transport seam for freshness alerts."""

    def notify(self, report: Mapping[str, Any]) -> None:
        """Emit one freshness report (or no-op)."""


class NullNotifier:
    """Default notifier: record locally only; never touch the network."""

    def notify(self, report: Mapping[str, Any]) -> None:
        return None


class RecordingNotifier:
    """Test double that stores reports in memory."""

    def __init__(self) -> None:
        self.reports: list[dict[str, Any]] = []

    def notify(self, report: Mapping[str, Any]) -> None:
        self.reports.append(dict(report))


class WebhookNotifier:
    """POST a JSON freshness report to a caller-supplied URL.

    The URL must be provided by the operator (environment variable); it is never
    stored in the repository.
    """

    def __init__(self, url: str, *, timeout_seconds: float = 5.0) -> None:
        if not url or not str(url).startswith(("https://", "http://")):
            raise FreshnessMonitorError("WebhookNotifier requires an http(s) URL")
        self._url = str(url)
        self._timeout = float(timeout_seconds)

    def notify(self, report: Mapping[str, Any]) -> None:
        body = json.dumps(dict(report), sort_keys=True).encode("utf-8")
        req = request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._timeout) as response:
                response.read()
        except error.URLError as exc:
            raise FreshnessMonitorError(f"Freshness webhook failed: {exc}") from exc


def parse_max_staleness(value: str | None) -> timedelta | None:
    """Parse registry ``max_staleness`` strings such as ``6h`` or ``7d``.

    Non-enforceable markers (``n/a``, ``pending``, ``slot-specific``) return
    ``None`` so callers skip the source rather than inventing a threshold.
    """

    if value is None:
        return None
    text = str(value).strip().lower()
    if text in _NON_ENFORCEABLE:
        return None
    match = _STALENESS_RE.fullmatch(text)
    if not match:
        raise FreshnessMonitorError(f"Unrecognised max_staleness: {value!r}")
    amount = int(match.group("value"))
    unit = match.group("unit").lower()
    if unit == "h":
        return timedelta(hours=amount)
    return timedelta(days=amount)


def _artifact_hash(value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _iso(value: datetime) -> str:
    return utc_timestamp(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_terminal_ids(state: Mapping[str, Any]) -> list[str]:
    try:
        validated = validate_scheduler_state(state)
    except DeadlineCaptureSchedulerError as exc:
        raise FreshnessMonitorError(str(exc)) from exc
    terminal = list(validated.get("terminal_job_ids") or [])
    if len(set(terminal)) != len(terminal):
        raise FreshnessMonitorError("Scheduler state contains duplicate terminal job IDs")
    return terminal


def _stale_sources(
    *,
    registry_sources: Sequence[Mapping[str, Any]],
    source_observations: Sequence[Mapping[str, Any]],
    now: datetime,
) -> list[dict[str, Any]]:
    latest: dict[str, datetime] = {}
    for row in source_observations:
        source_id = str(row.get("source_id") or "").strip()
        observed = row.get("observed_at")
        if not source_id or not observed:
            raise FreshnessMonitorError("source observation requires source_id and observed_at")
        stamp = utc_timestamp(str(observed))
        previous = latest.get(source_id)
        if previous is None or stamp > previous:
            latest[source_id] = stamp

    stale: list[dict[str, Any]] = []
    for source in registry_sources:
        source_id = str(source.get("source_id") or "").strip()
        if not source_id:
            continue
        if source.get("enabled") is False:
            continue
        maximum = parse_max_staleness(source.get("max_staleness"))
        if maximum is None:
            continue
        observed_at = latest.get(source_id)
        if observed_at is None:
            stale.append(
                {
                    "source_id": source_id,
                    "reason": "observation_absent",
                    "max_staleness": str(source.get("max_staleness")),
                    "age_seconds": None,
                    "observed_at": None,
                }
            )
            continue
        age = now - observed_at
        if age > maximum:
            stale.append(
                {
                    "source_id": source_id,
                    "reason": "older_than_max_staleness",
                    "max_staleness": str(source.get("max_staleness")),
                    "age_seconds": int(age.total_seconds()),
                    "observed_at": _iso(observed_at),
                }
            )
    return sorted(stale, key=lambda row: row["source_id"])


def evaluate_capture_freshness(
    *,
    policy: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    scheduler_state: Mapping[str, Any],
    now: datetime | str,
    registry_sources: Sequence[Mapping[str, Any]] | None = None,
    source_observations: Sequence[Mapping[str, Any]] | None = None,
    prior_alerts: Sequence[Mapping[str, Any]] | None = None,
    notifier: Notifier | None = None,
) -> dict[str, Any]:
    """Evaluate missed jobs and source staleness without network access.

    When ``notifier`` is supplied it receives the finished report if status is
    degraded. Tests should pass :class:`RecordingNotifier` or :class:`NullNotifier`.
    """

    current = utc_timestamp(now)
    terminal = _validate_terminal_ids(scheduler_state)
    try:
        planned = plan_due_jobs(
            bootstrap=bootstrap,
            now=current,
            policy=policy,
            completed_job_ids=terminal,
        )
    except DeadlineCaptureSchedulerError as exc:
        raise FreshnessMonitorError(str(exc)) from exc

    missed = [dict(job) for job in planned if job.get("status") == "missed"]
    due = [dict(job) for job in planned if job.get("status") == "due"]

    prior = list(prior_alerts or [])
    prior_missed_ids = {
        str(alert["job_id"])
        for alert in prior
        if alert.get("code") == "missed_checkpoint" and alert.get("job_id")
    }
    recovered = sorted(job_id for job_id in prior_missed_ids if job_id in terminal)

    stale = _stale_sources(
        registry_sources=list(registry_sources or []),
        source_observations=list(source_observations or []),
        now=current,
    )

    alerts: list[dict[str, Any]] = []
    degraded_reasons: list[str] = []
    for job in missed:
        checkpoint = str(job.get("checkpoint") or "unknown")
        alerts.append(
            {
                "severity": "error",
                "code": "missed_checkpoint",
                "checkpoint": checkpoint,
                "job_id": job["job_id"],
                "kind": job.get("kind"),
                "target_at": job.get("target_at"),
                "late_by_seconds": job.get("late_by_seconds"),
                "message": f"Missed capture checkpoint {checkpoint}",
            }
        )
        degraded_reasons.append(f"capture_missed:{checkpoint}")
    for row in stale:
        source_id = str(row["source_id"])
        alerts.append(
            {
                "severity": "warning",
                "code": "stale_source",
                "source_id": source_id,
                "reason": row["reason"],
                "message": f"Source {source_id} exceeds max_staleness",
            }
        )
        degraded_reasons.append(f"source_stale:{source_id}")
    for job_id in recovered:
        alerts.append(
            {
                "severity": "info",
                "code": "recovered_checkpoint",
                "job_id": job_id,
                "message": f"Previously missed job {job_id} is now terminal",
            }
        )

    status = "degraded" if missed or stale else "ok"
    report = {
        "freshness_monitor_version": FRESHNESS_MONITOR_VERSION,
        "observed_at": _iso(current),
        "status": status,
        "missed_jobs": missed,
        "due_jobs": due,
        "stale_sources": stale,
        "recovered_job_ids": recovered,
        "duplicate_job_ids": [],
        "alerts": alerts,
        "degraded_reasons": sorted(set(degraded_reasons)),
        "account_writes": False,
        "browser_actions": False,
    }
    report["content_sha256"] = _artifact_hash(report)

    transport = notifier or NullNotifier()
    if status == "degraded":
        transport.notify(report)
    return report


def apply_freshness_to_decision_record(
    record: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge a freshness report into a Gameweek Decision Record."""

    result = dict(record)
    reasons = list(result.get("degraded_reasons") or [])
    reasons.extend(str(item) for item in freshness.get("degraded_reasons") or [])
    degraded = bool(result.get("degraded")) or freshness.get("status") == "degraded"
    result["degraded"] = degraded
    result["degraded_reasons"] = sorted(set(reasons))
    if degraded:
        result["data_quality"] = "degraded"
    elif "data_quality" not in result:
        result["data_quality"] = "complete"
    freshness_block = dict(result.get("freshness") or {})
    freshness_block["capture"] = {
        "status": freshness.get("status"),
        "observed_at": freshness.get("observed_at"),
        "missed_job_count": len(freshness.get("missed_jobs") or []),
        "stale_source_count": len(freshness.get("stale_sources") or []),
        "recovered_job_ids": list(freshness.get("recovered_job_ids") or []),
        "degraded_reasons": list(freshness.get("degraded_reasons") or []),
        "content_sha256": freshness.get("content_sha256"),
    }
    result["freshness"] = freshness_block
    return result


def notifier_from_environment(
    environment: Mapping[str, str] | None = None,
) -> Notifier:
    """Build a notifier from ``FPL_FRESHNESS_WEBHOOK_URL`` when set."""

    env = environment if environment is not None else {}
    # Lazy import of os only when caller omits an explicit mapping.
    if environment is None:
        import os

        env = os.environ
    url = str(env.get("FPL_FRESHNESS_WEBHOOK_URL") or "").strip()
    if not url:
        return NullNotifier()
    return WebhookNotifier(url)
