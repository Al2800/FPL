"""Live initial-squad default prior is the completed 2025/26 envelope."""

from __future__ import annotations

import json
from pathlib import Path

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.initial_squad_checkpoint import DEFAULT_PLAYER_PRIOR_PATH


def test_default_player_prior_is_completed_2025_26_envelope() -> None:
    assert DEFAULT_PLAYER_PRIOR_PATH.name == (
        "2026-27-shared-player-prior-2025-26.json"
    )
    assert DEFAULT_PLAYER_PRIOR_PATH.is_file()
    prior = json.loads(DEFAULT_PLAYER_PRIOR_PATH.read_text(encoding="utf-8"))
    assert prior["season"] == "2025-26"
    assert prior["content_sha256"] == artifact_hash(prior)
    assert len(prior["players"]) >= 800
