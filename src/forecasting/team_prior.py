"""Longitudinal Elo calibration and cutoff-safe fixture-prior construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from src.forecasting.live_faithful import artifact_hash


class TeamPriorError(ValueError):
    """Raised when match chronology or team identities are unsafe."""


ALIASES = {
    "Man Utd": "Man United",
    "Spurs": "Tottenham",
    "Sheffield Utd": "Sheffield United",
}
RATING_TO_FPL = {value: key for key, value in ALIASES.items()}


@dataclass(frozen=True)
class EloParameters:
    k: float
    home_advantage: float
    draw_factor: float
    promoted_rating: float
    season_regression: float
    fixture_scale: float = 0.5


def _probabilities(
    home_rating: float,
    away_rating: float,
    params: EloParameters,
) -> tuple[float, float, float]:
    home_strength = 10 ** ((home_rating + params.home_advantage) / 400.0)
    away_strength = 10 ** (away_rating / 400.0)
    draw_strength = params.draw_factor * (home_strength * away_strength) ** 0.5
    normalizer = home_strength + draw_strength + away_strength
    return (
        home_strength / normalizer,
        draw_strength / normalizer,
        away_strength / normalizer,
    )


def fit_longitudinal_elo(
    seasons: Iterable[tuple[str, pd.DataFrame]],
    params: EloParameters,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Carry regressed ratings across seasons and emit strictly pre-match forecasts."""

    ratings: dict[str, float] = {}
    records: list[dict[str, Any]] = []
    first_season = True
    for season, source in seasons:
        frame = source.copy().sort_values("Date", kind="stable")
        if not first_season:
            ratings = {
                team: 1500.0 + (rating - 1500.0) * params.season_regression
                for team, rating in ratings.items()
            }
        first_season = False
        for _, match in frame.iterrows():
            home = str(match["HomeTeam"])
            away = str(match["AwayTeam"])
            home_rating = ratings.get(home, params.promoted_rating)
            away_rating = ratings.get(away, params.promoted_rating)
            p_home, p_draw, p_away = _probabilities(home_rating, away_rating, params)
            home_goals = float(match["FTHG"])
            away_goals = float(match["FTAG"])
            actual_home = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
            expected_home = p_home + 0.5 * p_draw
            records.append(
                {
                    "season": season,
                    "Date": match["Date"],
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "p_home": p_home,
                    "p_draw": p_draw,
                    "p_away": p_away,
                    "actual": "H" if actual_home == 1 else "D" if actual_home == 0.5 else "A",
                    "home_rating_pre": home_rating,
                    "away_rating_pre": away_rating,
                }
            )
            ratings[home] = home_rating + params.k * (actual_home - expected_home)
            ratings[away] = away_rating + params.k * ((1.0 - actual_home) - (1.0 - expected_home))
    return ratings, pd.DataFrame(records)


def match_log_loss(frame: pd.DataFrame) -> float:
    selected = np.where(
        frame["actual"] == "H",
        frame["p_home"],
        np.where(frame["actual"] == "D", frame["p_draw"], frame["p_away"]),
    )
    return float(-np.log(np.clip(selected.astype(float), 1e-9, 1)).mean())


def select_elo_parameters(
    seasons: list[tuple[str, pd.DataFrame]],
    *,
    training_seasons: set[str],
) -> tuple[EloParameters, list[dict[str, Any]]]:
    """Select one declared Elo grid using only named training-season outcomes."""

    candidates = []
    for k in (10.0, 20.0, 30.0, 40.0):
        for home in (40.0, 60.0, 80.0):
            for draw in (0.6, 0.8, 1.0):
                for promoted in (1400.0, 1450.0, 1500.0):
                    for regression in (0.5, 0.75, 1.0):
                        params = EloParameters(k, home, draw, promoted, regression)
                        _, forecasts = fit_longitudinal_elo(seasons, params)
                        training = forecasts[forecasts["season"].isin(training_seasons)]
                        candidates.append(
                            {
                                "parameters": asdict(params),
                                "training_log_loss": match_log_loss(training),
                            }
                        )
    candidates.sort(
        key=lambda row: (
            row["training_log_loss"],
            tuple(row["parameters"].values()),
        )
    )
    return EloParameters(**candidates[0]["parameters"]), candidates


def attach_pre_match_elo_scores(
    player_rows: pd.DataFrame,
    match_forecasts: pd.DataFrame,
) -> pd.DataFrame:
    """Attach each team's strictly pre-match expected result score to player rows."""

    players = player_rows.copy()
    if "kickoff_time" not in players.columns or "team" not in players.columns:
        raise TeamPriorError("Player rows need kickoff_time and team")
    players["_match_date"] = pd.to_datetime(
        players["kickoff_time"], utc=True, errors="coerce"
    ).dt.date
    if players["_match_date"].isna().any():
        raise TeamPriorError("Player rows contain invalid kickoff_time")
    forecasts = match_forecasts.copy()
    forecasts["_match_date"] = pd.to_datetime(
        forecasts["Date"], errors="coerce"
    ).dt.date
    home = forecasts.assign(
        team=forecasts["HomeTeam"].map(lambda value: RATING_TO_FPL.get(str(value), str(value))),
        expected_result_score=forecasts["p_home"] + 0.5 * forecasts["p_draw"],
    )[["_match_date", "team", "expected_result_score"]]
    away = forecasts.assign(
        team=forecasts["AwayTeam"].map(lambda value: RATING_TO_FPL.get(str(value), str(value))),
        expected_result_score=forecasts["p_away"] + 0.5 * forecasts["p_draw"],
    )[["_match_date", "team", "expected_result_score"]]
    lookup = pd.concat([home, away], ignore_index=True)
    if lookup.duplicated(["_match_date", "team"]).any():
        raise TeamPriorError("Ambiguous match forecast lookup")
    players = players.merge(
        lookup,
        on=["_match_date", "team"],
        how="left",
        validate="many_to_one",
    )
    if players["expected_result_score"].isna().any():
        unresolved = (
            players.loc[players["expected_result_score"].isna(), ["_match_date", "team"]]
            .drop_duplicates()
            .head(5)
            .to_dict("records")
        )
        raise TeamPriorError(f"Unresolved player fixture forecast(s): {unresolved}")
    return players.drop(columns=["_match_date"])


