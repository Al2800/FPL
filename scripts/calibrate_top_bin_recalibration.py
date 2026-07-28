#!/usr/bin/env python3
"""Fit and evaluate the W9 per-position recalibration challenger."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.calibrate_live_faithful import (
    ForecastParameters,
    build_calibration_cases,
    load_season_rows,
    predictions,
)
from src.forecasting.recalibration import build_recalibration_report


VAASTAV = REPO / "data/raw/vaastav/Fantasy-Premier-League/data"
CONFIG = REPO / "control/models/live-faithful-v2.recalibrated.json"
REPORT = REPO / "reports/forecasting/live-faithful-v2-recalibrated.json"


PARAMETERS = ForecastParameters(
    prior_equivalent_minutes=1350.0,
    start_prior_equivalent_matches=2.0,
    cameo_minutes=10.0,
    team_fixture_scale=0.25,
    player_prior_reliability_minutes=900.0,
    event_model_weight=0.0,
    recent_minutes_weight=0.5,
)


def _season_cases(
    prior_season: str,
    target_season: str,
) -> tuple[pd.DataFrame, list[dict]]:
    prior, prior_lineage = load_season_rows(
        prior_season,
        vaastav_root=VAASTAV,
    )
    target, target_lineage = load_season_rows(
        target_season,
        vaastav_root=VAASTAV,
    )
    cases = build_calibration_cases(
        prior_rows=prior,
        target_rows=target,
        prior_season=prior_season,
        target_season=target_season,
    )
    return predictions(cases, PARAMETERS), [prior_lineage, target_lineage]


def _write_repeatable(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"refusing to overwrite differing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def run() -> tuple[dict, dict]:
    train_22, lineage_22 = _season_cases("2021-22", "2022-23")
    train_23, lineage_23 = _season_cases("2022-23", "2023-24")
    validation, lineage_24 = _season_cases("2023-24", "2024-25")
    final, lineage_25 = _season_cases("2024-25", "2025-26")
    lineage = {
        (
            row["season"],
            row["merged_gw_sha256"],
            row["players_raw_sha256"],
        ): row
        for row in lineage_22 + lineage_23 + lineage_24 + lineage_25
    }
    config, report = build_recalibration_report(
        training=pd.concat([train_22, train_23], ignore_index=True),
        validation=validation,
        final=final,
        source_lineage=[
            lineage[key] for key in sorted(lineage)
        ],
    )
    _write_repeatable(CONFIG, config)
    _write_repeatable(REPORT, report)
    return config, report


def main() -> int:
    config, report = run()
    locked = report["locked_validation"]
    print(
        json.dumps(
            {
                "model_config_sha256": config["content_sha256"],
                "decision": report["decision"],
                "proxy_gate_passed": report["proxy_gate_passed"],
                "promotion_eligible": report["promotion_eligible"],
                "promotion_gates": report["promotion_gates"],
                "locked_validation_delta": locked[
                    "delta_challenger_minus_control"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
