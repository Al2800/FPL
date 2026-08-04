#!/usr/bin/env python3
"""Run official FPL field benchmarks and write reports/forecasting artefacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.official_field_benchmarks import (  # noqa: E402
    count_predeadline_bootstrap_snapshots,
    evaluate_official_fields,
    write_official_field_benchmark_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paired-rows",
        type=Path,
        help="Optional JSON list of paired ep_next/naive/actual rows",
    )
    parser.add_argument(
        "--bootstrap-strength-pairs",
        type=Path,
        help="Optional JSON list of official vs model attack pairs",
    )
    parser.add_argument(
        "--element-summary-root",
        type=Path,
        action="append",
        default=[],
        help="Root to search for element-summary JSON (repeatable)",
    )
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        action="append",
        default=[],
        help="Capture root for counting pre-deadline bootstraps (repeatable)",
    )
    parser.add_argument(
        "--minimum-paired",
        type=int,
        default=38,
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "reports" / "forecasting",
    )
    args = parser.parse_args(argv)

    paired = []
    if args.paired_rows and args.paired_rows.exists():
        paired = json.loads(args.paired_rows.read_text(encoding="utf-8"))
    strength = []
    if args.bootstrap_strength_pairs and args.bootstrap_strength_pairs.exists():
        strength = json.loads(args.bootstrap_strength_pairs.read_text(encoding="utf-8"))

    summary_paths: list[Path] = []
    for root in args.element_summary_root:
        if root.exists():
            summary_paths.extend(root.rglob("*element-summary*.json"))

    snapshot_roots = args.snapshot_root or [
        REPO / "data" / "live-shadow" / "fpl",
        REPO / "data" / "snapshots",
    ]
    predeadline = count_predeadline_bootstrap_snapshots(snapshot_roots)

    report = evaluate_official_fields(
        paired_rows=paired if isinstance(paired, list) else [],
        bootstrap_strength_pairs=strength if isinstance(strength, list) else [],
        element_summary_paths=summary_paths,
        predeadline_snapshot_count=predeadline,
        minimum_paired_outcomes=args.minimum_paired,
    )
    paths = write_official_field_benchmark_report(args.out_dir, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "n_predeadline_snapshots": report["n_predeadline_snapshots"],
                "n_paired_outcomes": report["n_paired_outcomes"],
                "json": str(paths["json"]),
                "markdown": str(paths["markdown"]),
                "content_sha256": report["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
