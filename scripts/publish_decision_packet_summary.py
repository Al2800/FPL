#!/usr/bin/env python3
"""Publish a committed decision-packet summary from gitignored checkpoint artefacts.

The full initial-squad checkpoint artefacts under ``reports/live/`` are local
only (raw scale, ADR-0002). The daily strategy agent runs from the committed
tree, so it can never bind a packet it cannot see. This publisher copies the
compact, derived, hash-bound decision surface — recommendation metadata,
selection, gap panel, availability blend and checkpoint binding — to a
committed path under ``reports/strategy-research/packets/``.

No raw capture bodies, EP vectors or fixture audits are included.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

LIVE_ROOT = REPO_ROOT / "reports" / "live"
PACKETS_ROOT = REPO_ROOT / "reports" / "strategy-research" / "packets"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default="2026-27")
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--output-root", type=Path, default=PACKETS_ROOT)
    args = parser.parse_args(argv)

    source_dir = LIVE_ROOT / args.season / "initial-squad" / args.checkpoint_id
    if not source_dir.is_dir():
        print(f"ERROR: no checkpoint artefacts at {source_dir}", file=sys.stderr)
        return 1

    recommendation = _read_json(source_dir / "recommendation.json")
    gap_panel = _read_json(source_dir / "gap-panel.json")
    availability_blend = _read_json(source_dir / "availability-blend.json")
    checkpoint = _read_json(source_dir / "checkpoint.json")

    summary = {
        "schema_version": "1.0",
        "kind": "decision_packet_summary",
        "season": args.season,
        "checkpoint_id": args.checkpoint_id,
        "note": (
            "Committed derived decision surface for the daily strategy agent. "
            "Full artefacts (input packet, fixture audit) remain local-only "
            "and are bound by the hashes below."
        ),
        "recommendation": recommendation,
        "gap_panel": gap_panel,
        "availability_blend": availability_blend,
        "checkpoint": checkpoint,
    }
    body = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()

    args.output_root.mkdir(parents=True, exist_ok=True)
    output = args.output_root / f"{args.checkpoint_id}.json"
    output.write_text(body, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output.relative_to(REPO_ROOT)).replace("\\", "/"),
                "summary_sha256": digest,
                "bound_packet_sha256": recommendation.get("input_packet_sha256"),
                "recommendation_sha256": recommendation.get("content_sha256"),
                "bytes": len(body),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
