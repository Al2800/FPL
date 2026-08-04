"""Offline contracts for portable capture scheduler installers (ticket 04)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_portable_installer_script_exists_and_mentions_uninstall_safety() -> None:
    installer = (REPO / "scripts" / "install_deadline_capture_scheduler.sh").read_text(
        encoding="utf-8"
    )
    uninstaller = (
        REPO / "scripts" / "uninstall_deadline_capture_scheduler.sh"
    ).read_text(encoding="utf-8")
    assert "run_deadline_capture_dispatch.py" in installer
    assert "--dry-run" in installer
    assert "bootstrap-fixture" in installer
    assert "No evidence artifacts or scheduler state were deleted" in uninstaller
    assert (REPO / "config" / "operations" / "fpl-deadline-capture.timer.example").is_file()


def test_check_capture_freshness_simulated_missed_t2h_exits_nonzero(
    tmp_path: Path,
) -> None:
    out = tmp_path / "freshness.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "check_capture_freshness.py"),
            "--config",
            str(REPO / "config" / "data_sources" / "2026-27-capture-scheduler.json"),
            "--bootstrap-fixture",
            str(REPO / "tests" / "fixtures" / "fpl-bootstrap-scheduler.json"),
            "--state",
            str(tmp_path / "missing-state.json"),
            "--now",
            "2026-08-21T16:01:00Z",
            "--out",
            str(out),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = out.read_text(encoding="utf-8")
    assert "missed_checkpoint" in payload
    assert "T-2h" in payload
