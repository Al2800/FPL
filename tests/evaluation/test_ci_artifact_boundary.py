"""Portable contracts for the CI artifact boundary."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_artifact_backed_suite_fails_clearly_without_episode_root(
    tmp_path: Path,
) -> None:
    env = dict(os.environ)
    env["FPL_ARTIFACT_ROOT"] = str(tmp_path / "empty-checkout")
    env["PYTHONPATH"] = str(REPO)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "artifact_backed",
            "tests/historical-replay/test_evidence_fork.py::test_isolated_gw12_fork_is_deterministic_and_preserves_control",
            "-q",
        ],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "artifact-backed suite requires governed historical artifacts" in combined
    assert "not artifact_backed" in combined
