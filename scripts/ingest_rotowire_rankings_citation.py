#!/usr/bin/env python3
"""Seal a Rotowire short-horizon FPL rankings citation from a local JSON envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.ingestion.rotowire_rankings import (
    build_rotowire_short_horizon_rankings_pack,
    write_rotowire_short_horizon_rankings_pack,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    envelope = json.loads(args.input.read_text(encoding="utf-8"))
    pack = build_rotowire_short_horizon_rankings_pack(
        players=envelope["players"],
        observed_at=envelope["observed_at"],
        published_at=envelope.get("published_at"),
        available_at=envelope.get("available_at"),
        citation_url=envelope.get("citation_url"),
        citation_title=envelope["citation_title"],
        author=envelope.get("author", "Adam Zdroik"),
        publisher=envelope.get("publisher", "RotoWire"),
        season=envelope.get("season", "2026-27"),
        horizon_gameweeks=envelope.get("horizon_gameweeks"),
        team_fixture_ranks=envelope.get("team_fixture_ranks"),
        narrative=envelope.get("narrative"),
        notes=envelope.get("notes"),
        require_registry=bool(envelope.get("require_registry", True)),
    )
    write_status = write_rotowire_short_horizon_rankings_pack(pack, args.out)
    print(
        json.dumps(
            {
                "status": write_status,
                "artifact": str(args.out),
                "content_sha256": pack["content_sha256"],
                "player_count": pack["player_count"],
                "canonical_url_status": pack["citation"]["canonical_url_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
