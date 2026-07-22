#!/usr/bin/env python3
"""Build outcome-isolated historical episodes from the frozen Benchmark v0 seed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.orchestration.historical_episode_builder import (
    DEFAULT_DATASET_MANIFEST,
    DEFAULT_RULES,
    HistoricalEpisodeError,
    build_historical_episodes,
    write_episode_index,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
DEFAULT_INDEX = (
    REPO_ROOT / "evals" / "episodes" / "structured" / "benchmark-v0-index-v2.json"
)


def _gameweeks(value: str | None) -> list[int] | None:
    if value is None:
        return None
    try:
        parsed = sorted({int(item.strip()) for item in value.split(",") if item.strip()})
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Gameweeks must be comma-separated integers") from exc
    if not parsed or any(item < 1 or item > 38 for item in parsed):
        raise argparse.ArgumentTypeError("Gameweeks must be between 1 and 38")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_DATASET_MANIFEST)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Root containing the manifest's local_artifact paths",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--gameweeks",
        type=str,
        help="Optional comma-separated Gameweeks; default builds the frozen set",
    )
    parser.add_argument(
        "--index",
        type=Path,
        help="Safe index path; full builds default to evals/episodes/structured",
    )
    args = parser.parse_args(argv)
    try:
        selected = _gameweeks(args.gameweeks)
        index = build_historical_episodes(
            dataset_manifest_path=args.manifest,
            data_root=args.data_root,
            out_dir=args.out,
            gameweeks=selected,
            rules_path=args.rules,
        )
        index_path = args.index
        if index_path is None:
            index_path = DEFAULT_INDEX if selected is None else args.out / "episode-index.json"
        write_episode_index(index, index_path)
    except (HistoricalEpisodeError, FileExistsError, OSError, ValueError) as exc:
        print(f"failed: {exc}", file=sys.stderr)
        return 1

    rows = index["episodes"]
    summary = {
        "dataset_id": index["dataset_id"],
        "episode_count": index["episode_count"],
        "first_gameweek": rows[0]["gameweek"] if rows else None,
        "last_gameweek": rows[-1]["gameweek"] if rows else None,
        "distinct_observed_hashes": len(
            {row["observed_episode_sha256"] for row in rows}
        ),
        "index": str(index_path),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
