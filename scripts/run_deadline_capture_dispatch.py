#!/usr/bin/env python3
"""Dispatch only due, immutable FPL capture jobs from the configured schedule."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.deadline_capture_scheduler import (  # noqa: E402
    DeadlineCaptureSchedulerError,
    artifact_hash,
    iso_utc,
    load_json_object,
    new_scheduler_state,
    plan_due_jobs,
    record_terminal_job,
    scheduler_report,
    utc_timestamp,
    validate_scheduler_state,
)


class SchedulerLockContended(RuntimeError):
    """A prior dispatcher still owns the create-only local lock."""


@contextmanager
def _single_writer_lock(path: Path):
    """Create a lock atomically; a stale lock requires manual review."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SchedulerLockContended(str(path)) from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

def _stamp(value: str) -> str:
    return value.replace(":", "").replace("-", "")


def _read_state(path: Path, *, now: datetime) -> dict[str, Any]:
    return validate_scheduler_state(load_json_object(path)) if path.exists() else new_scheduler_state(now=now)


def _write_json(path: Path, value: Mapping[str, Any], *, immutable: bool) -> None:
    body = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable:
        if path.exists() and path.read_bytes() != body:
            raise FileExistsError(f"Refusing to overwrite scheduler report: {path}")
        if not path.exists():
            path.write_bytes(body)
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _redact(value: str, environment: Mapping[str, str]) -> str:
    secret = environment.get("THE_ODDS_API_KEY", "")
    if secret:
        value = value.replace(secret, "[redacted]")
    return value.replace("apiKey=", "apiKey=[redacted]").replace(
        "api_key=", "api_key=[redacted]"
    )[:1000]


def _subprocess_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Ensure governed child scripts import this checkout, not a caller's cwd."""

    result = dict(environment)
    existing = result.get("PYTHONPATH", "")
    result["PYTHONPATH"] = str(REPO) + (os.pathsep + existing if existing else "")
    return result


