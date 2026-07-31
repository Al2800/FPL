"""Contracts for prospective Overall standings capture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ingestion.official_global_standings import (
    OfficialGlobalStandingsError,
    artifact_hash,
    assert_capture_permitted,
    build_standings_snapshot,
    load_rank_thresholds_config,
    thresholds_from_standings_snapshot,
)
from src.ingestion.registry import get_source


REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config/data_sources/2026-27-rank-thresholds.json"


def _page(*, page: int, has_next: bool, rows: list[dict], rank_count: int = 100) -> dict:
    return {
        "league": {"id": 314, "rank_count": rank_count},
        "standings": {
            "has_next": has_next,
            "page": page,
            "results": rows,
        },
    }


def test_config_and_registry_authorise_disabled_by_default_capture() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    assert config["collection_enabled"] is False
    assert config["owner_approved"] is True
    assert config["decision_path_use"] == "forbidden"
    source = get_source("fpl-official-endpoints")
    assert any("leagues-classic/314/standings" in endpoint for endpoint in source["endpoints"])
    with pytest.raises(OfficialGlobalStandingsError, match="collection_enabled is false"):
        assert_capture_permitted(config)


def test_disabled_config_never_captures() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    with pytest.raises(OfficialGlobalStandingsError, match="collection_enabled is false"):
        build_standings_snapshot(
            config=config,
            gameweek=1,
            observed_at="2026-08-24T09:00:00Z",
            available_at="2026-08-24T09:00:00Z",
            finalised_at="2026-08-24T09:00:00Z",
            pages=[_page(page=1, has_next=False, rows=[])],
        )


def test_enabled_capture_records_pages_gaps_and_temporal_fields() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    config = {**config, "collection_enabled": True}
    pages = [
        _page(
            page=1,
            has_next=True,
            rows=[
                {"rank": 1, "entry": 11, "total": 90, "event_total": 12},
                {"rank": 2, "entry": 12, "total": 88, "event_total": 10},
            ],
        ),
        None,
        _page(
            page=3,
            has_next=False,
            rows=[{"rank": 99, "entry": 99, "total": 40, "event_total": 4}],
        ),
    ]
    snapshot = build_standings_snapshot(
        config=config,
        gameweek=3,
        observed_at="2026-08-24T09:00:00Z",
        available_at="2026-08-24T08:55:00Z",
        finalised_at="2026-08-24T08:50:00Z",
        pages=pages,
    )
    assert snapshot["content_sha256"] == artifact_hash(snapshot)
    assert snapshot["gameweek"] == 3
    assert snapshot["finalisation_state"] == "post_finalisation"
    assert snapshot["field_size"] == 100
    assert len(snapshot["pages"]) == 2
    assert snapshot["gaps"] == [
        {
            "page": 2,
            "endpoint": config["endpoint_template"].format(page=2),
            "reason": "missing_page",
        }
    ]
    assert snapshot["decision_path_use"] == "forbidden"


def test_threshold_transformation_exact_bounded_and_gap_modes() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    config = {**config, "collection_enabled": True}
    snapshot = build_standings_snapshot(
        config=config,
        gameweek=2,
        observed_at="2026-08-24T09:00:00Z",
        available_at="2026-08-24T09:00:00Z",
        finalised_at="2026-08-24T09:00:00Z",
        pages=[
            _page(
                page=1,
                has_next=False,
                rows=[
                    {"rank": 1, "entry": 1, "total": 100, "event_total": 20},
                    {"rank": 2, "entry": 2, "total": 90, "event_total": 10},
                    {"rank": 3, "entry": 3, "total": 90, "event_total": 10},
                ],
                rank_count=3,
            )
        ],
    )
    pack = thresholds_from_standings_snapshot(
        snapshot, cumulative_points_targets=[100, 90, 50]
    )
    assert pack["content_sha256"] == artifact_hash(pack)
    by_points = {row["cumulative_points"]: row for row in pack["rows"]}
    assert by_points[100]["mode"] == "exact"
    assert by_points[100]["rank_lower"] == by_points[100]["rank_upper"] == 1
    assert by_points[90]["mode"] == "bounded"
    assert by_points[90]["rank_lower"] == 2
    assert by_points[90]["rank_upper"] == 3
    assert by_points[50]["mode"] == "unavailable"
    assert by_points[50]["rank_lower"] is None


def test_fetch_page_stops_at_has_next_false_without_prefetch() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    config = {**config, "collection_enabled": True, "max_pages": 5}
    calls: list[int] = []

    def fetch(page: int):
        calls.append(page)
        return _page(
            page=page,
            has_next=False,
            rows=[{"rank": 1, "entry": 1, "total": 10, "event_total": 1}],
            rank_count=1,
        )

    snapshot = build_standings_snapshot(
        config=config,
        gameweek=1,
        observed_at="2026-08-24T09:00:00Z",
        available_at="2026-08-24T09:00:00Z",
        finalised_at="2026-08-24T09:00:00Z",
        fetch_page=fetch,
    )
    assert calls == [1]
    assert len(snapshot["pages"]) == 1
    assert snapshot["gaps"] == []


def test_missing_pages_only_pack_is_unavailable_not_invented() -> None:
    config = load_rank_thresholds_config(CONFIG_PATH)
    config = {**config, "collection_enabled": True}
    snapshot = build_standings_snapshot(
        config=config,
        gameweek=4,
        observed_at="2026-08-24T09:00:00Z",
        available_at="2026-08-24T09:00:00Z",
        finalised_at="2026-08-24T09:00:00Z",
        pages=[None],
    )
    pack = thresholds_from_standings_snapshot(snapshot)
    assert len(pack["rows"]) == 1
    assert pack["rows"][0]["mode"] == "unavailable"
    assert pack["gaps"]
