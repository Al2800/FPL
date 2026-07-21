#!/usr/bin/env python3
"""Run the WP-09 Gameweek replay harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.replay_harness import DEFAULT_INPUT, DEFAULT_OUT, replay_batch, replay_gameweek


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Solver input JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--batch", type=int, default=0, help="If >0, time n replays of the fixture")
    parser.add_argument("--realised-points", type=float, default=None)
    parser.add_argument("--hindsight-best", type=float, default=None)
    args = parser.parse_args()

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
