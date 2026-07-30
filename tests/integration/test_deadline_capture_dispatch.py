"""Integration contracts for the local deadline-capture dispatcher."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run_deadline_capture_dispatch.py"
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


def _dispatcher_module():
    spec = importlib.util.spec_from_file_location("deadline_dispatch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_is_offline_and_returns_bounded_schedule(tmp_path: Path) -> None:
    fixture = tmp_path / "bootstrap.json"
    fixture.write_text(json.dumps(BOOTSTRAP), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dry-run",
            "--bootstrap-fixture",
            str(fixture),
            "--now",
            "2026-08-20T17:30:00Z",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["mode"] == "dry_run"
    assert payload["network_calls"] == 0
    assert payload["state_written"] is False
    assert payload["account_writes"] is False
    assert payload["browser_actions"] is False
    assert [(job["kind"], job["checkpoint"]) for job in payload["jobs"] if job["status"] == "due"] == [
        ("odds", "T-24h"),
        ("official", "T-24h"),
    ]


def test_absent_odds_key_degrades_without_an_odds_command(monkeypatch) -> None:
    dispatcher = _dispatcher_module()
    calls: list[list[str]] = []

    def fake_run(command, *, environment):
        calls.append(command)
        return {"returncode": 0, "stdout": "{}", "stderr": ""}

    monkeypatch.setattr(dispatcher, "_run", fake_run)
    now = datetime(2026, 8, 20, 17, 30, tzinfo=timezone.utc)
    state = dispatcher.new_scheduler_state(now=now)
    report, _ = dispatcher.dispatch(
        policy=POLICY,
        state=state,
        bootstrap=BOOTSTRAP,
        now=now,
        environment={},
        python=sys.executable,
        dry_run=False,
    )

    due = [job for job in report["jobs"] if job["checkpoint"] == "T-24h"]
    assert [(job["kind"], job["status"], job["detail"]) for job in due] == [
        ("odds", "degraded", "degraded_missing_secret_no_network"),
        ("official", "complete", "official_capture_completed"),
    ]
    assert len(calls) == 1
    assert calls[0][1] == "scripts/capture_fpl_live_shadow.py"
    assert report["account_writes"] is False
    assert report["browser_actions"] is False

def test_child_environment_includes_this_checkout_before_existing_pythonpath() -> None:
    dispatcher = _dispatcher_module()

    environment = dispatcher._subprocess_environment({"PYTHONPATH": "existing-path"})

    assert environment["PYTHONPATH"].split(dispatcher.os.pathsep) == [
        str(REPO),
        "existing-path",
    ]

def test_parse_channel_keeps_full_output_out_of_bounded_audit_output() -> None:
    dispatcher = _dispatcher_module()
    raw = "{" + ("x" * 1200) + "}"

    assert dispatcher._result_stdout_for_parse({"stdout_for_parse": raw, "stdout": "truncated"}) == raw
    assert dispatcher._result_stdout_for_parse({"stdout": "fixture"}) == "fixture"