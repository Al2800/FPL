#!/usr/bin/env python3
"""Replay the structured pilot Gameweek set (cheap volume check)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.orchestration.replay_harness import replay_gameweek

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SET = REPO / "evals" / "replay-set" / "structured-pilot-gameweeks.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", type=Path, default=DEFAULT_SET)
    parser.add_argument("--out", type=Path, default=REPO / "reports" / "replay-pilot")
    args = parser.parse_args()

    cfg = yaml.safe_load(args.set.read_text(encoding="utf-8"))
    solver_input = REPO / cfg["harness"]["solver_input"]
    rows = []
    for block in cfg["pilots"]:
        season = block["season"]
        for gw in block["gameweeks"]:
            out_dir = args.out / f"{season}-gw{gw}"
            # Label the run via out_dir; solver fixture is synthetic stand-in
            rec = replay_gameweek(solver_input, out_dir=out_dir)
            rows.append(
                {
                    "season": season,
                    "gameweek": gw,
                    "elapsed_ms": rec["replay_elapsed_ms"],
                    "repro_hash": rec["repro_hash"],
                    "expected_advantage": rec["baseline_comparison"]["expected_advantage"],
                }
            )
    summary = {
        "n": len(rows),
        "mean_elapsed_ms": round(sum(r["elapsed_ms"] for r in rows) / len(rows), 2),
        "unique_hashes": len({r["repro_hash"] for r in rows}),
        "rows": rows,
        "note": cfg["harness"]["strategy"],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n", "mean_elapsed_ms", "unique_hashes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
