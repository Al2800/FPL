"""Calibrate, evaluate, and materialise the separate team-context challenger."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.calibrate_team_context import select_team_context_parameters
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.team_context_challenger import (
    evaluate_team_context_challenger,
)


VAASTAV = (
    REPO / "data/raw/vaastav/Fantasy-Premier-League/data"
)


def _write_once(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"Refusing to overwrite differing artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main() -> int:
    seasons = ("2021-22", "2022-23", "2023-24", "2024-25")
    frames = {
        season: pd.read_csv(
            VAASTAV / season / "gws/merged_gw.csv",
            encoding="latin-1",
            low_memory=False,
        )
        for season in seasons
    }
    for frame in frames.values():
        if "round" not in frame and "GW" in frame:
            frame["round"] = frame["GW"]
        if "expected_goals" not in frame:
            frame["expected_goals"] = frame["goals_scored"]
    params, calibration = select_team_context_parameters(
        frames,
        training_seasons=("2022-23", "2023-24"),
        validation_season="2024-25",
    )
    config = {
        "model_version": "live-faithful-v2-team-context",
        "status": "experimental_preseason_team_context_challenger",
        "event_model_weight": 0.25,
        "parameters": params.__dict__,
        "source_policy": {
            "xg": "strictly_prior_fixture_player_xg_aggregation",
            "elo": "reuse_locked_pre_match_expected_score",
            "odds": "registered_predeadline_only_degrade_when_absent",
            "closing_or_unspecified_odds": "forbidden",
        },
        "limitations": [
            "2021-22_goals_used_only_for_pretraining_continuity_before_xg_available"
        ],
        "calibration": {
            "training_seasons": calibration["training_seasons"],
            "locked_validation_season": calibration["locked_validation_season"],
            "forbidden_fit_seasons": calibration["forbidden_fit_seasons"],
            "selection_objective": calibration["selection_objective"],
            "grid_size": calibration["grid_size"],
        },
    }
    config["content_sha256"] = artifact_hash(config)
    evaluation = evaluate_team_context_challenger(
        reports_root=REPO / "reports/benchmarks/2025-26",
        episodes_root=REPO / "data/benchmark-v0/episodes/v2/2025-26",
        outcomes_csv=(
            VAASTAV / "2025-26/gws/merged_gw.csv"
        ),
        params=params,
    )
    report = {
        "schema_version": "1.0",
        "report_id": "live-faithful-v2-team-context-evaluation",
        "model_config_sha256": config["content_sha256"],
        "calibration": calibration,
        "out_of_sample": evaluation,
        "note": (
            "Promotion requires every declared player-calibration check; "
            "a rejected model remains an inspectable experiment."
        ),
    }
    report["content_sha256"] = artifact_hash(report)
    _write_once(
        REPO / "control/models/live-faithful-v2.team-context.json",
        config,
    )
    _write_once(
        REPO
        / "reports/forecasting/live-faithful-v2-team-context/evaluation.json",
        report,
    )
    print(
        json.dumps(
            {
                "parameters": params.__dict__,
                "training_objective": calibration["selected"][
                    "training_objective"
                ],
                "validation": calibration["selected"]["metrics"]["2024-25"],
                "decision": evaluation["decision"],
                "promotion_rule": evaluation["promotion_rule"],
                "deltas": evaluation["deltas_team_context_minus"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
