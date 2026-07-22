"""Genuine historical episode construction and outcome-isolation tests."""

from __future__ import annotations

import hashlib
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.orchestration.historical_episode_builder import (
    HistoricalEpisodeError,
    build_historical_episodes,
)


ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_seed(tmp_path: Path, *, unknown_result_team: bool = False) -> tuple[Path, Path]:
    data_root = tmp_path / "seed"
    data_root.mkdir()
    frames = {
        "fpl_gameweeks": pd.DataFrame(
            [
                {
                    "GW": 1,
                    "element": 1,
                    "fixture": 1,
                    "name": "Alpha Keeper",
                    "position": "GK",
                    "team": "Alpha",
                    "opponent_team": 2,
                    "kickoff_time": "2025-08-16T14:00:00Z",
                    "minutes": 90,
                    "starts": 1,
                    "total_points": 6,
                    "goals_scored": 0,
                    "assists": 0,
                    "clean_sheets": 1,
                    "value": 45,
                    "xP": 99.0,
                },
                {
                    "GW": 1,
                    "element": 2,
                    "fixture": 1,
                    "name": "Beta Forward",
                    "position": "FWD",
                    "team": "Beta",
                    "opponent_team": 1,
                    "kickoff_time": "2025-08-16T14:00:00Z",
                    "minutes": 90,
                    "starts": 1,
                    "total_points": 2,
                    "goals_scored": 0,
                    "assists": 0,
                    "clean_sheets": 0,
                    "value": 70,
                    "xP": 88.0,
                },
                {
                    "GW": 1,
                    "element": 3,
                    "fixture": 1,
                    "name": "Late Row",
                    "position": "MID",
                    "team": "Alpha",
                    "opponent_team": 2,
                    "kickoff_time": "2025-08-30T19:00:00Z",
                    "minutes": 90,
                    "starts": 1,
                    "total_points": 20,
                    "goals_scored": 3,
                    "assists": 2,
                    "clean_sheets": 0,
                    "value": 50,
                    "xP": 77.0,
                },
                {
                    "GW": 2,
                    "element": 1,
                    "fixture": 2,
                    "name": "Alpha Keeper",
                    "position": "GK",
                    "team": "Alpha",
                    "opponent_team": 2,
                    "kickoff_time": "2025-08-23T14:00:00Z",
                    "minutes": 90,
                    "starts": 1,
                    "total_points": 3,
                    "goals_scored": 0,
                    "assists": 0,
                    "clean_sheets": 0,
                    "value": 45,
                    "xP": 66.0,
                },
            ]
        ),
        "fpl_fixtures": pd.DataFrame(
            [
                {
                    "id": 1,
                    "event": 1,
                    "kickoff_time": "2025-08-16T14:00:00Z",
                    "team_h": 1,
                    "team_a": 2,
                    "team_h_difficulty": 2,
                    "team_a_difficulty": 4,
                    "provisional_start_time": False,
                    "team_h_score": 1,
                    "team_a_score": 0,
                    "stats": "secret-gw1",
                    "finished": True,
                    "started": True,
                    "minutes": 90,
                },
                {
                    "id": 2,
                    "event": 2,
                    "kickoff_time": "2025-08-23T14:00:00Z",
                    "team_h": 2,
                    "team_a": 1,
                    "team_h_difficulty": 3,
                    "team_a_difficulty": 3,
                    "provisional_start_time": False,
                    "team_h_score": 2,
                    "team_a_score": 2,
                    "stats": "secret-gw2",
                    "finished": True,
                    "started": True,
                    "minutes": 90,
                },
            ]
        ),
        "fpl_players": pd.DataFrame(
            [
                {"id": 1, "code": 101, "team": 1},
                {"id": 2, "code": 102, "team": 2},
                {"id": 3, "code": 103, "team": 1},
            ]
        ),
        "fpl_teams": pd.DataFrame(
            [{"id": 1, "name": "Alpha"}, {"id": 2, "name": "Beta"}]
        ),
        "match_results": pd.DataFrame(
            [
                {
                    "Date": "16/08/2025",
                    "Time": "15:00",
                    "HomeTeam": "Unknown" if unknown_result_team else "Alpha",
                    "AwayTeam": "Beta",
                    "FTHG": 1,
                    "FTAG": 0,
                    "FTR": "H",
                    "B365H": 1.5,
                    "B365D": 4.0,
                    "B365A": 6.0,
                },
                {
                    "Date": "23/08/2025",
                    "Time": "15:00",
                    "HomeTeam": "Beta",
                    "AwayTeam": "Alpha",
                    "FTHG": 2,
                    "FTAG": 2,
                    "FTR": "D",
                    "B365H": 2.5,
                    "B365D": 3.0,
                    "B365A": 2.8,
                },
            ]
        ),
    }
    sources = []
    for role, frame in frames.items():
        path = data_root / f"{role}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {
                "dataset_role": role,
                "source_id": "football-data-co-uk" if role == "match_results" else "vaastav-fpl",
                "local_artifact": path.name,
                "content_hash_sha256": _sha256(path),
                "content_identity": f"sha256:{_sha256(path)}",
                "observed_at": "2026-07-22T12:57:20Z",
                "source_registry_version": "0.3.0",
            }
        )
    manifest = {
        "manifest_version": "1.0",
        "dataset_id": "benchmark-test-2025-26",
        "dataset_hash": "f" * 64,
        "status": "frozen",
        "season": "2025-26",
        "gameweeks": [1, 2],
        "created_at": "2026-07-22T12:57:20Z",
        "sources": sources,
        "point_in_time_policy": {
            "historical_evidence_mode": "structured_only",
            "excluded_from_observed_features": [
                "unshifted vaastav xP",
                "same-Gameweek outcomes",
                "untimestamped odds",
                "reconstructed historical injury or news evidence",
            ],
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, data_root


def _build(tmp_path: Path, **kwargs):
    manifest_path, data_root = _write_seed(tmp_path, **kwargs)
    out_dir = tmp_path / "episodes"
    index = build_historical_episodes(
        dataset_manifest_path=manifest_path,
        data_root=data_root,
        out_dir=out_dir,
        gameweeks=[1, 2],
        code_commit=COMMIT,
    )
    return index, out_dir, manifest_path, data_root


def test_builds_schema_valid_distinct_observed_and_hidden_episodes(tmp_path: Path) -> None:
    index, out_dir, _, _ = _build(tmp_path)
    assert index["episode_count"] == 2
    assert len({row["observed_episode_sha256"] for row in index["episodes"]}) == 2

    schema = json.loads(
        (ROOT / "control/schemas/benchmark/episode-manifest.json").read_text(encoding="utf-8")
    )
    episode = json.loads((out_dir / "gw-02" / "episode-manifest.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(episode)
    rules_path = ROOT / "control/rules/2025-26.yaml"
    rules_hash = hashlib.sha256(rules_path.read_bytes()).hexdigest()
    assert episode["ruleset"] == {
        "ruleset_id": "2025-26-v1.0",
        "content_sha256": rules_hash,
    }
    assert hashlib.sha256((out_dir / "gw-02" / "ruleset.yaml").read_bytes()).hexdigest() == rules_hash

    observed = json.loads((out_dir / "gw-02" / "observed.json").read_text())
    hidden = json.loads((out_dir / "gw-02" / "hidden-outcome.json").read_text())
    assert {row["GW"] for row in observed["lagged_player_features"]} == {1}
    assert {row["element"] for row in observed["lagged_player_features"]} == {1, 2}
    assert all("xP" not in row for row in observed["lagged_player_features"])
    assert all("team_h_score" not in row for row in observed["fixtures"])
    assert all("stats" not in row for row in observed["fixtures"])
    assert hidden["player_outcomes"][0]["GW"] == 2
    assert hidden["player_outcomes"][0]["total_points"] == 3
    assert hidden["player_outcomes"][0]["minutes"] == 90
    assert hidden["fixtures"][0]["team_h_score"] == 2
    assert "B365H" not in json.dumps(observed)


def test_gameweek_one_records_cold_start_and_unavailable_evidence(tmp_path: Path) -> None:
    _, out_dir, _, _ = _build(tmp_path)
    observed = json.loads((out_dir / "gw-01" / "observed.json").read_text())
    manager = json.loads((out_dir / "gw-01" / "manager-state.json").read_text())
    assert observed["lagged_player_features"] == []
    assert "cold_start_no_prior_gameweek" in observed["limitations"]
    assert "historical_news_unavailable" in observed["limitations"]
    assert "final_export_fixture_revision_not_archived" in observed["limitations"]
    assert "historical_rules_not_yet_executable" not in observed["limitations"]
    assert manager["status"] == "unavailable_requires_policy_state"


def test_rebuild_is_deterministic_and_does_not_overwrite_conflicts(tmp_path: Path) -> None:
    index, out_dir, manifest_path, data_root = _build(tmp_path)
    second = build_historical_episodes(
        dataset_manifest_path=manifest_path,
        data_root=data_root,
        out_dir=out_dir,
        gameweeks=[1, 2],
        code_commit=COMMIT,
    )
    assert second == index

    target = out_dir / "gw-02" / "observed.json"
    target.write_text('{"corrupt":true}', encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to replace immutable artefact"):
        build_historical_episodes(
            dataset_manifest_path=manifest_path,
            data_root=data_root,
            out_dir=out_dir,
            gameweeks=[1, 2],
            code_commit=COMMIT,
        )


def test_unknown_cross_source_team_identity_fails_closed(tmp_path: Path) -> None:
    manifest_path, data_root = _write_seed(tmp_path, unknown_result_team=True)
    with pytest.raises(HistoricalEpisodeError, match="Unresolved football-data team identities"):
        build_historical_episodes(
            dataset_manifest_path=manifest_path,
            data_root=data_root,
            out_dir=tmp_path / "episodes",
            gameweeks=[1, 2],
            code_commit=COMMIT,
        )


def test_public_index_contains_hashes_and_counts_not_restricted_rows(tmp_path: Path) -> None:
    index, _, _, _ = _build(tmp_path)
    encoded = json.dumps(index)
    assert '"total_points":' not in encoded
    assert '"minutes":' not in encoded
    assert "player_outcomes" not in encoded
    assert all(row["observed_rows"] >= 1 for row in index["episodes"])
    assert all(len(row["hidden_outcome_sha256"]) == 64 for row in index["episodes"])
    assert all(row["ruleset_id"] == "2025-26-v1.0" for row in index["episodes"])
    assert all(len(row["ruleset_sha256"]) == 64 for row in index["episodes"])
