from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.rank_calibration import (
    RankCalibrationError,
    UNAVAILABLE_SOURCE_HASH,
    build_unavailable_season,
    load_artifact,
    rank_label,
    resolve_rank,
    summarise_season,
    validate_artifact,
    validate_row,
)


def _row(*, gameweek: int = 1, points: int = 100, lower: int = 100, upper: int = 100, mode: str = "exact") -> dict:
    return {
        "season": "2025-26",
        "gameweek": gameweek,
        "cumulative_points": points,
        "rank_lower": lower,
        "rank_upper": upper,
        "exact": mode == "exact",
        "field_size": 11_000_000,
        "snapshot_at": "2025-08-17T23:59:00Z",
        "finalised": True,
        "auto_sub_finalised": True,
        "tie_rule": "competition_rank_after_points_then_entry_id",
        "source_id": "synthetic-test-source",
        "source_artifact_hash": "a" * 64,
        "derivation_method": "synthetic-test",
        "mode": mode,
    }


def test_exact_rows_require_equal_bounds() -> None:
    row = validate_row(_row())
    assert row["mode"] == "exact"
    with pytest.raises(RankCalibrationError, match="exact rows"):
        validate_row(_row(upper=101))


def test_bounded_rows_are_non_exact() -> None:
    row = validate_row(_row(lower=100, upper=200, mode="bounded"))
    assert row["exact"] is False
    with pytest.raises(RankCalibrationError, match="bounded rows"):
        validate_row((lambda row: (row.update({"exact": True}) or row))(_row(lower=100, upper=200, mode="bounded")))


def test_unavailable_artifact_reconciles_all_38_gameweeks() -> None:
    artifact = build_unavailable_season(source_registry_version="0.6.0")
    checked = validate_artifact(artifact)
    assert len(checked["rows"]) == 38
    assert {row["mode"] for row in checked["rows"]} == {"unavailable"}
    assert all(row["rank_lower"] is None and row["rank_upper"] is None for row in checked["rows"])
    assert all(row["source_artifact_hash"] == UNAVAILABLE_SOURCE_HASH for row in checked["rows"])
    assert all(row["field_size"] is None for row in checked["rows"])


def test_summary_rejects_missing_gameweek() -> None:
    rows = [_row(gameweek=gameweek) for gameweek in range(1, 38)]
    with pytest.raises(RankCalibrationError, match="exactly one row"):
        summarise_season(rows)


def test_interpolation_returns_conservative_bounded_band() -> None:
    rows = [
        _row(points=100, lower=100, upper=100),
        _row(points=120, lower=300, upper=300),
    ]
    result = resolve_rank(110, rows, gameweek=1)
    assert result["mode"] == "bounded"
    assert result["exact"] is False
    assert result["rank_lower"] == 100
    assert result["rank_upper"] == 300
    assert "non-exact" in rank_label(result)


def test_extrapolation_is_rejected() -> None:
    rows = [_row(points=100), _row(points=120, lower=300, upper=300)]
    with pytest.raises(RankCalibrationError, match="extrapolation"):
        resolve_rank(90, rows, gameweek=1)


def test_unavailable_resolution_does_not_invent_a_rank() -> None:
    rows = [
        {
            "season": "2025-26",
            "gameweek": 1,
            "cumulative_points": 0,
            "rank_lower": None,
            "rank_upper": None,
            "exact": False,
            "field_size": None,
            "snapshot_at": "2026-07-31T00:00:00Z",
            "finalised": False,
            "auto_sub_finalised": False,
            "tie_rule": "unavailable",
            "source_id": "unavailable",
            "source_artifact_hash": UNAVAILABLE_SOURCE_HASH,
            "derivation_method": "unavailable:no_approved_source",
            "mode": "unavailable",
        }
    ]
    result = resolve_rank(75, rows, gameweek=1)
    assert result["mode"] == "unavailable"
    assert result["rank_lower"] is None
    assert rank_label(result) == "rank unavailable (no approved source)"


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    artifact = build_unavailable_season()
    artifact["artifact_sha256"] = "0" * 64
    path = tmp_path / "rank-thresholds.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(RankCalibrationError, match="SHA-256 mismatch"):
        load_artifact(path)


def test_html_json_label_is_explicitly_non_exact() -> None:
    result = resolve_rank(110, [_row(points=100), _row(points=120, lower=300, upper=300)], gameweek=1)
    payload = {"mode": result["mode"], "label": rank_label(result)}
    assert payload == {"mode": "bounded", "label": "estimated rank band 100-300 (non-exact)"}