def _timestamp(value: Any) -> datetime:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise TeamPriorError(f"Invalid timestamp: {value}") from exc


def build_episode_team_prior(
    *,
    season: str,
    cutoff: str,
    identity_map: Mapping[str, Any],
    fixtures: Iterable[Mapping[str, Any]],
    prior_match_results: Iterable[Mapping[str, Any]],
    previous_ratings: Mapping[str, float],
    previous_active_teams: Iterable[str],
    params: EloParameters,
    lineage: Mapping[str, Any],
) -> dict[str, Any]:
    """Regress prior ratings, update with pre-cutoff results, and score fixtures."""

    cutoff_time = _timestamp(cutoff)
    teams_by_id: dict[int, dict[str, str]] = {}
    for row in identity_map.get("teams", []):
        fpl_id = int(row["fpl_team_id"])
        if fpl_id in teams_by_id:
            raise TeamPriorError(f"Duplicate FPL team identity: {fpl_id}")
        teams_by_id[fpl_id] = {
            "canonical_id": str(row["canonical_id"]),
            "rating_name": ALIASES.get(str(row["fpl_name"]), str(row["fpl_name"])),
        }
    ratings = {
        name: 1500.0 + (float(rating) - 1500.0) * params.season_regression
        for name, rating in previous_ratings.items()
    }
    active_previous = {str(team) for team in previous_active_teams}
    fallback_teams: set[str] = set()
    for team in teams_by_id.values():
        if (
            team["rating_name"] not in ratings
            or team["rating_name"] not in active_previous
        ):
            ratings[team["rating_name"]] = params.promoted_rating
            fallback_teams.add(team["canonical_id"])

    latest_result: datetime | None = None
    for result in sorted(prior_match_results, key=lambda row: str(row["kickoff_time"])):
        kickoff = _timestamp(result["kickoff_time"])
        if kickoff >= cutoff_time:
            raise TeamPriorError("Prior match result is not strictly before cutoff")
        latest_result = kickoff
        home = ALIASES.get(str(result["home_team_name"]), str(result["home_team_name"]))
        away = ALIASES.get(str(result["away_team_name"]), str(result["away_team_name"]))
        if home not in ratings or away not in ratings:
            raise TeamPriorError(f"Unresolved prior-result team: {home} vs {away}")
        p_home, p_draw, _ = _probabilities(ratings[home], ratings[away], params)
        expected_home = p_home + 0.5 * p_draw
        home_goals = int(result["home_goals"])
        away_goals = int(result["away_goals"])
        actual_home = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
        home_rating, away_rating = ratings[home], ratings[away]
        ratings[home] = home_rating + params.k * (actual_home - expected_home)
        ratings[away] = away_rating + params.k * ((1 - actual_home) - (1 - expected_home))

    adjustments: list[dict[str, Any]] = []
    for fixture in fixtures:
        home_team = teams_by_id[int(fixture["team_h"])]
        away_team = teams_by_id[int(fixture["team_a"])]
        home = home_team["rating_name"]
        away = away_team["rating_name"]
        p_home, p_draw, p_away = _probabilities(ratings[home], ratings[away], params)
        expected_home = p_home + 0.5 * p_draw
        expected_away = p_away + 0.5 * p_draw
        for team, expected_score in (
            (home_team, expected_home),
            (away_team, expected_away),
        ):
            multiplier = float(np.clip((expected_score / 0.5) ** params.fixture_scale, 0.7, 1.3))
            adjustments.append(
                {
                    "fixture_id": int(fixture["id"]),
                    "club_id": team["canonical_id"],
                    "attack_multiplier": round(multiplier, 6),
                    "defence_multiplier": round(multiplier, 6),
                    "expected_result_score": round(float(expected_score), 6),
                }
            )

    result = {
        "schema_version": "1.0",
        "season": season,
        "as_of": cutoff,
        "last_result_at": latest_result.isoformat().replace("+00:00", "Z") if latest_result else None,
        "model": {"type": "longitudinal_elo", **asdict(params)},
        "fallback_teams": sorted(fallback_teams),
        "fixture_adjustments": sorted(
            adjustments, key=lambda row: (row["fixture_id"], row["club_id"])
        ),
        "lineage": dict(lineage),
    }
    result["content_sha256"] = artifact_hash(result)
    return result
