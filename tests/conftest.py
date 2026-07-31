"""Shared pytest hooks for the portable / artifact-backed boundary."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EPISODE_ROOT = REPO_ROOT / "data" / "benchmark-v0" / "episodes"
DEFAULT_VAASTAV_ROOT = (
    REPO_ROOT / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
)


def _artifact_root() -> Path:
    configured = os.environ.get("FPL_ARTIFACT_ROOT", "").strip()
    return Path(configured).expanduser().resolve() if configured else REPO_ROOT


def artifact_roots_available() -> bool:
    """Return True when governed episode artifacts are present for local runs."""

    root = _artifact_root()
    episodes = root / "data" / "benchmark-v0" / "episodes"
    return episodes.is_dir() and any(episodes.iterdir())


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "artifact_backed: requires governed local historical artifacts "
        "(set FPL_ARTIFACT_ROOT or provide data/benchmark-v0/episodes)",
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    if "artifact_backed" not in item.keywords:
        return
    if artifact_roots_available():
        return
    root = _artifact_root()
    pytest.fail(
        "artifact-backed suite requires governed historical artifacts. "
        "Provide data/benchmark-v0/episodes under the repo or set "
        f"FPL_ARTIFACT_ROOT to an approved artifact checkout (tried: {root}). "
        "The portable suite is: python -m pytest -m 'not artifact_backed'."
    )
