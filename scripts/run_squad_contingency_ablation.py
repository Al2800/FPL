#!/usr/bin/env python3
"""Run the squad-contingency component ablation study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.evaluation.squad_contingency_ablation import (
    run_full_ablation,
    verify_w10_reference,
)


OUTPUT = REPO / "reports/evaluation/squad-contingency-ablation-v1.json"
W10_OUTPUT = REPO / "reports/evaluation/squad-contingency-v1.json"


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
        raise argparse.ArgumentTypeError(
            "gameweeks must be all or comma-separated 1..38"
        )
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
        "--artifact-root",
        type=Path,
        default=REPO,
        help="root containing approved ignored historical artifacts",
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
    calibration = _read(REPO / "control/models/appearance-distribution-v1.json")
    w10_report = _read(W10_OUTPUT)
    verify_w10_reference(w10_report)
    report = run_full_ablation(
        repo_root=REPO,
        calibration=calibration,
        w10_report=w10_report,
        artifact_root=args.artifact_root,
        locked_gameweeks=args.locked_gameweeks,
        descriptive_gameweeks=args.descriptive_gameweeks,
    )
    _write_repeatable(args.output, report, replace_draft=args.replace_draft)
    print(
        json.dumps(
            {
                "output": args.output.as_posix(),
                "content_sha256": report["content_sha256"],
                "locked_attribution": report["locked_2024_25"]["attribution"],
                "descriptive_attribution": report["descriptive_2025_26"][
                    "attribution"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
