#!/usr/bin/env python3
"""Run the W10 paired squad-contingency evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.evaluation.squad_contingency import (
    build_contingency_report,
    evaluate_locked_lineups,
    evaluate_sealed_forks,
)


OUTPUT = REPO / "reports/evaluation/squad-contingency-v1.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_repeatable(
    path: Path, value: dict, *, replace_draft: bool = False
) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if (
        path.exists()
        and path.read_text(encoding="utf-8") != rendered
        and not replace_draft
    ):
        raise RuntimeError(f"refusing to overwrite differing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _gameweeks(value: str) -> tuple[int, ...]:
    if value == "all":
        return tuple(range(1, 39))
    result = tuple(int(item) for item in value.split(",") if item)
    if not result or any(item < 1 or item > 38 for item in result):
        raise argparse.ArgumentTypeError("gameweeks must be all or comma-separated 1..38")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--locked-gameweeks",
        type=_gameweeks,
        default=tuple(range(1, 39)),
    )
    parser.add_argument(
        "--descriptive-gameweeks",
        type=_gameweeks,
        default=tuple(range(2, 39)),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
    )
    parser.add_argument(
        "--replace-draft",
        action="store_true",
        help="replace the current uncommitted evaluation draft",
    )
    args = parser.parse_args()
    calibration = _read(
        REPO / "control/models/appearance-distribution-v1.json"
    )
    locked = evaluate_locked_lineups(
        vaastav_root=(
            REPO / "data/raw/vaastav/Fantasy-Premier-League/data"
        ),
        calibration=calibration,
        rules_path=REPO / "control/rules/2025-26.yaml",
        gameweeks=args.locked_gameweeks,
    )
    descriptive = evaluate_sealed_forks(
        reports_root=REPO / "reports/benchmarks/2025-26",
        episodes_root=REPO / "data/benchmark-v0/episodes/v1/2025-26",
        calibration=calibration,
        rules_path=REPO / "control/rules/2025-26.yaml",
        gameweeks=args.descriptive_gameweeks,
    )
    report = build_contingency_report(
        calibration=calibration,
        locked=locked,
        descriptive=descriptive,
    )
    _write_repeatable(
        args.output, report, replace_draft=args.replace_draft
    )
    print(
        json.dumps(
            {
                "output": args.output.as_posix(),
                "decision": report["decision"],
                "evidence_gate_passed": report["evidence_gate_passed"],
                "promotion_eligible": report["promotion_eligible"],
                "locked_summary": locked["summary"],
                "descriptive_summary": descriptive["summary"],
                "content_sha256": report["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
