#!/usr/bin/env python3
"""Capture one point-in-time ClubElo daily ranking (gitignored local retention)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ingestion.acquisition import content_hash  # noqa: E402
from src.ingestion.registry import assert_collectable  # noqa: E402

SOURCE_ID = "clubelo"
DEFAULT_OUT = REPO_ROOT / "data" / "live-shadow" / "clubelo"
USER_AGENT = "fpl-agentic-decision-lab/0.1 (private read-only research; ClubElo attribution)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        default=None,
        help="UTC calendar date YYYY-MM-DD for api.clubelo.com/<date> (default: today UTC)",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    source = assert_collectable(SOURCE_ID)
    as_of = args.as_of or datetime.now(timezone.utc).date().isoformat()
    try:
        date.fromisoformat(as_of)
    except ValueError:
        print(f"ERROR: invalid --as-of date: {as_of}", file=sys.stderr)
        return 1

    url = f"http://api.clubelo.com/{as_of}"
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0) as client:
        response = client.get(url)
    if response.status_code != 200:
        print(
            f"ERROR: ClubElo fetch failed status={response.status_code}",
            file=sys.stderr,
        )
        return 1

    body = response.content
    digest = content_hash(body)
    stamp = observed_at.replace(":", "").replace("-", "")
    out_dir = args.output_root / as_of / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    body_path = out_dir / "clubelo-ranking.csv"
    body_path.write_bytes(body)
    meta = {
        "source_id": SOURCE_ID,
        "attribution": source.get("attribution"),
        "as_of": as_of,
        "observed_at": observed_at,
        "available_at": f"{as_of}T00:00:00Z",
        "request_url": url,
        "http_status": response.status_code,
        "body_sha256": digest,
        "body_file": body_path.name,
        "row_count": body.decode("utf-8", errors="replace").count("\n"),
        "note": "Point-in-time capture only; do not backfill into older episodes.",
    }
    meta_path = out_dir / "clubelo-ranking.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"meta_path": str(meta_path), **meta}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
