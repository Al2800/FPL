#!/usr/bin/env python3
"""Run or compare an immutable, advisory-only GW1 readiness rehearsal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.orchestration.live_readiness_rehearsal import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    LiveReadinessRehearsalError,
    compare_final_checkpoint,
    run_live_readiness_rehearsal,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a hash-bound, advisory-only GW1 T-48h readiness rehearsal"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--policy",
        type=Path,
        default=REPO_ROOT / "control" / "policies" / "initial-squad-2026-27.json",
    )
    parser.add_argument("--checkpoint", choices=("T-48h",), default="T-48h")
    parser.add_argument("--maximum-lag-minutes", type=int, default=15)
    parser.add_argument("--maximum-total-seconds", type=float, default=30 * 60)
    parser.add_argument("--maximum-checkpoint-seconds", type=float, default=10 * 60)
    parser.add_argument(
        "--final-checkpoint",
        type=Path,
        help="Optional final checkpoint to compare additively after the rehearsal",
    )
    args = parser.parse_args(argv)
    try:
        report = run_live_readiness_rehearsal(
            manifest_path=args.manifest,
            output_root=args.output_root,
            policy_path=args.policy,
            checkpoint=args.checkpoint,
            maximum_lag_minutes=args.maximum_lag_minutes,
            maximum_total_seconds=args.maximum_total_seconds,
            maximum_checkpoint_seconds=args.maximum_checkpoint_seconds,
        )
        result: dict[str, object] = {
            "checkpoint_id": report["checkpoint_id"],
            "operational_status": report["operational_status"],
            "approval_status": report["approval_status"],
            "report_sha256": report["content_sha256"],
            "account_writes": report["account_writes"],
        }
        if args.final_checkpoint is not None:
            comparison = compare_final_checkpoint(
                rehearsal_root=args.output_root,
                rehearsal_checkpoint_id=str(report["checkpoint_id"]),
                final_checkpoint_path=args.final_checkpoint,
            )
            result["final_comparison_sha256"] = comparison["content_sha256"]
    except (LiveReadinessRehearsalError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
