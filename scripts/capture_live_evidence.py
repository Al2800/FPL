#!/usr/bin/env python3
"""Capture governed official-FPL evidence into an immutable local ledger."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx

from src.evidence.live_evidence_ledger import write_live_evidence_artifact
from src.ingestion.live_evidence_collector import capture_official_fpl_evidence


REPO = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture automated, governed official FPL evidence"
    )
    parser.add_argument("--season", default="2026-27")
    parser.add_argument(
        "--observed-at",
        default=datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO / "config" / "data_sources" / "2026-27-evidence.json",
    )
    parser.add_argument(
        "--raw-out",
        type=Path,
        default=REPO / "data" / "live-shadow" / "evidence" / "raw",
    )
    parser.add_argument("--previous-ledger", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--base-url", default="https://fantasy.premierleague.com"
    )
    args = parser.parse_args()

    config = _read(args.config)
    previous = (
        _read(args.previous_ledger) if args.previous_ledger is not None else None
    )
    with httpx.Client(
        headers={
            "User-Agent": "fpl-agentic-decision-lab/0.1 (private research)"
        }
    ) as client:
        capture = capture_official_fpl_evidence(
            client,
            season=args.season,
            observed_at=args.observed_at,
            raw_out_dir=args.raw_out,
            config=config,
            base_url=args.base_url,
            previous_ledger=previous,
        )
    write_live_evidence_artifact(args.output, capture)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": capture["status"],
                "claim_count_added": capture["claim_count_added"],
                "gap_count": len(capture["gaps"]),
                "content_sha256": capture["content_sha256"],
                "account_writes": capture["account_writes"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
