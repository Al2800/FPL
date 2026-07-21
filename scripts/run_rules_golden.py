#!/usr/bin/env python3
"""Run the WP-01/WP-06 rules golden-case catalogue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.scoring.golden_runner import DEFAULT_GOLDEN, run_all


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = run_all(args.golden)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"passed={report['passed']}/{report['n']} ruleset={report['ruleset_id']}")
    for f in report["failed"]:
        print(f"FAIL {f['case_id']}: {f['detail']}")
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
