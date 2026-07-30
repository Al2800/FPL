#!/usr/bin/env python3
"""Build one immutable, cutoff-safe 2026/27 launch-context successor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.forecasting.launch_context import (
    LaunchContextBuildConflict,
    LaunchContextBuildError,
    build_launch_context,
)

DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "snapshots" / "2026-27" / "launch-context"
DEFAULT_WORLD_CUP_PRIORS = REPO_ROOT / "control" / "identities" / "world-cup-2026-priors.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an immutable 2026/27 successor launch context from local files"
    )
    parser.add_argument("--season", default="2026-27")
    parser.add_argument("--bootstrap-file", type=Path, required=True)
    parser.add_argument("--bootstrap-observed-at", required=True)
    parser.add_argument("--bootstrap-available-at", required=True)
    parser.add_argument("--prior-roster-file", type=Path, required=True)
    parser.add_argument("--prior-roster-observed-at", required=True)
    parser.add_argument("--prior-roster-available-at", required=True)
    parser.add_argument("--previous-season", default="2025-26")
    parser.add_argument("--world-cup-priors-file", type=Path, default=DEFAULT_WORLD_CUP_PRIORS)
    parser.add_argument("--world-cup-observed-at", required=True)
    parser.add_argument("--world-cup-available-at", required=True)
    parser.add_argument("--context-observed-at", required=True)
    parser.add_argument("--context-available-at", required=True)
    parser.add_argument("--decision-cutoff", required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    try:
        result = build_launch_context(
            season=args.season,
            bootstrap_path=args.bootstrap_file,
            bootstrap_observed_at=args.bootstrap_observed_at,
            bootstrap_available_at=args.bootstrap_available_at,
            prior_roster_path=args.prior_roster_file,
            prior_roster_observed_at=args.prior_roster_observed_at,
            prior_roster_available_at=args.prior_roster_available_at,
            previous_season=args.previous_season,
            world_cup_priors_path=args.world_cup_priors_file,
            world_cup_observed_at=args.world_cup_observed_at,
            world_cup_available_at=args.world_cup_available_at,
            context_observed_at=args.context_observed_at,
            context_available_at=args.context_available_at,
            decision_cutoff=args.decision_cutoff,
            output_root=args.output_root,
        )
    except (LaunchContextBuildError, LaunchContextBuildConflict, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    context = result["context"]
    manifest = result["manifest"]
    print(
        json.dumps(
            {
                "context_path": str(result["context_path"]),
                "manifest_path": str(result["manifest_path"]),
                "context_content_sha256": context["content_sha256"],
                "manifest_content_sha256": manifest["content_sha256"],
                "source_hashes": {
                    key: value["sha256"]
                    for key, value in context["source_bindings"].items()
                },
                "universe_delta": context["universe_delta"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