def _run(command: list[str], *, environment: Mapping[str, str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=REPO,
        env=_subprocess_environment(environment),
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": _redact(result.stdout, environment),
        "stdout_for_parse": result.stdout,
        "stderr": _redact(result.stderr, environment),
    }


def _result_stdout_for_parse(result: Mapping[str, Any]) -> str:
    """Return unreported child output for local JSON parsing only."""

    return str(result.get("stdout_for_parse", result.get("stdout", "")))


def _read_capture_bootstrap(summary: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    observed = summary.get("observed_at")
    endpoint_rows = summary.get("endpoints")
    if not isinstance(observed, str) or not isinstance(endpoint_rows, list):
        raise DeadlineCaptureSchedulerError("Official capture summary has no bootstrap provenance")
    endpoint = next(
        (
            row
            for row in endpoint_rows
            if isinstance(row, Mapping)
            and str(row.get("request_url", "")).endswith("/api/bootstrap-static/")
            and row.get("acquisition_status") == "success"
        ),
        None,
    )
    if not isinstance(endpoint, Mapping) or not isinstance(endpoint.get("body_file"), str):
        raise DeadlineCaptureSchedulerError("Official capture has no successful bootstrap")
    path = REPO / "data" / "live-shadow" / "fpl" / _stamp(observed) / str(endpoint["body_file"])
    body = load_json_object(path)
    return body, {
        "path": str(path.relative_to(REPO)).replace("\\", "/"),
        "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "observed_at": observed,
    }


def _cached_bootstrap(state: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    latest = state.get("latest_bootstrap")
    if not isinstance(latest, Mapping):
        return None
    path_value, expected = latest.get("path"), latest.get("content_sha256")
    if not isinstance(path_value, str) or not isinstance(expected, str):
        return None
    path = (REPO / path_value).resolve()
    try:
        path.relative_to(REPO.resolve())
        raw = path.read_bytes()
    except (OSError, ValueError):
        return None
    if hashlib.sha256(raw).hexdigest() != expected:
        raise DeadlineCaptureSchedulerError("Cached scheduler bootstrap hash mismatch")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeadlineCaptureSchedulerError("Cached scheduler bootstrap is invalid JSON") from exc
    if not isinstance(body, dict):
        raise DeadlineCaptureSchedulerError("Cached scheduler bootstrap is not an object")
    return body, dict(latest)


def _official_command(*, python: str, deadline: str | None, market: Path | None) -> list[str]:
    command = [python, "scripts/capture_fpl_live_shadow.py"]
    if deadline:
        command += ["--decision-cutoff", deadline]
    if market:
        command += ["--market-snapshot", str(market)]
    return command


def _capture_bootstrap(*, python: str, environment: Mapping[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = _run(_official_command(python=python, deadline=None, market=None), environment=environment)
    try:
        summary = json.loads(_result_stdout_for_parse(result))
    except json.JSONDecodeError as exc:
        detail = str(result["stderr"]).strip() or "empty stdout"
        raise DeadlineCaptureSchedulerError(
            f"Initial official capture did not return JSON: {detail}"
        ) from exc
    if not isinstance(summary, dict):
        raise DeadlineCaptureSchedulerError("Initial official capture did not return an object")
    bootstrap, reference = _read_capture_bootstrap(summary)
    return bootstrap, reference, result


def _outcome(job: Mapping[str, Any], status: str, detail: str, result: Mapping[str, Any] | None = None) -> dict[str, Any]:
    value = {**dict(job), "status": status, "detail": detail}
    if result:
        value.update({"returncode": result["returncode"], "stderr": result["stderr"]})
    return value


def dispatch(
    *,
    policy: Mapping[str, Any],
    state: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    now: datetime,
    environment: Mapping[str, str],
    python: str,
    dry_run: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the planned work; dry-run is offline and does not alter state."""

    current = utc_timestamp(now)
    next_state = validate_scheduler_state(state)
    planned = plan_due_jobs(
        bootstrap=bootstrap,
        now=current,
        policy=policy,
        completed_job_ids=next_state["terminal_job_ids"],
    )
    if dry_run:
        report = scheduler_report(now=current, policy=policy, jobs=planned)
        report.update({"mode": "dry_run", "network_calls": 0, "state_written": False})
        report["content_sha256"] = artifact_hash({k: v for k, v in report.items() if k != "content_sha256"})
        return report, next_state

    outcomes: list[dict[str, Any]] = []
    odds_outputs: dict[tuple[int, str], Path] = {}
    network_calls = 0
    for job in planned:
        if job["status"] == "missed":
            outcome = _outcome(job, "missed", "checkpoint_window_expired")
        elif job["kind"] == "odds":
            key = str(policy["secret_environment_variable"])
            if not environment.get(key, "").strip():
                outcome = _outcome(job, "degraded", "degraded_missing_secret_no_network")
            else:
                output = (
                    REPO / str(policy["odds_output_root"]) / f"gw-{job['gameweek']:02d}"
                    / f"{job['checkpoint']}-{_stamp(str(job['target_at']))}.json"
                )
                command = [
                    python, str(policy["odds_capture_script"]), "--slot", str(job["odds_slot"]),
                    "--decision-cutoff", str(job["deadline_at"]), "--output", str(output),
                ]
                network_calls += 1
                result = _run(command, environment=environment)
                if result["returncode"] == 0 and output.exists():
                    odds_outputs[(int(job["gameweek"]), str(job["checkpoint"]))] = output
                    outcome = _outcome(job, "complete", "odds_captured", result)
                else:
                    outcome = _outcome(job, "degraded", "odds_capture_failed", result)
        else:
            market = odds_outputs.get((int(job["gameweek"]), str(job["checkpoint"])))
            network_calls += 1
            result = _run(
                _official_command(python=python, deadline=job["deadline_at"], market=market),
                environment=environment,
            )
            outcome = _outcome(
                job,
                "complete" if result["returncode"] == 0 else "degraded",
                "official_capture_completed" if result["returncode"] == 0 else "official_capture_partial_or_failed",
                result,
            )
            if result["returncode"] == 0:
                try:
                    summary = json.loads(_result_stdout_for_parse(result))
                    if isinstance(summary, dict):
                        _, reference = _read_capture_bootstrap(summary)
                        next_state = dict(next_state)
                        next_state["latest_bootstrap"] = reference
                except (DeadlineCaptureSchedulerError, json.JSONDecodeError):
                    # A successful existing capture remains a terminal checkpoint even
                    # when its summary cannot safely advance scheduler provenance.
                    pass
        outcomes.append(outcome)
        next_state = record_terminal_job(
            next_state, job_id=str(job["job_id"]), status=str(outcome["status"]), now=current
        )

    report = scheduler_report(now=current, policy=policy, jobs=outcomes)
    report.update({"mode": "live", "network_calls": network_calls})
    report["content_sha256"] = artifact_hash({k: v for k, v in report.items() if k != "content_sha256"})
    return report, next_state


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=REPO / "config" / "data_sources" / "2026-27-capture-scheduler.json")
    parser.add_argument("--bootstrap-fixture", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    now = utc_timestamp(args.now) if args.now else datetime.now(timezone.utc)
    try:
        policy = load_json_object(args.config)
        state_path = REPO / str(policy["state_path"])
        report_root = REPO / str(policy["report_root"])
        lock_path = REPO / str(policy["lock_path"])

        if args.dry_run:
            state = _read_state(state_path, now=now)
            if args.bootstrap_fixture:
                bootstrap = load_json_object(args.bootstrap_fixture)
            else:
                cached = _cached_bootstrap(state)
                if cached is None:
                    raise DeadlineCaptureSchedulerError(
                        "Dry run needs --bootstrap-fixture before the first official capture"
                    )
                bootstrap, _ = cached
            report, _ = dispatch(
                policy=policy,
                state=state,
                bootstrap=bootstrap,
                now=now,
                environment=os.environ,
                python=args.python,
                dry_run=True,
            )
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0

        try:
            with _single_writer_lock(lock_path):
                state = _read_state(state_path, now=now)
                bootstrap_probe: dict[str, Any] | None = None
                if args.bootstrap_fixture:
                    bootstrap = load_json_object(args.bootstrap_fixture)
                else:
                    cached = _cached_bootstrap(state)
                    if cached is None:
                        bootstrap, reference, initial = _capture_bootstrap(
                            python=args.python, environment=os.environ
                        )
                        state["latest_bootstrap"] = reference
                        bootstrap_probe = {
                            "status": "complete" if initial["returncode"] == 0 else "degraded",
                            "observed_at": reference["observed_at"],
                            "path": reference["path"],
                            "content_sha256": reference["content_sha256"],
                        }
                    else:
                        bootstrap, _ = cached
                report, state = dispatch(
                    policy=policy,
                    state=state,
                    bootstrap=bootstrap,
                    now=now,
                    environment=os.environ,
                    python=args.python,
                    dry_run=False,
                )
                if bootstrap_probe is not None:
                    report["bootstrap_probe"] = bootstrap_probe
                    report["network_calls"] = int(report["network_calls"]) + 1
                report["content_sha256"] = artifact_hash(
                    {key: value for key, value in report.items() if key != "content_sha256"}
                )
                _write_json(report_root / f"{_stamp(iso_utc(now))}.json", report, immutable=True)
                _write_json(state_path, state, immutable=False)
        except SchedulerLockContended:
            report = scheduler_report(
                now=now,
                policy=policy,
                jobs=[{"status": "refused", "detail": "single_writer_lock_contended"}],
            )
            report.update({"mode": "live", "network_calls": 0})
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
    except (DeadlineCaptureSchedulerError, FileExistsError, OSError) as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())