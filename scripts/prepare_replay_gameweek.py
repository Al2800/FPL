#!/usr/bin/env python3
"""Prepare one sealed, reviewed historical Gameweek without opening outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.replay_adapter import build_replay_solver_input
from src.forecasting.replay_forecast import build_locked_replay_forecast
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.orchestration.genuine_replay import (
    FUTURE_TRANSFER_DISCOUNT,
    PROBABILITY_EXTRA_TRANSFER_NEEDED,
    TRANSFER_VALUE_POLICY,
    prepare_historical_gameweek,
    select_policy_candidate,
)
from src.orchestration.policy_state import POLICY_ARMS


REPO = Path(__file__).resolve().parents[1]
VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
FOOTBALL_DATA = REPO / "data" / "raw" / "football-data"
CONFIG = REPO / "control" / "models" / "live-faithful-v1.feature-complete.json"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_once(path: Path, value: dict[str, Any]) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"Refusing to overwrite sealed artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan_summary(
    candidate: dict[str, Any], names: dict[str, str]
) -> dict[str, Any]:
    lineup = candidate["lineup"]
    return {
        "transfer_count": len(candidate["transfers"]),
        "immediate_objective": candidate.get(
            "immediate_objective", candidate["objective"]
        ),
        "transfer_option_value": candidate.get("transfer_option_value", 0.0),
        "planning_objective": candidate["objective"],
        "hit_cost": candidate["hit_cost"],
        "next_gameweek_free_transfers": candidate.get(
            "next_gameweek_free_transfers"
        ),
        "transfers": [
            {
                **move,
                "player_out_name": names[move["player_out_id"]],
                "player_in_name": names[move["player_in_id"]],
            }
            for move in candidate["transfers"]
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


def prepare(
    *,
    season: str,
    gameweek: int,
    episode_root: Path,
    output_root: Path,
    previous_checkpoint_dir: Path,
    code_commit: str,
    vaastav_root: Path = VAASTAV,
    football_data_root: Path = FOOTBALL_DATA,
    config_path: Path = CONFIG,
) -> dict[str, Any]:
    """Build common forecast evidence and state-bound arm decisions, still sealed."""

    prepare_historical_gameweek(
        season=season,
        gameweek=gameweek,
        episode_root=episode_root,
        previous_checkpoint_dir=previous_checkpoint_dir,
        output_root=output_root,
        code_commit=code_commit,
    )
    setup = output_root / f"gw-{gameweek:02d}" / "setup"
    episode = episode_root / f"gw-{gameweek:02d}"
    feature_state = _read(setup / "shared-feature-state.json")
    observed = _read(episode / "observed.json")
    identity = _read(episode / "identity-map.json")
    manifest = _read(episode / "episode-manifest.json")
    config = _read(config_path)
    if config.get("content_sha256") != artifact_hash(config):
        raise RuntimeError("Locked forecast config hash mismatch")
    if config.get("status") != "structured_calibrated_locked_pre_2025_26":
        raise RuntimeError("Forecast config is not locked before 2025/26")
    bundle = build_locked_replay_forecast(
        feature_state=feature_state,
        observed=observed,
        identity_map=identity,
        model_config=config,
        vaastav_root=vaastav_root,
        football_data_root=football_data_root,
    )
    forecast = bundle["forecast"]
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    names = {
        str(row["player_id"]): str(row["name"])
        for row in feature_state["players"]
    }
    arm_reviews: dict[str, Any] = {}
    input_hashes: set[str] = set()
    output_hashes: set[str] = set()
    output_cache: dict[str, dict[str, Any]] = {}
    for arm in POLICY_ARMS:
        arm_dir = setup / "arms" / arm
        state = _read(arm_dir / "starting-policy-state.json")
        solver_input = build_replay_solver_input(
            feature_state=feature_state,
            policy_state=state,
            forecast_view=forecast,
            max_transfers=3,
            transfer_value_policy=TRANSFER_VALUE_POLICY,
            probability_extra_transfer_needed=(
                PROBABILITY_EXTRA_TRANSFER_NEEDED
            ),
            future_transfer_discount=FUTURE_TRANSFER_DISCOUNT,
        )
        input_value = solver_input.as_dict()
        input_hash = fingerprint(input_value)
        if input_hash not in output_cache:
            output_cache[input_hash] = solve(
                solver_input,
                rules=rules,
                ruleset_sha256=rules_hash,
            )
        output = output_cache[input_hash]
        output_hash = fingerprint(output)
        selected = select_policy_candidate(arm, output)
        input_hashes.add(input_hash)
        output_hashes.add(output_hash)
        review = {
            "schema_version": "1.0",
            "season": season,
            "gameweek": gameweek,
            "policy_arm": arm,
            "status": "sealed_setup_awaiting_human_review",
            "contains_hidden_outcome": False,
            "contains_validated_plan": False,
            "contains_state_transition": False,
            "state_sha256": state["content_sha256"],
            "feature_state_sha256": feature_state["content_sha256"],
            "forecast_sha256": forecast["content_sha256"],
            "selection_policy": (
                "do_nothing_bank_transfers"
                if arm == "naive_baseline"
                else "reviewed_solver_selected"
            ),
            "selected": _plan_summary(selected, names),
            "plans_by_transfer_count": {
                count: _plan_summary(candidate, names)
                for count, candidate in output["best_by_transfer_count"].items()
            },
            "transfer_value_policy": output["transfer_value_policy"],
            "lineage": {
                "solver_input_sha256": input_hash,
                "solver_output_sha256": output_hash,
                "model_config_sha256": config["content_sha256"],
            },
        }
        review["content_sha256"] = artifact_hash(review)
        _write_once(arm_dir / "reviewed-engine-input.json", input_value)
        _write_once(arm_dir / "reviewed-engine-output.json", output)
        _write_once(arm_dir / "forecast-plan-review.json", review)
        arm_reviews[arm] = {
            "state_sha256": state["content_sha256"],
            "solver_input_sha256": input_hash,
            "solver_output_sha256": output_hash,
            "review_sha256": review["content_sha256"],
            "selection_policy": review["selection_policy"],
            "selected": review["selected"],
        }

    summary = {
        "schema_version": "1.0",
        "season": season,
        "gameweek": gameweek,
        "status": "sealed_setup_awaiting_human_review",
        "code_commit": code_commit,
        "contains_hidden_outcome": False,
        "contains_validated_plan": False,
        "contains_state_transition": False,
        "feature_state_sha256": feature_state["content_sha256"],
        "forecast_sha256": forecast["content_sha256"],
        "model_config_sha256": config["content_sha256"],
        "shared_forecast": True,
        "shared_solver_input": len(input_hashes) == 1,
        "shared_solver_output": len(output_hashes) == 1,
        "forecast_diagnostics": {
            "model_version": forecast["model_version"],
            "model_status": forecast["model_status"],
            "maximum_expected_points": max(
                float(row["expected_points"]) for row in forecast["players"]
            ),
            "team_fallbacks": bundle["team_prior"]["fallback_teams"],
            "event_model_weight": config["event_model_weight"],
            "recent_minutes_weight": config["recent_minutes_weight"],
            "availability_policy": (
                "historical availability/news unavailable; market rows remain "
                "available and expected minutes carries the observable signal"
            ),
        },
        "limitations": sorted(
            set(feature_state["limitations"])
            | {
                "historical_player_availability_status_unavailable",
                "historical_unstructured_evidence_not_reconstructed",
            }
        ),
        "arms": arm_reviews,
    }
    summary["content_sha256"] = artifact_hash(summary)
    _write_once(setup / "shared-locked-player-prior.json", bundle["player_prior"])
    _write_once(setup / "shared-locked-team-prior.json", bundle["team_prior"])
    _write_once(setup / "shared-locked-forecast.json", forecast)
    _write_once(setup / "forecast-review-summary.json", summary)
    return summary


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", required=True)
    parser.add_argument("--gameweek", required=True, type=int)
    parser.add_argument("--episode-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--previous-checkpoint", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(
        season=args.season,
        gameweek=args.gameweek,
        episode_root=args.episode_root,
        output_root=args.output_root,
        previous_checkpoint_dir=args.previous_checkpoint,
        code_commit=_git_commit(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
