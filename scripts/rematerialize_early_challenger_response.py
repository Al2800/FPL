#!/usr/bin/env python3
"""Rebuild an early challenger envelope with host-owned response hashing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.hosted_response import build_hosted_response
from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "reports/benchmarks/2025-26-early-evidence/hosted"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gameweek", type=int, choices=range(2, 12), required=True)
    args = parser.parse_args()
    root = OUTPUT / f"gw-{args.gameweek:02d}"
    request = _read(root / "challenger-request.json")
    original = _read(root / "challenger-hosted-response.json")
    response = build_hosted_response(
        request=request,
        structured_output=original["structured_output"],
        completed_at=str(original["completed_at"]),
        usage={
            "wall_clock_ms": 0,
            "tool_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
        model_version="gpt-5.6-sol",
        cli_version="collaboration-subagent",
    )
    _write_once(root / "challenger-hosted-response-v2.json", response)
    print(
        json.dumps(
            {
                "gameweek": args.gameweek,
                "request_sha256": response["request_sha256"],
                "response_sha256": response["response_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
