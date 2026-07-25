"""Pre-2025/26 walk-forward calibration for separate team xG strengths."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from itertools import product
from statistics import mean
from typing import Any, Mapping

import pandas as pd

from src.forecasting.team_attack_defence import (
    AttackDefenceParameters,
    estimate_team_strengths,
)
from src.forecasting.team_context_challenger import historical_xg_observations


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _fixture_xg(
    strengths: Mapping[str, Mapping[str, Any]],
    home: str,
    away: str,
    params: AttackDefenceParameters,
) -> tuple[float, float]:
    base = params.league_xg_per_team
    return (
        base
        * params.home_xg_multiplier
        * float(strengths[home]["attack_xg"])
        / base
        * float(strengths[away]["defence_xga"])
        / base,
        base
        * float(strengths[away]["attack_xg"])
        / base
        * float(strengths[home]["defence_xga"])
        / base,
    )


def evaluate_team_xg_parameters(
    season_frames: Mapping[str, pd.DataFrame],
    params: AttackDefenceParameters,
) -> dict[str, Any]:
    """Evaluate strictly earlier fixtures within each named season."""
    results: dict[str, Any] = {}
    previous_teams: set[str] = set()
    for season, frame in season_frames.items():
        matches = historical_xg_observations(frame, before_gameweek=99)
        teams = {str(value) for value in frame["team"].dropna().unique()}
        promoted = teams - previous_teams if previous_teams else set()
        errors: list[float] = []
        for match in matches:
            kickoff = _timestamp(str(match["kickoff_time"]))
            prior = [
                row
                for row in matches
                if _timestamp(str(row["kickoff_time"])) < kickoff
            ]
            strengths = estimate_team_strengths(
                teams=teams,
                observations=prior,
                cutoff=str(match["kickoff_time"]),
                promoted_teams=promoted,
                params=params,
            )
            home_xg, away_xg = _fixture_xg(
                strengths,
                str(match["home_team"]),
                str(match["away_team"]),
                params,
            )
            errors.extend(
                [
                    abs(home_xg - float(match["home_xg"])),
                    abs(away_xg - float(match["away_xg"])),
                ]
            )
        results[season] = {
            "matches": len(matches),
            "team_xg_mae": mean(errors) if errors else None,
            "promoted_teams": sorted(promoted),
        }
        previous_teams = teams
    return results


def select_team_context_parameters(
    season_frames: Mapping[str, pd.DataFrame],
    *,
    training_seasons: tuple[str, ...],
    validation_season: str,
) -> tuple[AttackDefenceParameters, dict[str, Any]]:
    """Select a declared grid on training seasons, then reveal validation."""
    candidates: list[dict[str, Any]] = []
    for prior, home, promoted_attack, promoted_defence in product(
        (6.0, 12.0, 20.0),
        (1.04, 1.08, 1.12),
        (0.85, 0.95),
        (1.05, 1.15),
    ):
        params = AttackDefenceParameters(
            prior_matches=prior,
            home_xg_multiplier=home,
            promoted_attack_multiplier=promoted_attack,
            promoted_defence_vulnerability=promoted_defence,
        )
        training_frames = {
            season: frame
            for season, frame in season_frames.items()
            if season != validation_season
        }
        metrics = evaluate_team_xg_parameters(training_frames, params)
        objective = mean(
            float(metrics[season]["team_xg_mae"]) for season in training_seasons
        )
        candidates.append(
            {
                "parameters": asdict(params),
                "training_objective": objective,
                "metrics": metrics,
            }
        )
    candidates.sort(
        key=lambda row: (
            row["training_objective"],
            tuple(row["parameters"].values()),
        )
    )
    selected = AttackDefenceParameters(**candidates[0]["parameters"])
    selected_metrics = evaluate_team_xg_parameters(season_frames, selected)
    return selected, {
        "selection_objective": "mean_team_xg_mae",
        "training_seasons": list(training_seasons),
        "locked_validation_season": validation_season,
        "forbidden_fit_seasons": [validation_season, "2025-26"],
        "grid_size": len(candidates),
        "selected": {**candidates[0], "metrics": selected_metrics},
        "top_5": candidates[:5],
    }
