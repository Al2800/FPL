#!/usr/bin/env python3
"""Write the Understat→FPL player join report for the current checkpoint universe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.forecasting.understat_player_context import build_understat_player_join
from src.forecasting.understat_team_context import discover_latest_understat_capture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bootstrap",
        type=Path,
        default=Path(
            "data/snapshots/2026-27/preseason/weekly-2026-08-02/raw/"
            "20260802T100000Z/bootstrap-static.json"
        ),
    )
    parser.add_argument(
        "--understat-root",
        type=Path,
        default=Path("data/live-shadow/understat"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "reports/forecasting/understat-player-join-2025-to-2026-27.json"
        ),
    )
    args = parser.parse_args()

    capture_path = discover_latest_understat_capture(args.understat_root)
    if capture_path is None:
        raise SystemExit(f"No Understat capture under {args.understat_root}")
    bootstrap = json.loads(args.bootstrap.read_text(encoding="utf-8"))
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    report = build_understat_player_join(
        bootstrap=bootstrap, understat_capture=capture
    )
    # Compact committed report: drop full unmatched/matched row dumps if huge.
    compact = {
        "schema_version": report["schema_version"],
        "source_id": report["source_id"],
        "capture_season": report["capture_season"],
        "capture_path": str(capture_path),
        "bootstrap_path": str(args.bootstrap),
        "bootstrap_player_count": report["bootstrap_player_count"],
        "understat_player_count": report["understat_player_count"],
        "counts": report["counts"],
        "quarantined": report["quarantined"],
        "unmatched_reason_counts": {},
        "content_sha256": report["content_sha256"],
        "full_report_note": (
            "rates_by_fpl_code omitted from the compact report; regenerate with "
            "build_understat_player_join for the full mapping."
        ),
    }
    reasons: dict[str, int] = {}
    for row in report["unmatched"]:
        reason = str(row.get("reason", "unknown"))
        reasons[reason] = reasons.get(reason, 0) + 1
    compact["unmatched_reason_counts"] = dict(sorted(reasons.items()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(compact["counts"], indent=2, sort_keys=True))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
