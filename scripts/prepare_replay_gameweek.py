#!/usr/bin/env python3
"""Prepare a sealed historical Gameweek workspace for policy review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from src.orchestration.genuine_replay import prepare_historical_gameweek


REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--gameweek", type=int, required=True)
    parser.add_argument("--episode-root", type=Path, default=None)
    parser.add_argument("--previous-checkpoint", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    episode_root = args.episode_root or (
        REPO / "data" / "benchmark-v0" / "episodes" / "v2" / args.season
    )
    previous = args.previous_checkpoint or (
        REPO
        / "reports"
        / "benchmarks"
        / args.season
        / f"gw-{args.gameweek - 1:02d}"
    )
    output_root = args.out or (
        REPO / "reports" / "benchmarks" / args.season
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    summary = prepare_historical_gameweek(
        season=args.season,
        gameweek=args.gameweek,
        episode_root=episode_root,
        previous_checkpoint_dir=previous,
        output_root=output_root,
        code_commit=commit,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
