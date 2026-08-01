#!/usr/bin/env python3
"""Capture bounded EPL Understat league tables via understatAPI (gitignored)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ingestion.acquisition import content_hash  # noqa: E402
from src.ingestion.registry import assert_collectable  # noqa: E402

SOURCE_ID = "understat"
DEFAULT_OUT = REPO_ROOT / "data" / "live-shadow" / "understat"
CLIENT = "https://github.com/collinb9/understatAPI"


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--season",
        required=True,
        help="Understat season start year, e.g. 2025 for 2025/26",
    )
    parser.add_argument("--league", default="EPL")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--include-matches",
        action="store_true",
        help="Also pull league match list (larger payload)",
    )
    args = parser.parse_args(argv)

    source = assert_collectable(SOURCE_ID)
    try:
        from understatapi import UnderstatClient
    except ImportError:
        print(
            "ERROR: understatapi not installed. "
            "Run: pip install '.[understat]' or pip install understatapi",
            file=sys.stderr,
        )
        return 1

    observed_at = _now()
    with UnderstatClient() as understat:
        league = understat.league(league=args.league)
        players = league.get_player_data(season=args.season)
        teams = league.get_team_data(season=args.season)
        matches = (
            league.get_match_data(season=args.season) if args.include_matches else None
        )

    if not players and not teams:
        print(
            json.dumps(
                {
                    "status": "empty",
                    "season": args.season,
                    "league": args.league,
                    "note": "No rows returned (common before the season starts).",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    stamp = observed_at.replace(":", "").replace("-", "")
    out_dir = args.output_root / args.league / str(args.season) / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "understat-epl-capture-v1",
        "source_id": SOURCE_ID,
        "client": CLIENT,
        "attribution": source.get("attribution"),
        "league": args.league,
        "season": str(args.season),
        "observed_at": observed_at,
        "available_at": observed_at,
        "players": players or [],
        "teams": teams or [],
        "matches": matches,
        "counts": {
            "players": len(players or []),
            "teams": len(teams or []),
            "matches": len(matches or []) if matches is not None else None,
        },
        "note": (
            "Post-match xG/xA rates via understatAPI. Not live minutes/news. "
            "Private local retention only; do not redistribute."
        ),
    }
    body = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    digest = content_hash(body)
    body_path = out_dir / "understat-league.json"
    body_path.write_bytes(body)
    meta = {
        "source_id": SOURCE_ID,
        "client": CLIENT,
        "league": args.league,
        "season": str(args.season),
        "observed_at": observed_at,
        "available_at": observed_at,
        "body_file": body_path.name,
        "body_sha256": digest,
        "counts": payload["counts"],
        "status": "complete",
    }
    meta_path = out_dir / "understat-league.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"meta_path": str(meta_path), **meta}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
