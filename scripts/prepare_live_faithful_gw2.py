#!/usr/bin/env python3
"""Add a sealed live-faithful comparison to the existing GW2 setup."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.forecasting.live_faithful import (
    artifact_hash,
    build_live_faithful_forecast,
)
from src.forecasting.player_priors import build_player_prior
from src.forecasting.replay_adapter import build_replay_solver_input
from src.forecasting.team_prior import (
    EloParameters,
    build_episode_team_prior,
    fit_longitudinal_elo,
)
from src.forecasting.team_strength import SEASON_FILES, load_results
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve


SETUP = REPO / "reports" / "benchmarks" / "2025-26" / "gw-02" / "setup"
EPISODE = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26" / "gw-02"
VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
FOOTBALL_DATA = REPO / "data" / "raw" / "football-data"
CONFIG = REPO / "control" / "models" / "live-faithful-v1.feature-complete.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_once(path: Path, value: dict[str, Any]) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError(f"Refusing to overwrite differing sealed artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _selection(output: dict[str, Any], names: dict[str, str]) -> dict[str, Any]:
    selected = output["selected"]
    lineup = selected["lineup"]
    return {
        "objective": selected["objective"],
        "strategy": selected["strategy"],
        "hit_cost": selected["hit_cost"],
        "transfers": [
            {
                **move,
                "player_out_name": names[move["player_out_id"]],
                "player_in_name": names[move["player_in_id"]],
            }
            for move in selected["transfers"]
        ],
        "captain_id": lineup["captain_id"],
        "captain_name": names[lineup["captain_id"]],
        "vice_captain_id": lineup["vice_captain_id"],
        "vice_captain_name": names[lineup["vice_captain_id"]],
        "starting_xi": [
            {"player_id": player_id, "name": names[player_id]}
            for player_id in lineup["starting_xi_ids"]
        ],
    }


def run(
    *,
    setup_dir: Path = SETUP,
    episode_dir: Path = EPISODE,
    vaastav_root: Path = VAASTAV,
    football_data_root: Path = FOOTBALL_DATA,
    config_path: Path = CONFIG,
) -> dict[str, Any]:
    feature_state = _read_json(setup_dir / "shared-feature-state.json")
    observed = _read_json(episode_dir / "observed.json")
    identity = _read_json(episode_dir / "identity-map.json")
    manifest = _read_json(episode_dir / "episode-manifest.json")
    config = _read_json(config_path)
    if config["content_sha256"] != artifact_hash(config):
        raise RuntimeError("Calibrated model config hash mismatch")
    if config["status"] != "structured_calibrated_locked_pre_2025_26":
        raise RuntimeError("Model config is not locked for sealed replay comparison")

    prior_season = "2024-25"
    prior_root = vaastav_root / prior_season
    prior_rows_path = prior_root / "gws" / "merged_gw.csv"
    prior_players_path = prior_root / "players_raw.csv"
    prior_rows = pd.read_csv(prior_rows_path, low_memory=False)
    prior_rows = prior_rows[prior_rows["position"].astype(str).str.upper() != "AM"].copy()
    prior_players = pd.read_csv(prior_players_path, low_memory=False)
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
        price_bands=config["price_bands"],
    )

    elo_values = config["calibration"]["elo_parameters"]
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
        "model_config_sha256": config["content_sha256"],
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
        season="2025-26",
        cutoff=str(feature_state["cutoff"]),
        identity_map=identity,
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
        identity_map=identity,
        player_prior=player_prior,
        team_prior=team_prior,
        model_config=config,
    )

    policy = _read_json(
        setup_dir / "arms" / "forecast_optimizer" / "starting-policy-state.json"
    )
    solver_input = build_replay_solver_input(
        feature_state=feature_state,
        policy_state=policy,
        forecast_view=forecast,
        max_transfers=3,
    )
    rules = yaml.safe_load((episode_dir / "ruleset.yaml").read_text(encoding="utf-8"))
    output = solve(
        solver_input,
        rules=rules,
        ruleset_sha256=str(manifest["ruleset"]["content_sha256"]),
    )
    raw_output = _read_json(setup_dir / "shared-engine-output.json")
    names = {
        str(row["player_id"]): str(row["name"])
        for row in feature_state["players"]
    }
    comparison = {
        "schema_version": "1.0",
        "season": "2025-26",
        "gameweek": 2,
        "status": "sealed_setup_comparison_not_frozen",
        "contains_hidden_outcome": False,
        "contains_validated_plan": False,
        "contains_state_transition": False,
        "feature_state_sha256": feature_state["content_sha256"],
        "raw_rolling": _selection(raw_output, names),
        "live_faithful": _selection(output, names),
        "forecast_diagnostics": {
            "model_version": forecast["model_version"],
            "model_status": forecast["model_status"],
            "forecast_sha256": forecast["content_sha256"],
            "maximum_expected_points": max(
                row["expected_points"] for row in forecast["players"]
            ),
            "position_price_fallback_players": sum(
                row["prior"]["source"] == "position_price_fallback"
                for row in forecast["players"]
            ),
            "known_player_count": len(forecast["players"]),
            "team_fallbacks": team_prior["fallback_teams"],
            "event_model_weight": config["event_model_weight"],
            "event_model_decision": (
                "selected"
                if config["event_model_weight"] > 0
                else "rejected_by_training_selection"
            ),
            "recent_minutes_weight": config["recent_minutes_weight"],
        },
        "lineage": {
            "player_prior_sha256": player_prior["content_sha256"],
            "team_prior_sha256": team_prior["content_sha256"],
            "model_config_sha256": config["content_sha256"],
            "solver_input_sha256": fingerprint(solver_input.as_dict()),
            "solver_output_sha256": fingerprint(output),
        },
    }
    comparison["content_sha256"] = artifact_hash(comparison)
    _write_once(setup_dir / "shared-feature-complete-player-prior.json", player_prior)
    _write_once(setup_dir / "shared-feature-complete-team-prior.json", team_prior)
    _write_once(setup_dir / "shared-feature-complete-forecast.json", forecast)
    _write_once(setup_dir / "shared-feature-complete-engine-input.json", solver_input.as_dict())
    _write_once(setup_dir / "shared-feature-complete-engine-output.json", output)
    _write_once(setup_dir / "forecast-feature-complete-comparison.json", comparison)
    return comparison


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    comparison = run()
    print(
        json.dumps(
            {
                "raw_rolling": comparison["raw_rolling"],
                "live_faithful": comparison["live_faithful"],
                "diagnostics": comparison["forecast_diagnostics"],
                "content_sha256": comparison["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
