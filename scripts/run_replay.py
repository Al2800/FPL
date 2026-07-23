#!/usr/bin/env python3
"""Run the WP-09 Gameweek replay harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from src.orchestration.genuine_replay import run_historical_replay
from src.orchestration.replay_harness import DEFAULT_INPUT, DEFAULT_OUT, replay_batch, replay_gameweek

REPO = Path(__file__).resolve().parents[1]


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--season",
        default=None,
        help="Historical season for genuine replay, for example 2025-26",
    )
    parser.add_argument("--start-gameweek", type=int, default=1)
    parser.add_argument("--stop-after-gameweek", type=int, default=None)
    parser.add_argument(
        "--episode-root",
        type=Path,
        default=None,
        help="Local immutable episode root; defaults to data/benchmark-v0/episodes/v2/<season>",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Solver input JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--batch", type=int, default=0, help="If >0, time n replays of the fixture")
    parser.add_argument("--realised-points", type=float, default=None)
    parser.add_argument("--hindsight-best", type=float, default=None)
    args = parser.parse_args()

    if args.season is not None:
        if args.stop_after_gameweek is None:
            parser.error("--stop-after-gameweek is required for genuine replay")
        episode_root = args.episode_root or (
            REPO
            / "data"
            / "benchmark-v0"
            / "episodes"
            / "v2"
            / args.season
        )
        output_root = (
            args.out
            if args.out != DEFAULT_OUT
            else REPO / "reports" / "benchmarks" / args.season
        )
        summary = run_historical_replay(
            season=args.season,
            episode_root=episode_root,
            output_root=output_root,
            start_gameweek=args.start_gameweek,
            stop_after_gameweek=args.stop_after_gameweek,
            code_commit=_git_commit(),
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.batch and args.batch > 0:
        summary = replay_batch(args.input, n=args.batch, out_root=args.out)
        print(json.dumps(summary, indent=2))
        return 0

    record = replay_gameweek(
        args.input,
        out_dir=args.out,
        attach_outcome_points=args.realised_points,
        hindsight_best_points=args.hindsight_best,
    )
    print(
        f"gw={record['gameweek']} advantage={record['baseline_comparison']['expected_advantage']} "
        f"elapsed_ms={record['replay_elapsed_ms']} repro={record['repro_hash'][:12]}…"
    )
    print(f"Wrote {args.out / 'decision-record.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
