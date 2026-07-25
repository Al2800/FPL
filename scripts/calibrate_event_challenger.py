"""Materialise the sealed event challenger and its out-of-sample report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.calibrate_event_challenger import run_event_challenger


def _write_once(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"Refusing to overwrite differing artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=REPO / "control/models/live-faithful-v2.events.json")
    parser.add_argument("--report", type=Path, default=REPO / "reports/forecasting/live-faithful-v2-events/evaluation.json")
    args = parser.parse_args()
    config, report = run_event_challenger(
        base_config_path=REPO / "control/models/live-faithful-v1.feature-complete.json",
        locked_calibration_path=REPO / "reports/forecasting/live-faithful-v1-feature-complete-calibration.json",
        reports_root=REPO / "reports/benchmarks/2025-26",
        outcomes_csv=REPO / "data/raw/vaastav/Fantasy-Premier-League/data/2025-26/gws/merged_gw.csv",
    )
    _write_once(args.config, config)
    _write_once(args.report, report)
    print(json.dumps({"decision": report["decision"], "weight": report["event_model_weight"], "deltas": report["deltas_challenger_minus_control"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
