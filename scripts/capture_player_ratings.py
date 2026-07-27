#!/usr/bin/env python3
"""Build one immutable player-rating snapshot from a local input envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.ingestion.player_ratings import (
    normalise_player_rating_snapshot,
    write_immutable_json,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    envelope = json.loads(args.input.read_text(encoding="utf-8"))
    methodology = envelope["methodology"]
    snapshot = normalise_player_rating_snapshot(
        envelope["rows"],
        source_id=envelope["source_id"],
        source_sha256=envelope["source_sha256"],
        origin=envelope["origin"],
        methodology_id=methodology["methodology_id"],
        methodology_version=methodology["version"],
        observed_at=envelope["observed_at"],
        available_at=envelope["available_at"],
        decision_cutoff=envelope["decision_cutoff"],
        identity_map=envelope["identity_map"],
        published_at=envelope.get("published_at"),
        effective_at=envelope.get("effective_at"),
        finalised_at=envelope.get("finalised_at"),
        max_age_hours=int(envelope.get("max_age_hours", 720)),
    )
    write_status = write_immutable_json(args.out, snapshot)
    print(
        json.dumps(
            {
                "status": write_status,
                "artifact": str(args.out),
                "content_sha256": snapshot["content_sha256"],
                "admitted_count": snapshot["admitted_count"],
                "quarantined_count": snapshot["quarantined_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
