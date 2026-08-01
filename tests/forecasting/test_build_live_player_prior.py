from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_live_player_prior import (
    LivePlayerPriorBuildError,
    _deduplicate_exact_rows,
    build_prior_from_local_source,
)
from src.forecasting.live_faithful import artifact_hash


def _rows() -> list[dict[str, object]]:
    return [
        {
            "element": 1,
            "fixture": 1,
            "position": "MID",
            "minutes": 90,
            "starts": 1,
            "value": 60,
            "total_points": 8,
            "expected_goals": 0.2,
            "expected_assists": 0.1,
            "clean_sheets": 1,
            "saves": 0,
            "bonus": 1,
            "yellow_cards": 0,
            "red_cards": 0,
        }
    ]


def test_only_exact_duplicate_player_fixture_rows_are_removed() -> None:
    rows = pd.DataFrame(_rows() * 2)
    deduplicated, stats = _deduplicate_exact_rows(rows)

    assert len(deduplicated) == 1
    assert stats == {
        "duplicate_player_fixture_keys": 1,
        "exact_duplicate_rows_removed": 1,
    }


def test_conflicting_duplicate_player_fixture_rows_fail_closed() -> None:
    rows = pd.DataFrame(_rows() + [{**_rows()[0], "total_points": 9}])

    with pytest.raises(
        LivePlayerPriorBuildError,
        match="Conflicting duplicate player-fixture rows",
    ):
        _deduplicate_exact_rows(rows)


def test_build_prior_is_registry_gated_hash_bound_and_lineage_complete(
    tmp_path: Path,
) -> None:
    season_root = tmp_path / "data" / "2025-26"
    (season_root / "gws").mkdir(parents=True)
    pd.DataFrame(_rows() * 2).to_csv(
        season_root / "gws" / "merged_gw.csv", index=False
    )
    pd.DataFrame([{"id": 1, "code": 1001}]).to_csv(
        season_root / "players_raw.csv", index=False
    )
    model = tmp_path / "model.json"
    model.write_text(
        json.dumps({"price_bands": [[0, 5.5], [5.5, 7.5], [7.5, 10], [10, 20]]}),
        encoding="utf-8",
    )

    prior = build_prior_from_local_source(
        season="2025-26",
        as_of="2026-05-25T09:00:00Z",
        vaastav_root=tmp_path,
        model_config_path=model,
    )

    assert prior["content_sha256"] == artifact_hash(prior)
    assert prior["source"]["source_registry_id"] == "vaastav-fpl"
    assert prior["source"]["input_row_count"] == 2
    assert prior["source"]["exact_duplicate_rows_removed"] == 1
    assert prior["source"]["duplicate_player_fixture_keys"] == 1
    assert len(prior["players"]) == 1
