#!/usr/bin/env python3
"""Run reusable isolated and longitudinal historical evidence evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.weekly_evidence_programme import (
    run_weekly_evidence_programme,
    write_weekly_evidence_report,
)


REPO = Path(__file__).resolve().parents[1]


def _bundle(value: str) -> tuple[int, Path]:
    try:
        gameweek, path = value.split("=", 1)
        return int(gameweek), Path(path)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "bundle must use GAMEWEEK=PATH"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--terminal-gameweek", type=int, default=38)
    parser.add_argument(
        "--bundle",
        action="append",
        type=_bundle,
        default=None,
        help="Repeat GAMEWEEK=PATH for every evidence-injection week.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=(
            REPO
            / "reports"
            / "benchmarks"
            / "2025-26-evidence-programme"
            / "evaluation.json"
        ),
    )
    args = parser.parse_args()
    raw_bundles = args.bundle or [
        (
            12,
            REPO
            / "evals"
            / "evidence-forks"
            / "2025-26"
            / "gw-12"
            / "evidence-bundle.json",
        )
    ]
    bundles: dict[int, Path] = {}
    for gameweek, path in raw_bundles:
        if gameweek in bundles:
            parser.error(f"duplicate --bundle for GW{gameweek}")
        bundles[gameweek] = path
    report = run_weekly_evidence_programme(
        season=args.season,
        bundle_paths=bundles,
        canonical_root=REPO / "reports" / "benchmarks" / args.season,
        episode_root=(
            REPO
            / "data"
            / "benchmark-v0"
            / "episodes"
            / "v2"
            / args.season
        ),
        terminal_gameweek=args.terminal_gameweek,
    )
    write_weekly_evidence_report(args.out, report)
    print(
        json.dumps(
            {
                "output": args.out.as_posix(),
                "selected_evidence_gameweeks": report[
                    "selected_evidence_gameweeks"
                ],
                "isolated_direct_net_points_delta": report["attribution"][
                    "isolated_direct_net_points_delta"
                ],
                "longitudinal_net_points_delta": report["attribution"][
                    "longitudinal_net_points_delta"
                ],
                "state_compounding_net_points_delta": report["attribution"][
                    "state_compounding_net_points_delta"
                ],
                "promotion_eligible": report["promotion_eligible"],
                "content_sha256": report["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
