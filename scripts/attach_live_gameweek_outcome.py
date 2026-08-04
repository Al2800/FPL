#!/usr/bin/env python3
"""Attach post-lock outcomes and retrospectives to a live Gameweek Decision Record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.live_outcome_attachment import (  # noqa: E402
    LiveOutcomeAttachmentError,
    attach_live_outcome_files,
)
from src.scoring.rules_loader import DEFAULT_RULES_PATH  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-record", type=Path, required=True)
    parser.add_argument("--event-live", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES_PATH)
    parser.add_argument("--revealed-at", required=True, help="ISO-8601 reveal timestamp")
    parser.add_argument(
        "--status",
        choices=("provisional", "final"),
        default="final",
        help="Outcome revision status; provisional cannot overwrite final",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--do-nothing-plan", type=Path, default=None)
    parser.add_argument("--alternate-captain-plan", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        result = attach_live_outcome_files(
            decision_record_path=args.decision_record,
            event_live_path=args.event_live,
            bootstrap_path=args.bootstrap,
            rules_path=args.rules,
            revealed_at=args.revealed_at,
            status=args.status,
            out_path=args.out,
            do_nothing_plan_path=args.do_nothing_plan,
            alternate_captain_plan_path=args.alternate_captain_plan,
        )
    except (LiveOutcomeAttachmentError, OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "decision_record_path": result["decision_record_path"],
                "realised_outcome_path": result["realised_outcome_path"],
                "points": result["points"],
                "status": result["status"],
                "realised_outcome_sha256": result["realised_outcome_sha256"],
                "transfer_gain_vs_do_nothing": result["metrics"].get(
                    "transfer_gain_vs_do_nothing"
                ),
                "captaincy_gain_vs_alternate": result["metrics"].get(
                    "captaincy_gain_vs_alternate"
                ),
                "bench_points": result["metrics"].get("bench_points"),
                "hit_recovery": result["metrics"].get("hit_recovery"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
