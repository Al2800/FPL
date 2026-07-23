#!/usr/bin/env python3
"""Run a genuine historical replay checkpoint; no synthetic relabelling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import subprocess

from src.orchestration.genuine_replay import run_historical_replay

REPO = Path(__file__).resolve().parents[1]
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--start-gameweek", type=int, default=1)
    parser.add_argument("--stop-after-gameweek", type=int, required=True)
    parser.add_argument("--episode-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    episode_root = args.episode_root or (
        REPO / "data/benchmark-v0/episodes/v2" / args.season
    )
    output_root = args.out or (
        REPO / "reports/benchmarks" / args.season
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    summary = run_historical_replay(
        season=args.season,
        episode_root=episode_root,
        output_root=output_root,
        start_gameweek=args.start_gameweek,
        stop_after_gameweek=args.stop_after_gameweek,
        code_commit=commit,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
