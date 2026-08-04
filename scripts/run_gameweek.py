#!/usr/bin/env python3
"""Run the deterministic live Gameweek advisory chain end-to-end."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.manager_state import ManagerStateError, normalise_manager_state  # noqa: E402
from src.orchestration.run_gameweek import (  # noqa: E402
    RunGameweekError,
    load_snapshot_candidates,
    run_gameweek,
)
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


def _is_normalised(value: dict[str, Any]) -> bool:
    squad = value.get("squad")
    return (
        isinstance(squad, list)
        and bool(squad)
        and isinstance(squad[0], dict)
        and "current_price" in squad[0]
        and "manager_state_id" in value
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gw", type=int, required=True, help="Gameweek number")
    parser.add_argument("--manager-state", type=Path, required=True)
    parser.add_argument(
        "--forecast",
        type=Path,
        default=None,
        help="Pre-built forecast market JSON (skips live-faithful composition)",
    )
    parser.add_argument("--feature-state", type=Path, default=None)
    parser.add_argument("--identity-map", type=Path, default=None)
    parser.add_argument("--player-prior", type=Path, default=None)
    parser.add_argument("--team-prior", type=Path, default=None)
    parser.add_argument("--model-config", type=Path, default=None)
    parser.add_argument(
        "--snapshot",
        type=Path,
        action="append",
        default=[],
        help="Capture-summary JSON candidate (repeatable); latest pre-deadline wins",
    )
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--freshness-report",
        type=Path,
        default=None,
        help="Freshness monitor JSON from check_capture_freshness.py",
    )
    parser.add_argument(
        "--monte-carlo",
        type=Path,
        default=None,
        help="Monte Carlo input JSON (fixtures, players, n_paths, seed)",
    )
    parser.add_argument("--bootstrap", type=Path, default=None)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES_PATH)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--active-chip", default=None)
    parser.add_argument("--max-transfers", type=int, default=3)
    parser.add_argument("--validate-record", action="store_true", default=True)
    parser.add_argument("--no-validate-record", action="store_false", dest="validate_record")
    args = parser.parse_args(argv)

    try:
        raw_state = _load_json(args.manager_state)
        if _is_normalised(raw_state):
            manager_state = raw_state
        else:
            if args.bootstrap is None:
                raise RunGameweekError(
                    "Manual manager-state entry requires --bootstrap for normalisation"
                )
            manager_state = normalise_manager_state(
                raw_state,
                bootstrap=_load_json(args.bootstrap),
                rules=load_rules(args.rules),
                ruleset_sha256=ruleset_sha256(args.rules),
            )
        if int(manager_state["gameweek"]) != int(args.gw):
            raise RunGameweekError(
                f"--gw {args.gw} does not match manager_state gameweek "
                f"{manager_state['gameweek']}"
            )

        forecast = _load_json(args.forecast) if args.forecast else None
        live_inputs = None
        if forecast is None:
            required = {
                "feature_state": args.feature_state,
                "identity_map": args.identity_map,
                "player_prior": args.player_prior,
                "team_prior": args.team_prior,
                "model_config": args.model_config,
            }
            missing = [name for name, path in required.items() if path is None]
            if missing:
                raise RunGameweekError(
                    "Provide --forecast or all live-faithful inputs; missing "
                    + ", ".join(missing)
                )
            live_inputs = {name: _load_json(path) for name, path in required.items()}

        snapshots = load_snapshot_candidates(args.snapshot) if args.snapshot else None
        evidence = _load_json(args.evidence) if args.evidence else None
        freshness = _load_json(args.freshness_report) if args.freshness_report else None
        monte_carlo = _load_json(args.monte_carlo) if args.monte_carlo else None
        result = run_gameweek(
            manager_state=manager_state,
            forecast=forecast,
            live_faithful_inputs=live_inputs,
            snapshot_candidates=snapshots,
            evidence=evidence,
            freshness_report=freshness,
            monte_carlo=monte_carlo,
            rules_path=args.rules,
            out_dir=args.out_dir,
            active_chip=args.active_chip,
            max_transfers=args.max_transfers,
            validate_record=args.validate_record,
        )
    except (RunGameweekError, ManagerStateError, ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "out_dir": result["out_dir"],
                "decision_record_path": result["decision_record_path"],
                "decision_record_sha256": result["decision_record_sha256"],
                "solver_output_fingerprint": result["solver_output_fingerprint"],
                "degraded": result["degraded"],
                "degraded_reasons": result["degraded_reasons"],
                "strategy": (result["solver_output"].get("selected") or {}).get("strategy"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
