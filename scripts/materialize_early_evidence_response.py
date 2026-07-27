#!/usr/bin/env python3
"""Wrap a semantic early-season response in trusted host metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.hosted_response import build_hosted_response
from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "evals/evidence-forks/2025-26"
OUTPUT = REPO / "reports/benchmarks/2025-26-early-evidence/hosted"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gameweek", type=int, choices=range(2, 12), required=True)
    args = parser.parse_args()
    root = OUTPUT / f"gw-{args.gameweek:02d}"
    bundle = _read(
        EVIDENCE
        / f"gw-{args.gameweek:02d}"
        / "agent-host-bundle-v2.json"
    )
    semantic = _read(root / "semantic-evidence-output.json")
    response = build_hosted_response(
        request=bundle["evidence_request"],
        structured_output=semantic,
        completed_at="2026-07-27T11:45:00Z",
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
    _write_once(root / "evidence-hosted-response.json", response)
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
