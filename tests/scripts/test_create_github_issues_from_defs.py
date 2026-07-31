"""Tracked-safe checks for the Beads → GitHub Issues creator."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.create_github_issues_from_defs import DEFS, MANIFEST, main

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_lists_seven_outstanding_beads() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    issues = manifest["issues"]
    assert len(issues) == 7
    bead_ids = {entry["bead_id"] for entry in issues}
    assert bead_ids == {
        "FPL-2xu",
        "FPL-761",
        "FPL-762",
        "FPL-bsw",
        "FPL-bsw.38",
        "FPL-cfb",
        "FPL-eah",
    }
    for entry in issues:
        body = DEFS / entry["file"]
        assert body.is_file(), entry["file"]
        text = body.read_text(encoding="utf-8")
        assert "Acceptance criteria" in text
        assert entry["bead_id"] in text or entry["bead_id"].replace(".", "-") in entry["file"]


def test_dry_run_exits_zero(capsys) -> None:
    assert main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "dry-run create:" in out
    assert "created=7" in out
