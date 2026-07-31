from __future__ import annotations

import pytest

pytestmark = pytest.mark.artifact_backed

import json
from pathlib import Path

from src.evidence.fpl_knowledge_materializer import resolve_fpl_knowledge_profile


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-fpl-retrieval.json").read_text(
        encoding="utf-8"
    )
)


def test_fpl_overlay_resolves_an_isolated_project_runtime(tmp_path: Path) -> None:
    profile = resolve_fpl_knowledge_profile(
        CONFIG, environ={"FPL_KB_ROOT": str(tmp_path / "fpl-evidence")}
    )

    root = Path(profile["root"])
    assert profile["profile_id"] == "fpl"
    assert Path(profile["intake_dir"]).is_relative_to(root)
    assert Path(profile["evidence_db"]).is_relative_to(root)
    assert "knowledge\\store" not in profile["root"].lower()
    assert "emailsearchlocal" not in profile["root"].lower()
    assert "emailmarkdown_staging" not in profile["root"].lower()
