#!/usr/bin/env python3
"""Calibrate cold-start parameters before touching the 2025/26 replay."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.calibrate_live_faithful import (
    build_calibration_cases,
    evaluate_cases,
    load_season_rows,
    predictions,
    select_parameters,
)
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.team_prior import (
    EloParameters,
    attach_pre_match_elo_scores,
    fit_longitudinal_elo,
    match_log_loss,
    select_elo_parameters,
)
from src.forecasting.team_strength import SEASON_FILES, load_results


DEFAULT_VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
DEFAULT_FOOTBALL_DATA = REPO / "data" / "raw" / "football-data"
DEFAULT_REPORT = REPO / "reports" / "forecasting" / "live-faithful-v1-reliability-calibration.json"
DEFAULT_CONFIG = REPO / "control" / "models" / "live-faithful-v1.reliability-calibrated.json"


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"Refusing to overwrite differing artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _decision_diagnostics(frame: pd.DataFrame) -> dict[str, Any]:
    rows = []
    for gameweek, group in frame.groupby("GW", sort=True):
        count = min(15, len(group))
        raw_top = set(group.nlargest(count, "raw_rolling_expected_points")["code"])
        live_top = set(group.nlargest(count, "live_faithful_expected_points")["code"])
        actual_top = set(group.nlargest(count, "actual_points")["code"])
        rows.append(
            {
                "gameweek": int(gameweek),
                "players": int(len(group)),
                "raw_vs_live_top15_overlap": round(len(raw_top & live_top) / count, 4),
                "raw_actual_top15_precision": round(len(raw_top & actual_top) / count, 4),
                "live_actual_top15_precision": round(len(live_top & actual_top) / count, 4),
                "raw_max_expected_points": round(
                    float(group["raw_rolling_expected_points"].max()), 3
                ),
                "live_max_expected_points": round(
                    float(group["live_faithful_expected_points"].max()), 3
                ),
            }
        )
    early = [row for row in rows if 2 <= row["gameweek"] <= 5]
    return {
        "by_gameweek": rows,
        "early_gw2_5": {
            "mean_raw_vs_live_top15_overlap": round(
                sum(row["raw_vs_live_top15_overlap"] for row in early) / len(early), 4
            ),
            "mean_raw_actual_top15_precision": round(
                sum(row["raw_actual_top15_precision"] for row in early) / len(early), 4
            ),
            "mean_live_actual_top15_precision": round(
                sum(row["live_actual_top15_precision"] for row in early) / len(early), 4
            ),
            "max_raw_expected_points": max(row["raw_max_expected_points"] for row in early),
            "max_live_expected_points": max(row["live_max_expected_points"] for row in early),
        },
    }


def run(
    *,
    vaastav_root: Path,
    report_path: Path,
    config_path: Path,
    source_commit: str,
    football_data_root: Path = DEFAULT_FOOTBALL_DATA,
) -> dict[str, Any]:
    seasons = ("2021-22", "2022-23", "2023-24", "2024-25")
    loaded: dict[str, pd.DataFrame] = {}
    lineage: dict[str, Any] = {}
    for season in seasons:
        loaded[season], lineage[season] = load_season_rows(
            season,
            vaastav_root=vaastav_root,
        )

    match_seasons = [
        (season, load_results(season, root=football_data_root))
        for season in ("2020-21", "2021-22", "2022-23", "2023-24", "2024-25")
    ]
    football_lineage = {
        season: {
            "file": SEASON_FILES[season],
            "sha256": _file_sha256(football_data_root / SEASON_FILES[season]),
            "row_count": int(len(frame)),
        }
        for season, frame in match_seasons
    }
    lineage["football_data"] = football_lineage
    selected_elo, elo_candidates = select_elo_parameters(
        match_seasons,
        training_seasons={"2021-22", "2022-23", "2023-24"},
    )
    _, match_forecasts = fit_longitudinal_elo(match_seasons, selected_elo)
    for season in ("2022-23", "2023-24", "2024-25"):
        loaded[season] = attach_pre_match_elo_scores(
            loaded[season],
            match_forecasts[match_forecasts["season"] == season],
        )

    training_pairs = (("2021-22", "2022-23"), ("2022-23", "2023-24"))
    training_cases = pd.concat(
        [
            build_calibration_cases(
                prior_rows=loaded[prior],
                target_rows=loaded[target],
                prior_season=prior,
                target_season=target,
            )
            for prior, target in training_pairs
        ],
        ignore_index=True,
    )
    validation_cases = build_calibration_cases(
        prior_rows=loaded["2023-24"],
        target_rows=loaded["2024-25"],
        prior_season="2023-24",
        target_season="2024-25",
    )
    selected, candidates = select_parameters(
        training_cases,
        prior_equivalent_minutes=(720, 900, 1350),
        start_prior_equivalent_matches=(2, 4),
        cameo_minutes=(10, 18),
        team_fixture_scale=(0.0, 0.25, 0.5),
        player_prior_reliability_minutes=(450, 900, 1800),
    )
    training_evaluation = evaluate_cases(training_cases, selected)
    validation_evaluation = evaluate_cases(validation_cases, selected)
    validation_predictions = predictions(validation_cases, selected)

    config = {
        "model_version": "live-faithful-v1",
        "status": "structured_calibrated_locked_pre_2025_26",
        **{
            key: float(value)
            for key, value in candidates[0]["parameters"].items()
        },
        "price_bands": [[0.0, 5.5], [5.5, 7.5], [7.5, 10.0], [10.0, 20.0]],
        "fixture_multiplier_bounds": [0.7, 1.3],
        "position_attack_weight": {
            "GKP": 0.0,
            "DEF": 0.2,
            "MID": 0.85,
            "FWD": 1.0,
        },
        "optional_components": {
            "timestamped_odds": "degrade_when_absent",
            "unstructured_evidence": "degrade_when_absent",
        },
        "calibration": {
            "training_target_seasons": ["2022-23", "2023-24"],
            "locked_validation_season": "2024-25",
            "source_commit": source_commit,
            "source_lineage_sha256": _fingerprint(lineage),
            "selection_objective": (
                "early_gw2_5_mae + 0.01*expected_minutes_mae + 0.5*start_brier"
            ),
            "team_component_status": "calibrated_match_and_player_training",
            "elo_parameters": {
                **elo_candidates[0]["parameters"],
                "fixture_scale": candidates[0]["parameters"]["team_fixture_scale"],
            },
            "elo_training_log_loss": elo_candidates[0]["training_log_loss"],
            "elo_locked_validation_log_loss": match_log_loss(
                match_forecasts[match_forecasts["season"] == "2024-25"]
            ),
        },
    }
    config["content_sha256"] = artifact_hash(config)

    report = {
        "schema_version": "1.0",
        "report_id": "live-faithful-v1-cold-start-calibration",
        "source_commit": source_commit,
        "source_lineage": lineage,
        "split": {
            "training_target_seasons": ["2022-23", "2023-24"],
            "locked_validation_season": "2024-25",
            "forbidden_fit_seasons": ["2024-25", "2025-26"],
        },
        "selection": {
            "grid_size": len(candidates),
            "selected_parameters": candidates[0]["parameters"],
            "selected_objective": candidates[0]["objective"],
            "top_10": [
                {
                    "rank": index + 1,
                    "parameters": row["parameters"],
                    "objective": row["objective"],
                }
                for index, row in enumerate(candidates[:10])
            ],
        },
        "team_selection": {
            "grid_size": len(elo_candidates),
            "selected_parameters": elo_candidates[0]["parameters"],
            "training_log_loss": elo_candidates[0]["training_log_loss"],
            "locked_validation_log_loss": match_log_loss(
                match_forecasts[match_forecasts["season"] == "2024-25"]
            ),
            "fixture_scale_selected_with_player_training": (
                candidates[0]["parameters"]["team_fixture_scale"]
            ),
        },
        "training": training_evaluation,
        "locked_validation": validation_evaluation,
        "locked_validation_decision_diagnostics": _decision_diagnostics(
            validation_predictions
        ),
        "limitations": [
            "2021-22_prior_start_flag_uses_minutes_ge_60_because_recorded_starts_absent",
            "historical_unstructured_evidence_not_recoverable_at_full_coverage",
            "historical_odds_excluded_from_fit_without_predeadline_quote_timestamp",
        ],
        "model_config_sha256": config["content_sha256"],
    }
    report["content_sha256"] = artifact_hash(report)
    _write_once(config_path, config)
    _write_once(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vaastav-root", type=Path, default=DEFAULT_VAASTAV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--football-data-root", type=Path, default=DEFAULT_FOOTBALL_DATA)
    args = parser.parse_args(argv)
    report = run(
        vaastav_root=args.vaastav_root,
        report_path=args.report,
        config_path=args.config,
        source_commit=args.source_commit,
        football_data_root=args.football_data_root,
    )
    summary = {
        "selected": report["selection"]["selected_parameters"],
        "training": report["training"]["early_gw2_5"],
        "validation": report["locked_validation"]["early_gw2_5"],
        "report_sha256": report["content_sha256"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
