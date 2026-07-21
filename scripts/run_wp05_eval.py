#!/usr/bin/env python3
"""Run WP-05 baseline evaluation and write a JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.forecasting.evaluate import evaluate_seasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=["2022-23", "2023-24", "2024-25"],
        help="Seasons to evaluate",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/data-sources/wp05/baseline-eval.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    report = evaluate_seasons(list(args.seasons))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report.get("summary", {}), indent=2))
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
