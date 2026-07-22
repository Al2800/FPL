"""Repository guardrails for data-plane ignore rules."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_gitignore_has_no_conflict_markers():
    text = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "<<<<<<<" not in text
    assert "=======" not in text
    assert ">>>>>>>" not in text


def test_only_root_data_plane_is_ignored():
    assert _is_ignored("data/raw/source/response.json")
    assert _is_ignored("data/normalised/table.parquet")
    assert not _is_ignored("data/README.md")
    assert not _is_ignored("control/schemas/data/example.json")
