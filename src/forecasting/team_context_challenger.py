"""Reforecast frozen players with independent attack and defence context."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.evaluation.calibration import calibration_by_cohort
from src.forecasting.event_challenger import reblend_locked_forecast
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.team_attack_defence import (
    AttackDefenceParameters,
    build_attack_defence_prior,
)


ATTACK_WEIGHTS = {"GKP": 0.0, "DEF": 0.2, "MID": 0.85, "FWD": 1.0}
GOAL_POINTS = {"GKP": 6.0, "DEF": 6.0, "MID": 5.0, "FWD": 4.0}
CLEAN_SHEET_POINTS = {"GKP": 4.0, "DEF": 4.0, "MID": 1.0, "FWD": 0.0}


def historical_xg_observations(
    rows: pd.DataFrame,
    *,
    before_gameweek: int,
) -> list[dict[str, Any]]:
    """Aggregate player xG into completed team-fixture observations."""
    frame = rows[pd.to_numeric(rows["round"]) < before_gameweek].copy()
    if frame.empty:
        return []
    frame["expected_goals"] = pd.to_numeric(
        frame["expected_goals"], errors="coerce"
    ).fillna(0.0)
    grouped = (
        frame.groupby(
            ["fixture", "team", "was_home", "kickoff_time"],
            as_index=False,
        )["expected_goals"]
        .sum()
        .sort_values(["kickoff_time", "fixture"], kind="stable")
    )
    observations: list[dict[str, Any]] = []
    for _, fixture in grouped.groupby("fixture", sort=True):
        if len(fixture) != 2:
            continue
        home = fixture[
            fixture["was_home"].astype(str).str.lower().isin({"true", "1"})
        ]
        away = fixture[
            ~fixture["was_home"].astype(str).str.lower().isin({"true", "1"})
        ]
        if len(home) != 1 or len(away) != 1:
            continue
        observations.append(
            {
                "kickoff_time": str(home.iloc[0]["kickoff_time"]),
                "home_team": str(home.iloc[0]["team"]),
                "away_team": str(away.iloc[0]["team"]),
                "home_xg": float(home.iloc[0]["expected_goals"]),
                "away_xg": float(away.iloc[0]["expected_goals"]),
                "fixture_id": int(home.iloc[0]["fixture"]),
            }
        )
    return observations


def fixture_specs(
    forecast: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Recover unique home/away canonical clubs from frozen player fixtures."""
    fixtures: dict[int, dict[str, Any]] = {}
    for player in forecast["players"]:
        club_id = str(player["club_id"])
        for component in player["fixture_components"]:
            fixture_id = int(component["fixture_id"])
            opponent = str(component["opponent_club_id"])
            candidate = {
                "fixture_id": fixture_id,
                "home_club_id": club_id if component["was_home"] else opponent,
                "away_club_id": opponent if component["was_home"] else club_id,
            }
            if fixture_id in fixtures and fixtures[fixture_id] != candidate:
                raise ValueError(f"ambiguous frozen fixture {fixture_id}")
            fixtures[fixture_id] = candidate
    return [fixtures[key] for key in sorted(fixtures)]


def reforecast_with_team_context(
    forecast: Mapping[str, Any],
    team_prior: Mapping[str, Any],
    *,
    event_model_weight: float = 0.25,
) -> dict[str, Any]:
    """Apply independent attack/defence multipliers to frozen player rates."""
    weight = float(event_model_weight)
    if not 0 <= weight <= 1:
        raise ValueError("event_model_weight must be in [0, 1]")
    adjustments = {
        (int(row["fixture_id"]), str(row["club_id"])): row
        for row in team_prior["fixture_adjustments"]
    }
    result = deepcopy(dict(forecast))
    result.pop("content_sha256", None)
    result["model_version"] = "live-faithful-v2-team-context"
    result["model_status"] = "experimental_separate_attack_defence"
    result["lineage"] = {
        **deepcopy(dict(result["lineage"])),
        "base_forecast_sha256": str(forecast["content_sha256"]),
        "team_context_sha256": str(team_prior["content_sha256"]),
    }
    for player in result["players"]:
        position = str(player["position"])
        events = player["posterior_event_rates"]
        start_probability = float(player["start_probability"])
        total = 0.0
        for component in player["fixture_components"]:
            key = (int(component["fixture_id"]), str(player["club_id"]))
            if key not in adjustments:
                raise ValueError(f"missing separate team adjustment {key}")
            context = adjustments[key]
            attack = float(context["attack_multiplier"])
            defence = float(context["defence_multiplier"])
            minutes = float(component["expected_minutes"])
            team_multiplier = (
                ATTACK_WEIGHTS[position] * attack
                + (1.0 - ATTACK_WEIGHTS[position]) * defence
            )
            rate_points = (
                float(component["posterior_points_per_90"])
                * minutes
                / 90.0
                * team_multiplier
            )
            appearance = 1.0 + start_probability
            attacking = (
                float(events["expected_goals"]) * GOAL_POINTS[position]
                + float(events["expected_assists"]) * 3.0
            ) * minutes / 90.0 * attack
            defensive = (
                float(events["clean_sheets"]) * CLEAN_SHEET_POINTS[position]
            ) * minutes / 90.0 * defence
            saves = (
                float(events["saves"]) / 3.0 if position == "GKP" else 0.0
            ) * minutes / 90.0
            residual = (
                float(events["bonus"])
                - float(events["yellow_cards"])
                - 3.0 * float(events["red_cards"])
            ) * minutes / 90.0
            event_points = appearance + attacking + defensive + saves + residual
            expected = (1.0 - weight) * rate_points + weight * event_points
            component.update(
                {
                    "attack_multiplier": round(attack, 4),
                    "defence_multiplier": round(defence, 4),
                    "team_multiplier": round(team_multiplier, 4),
                    "rate_expected_points": round(rate_points, 4),
                    "event_expected_points": round(event_points, 4),
                    "event_model_weight": round(weight, 4),
                    "expected_points": round(expected, 2),
                }
            )
            total += component["expected_points"]
        player["expected_points"] = round(total, 2)
    result["content_sha256"] = artifact_hash(result)
    return result


