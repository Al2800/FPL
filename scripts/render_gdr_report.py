#!/usr/bin/env python3
"""Render a live Gameweek Decision Record to static HTML (ticket 14)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.reporting.gdr_html import (  # noqa: E402
    GdrHtmlError,
    write_gdr_html,
    write_season_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record",
        type=Path,
        help="Path to decision-record.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output HTML path (default: beside the record)",
    )
    parser.add_argument(
        "--season-index",
        action="store_true",
        help="Render reports/gameweeks/index.html from discovered GDRs",
    )
    parser.add_argument(
        "--gameweeks-root",
        type=Path,
        default=REPO / "reports" / "gameweeks",
    )
    args = parser.parse_args(argv)

    try:
        if args.season_index:
            out = args.out or (args.gameweeks_root / "index.html")
            path = write_season_index(args.gameweeks_root, out)
            print(json.dumps({"index": str(path)}, indent=2))
            return 0
        if args.record is None:
            raise GdrHtmlError("Provide --record or --season-index")
        record = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise GdrHtmlError("decision record must be a JSON object")
        out = args.out or (args.record.parent / "decision-record.html")
        path = write_gdr_html(record, out)
        print(json.dumps({"html": str(path), "record_id": record.get("record_id")}, indent=2))
        return 0
    except (GdrHtmlError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
