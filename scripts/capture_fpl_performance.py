#!/usr/bin/env python3
"""Derive one immutable FPL-native weekly performance snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.fpl_performance_features import (
    FplPerformanceError,
    apply_fpl_performance_ablation,
    build_fpl_performance_snapshot,
    write_immutable_json,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO / "config" / "data_sources" / "2026-27-fpl-performance.json"
)


def _read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FplPerformanceError(f"Expected a JSON object: {path}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Derive point-in-time weekly FPL performance features"
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--ablation-output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        snapshot = build_fpl_performance_snapshot(
            _read_object(args.bundle),
            config=_read_object(args.config),
        )
        write_status = write_immutable_json(args.output, snapshot)
        ablation_status = None
        if args.baseline is not None or args.ablation_output is not None:
            if args.baseline is None or args.ablation_output is None:
                raise FplPerformanceError(
                    "--baseline and --ablation-output must be supplied together"
                )
            overlaid = apply_fpl_performance_ablation(
                _read_object(args.baseline),
                snapshot=snapshot,
            )
            ablation_status = write_immutable_json(
                args.ablation_output, overlaid
            )
    except (
        FplPerformanceError,
        FileExistsError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": snapshot["status"],
                "snapshot_id": snapshot["snapshot_id"],
                "output": str(args.output),
                "write": write_status,
                "content_sha256": snapshot["content_sha256"],
                "player_count": snapshot["quality"]["player_count"],
                "quarantined_metric_count": snapshot["quality"][
                    "quarantined_metric_count"
                ],
                "gap_count": len(snapshot["quality"]["gaps"]),
                "ablation_write": ablation_status,
                "account_writes": snapshot["account_writes"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if snapshot["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
