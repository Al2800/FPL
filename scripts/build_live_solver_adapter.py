#!/usr/bin/env python3
"""Build SolverInput and a Gameweek Decision Record from manual manager state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.optimisation.io import save_json  # noqa: E402
from src.orchestration.live_solver_adapter import (  # noqa: E402
    LiveSolverAdapterError,
    adapt_solve_and_record,
)
from src.orchestration.manager_state import ManagerStateError, normalise_manager_state  # noqa: E402
from src.scoring.rules_loader import (  # noqa: E402
    DEFAULT_RULES_PATH,
    load_rules,
    ruleset_sha256,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _is_normalised_manager_state(value: Mapping[str, Any]) -> bool:
    squad = value.get("squad")
    if not isinstance(squad, list) or not squad:
        return False
    first = squad[0]
    return isinstance(first, dict) and "current_price" in first and "manager_state_id" in value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manager-state",
        type=Path,
        required=True,
        help="Manual entry JSON or already-normalised manager-state.json",
    )
    parser.add_argument(
        "--forecast",
        type=Path,
        required=True,
        help="Live forecast artefact with a players market",
    )
    parser.add_argument(
        "--bootstrap",
        type=Path,
        default=None,
        help="Official bootstrap JSON required when normalising a manual entry",
    )
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES_PATH)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--active-chip", default=None)
    parser.add_argument("--max-transfers", type=int, default=3)
    parser.add_argument(
        "--validate-record",
        action="store_true",
        help="Run full Gameweek Decision Record schema validation",
    )
    args = parser.parse_args(argv)

    try:
        raw_state = _load_json(args.manager_state)
        forecast = _load_json(args.forecast)
        if _is_normalised_manager_state(raw_state):
            manager_state = raw_state
        else:
            if args.bootstrap is None:
                raise LiveSolverAdapterError(
                    "Manual manager-state entry requires --bootstrap for normalisation"
                )
            bootstrap = _load_json(args.bootstrap)
            manager_state = normalise_manager_state(
                raw_state,
                bootstrap=bootstrap,
                rules=load_rules(args.rules),
                ruleset_sha256=ruleset_sha256(args.rules),
            )
        bundle = adapt_solve_and_record(
            manager_state=manager_state,
            forecast=forecast,
            rules_path=args.rules,
            active_chip=args.active_chip,
            max_transfers=args.max_transfers,
            validate_record=args.validate_record,
        )
    except (LiveSolverAdapterError, ManagerStateError, ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    save_json(args.out_dir / "solver-input.json", bundle["solver_input"])
    save_json(args.out_dir / "solver-output.json", bundle["solver_output"])
    save_json(args.out_dir / "decision-record.json", bundle["decision_record"])
    selected = bundle["solver_output"].get("selected") or {}
    print(
        json.dumps(
            {
                "out_dir": str(args.out_dir),
                "strategy": selected.get("strategy"),
                "objective": selected.get("objective"),
                "transfers": selected.get("transfers") or [],
                "decision_record_id": bundle["decision_record"].get("record_id"),
                "validated_plan_sha256": bundle["decision_record"]["validated_plan"][
                    "content_sha256"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
