"""Read-only post-season review of frozen genuine-replay artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.evaluation.calibration import calibration_by_cohort
from src.evaluation.paired_metrics import paired_summary, resource_summary
from src.evaluation.power import minimum_detectable_paired_effect


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def review_replay_season(
    reports_root: Path,
    outcomes_csv: Path,
    *,
    evaluated_arm: str = "forecast_optimizer",
    baseline_arm: str = "naive_baseline",
) -> dict[str, Any]:
    """Evaluate one frozen season without changing any replay artifact."""
    outcome_frame = pd.read_csv(
        outcomes_csv,
        encoding="latin-1",
        low_memory=False,
        usecols=["element", "round", "total_points"],
    )
    outcomes = (
        outcome_frame.groupby(["round", "element"], as_index=False)["total_points"]
        .sum()
        .set_index(["round", "element"])["total_points"]
        .to_dict()
    )
    pairs: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    transfers = 0
    transfer_weeks = 0
    hit_cost = 0
    autosubs = 0
    autosub_points = 0.0
    bench_points = 0.0
    season: str | None = None

    for gameweek in range(1, 39):
        gameweek_root = reports_root / f"gw-{gameweek:02d}"
        summary = _read(gameweek_root / "run-summary.json")
        season = str(summary["season"])
        evaluated = summary["arms"][evaluated_arm]
        baseline = summary["arms"][baseline_arm]
        pairs.append(
            {
                "episode_id": summary["episode_id"],
                "cluster_id": f"{season}:gw{gameweek}",
                "evaluated_value": float(evaluated["net_points"]),
                "baseline_value": float(baseline["net_points"]),
            }
        )

        plan = _read(gameweek_root / evaluated_arm / "validated-plan.json")
        realised = _read(gameweek_root / evaluated_arm / "realised-outcome.json")
        forecast_path = gameweek_root / "setup" / "shared-locked-forecast.json"
        forecast = _read(forecast_path) if forecast_path.exists() else {"players": []}
        owned = {row["player_id"] for row in plan["squad_after"]}
        selected = set(plan["lineup"]["starting_xi_ids"])
        for row in forecast["players"]:
            element = int(str(row["player_id"]).rsplit(":", 1)[-1])
            actual = outcomes.get((gameweek, element))
            if actual is None or int(row.get("fixture_count", 0)) == 0:
                continue
            cohorts: list[str] = []
            if row["player_id"] in owned:
                cohorts.append("owned")
            if row["player_id"] in selected:
                cohorts.append("selected_xi")
            calibration_rows.append(
                {
                    "predicted": float(row["expected_points"]),
                    "actual": float(actual),
                    "cohorts": cohorts,
                }
            )

        count = int(plan["finance"]["transfer_count"])
        transfers += count
        transfer_weeks += int(count > 0)
        hit_cost += int(plan["finance"]["hit_cost"])
        autosubs += len(realised["substitutions"])
        actual_by_player = {
            row["player_id"]: float(row["total_points"])
            for row in realised["aggregated_players"]
        }
        autosub_points += sum(
            actual_by_player[row["player_in_id"]] for row in realised["substitutions"]
        )
        bench_points += float(realised["bench_points"])

    paired = paired_summary(pairs)
    detectable = minimum_detectable_paired_effect(
        n_clusters=paired["n_clusters"],
        sample_standard_deviation=paired["sample_standard_deviation"],
    )
    return {
        "schema_version": "1.0",
        "season": season,
        "evaluated_arm": evaluated_arm,
        "baseline_arm": baseline_arm,
        "comparison_basis": "realised_longitudinal_policy_arm",
        "paired_metrics": paired,
        "detectable_effect": detectable,
        "calibration": calibration_by_cohort(calibration_rows),
        "decision_activity": {
            "transfers": transfers,
            "transfer_weeks": transfer_weeks,
            "hit_cost": hit_cost,
            "automatic_substitutions": autosubs,
            "automatic_substitution_points": autosub_points,
            "recorded_bench_points": bench_points,
        },
        "resource_use": resource_summary(pairs),
        "counterfactual_coverage": {
            "policy_arm": "realised_longitudinal",
            "do_nothing": "requires same-starting-state rescoring",
            "captain": "requires captain-only rescoring",
            "transfer": "requires frozen hold-plan rescoring",
            "bench": "requires lineup-only rescoring",
            "chip": "delegated to FPL-q8s",
        },
        "limitations": [
            "Policy arms have independent longitudinal states after their first divergence.",
            "Historical replay did not record latency or cost, so resource counts are null rather than imputed.",
            "Calibration uses official realised points and deadline-locked forecasts; it does not use same-Gameweek xP.",
        ],
    }
