"""Fit the planning-only appearance distribution from local historical data."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.forecasting.appearance_distribution import (  # noqa: E402
    calibration_hash,
    distribution_for_probability,
    fit_binned_calibration,
)


DEFAULT_DATA_ROOT = (
    ROOT / "data/raw/vaastav/Fantasy-Premier-League/data"
)
DEFAULT_OUTPUT = ROOT / "control/models/appearance-distribution-v1.json"
TRAINING_SEASONS = ("2022-23", "2023-24")
VALIDATION_SEASON = "2024-25"


def _season_rows(path: Path, season: str) -> list[dict[str, Any]]:
    frame = pd.read_csv(
        path / season / "gws/merged_gw.csv",
        usecols=["element", "GW", "minutes", "starts"],
    )
    # One decision state per player-Gameweek; Double Gameweeks are aggregated.
    grouped = (
        frame.groupby(["element", "GW"], as_index=False)
        .agg(minutes=("minutes", "sum"), started=("starts", "max"))
        .sort_values(["element", "GW"], kind="mergesort")
    )
    by_player = grouped.groupby("element", sort=False)
    grouped["last_started"] = by_player["started"].shift(1)
    grouped["recent_minutes"] = by_player["minutes"].transform(
        lambda values: values.shift(1).rolling(3, min_periods=1).mean()
    )
    last = grouped["last_started"].fillna(0.5).astype(float)
    soft = (grouped["recent_minutes"].fillna(45.0) / 90.0).clip(0.05, 0.95)
    grouped["start_probability"] = (0.6 * last + 0.4 * soft).clip(0.05, 0.95)
    return [
        {
            "season": season,
            "player_id": str(row.element),
            "gameweek": int(row.GW),
            "start_probability": float(row.start_probability),
            "minutes": int(row.minutes),
        }
        for row in grouped.itertuples(index=False)
    ]


def _category(minutes: int) -> int:
    return 0 if minutes == 0 else 1 if minutes < 60 else 2


def _metrics(
    rows: list[dict[str, Any]],
    *,
    probability_for_row: Any,
) -> dict[str, Any]:
    brier = 0.0
    log_loss = 0.0
    predicted = [0.0, 0.0, 0.0]
    observed = [0, 0, 0]
    for row in rows:
        probabilities = probability_for_row(row)
        values = [
            float(probabilities["zero"]),
            float(probabilities["under_60"]),
            float(probabilities["60_plus"]),
        ]
        target = _category(int(row["minutes"]))
        brier += sum(
            (probability - (1.0 if index == target else 0.0)) ** 2
            for index, probability in enumerate(values)
        )
        log_loss -= math.log(max(values[target], 1e-12))
        for index, probability in enumerate(values):
            predicted[index] += probability
        observed[target] += 1
    count = len(rows)
    return {
        "n": count,
        "multiclass_brier": round(brier / count, 8),
        "log_loss": round(log_loss / count, 8),
        "mean_predicted": {
            state: round(predicted[index] / count, 8)
            for index, state in enumerate(("zero", "under_60", "60_plus"))
        },
        "observed_frequency": {
            state: round(observed[index] / count, 8)
            for index, state in enumerate(("zero", "under_60", "60_plus"))
        },
    }


def calibrate(data_root: Path = DEFAULT_DATA_ROOT) -> dict[str, Any]:
    training = [
        row
        for season in TRAINING_SEASONS
        for row in _season_rows(data_root, season)
    ]
    validation = _season_rows(data_root, VALIDATION_SEASON)
    result = fit_binned_calibration(
        training,
        model_version="appearance-distribution-v1",
        training_seasons=list(TRAINING_SEASONS),
    )
    result.update(
        {
            "feature_contract": (
                "0.6*lagged_started+0.4*clip(mean(previous_3_gw_minutes)/90,"
                "0.05,0.95)"
            ),
            "category_contract": {
                "zero": "gameweek_minutes == 0",
                "under_60": "0 < gameweek_minutes < 60",
                "60_plus": "gameweek_minutes >= 60",
            },
            "validation_season": VALIDATION_SEASON,
            "validation": _metrics(
                validation,
                probability_for_row=lambda row: distribution_for_probability(
                    row["start_probability"], result
                ).as_dict(),
            ),
            "uncalibrated_reference": _metrics(
                validation,
                probability_for_row=lambda row: {
                    "zero": (1.0 - row["start_probability"]) * 0.78,
                    "under_60": (
                        row["start_probability"] * 0.18
                        + (1.0 - row["start_probability"]) * 0.22
                    ),
                    "60_plus": row["start_probability"] * 0.82,
                },
            ),
            "selection_rule": (
                "fixed five equal-width bins with Dirichlet(1,1,1) smoothing; "
                "no 2024-25 or 2025-26 fitting"
            ),
        }
    )
    result["content_sha256"] = calibration_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = calibrate(args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "content_sha256": result["content_sha256"],
                "validation": result["validation"],
                "uncalibrated_reference": result["uncalibrated_reference"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