def evaluate_team_context_challenger(
    *,
    reports_root: Path,
    episodes_root: Path,
    outcomes_csv: Path,
    params: AttackDefenceParameters = AttackDefenceParameters(),
) -> dict[str, Any]:
    """Walk forward over 2025/26 and compare v1, event-only, and team context."""
    raw = pd.read_csv(outcomes_csv, encoding="latin-1", low_memory=False)
    raw["round"] = pd.to_numeric(raw["round"], errors="raise").astype(int)
    actuals = (
        raw.groupby(["round", "element"], as_index=False)["total_points"]
        .sum()
        .set_index(["round", "element"])["total_points"]
        .to_dict()
    )
    rows: dict[str, list[dict[str, Any]]] = {
        "v1": [],
        "event_only": [],
        "team_context": [],
    }
    promoted = {"Burnley", "Leeds", "Sunderland"}
    degraded_counts: dict[str, int] = {}
    for gameweek in range(2, 39):
        root = reports_root / f"gw-{gameweek:02d}"
        forecast = json.loads(
            (root / "setup/shared-locked-forecast.json").read_text(encoding="utf-8")
        )
        old_team = json.loads(
            (root / "setup/shared-locked-team-prior.json").read_text(encoding="utf-8")
        )
        identity = json.loads(
            (
                episodes_root
                / f"gw-{gameweek:02d}"
                / "identity-map.json"
            ).read_text(encoding="utf-8")
        )
        identities = [
            {"team_name": row["fpl_name"], "club_id": row["canonical_id"]}
            for row in identity["teams"]
        ]
        elo = {
            (int(row["fixture_id"]), str(row["club_id"])): float(
                row["expected_result_score"]
            )
            for row in old_team["fixture_adjustments"]
        }
        team_prior = build_attack_defence_prior(
            season="2025-26",
            cutoff=str(forecast["cutoff"]),
            team_identities=identities,
            fixtures=fixture_specs(forecast),
            observations=historical_xg_observations(
                raw, before_gameweek=gameweek
            ),
            promoted_teams=promoted,
            elo_expected_scores=elo,
            odds_snapshots=None,
            params=params,
            lineage={
                "base_team_prior_sha256": old_team["content_sha256"],
                "odds_policy": "registered_predeadline_only",
            },
        )
        for reason in team_prior["degraded_reasons"]:
            degraded_counts[reason] = degraded_counts.get(reason, 0) + 1
        event_only = reblend_locked_forecast(
            forecast, event_model_weight=0.25
        )
        challenger = reforecast_with_team_context(
            forecast, team_prior, event_model_weight=0.25
        )
        plan = json.loads(
            (root / "forecast_optimizer/validated-plan.json").read_text(
                encoding="utf-8"
            )
        )
        owned = {row["player_id"] for row in plan["squad_after"]}
        selected = set(plan["lineup"]["starting_xi_ids"])
        by_model = {
            "v1": {row["player_id"]: row for row in forecast["players"]},
            "event_only": {
                row["player_id"]: row for row in event_only["players"]
            },
            "team_context": {
                row["player_id"]: row for row in challenger["players"]
            },
        }
        for player_id, base_player in by_model["v1"].items():
            element = int(player_id.rsplit(":", 1)[-1])
            actual = actuals.get((gameweek, element))
            if actual is None or int(base_player.get("fixture_count", 0)) == 0:
                continue
            cohorts = []
            if player_id in owned:
                cohorts.append("owned")
            if player_id in selected:
                cohorts.append("selected_xi")
            for model, players in by_model.items():
                rows[model].append(
                    {
                        "predicted": float(players[player_id]["expected_points"]),
                        "actual": float(actual),
                        "cohorts": cohorts,
                    }
                )
    calibration = {
        model: calibration_by_cohort(values) for model, values in rows.items()
    }
    deltas = {
        baseline: {
            cohort: {
                metric: (
                    calibration["team_context"][cohort][metric]
                    - calibration[baseline][cohort][metric]
                )
                for metric in (
                    "mean_absolute_error",
                    "root_mean_square_error",
                    "bias_actual_minus_predicted",
                )
            }
            for cohort in ("all", "owned", "selected_xi")
        }
        for baseline in ("v1", "event_only")
    }
    checks = {
        "all_mae_beats_v1": deltas["v1"]["all"]["mean_absolute_error"] < 0,
        "owned_mae_beats_v1": deltas["v1"]["owned"]["mean_absolute_error"] < 0,
        "selected_xi_mae_beats_v1": (
            deltas["v1"]["selected_xi"]["mean_absolute_error"] < 0
        ),
        "all_mae_beats_event_only": (
            deltas["event_only"]["all"]["mean_absolute_error"] < 0
        ),
    }
    return {
        "schema_version": "1.0",
        "evaluation_season": "2025-26",
        "fit_policy": "strictly_prior_gameweeks_only",
        "parameters": params.__dict__,
        "calibration": calibration,
        "deltas_team_context_minus": deltas,
        "degraded_mode_counts": degraded_counts,
        "promotion_rule": checks,
        "promotion_eligible": all(checks.values()),
        "decision": "promote" if all(checks.values()) else "reject",
    }
