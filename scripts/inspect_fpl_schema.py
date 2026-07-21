#!/usr/bin/env python3
"""Inspect live FPL bootstrap-static keys without retaining player payloads in Git.

Writes a small summary under docs/data-sources/ (safe metadata only).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.ingestion.registry import assert_collectable

OUT = REPO / "docs" / "data-sources" / "fpl-endpoint-schema-notes.md"


def main() -> int:
    assert_collectable("fpl-official-endpoints")
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with httpx.Client(headers={"User-Agent": "fpl-agentic-decision-lab/0.1 (private research)"}) as client:
        resp = client.get(url, timeout=30.0)
    observed = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# FPL endpoint schema notes",
        "",
        f"Observed at: `{observed}`",
        f"URL: `{url}`",
        f"HTTP status: `{resp.status_code}`",
        "",
    ]
    if resp.status_code != 200:
        lines.append("Endpoints unavailable or erroring; retry after launch/reset.")
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(resp.status_code)
        return 0

    data = resp.json()
    lines.append("## Top-level keys")
    for key in sorted(data.keys()):
        val = data[key]
        if isinstance(val, list):
            lines.append(f"- `{key}`: list[{len(val)}]")
        elif isinstance(val, dict):
            lines.append(f"- `{key}`: object keys={sorted(val.keys())[:20]}")
        else:
            lines.append(f"- `{key}`: {type(val).__name__}")

    elements = data.get("elements") or []
    if elements:
        sample = elements[0]
        interesting = [
            k
            for k in sample.keys()
            if any(
                s in k
                for s in (
                    "chance",
                    "ep_",
                    "news",
                    "status",
                    "defensive",
                    "clearance",
                    "tackle",
                    "recover",
                    "selected",
                    "transfers_",
                    "cost_",
                )
            )
        ]
        lines.append("")
        lines.append("## Decision-relevant element fields present on sample player")
        for k in sorted(interesting):
            lines.append(f"- `{k}`")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
