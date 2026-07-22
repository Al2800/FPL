#!/usr/bin/env python3
"""Acquire and freeze the complete 2025/26 benchmark-v0 source pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from src.ingestion.acquisition import acquire_http, utc_now

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "benchmark-v0" / "2025-26"
DEFAULT_MANIFEST = REPO_ROOT / "control" / "manifests" / "datasets" / "benchmark-v0.json"
SEASON = "2025-26"
EXPECTED_GAMEWEEKS = list(range(1, 39))

SOURCE_FILES = (
    {
        "key": "fpl_gameweeks",
        "source_id": "vaastav-fpl",
        "artifact_name": "vaastav_merged_gw.csv",
        "url": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/gws/merged_gw.csv",
    },
    {
        "key": "fpl_fixtures",
        "source_id": "vaastav-fpl",
        "artifact_name": "vaastav_fixtures.csv",
        "url": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/fixtures.csv",
    },
    {
        "key": "fpl_players",
        "source_id": "vaastav-fpl",
        "artifact_name": "vaastav_players_raw.csv",
        "url": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/players_raw.csv",
    },
    {
        "key": "fpl_teams",
        "source_id": "vaastav-fpl",
        "artifact_name": "vaastav_teams.csv",
        "url": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/teams.csv",
    },
    {
        "key": "match_results",
        "source_id": "football-data-co-uk",
        "artifact_name": "football_data_E0_2526.csv",
        "url": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    },
)


def _stamp(observed_at: str) -> str:
    return observed_at.replace(":", "").replace("-", "")


def _hash_rows(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values(list(frame.columns)).to_csv(index=False)
    return hashlib.sha256(ordered.encode("utf-8")).hexdigest()


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def validate_seed_files(paths: dict[str, Path]) -> dict[str, Any]:
    """Fail closed on incomplete coverage, duplicate keys or identity gaps."""

    merged = pd.read_csv(paths["fpl_gameweeks"], low_memory=False, encoding="latin-1")
    fixtures = pd.read_csv(paths["fpl_fixtures"], low_memory=False, encoding="latin-1")
    players = pd.read_csv(paths["fpl_players"], low_memory=False, encoding="latin-1")
    teams = pd.read_csv(paths["fpl_teams"], low_memory=False, encoding="latin-1")
    results = pd.read_csv(paths["match_results"], low_memory=False, encoding="latin-1")

    _require_columns(merged, {"GW", "element", "fixture", "total_points"}, "merged_gw")
    _require_columns(fixtures, {"id", "event", "team_h", "team_a"}, "fixtures")
    _require_columns(players, {"id", "code", "team"}, "players_raw")
    _require_columns(teams, {"id", "name"}, "teams")
    _require_columns(results, {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}, "E0")

    gameweeks = sorted(int(value) for value in merged["GW"].dropna().unique())
    if gameweeks != EXPECTED_GAMEWEEKS:
        missing = sorted(set(EXPECTED_GAMEWEEKS) - set(gameweeks))
        extra = sorted(set(gameweeks) - set(EXPECTED_GAMEWEEKS))
        raise ValueError(f"merged_gw coverage mismatch: missing={missing}, extra={extra}")

    fixture_gameweeks = sorted(int(value) for value in fixtures["event"].dropna().unique())
    if fixture_gameweeks != EXPECTED_GAMEWEEKS:
        missing = sorted(set(EXPECTED_GAMEWEEKS) - set(fixture_gameweeks))
        extra = sorted(set(fixture_gameweeks) - set(EXPECTED_GAMEWEEKS))
        raise ValueError(f"fixture coverage mismatch: missing={missing}, extra={extra}")

    natural_key = ["element", "GW", "fixture"]
    duplicate_groups = merged.loc[merged.duplicated(subset=natural_key, keep=False)]
    conflicting_duplicate_keys = sum(
        len(group.drop_duplicates()) > 1
        for _, group in duplicate_groups.groupby(natural_key, dropna=False)
    )
    if conflicting_duplicate_keys:
        raise ValueError(
            f"merged_gw conflicting duplicate natural keys: {conflicting_duplicate_keys}"
        )
    exact_duplicate_rows = int(merged.duplicated(keep="first").sum())
    merged = merged.drop_duplicates().reset_index(drop=True)

    duplicate_fixtures = int(fixtures.duplicated(subset=["id"]).sum())
    if duplicate_fixtures:
        raise ValueError(f"fixture duplicate ids: {duplicate_fixtures}")
    duplicate_results = int(results.duplicated(subset=["Date", "HomeTeam", "AwayTeam"]).sum())
    if duplicate_results:
        raise ValueError(f"football-data duplicate match keys: {duplicate_results}")

    player_ids = set(players["id"].dropna().astype(int))
    observed_players = set(merged["element"].dropna().astype(int))
    unresolved_players = sorted(observed_players - player_ids)
    if unresolved_players:
        raise ValueError(f"merged_gw player identity gaps: {unresolved_players[:10]}")

    team_ids = set(teams["id"].dropna().astype(int))
    fixture_teams = set(fixtures["team_h"].dropna().astype(int)) | set(
        fixtures["team_a"].dropna().astype(int)
    )
    unresolved_teams = sorted(fixture_teams - team_ids)
    if unresolved_teams:
        raise ValueError(f"fixture team identity gaps: {unresolved_teams}")

    gw_hashes = {
        str(gw): _hash_rows(merged.loc[merged["GW"] == gw])
        for gw in EXPECTED_GAMEWEEKS
    }
    if len(set(gw_hashes.values())) != len(EXPECTED_GAMEWEEKS):
        raise ValueError("Gameweek partitions are not materially distinct")
    if len(results) != 380:
        raise ValueError(f"football-data expected 380 EPL matches, found {len(results)}")

    return {
        "gameweeks": EXPECTED_GAMEWEEKS,
        "gameweek_count": 38,
        "gameweek_rows": int(len(merged)),
        "players": int(len(player_ids)),
        "fixtures": int(len(fixtures)),
        "teams": int(len(team_ids)),
        "matches": int(len(results)),
        "exact_duplicate_rows_collapsed": exact_duplicate_rows,
        "conflicting_duplicate_keys": 0,
        "unresolved_player_ids": 0,
        "unresolved_team_ids": 0,
        "gameweek_partition_hashes": gw_hashes,
    }


def _write_frozen_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("dataset_hash") != manifest.get("dataset_hash"):
            raise FileExistsError(f"Refusing to replace frozen benchmark manifest: {path}")
        return existing
    path.write_bytes(encoded)
    return manifest


def seed_benchmark_v0(
    *,
    out_dir: Path = DEFAULT_OUT,
    manifest_path: Path = DEFAULT_MANIFEST,
    observed_at: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    observed = observed_at or utc_now()
    owns_client = client is None
    active_client = client or httpx.Client(
        headers={"User-Agent": "fpl-agentic-decision-lab/0.1 (private research)"},
        follow_redirects=True,
    )
    acquisitions: list[tuple[dict[str, str], dict[str, Any]]] = []
    try:
        for spec in SOURCE_FILES:
            acquisition = acquire_http(
                active_client,
                source_id=spec["source_id"],
                url=spec["url"],
                out_dir=out_dir,
                artifact_name=spec["artifact_name"],
                observed_at=observed,
                timeout=90.0,
            )
            acquisitions.append((spec, acquisition))
    finally:
        if owns_client:
            active_client.close()

    failures = [
        acquisition
        for _, acquisition in acquisitions
        if acquisition["acquisition_status"] != "success"
    ]
    if failures:
        details = [(item["request_url"], item["acquisition_status"]) for item in failures]
        raise RuntimeError(f"benchmark source acquisition failed: {details}")

    run_dir = out_dir / _stamp(observed)
    paths = {spec["key"]: run_dir / acquisition["body_file"] for spec, acquisition in acquisitions}
    coverage = validate_seed_files(paths)
    source_entries = [
        {
            "dataset_role": spec["key"],
            "source_id": acquisition["source_id"],
            "origin": acquisition["origin"],
            "observed_at": acquisition["observed_at"],
            "source_registry_version": acquisition["source_registry_version"],
            "content_identity": acquisition["content_identity"],
            "content_hash_sha256": acquisition["content_hash_sha256"],
            "bytes": acquisition["bytes"],
            "acquisition_manifest_id": acquisition["manifest_id"],
            "local_artifact": str(paths[spec["key"]].relative_to(out_dir)),
        }
        for spec, acquisition in acquisitions
    ]
    stable = {
        "dataset_id": "benchmark-v0-2025-26",
        "season": SEASON,
        "gameweeks": EXPECTED_GAMEWEEKS,
        "source_content_identities": [entry["content_identity"] for entry in source_entries],
        "gameweek_partition_hashes": coverage["gameweek_partition_hashes"],
    }
    dataset_hash = hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    manifest: dict[str, Any] = {
        "manifest_version": "1.0",
        "dataset_id": "benchmark-v0-2025-26",
        "dataset_hash": dataset_hash,
        "status": "frozen",
        "season": SEASON,
        "gameweeks": EXPECTED_GAMEWEEKS,
        "all_gameweeks": True,
        "created_at": observed,
        "sources": source_entries,
        "coverage": coverage,
        "point_in_time_policy": {
            "observed_allowed": [
                "lagged prior-Gameweek player outcomes",
                "fixture structure available by episode cutoff",
                "match results strictly earlier than episode cutoff",
            ],
            "excluded_from_observed_features": [
                "unshifted vaastav xP",
                "same-Gameweek outcomes including total_points and minutes",
                "football-data odds without a timestamp before the FPL deadline",
                "reconstructed historical injury or news evidence",
            ],
            "historical_evidence_mode": "structured_only",
        },
    }
    return _write_frozen_manifest(manifest_path, manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        manifest = seed_benchmark_v0(out_dir=args.out, manifest_path=args.manifest)
    except (PermissionError, FileExistsError, RuntimeError, ValueError) as exc:
        print(f"failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
