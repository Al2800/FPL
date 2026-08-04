#!/usr/bin/env python3
"""Optional deadline reminder using the ticket-04 pluggable notifier."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.deadline_capture_scheduler import utc_timestamp  # noqa: E402
from src.orchestration.freshness_monitor import (  # noqa: E402
    NullNotifier,
    notifier_from_environment,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deadline", required=True, help="ISO-8601 deadline")
    parser.add_argument("--season", required=True)
    parser.add_argument("--gameweek", type=int, required=True)
    parser.add_argument("--now", help="ISO-8601 evaluation time (tests)")
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Emit via FPL_FRESHNESS_WEBHOOK_URL when set",
    )
    parser.add_argument("--hours-before", type=float, default=2.0)
    args = parser.parse_args(argv)

    now = utc_timestamp(args.now) if args.now else datetime.now(timezone.utc)
    deadline = utc_timestamp(args.deadline)
    hours_left = (deadline - now).total_seconds() / 3600.0
    due = 0 <= hours_left <= float(args.hours_before)
    payload = {
        "kind": "deadline_reminder",
        "season": args.season,
        "gameweek": int(args.gameweek),
        "deadline": deadline.isoformat().replace("+00:00", "Z"),
        "hours_remaining": round(hours_left, 3),
        "due": due,
        "account_writes": False,
        "browser_actions": False,
        "message": (
            f"GW{args.gameweek} deadline reminder: {hours_left:.1f}h remaining"
            if due
            else f"GW{args.gameweek} reminder not in window ({hours_left:.1f}h)"
        ),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if due and args.notify:
        notifier = notifier_from_environment()
        if isinstance(notifier, NullNotifier):
            return 0
        notifier.notify(payload)
    return 0 if not due else 1


if __name__ == "__main__":
    raise SystemExit(main())
