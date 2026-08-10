#!/usr/bin/env python3
"""Build a 2026/27 availability ledger from high-impact official citation leads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evidence.availability_ledger import (  # noqa: E402
    append_availability_claim,
    new_availability_ledger,
)

# Official / near-official leads from strategy dry-runs (metadata only).
# Status=doubtful: late return / missed tour — not a hard unavailable call.
CLAIMS = [
    {
        "claim_id": "2026-27-preseason-rogers-missed-chelsea-tour",
        "player_uid": "player:2026-27:40",
        "web_name": "Rogers",
        "status": "doubtful",
        "confidence": 0.72,
        "published_at": "2026-07-20T12:00:00Z",
        "observed_at": "2026-08-01T09:01:02Z",
        "available_at": "2026-08-01T09:01:02Z",
        "expires_at": "2026-08-16T17:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
            "urls": [
                "https://www.chelseafc.com/en/news/article/xabi-alonso-on-his-plan-for-great-signing-morgan-rogers-and-cole-palmer"
            ],
            "note": "Not on Chelsea pre-season tour after England WC; minutes risk for GW1",
        },
    },
    {
        "claim_id": "2026-27-preseason-guehi-late-city-return",
        "player_uid": "player:2026-27:388",
        "web_name": "Guéhi",
        "status": "doubtful",
        "confidence": 0.7,
        "published_at": "2026-07-15T12:00:00Z",
        "observed_at": "2026-08-01T09:01:02Z",
        "available_at": "2026-08-01T09:05:00Z",
        "expires_at": "2026-08-16T17:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
            "urls": [
                "https://www.mancity.com/news/mens/enzo-maresca-man-city-unveiling-press-conference-written-two-63920485"
            ],
            "note": "Maresca: last WC group joins days before Community Shield",
        },
    },
    {
        "claim_id": "2026-27-preseason-senesi-late-spurs-return",
        "player_uid": "player:2026-27:498",
        "web_name": "Senesi",
        "status": "doubtful",
        "confidence": 0.68,
        "published_at": "2026-07-30T12:00:00Z",
        "observed_at": "2026-08-01T09:01:02Z",
        "available_at": "2026-08-01T09:10:00Z",
        "expires_at": "2026-08-16T17:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
            "urls": [
                "https://www.tottenhamhotspur.com/news/1080876/gallery-senesi-joined-by-bentancur-and-sarr-as-he-starts-at-hotspur-way"
            ],
            "note": "First Hotspur Way day 30 Jul after WC final",
        },
    },
    {
        "claim_id": "2026-27-preseason-anderson-missed-asia-tour",
        "player_uid": "player:2026-27:481",
        "web_name": "Anderson",
        "status": "doubtful",
        "confidence": 0.66,
        "published_at": "2026-07-20T12:00:00Z",
        "observed_at": "2026-08-01T09:01:02Z",
        "available_at": "2026-08-01T09:15:00Z",
        "expires_at": "2026-08-16T17:00:00Z",
        "provenance": {
            "source_ids": ["official-club-communications"],
            "transformation_version": "availability-ledger-v1",
            "urls": [
                "https://www.mancity.com/news/mens/enzo-maresca-man-city-unveiling-press-conference-written-two-63920485"
            ],
            "note": "England WC load; reported missing City Asia tour with late return group",
        },
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT
        / "data"
        / "live-shadow"
        / "availability"
        / "2026-27-preseason-citations-ledger.json",
    )
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=REPO_ROOT
        / "data"
        / "live-shadow"
        / "availability"
        / "2026-27-preseason-citations.sidecar.json",
    )
    args = parser.parse_args(argv)

    ledger = new_availability_ledger(
        season="2026-27", created_at="2026-08-01T09:00:00Z"
    )
    for claim in CLAIMS:
        payload = {k: v for k, v in claim.items() if k != "web_name"}
        ledger = append_availability_claim(ledger, payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sidecar = {
        "source_id": "official-club-communications",
        "observed_at": "2026-08-01T09:15:00Z",
        "available_at": "2026-08-01T09:01:02Z",
        "ledger_content_sha256": ledger["content_sha256"],
        "claim_count": len(ledger["claims"]),
        "note": (
            "High-impact preseason minutes-risk citations; doubtful≠unavailable. "
            "Haaland deliberately omitted (start likely; sharpness risk only)."
        ),
    }
    args.sidecar.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ledger_path": str(args.output),
                "sidecar_path": str(args.sidecar),
                "content_sha256": ledger["content_sha256"],
                "claims": len(ledger["claims"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
