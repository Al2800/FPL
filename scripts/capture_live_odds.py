#!/usr/bin/env python3
"""Capture one governed The Odds API checkpoint without exposing credentials."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import httpx

from src.ingestion.live_odds_provider import (
    LiveOddsProviderError,
    capture_the_odds_api,
    write_immutable_json,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    REPO / "config" / "data_sources" / "2026-27-live-odds-provider.json"
)
DEFAULT_RAW_OUT = REPO / "data" / "live-shadow" / "odds" / "raw"
USER_AGENT = "fpl-agentic-decision-lab/0.1 (private read-only research)"


def _read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LiveOddsProviderError(f"Expected a JSON object: {path}")
    return value


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture one immutable, cutoff-safe EPL odds checkpoint"
    )
    parser.add_argument("--season", default="2026-27")
    parser.add_argument(
        "--slot",
        required=True,
        choices=("T-24h", "T-8h", "T-2h", "final"),
    )
    parser.add_argument("--observed-at", default=_now())
    parser.add_argument("--decision-cutoff", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--raw-out", type=Path, default=DEFAULT_RAW_OUT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        config = _read_object(args.config)
        with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
            capture = capture_the_odds_api(
                client,
                season=args.season,
                slot=args.slot,
                observed_at=args.observed_at,
                decision_cutoff=args.decision_cutoff,
                raw_out_dir=args.raw_out,
                config=config,
                base_url=args.base_url,
            )
        write_result = write_immutable_json(args.output, capture)
    except (LiveOddsProviderError, FileExistsError, OSError) as exc:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": capture["status"],
                "slot": args.slot,
                "output": str(args.output),
                "write": write_result,
                "quota": capture["quota"],
                "retry_after_seconds": capture["retry_after_seconds"],
                "degraded_reasons": capture["degraded_reasons"],
                "content_sha256": capture["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if capture["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
