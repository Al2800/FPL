"""WP-10: every §19 deferred feature has an interface-only design note."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFERRED = REPO / "docs" / "architecture" / "deferred"

REQUIRED_NOTES = [
    "article-corpus.md",
    "vector-rag.md",
    "podcast-transcripts.md",
    "source-reputation.md",
    "rival-analysis.md",
    "effective-ownership.md",
    "price-strategy.md",
    "rank-aware-strategy.md",
    "live-match-agents.md",
    "realtime-ranks-bonus.md",
    "browser-dry-run.md",
    "auto-lineup.md",
    "auto-transfers.md",
    "autonomous-chips.md",
    "cloud-warehouse.md",
    "distributed-orchestration.md",
]

REQUIRED_SECTIONS = (
    "## Purpose",
    "## Anticipated interfaces",
    "## Prerequisites",
    "## Activation criteria",
    "## Non-goals",
)


def test_deferred_notes_exist_with_required_sections() -> None:
    assert (DEFERRED / "README.md").exists()
    for name in REQUIRED_NOTES:
        path = DEFERRED / name
        assert path.exists(), name
        text = path.read_text(encoding="utf-8")
        for heading in REQUIRED_SECTIONS:
            assert heading in text, f"{name} missing {heading}"


def test_no_deferred_execution_implementation_added() -> None:
    """Execution remains deferred; evidence agents were activated by FPL-bsw.15."""
    for pkg in ("execution",):
        root = REPO / "src" / pkg
        if not root.exists():
            continue
        py_files = [p for p in root.rglob("*.py") if p.name != "__init__.py" or p.stat().st_size > 0]
        # Allow empty package dirs / empty __init__.py only
        non_empty = []
        for p in root.rglob("*.py"):
            content = p.read_text(encoding="utf-8").strip()
            if content:
                non_empty.append(p)
        assert non_empty == [], f"Unexpected implementation in src/{pkg}: {non_empty}"
