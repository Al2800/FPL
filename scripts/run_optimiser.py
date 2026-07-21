#!/usr/bin/env python3
"""Run the WP-07 optimiser on a solver-input JSON and write the output artefact."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.optimisation.io import load_solver_input, save_json
from src.optimisation.solver import solve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="Solver input JSON path")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: alongside input with .output.json)",
    )
    args = parser.parse_args()
    inp = load_solver_input(args.input_json)
    out = solve(inp)
    dest = args.out or args.input_json.with_suffix(".output.json")
    save_json(dest, out)
    selected = out.get("selected") or {}
    print(
        f"selected={selected.get('strategy')} "
        f"objective={selected.get('objective')} "
        f"transfers={len(selected.get('transfers') or [])} "
        f"hit={selected.get('hit_cost')} "
        f"candidates={out.get('n_candidates')}"
    )
    print(f"Wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
