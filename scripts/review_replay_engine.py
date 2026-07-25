"""Generate a read-only evaluation report for a frozen replay season."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.evaluation.replay_review import review_replay_season


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-root", type=Path, default=REPO / "reports/benchmarks/2025-26")
    parser.add_argument(
        "--outcomes-csv",
        type=Path,
        default=(
            REPO
            / "data/raw/vaastav/Fantasy-Premier-League/data/2025-26/gws/merged_gw.csv"
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = review_replay_season(args.reports_root, args.outcomes_csv)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
