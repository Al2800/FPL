"""Offline tests for the complete 2025/26 benchmark-v0 seed."""

from __future__ import annotations

from pathlib import Path

import httpx
import pandas as pd
import pytest

from scripts.seed_benchmark_v0 import (
    EXPECTED_GAMEWEEKS,
    SOURCE_FILES,
    seed_benchmark_v0,
    validate_seed_files,
)

OBSERVED_AT = "2026-07-22T13:00:00Z"


def _frames() -> dict[str, pd.DataFrame]:
    merged = pd.DataFrame(
        [
            {
                "GW": gw,
                "element": 1,
                "fixture": gw,
                "total_points": gw % 10,
                "minutes": 90,
                "xP": float(gw),
            }
            for gw in EXPECTED_GAMEWEEKS
        ]
    )
    fixtures = pd.DataFrame(
        [
            {"id": gw, "event": gw, "team_h": 1, "team_a": 2}
            for gw in EXPECTED_GAMEWEEKS
        ]
    )
    players = pd.DataFrame([{"id": 1, "code": 1001, "team": 1}])
    teams = pd.DataFrame([{"id": 1, "name": "Alpha"}, {"id": 2, "name": "Beta"}])
    results = pd.DataFrame(
        [
            {
                "Date": f"{(index % 28) + 1:02d}/{(index % 12) + 1:02d}/26-{index}",
                "HomeTeam": f"H{index % 20}",
                "AwayTeam": f"A{(index + 1) % 20}",
                "FTHG": index % 5,
                "FTAG": (index + 1) % 4,
            }
            for index in range(380)
        ]
    )
    return {
        "fpl_gameweeks": merged,
        "fpl_fixtures": fixtures,
        "fpl_players": players,
        "fpl_teams": teams,
        "match_results": results,
    }


def _write_frames(root: Path, frames: dict[str, pd.DataFrame]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for key, frame in frames.items():
        path = root / f"{key}.csv"
        frame.to_csv(path, index=False)
        paths[key] = path
    return paths


def _client(frames: dict[str, pd.DataFrame]) -> httpx.Client:
    by_url = {
        spec["url"]: frames[spec["key"]].to_csv(index=False).encode("utf-8")
        for spec in SOURCE_FILES
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(200, content=by_url[str(request.url)], request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_seed_downloads_validates_and_freezes_all_gameweeks(tmp_path: Path) -> None:
    manifest_path = tmp_path / "control" / "benchmark-v0.json"
    out_dir = tmp_path / "data"
    with _client(_frames()) as client:
        first = seed_benchmark_v0(
            out_dir=out_dir,
            manifest_path=manifest_path,
            observed_at=OBSERVED_AT,
            client=client,
        )
        second = seed_benchmark_v0(
            out_dir=out_dir,
            manifest_path=manifest_path,
            observed_at="2026-07-23T13:00:00Z",
            client=client,
        )

    assert first == second
    assert first["status"] == "frozen"
    assert first["season"] == "2025-26"
    assert first["gameweeks"] == EXPECTED_GAMEWEEKS
    assert first["all_gameweeks"] is True
    assert first["coverage"]["gameweek_count"] == 38
    assert first["coverage"]["matches"] == 380
    assert len(first["sources"]) == 5
    exclusions = first["point_in_time_policy"]["excluded_from_observed_features"]
    assert "unshifted vaastav xP" in exclusions
    assert any("same-Gameweek outcomes" in value for value in exclusions)
    assert any("odds" in value for value in exclusions)
    assert manifest_path.exists()
    assert len(list((out_dir / "20260722T130000Z").glob("*.meta.json"))) == 5


def test_missing_gameweek_fails_closed(tmp_path: Path) -> None:
    frames = _frames()
    frames["fpl_gameweeks"] = frames["fpl_gameweeks"].query("GW != 38")
    with pytest.raises(ValueError, match=r"missing=\[38\]"):
        validate_seed_files(_write_frames(tmp_path, frames))


def test_exact_duplicate_row_is_counted_and_collapsed(tmp_path: Path) -> None:
    frames = _frames()
    frames["fpl_gameweeks"] = pd.concat(
        [frames["fpl_gameweeks"], frames["fpl_gameweeks"].iloc[[0]]],
        ignore_index=True,
    )
    report = validate_seed_files(_write_frames(tmp_path, frames))
    assert report["exact_duplicate_rows_collapsed"] == 1
    assert report["gameweek_rows"] == 38


def test_conflicting_duplicate_natural_key_fails_closed(tmp_path: Path) -> None:
    frames = _frames()
    conflict = frames["fpl_gameweeks"].iloc[[0]].copy()
    conflict["total_points"] = 999
    frames["fpl_gameweeks"] = pd.concat(
        [frames["fpl_gameweeks"], conflict],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="conflicting duplicate natural keys"):
        validate_seed_files(_write_frames(tmp_path, frames))


def test_player_identity_gap_fails_closed(tmp_path: Path) -> None:
    frames = _frames()
    frames["fpl_gameweeks"].loc[0, "element"] = 999
    with pytest.raises(ValueError, match="player identity gaps"):
        validate_seed_files(_write_frames(tmp_path, frames))
