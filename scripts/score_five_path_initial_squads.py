"""Validate five GW1 strategy-path squads against the 2026/27 ruleset.

Paths A–B are the frozen weekly-2026-08-11 optimiser arms (published
objectives). Paths C–E are declared alternatives. Host rescoring lives in
``scripts/host_rescore_five_path_squads.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.optimisation.five_path_squads import PATHS, validate_path_rules
from src.scoring.rules_loader import load_rules

REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "reports" / "strategy-research" / "2026-08-19-five-path-squads.json"


def main() -> int:
    rules = load_rules(REPO / "control" / "rules" / "2026-27.yaml")
    results = [validate_path_rules(path, rules=rules) for path in PATHS]
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    failed = [row for row in results if not (row["squad_ok"] and row["lineup_ok"])]
    for row in results:
        status = "OK" if row["squad_ok"] and row["lineup_ok"] else "FAIL"
        print(
            f"{status} {row['path_id']} £{row['spent']:.1f} bank {row['bank']:.1f} "
            f"obj={row['published_objective']}"
        )
        if row["squad_errors"] or row["lineup_errors"]:
            print(" ", row["squad_errors"], row["lineup_errors"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
