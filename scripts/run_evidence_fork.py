#!/usr/bin/env python3
"""Run the complete retrospective GW12 evidence experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.evidence_fork import (
    build_gw12_score_ceiling_review,
    run_isolated_evidence_fork,
    run_longitudinal_evidence_fork,
)


REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--gameweek", type=int, default=12)
    parser.add_argument(
        "--mode",
        choices=("complete", "isolated", "longitudinal"),
        default="complete",
    )
    parser.add_argument(
        "--evidence-bundle",
        type=Path,
        default=REPO
        / "evals"
        / "evidence-forks"
        / "2025-26"
        / "gw-12"
        / "evidence-bundle.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO
        / "reports"
        / "benchmarks"
        / "2025-26-forks"
        / "gw-12"
        / "retrospective-availability-v1",
    )
    args = parser.parse_args()
    canonical_root = REPO / "reports" / "benchmarks" / args.season
    episode_root = (
        REPO
        / "data"
        / "benchmark-v0"
        / "episodes"
        / "v2"
        / args.season
    )
    common = {
        "season": args.season,
        "gameweek": args.gameweek,
        "evidence_bundle_path": args.evidence_bundle,
        "canonical_root": canonical_root,
        "episode_root": episode_root,
        "output_root": args.out,
    }
    isolated = run_isolated_evidence_fork(**common)
    if args.mode == "isolated":
        result = isolated
    else:
        ceilings = build_gw12_score_ceiling_review(
            canonical_root=canonical_root,
            episode_root=episode_root,
            fork_root=args.out,
        )
        longitudinal = run_longitudinal_evidence_fork(**common)
        result = {
            "isolated": isolated,
            "score_ceilings": ceilings,
            "longitudinal": longitudinal,
        }
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
