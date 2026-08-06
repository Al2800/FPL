#!/usr/bin/env python3
"""Evaluate Rotowire lineup trial metrics against the preregistered gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.evidence.lineup_consolidator import evaluate_trial_admission, load_trial_policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("control/policies/rotowire-lineups-trial-v1.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    policy = load_trial_policy(args.policy)
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    verdict = evaluate_trial_admission(metrics, trial_policy=policy)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(
        {
            "live_influence_admitted": verdict["live_influence_admitted"],
            "artifact": str(args.out),
            "content_sha256": verdict["content_sha256"],
        },
        sort_keys=True,
    ))
    return 0 if verdict["live_influence_admitted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
