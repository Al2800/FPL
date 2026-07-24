"""Build the locked structured forecast shared by historical replay arms."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.forecasting.live_faithful import build_live_faithful_forecast
from src.forecasting.player_priors import build_player_prior
from src.forecasting.team_prior import (
    EloParameters,
    build_episode_team_prior,
    fit_longitudinal_elo,
)
from src.forecasting.team_strength import SEASON_FILES, load_results


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_locked_replay_forecast(
    *,
    feature_state: Mapping[str, Any],
    observed: Mapping[str, Any],
    identity_map: Mapping[str, Any],
    model_config: Mapping[str, Any],
    vaastav_root: Path,
    football_data_root: Path,
) -> dict[str, dict[str, Any]]:
    """Return content-addressed player/team priors and the cutoff-safe forecast."""

    prior_season = "2024-25"
    prior_root = vaastav_root / prior_season
    prior_rows = pd.read_csv(
        prior_root / "gws" / "merged_gw.csv", low_memory=False
    )
    prior_rows = prior_rows[
        prior_rows["position"].astype(str).str.upper() != "AM"
    ].copy()
    prior_players = pd.read_csv(
        prior_root / "players_raw.csv", low_memory=False
    )
    prior_identity = {
        "season": prior_season,
        "players": [
            {"fpl_player_id": int(row.id), "fpl_code": int(row.code)}
            for row in prior_players[["id", "code"]].itertuples(index=False)
        ],
    }
    player_prior = build_player_prior(
        season=prior_season,
        as_of=date(2025, 5, 26).isoformat() + "T00:00:00Z",
        rows=prior_rows.to_dict("records"),
        identity_map=prior_identity,
        price_bands=model_config["price_bands"],
    )

    elo_values = model_config["calibration"]["elo_parameters"]
    elo_params = EloParameters(
        k=float(elo_values["k"]),
        home_advantage=float(elo_values["home_advantage"]),
        draw_factor=float(elo_values["draw_factor"]),
        promoted_rating=float(elo_values["promoted_rating"]),
        season_regression=float(elo_values["season_regression"]),
        fixture_scale=float(elo_values["fixture_scale"]),
    )
    match_seasons = [
        (season, load_results(season, root=football_data_root))
        for season in ("2020-21", "2021-22", "2022-23", "2023-24", "2024-25")
    ]
    previous_ratings, _ = fit_longitudinal_elo(match_seasons, elo_params)
    team_lineage = {
        "model_config_sha256": model_config["content_sha256"],
        "football_data": {
            season: {
                "file": SEASON_FILES[season],
                "sha256": _sha256(football_data_root / SEASON_FILES[season]),
            }
            for season, _ in match_seasons
        },
        "observed_sha256": hashlib.sha256(
            json.dumps(
                observed,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest(),
    }
    team_prior = build_episode_team_prior(
        season=str(feature_state["season"]),
        cutoff=str(feature_state["cutoff"]),
        identity_map=identity_map,
        fixtures=observed["fixtures"],
        prior_match_results=observed["prior_match_results"],
        previous_ratings=previous_ratings,
        previous_active_teams=set(match_seasons[-1][1]["HomeTeam"])
        | set(match_seasons[-1][1]["AwayTeam"]),
        params=elo_params,
        lineage=team_lineage,
    )
    forecast = build_live_faithful_forecast(
        feature_state=feature_state,
        identity_map=identity_map,
        player_prior=player_prior,
        team_prior=team_prior,
        model_config=model_config,
    )
    return {
        "player_prior": player_prior,
        "team_prior": team_prior,
        "forecast": forecast,
    }
