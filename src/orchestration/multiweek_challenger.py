"""Same-cutoff horizon construction and additive multiweek challenger runner."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.multiweek import multiweek_plan_hash, plan_multiweek
from src.optimisation.types import SolverInput
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import ruleset_sha256


class MultiweekChallengerError(ValueError):
    """Raised when historical horizon evidence is unsafe or incomplete."""


def multiweek_report_hash(value: Mapping[str, Any]) -> str:
    projection = deepcopy(dict(value))
    projection.pop("content_sha256", None)
    projection.get("plan", {}).get("search", {}).pop("elapsed_seconds", None)
    return artifact_hash(projection)


def _fixture_components(
    *,
    club_id: str,
    fixtures: Sequence[Mapping[str, Any]],
    season: str,
    multipliers: Mapping[str, Any],
) -> list[dict[str, Any]]:
    team_id = int(club_id.rsplit(":", 1)[-1])
    result: list[dict[str, Any]] = []
    allowed = {
        "event",
        "id",
        "kickoff_time",
        "provisional_start_time",
        "team_a",
        "team_a_difficulty",
        "team_h",
        "team_h_difficulty",
    }
    for source in fixtures:
        extra = set(source) - allowed
        if extra:
            raise MultiweekChallengerError(
                f"fixture schedule contains outcome-capable fields: {sorted(extra)}"
            )
        row = dict(source)
        if int(row["team_h"]) == team_id:
            opponent = int(row["team_a"])
            difficulty = int(row["team_h_difficulty"])
            was_home = True
        elif int(row["team_a"]) == team_id:
            opponent = int(row["team_h"])
            difficulty = int(row["team_a_difficulty"])
            was_home = False
        else:
            continue
        result.append(
            {
                "fixture_id": int(row["id"]),
                "opponent_club_id": f"team:{season}:{opponent}",
                "was_home": was_home,
                "difficulty": difficulty,
                "multiplier": float(multipliers[str(difficulty)]),
            }
        )
    return sorted(result, key=lambda row: row["fixture_id"])


def build_same_cutoff_horizon(
    *,
    base_input: Mapping[str, Any],
    locked_forecast: Mapping[str, Any],
    fixture_weeks: Sequence[Mapping[str, Any]],
    feature_state_sha256: str,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Project future fixtures from one frozen player-rate/cutoff state."""
    if locked_forecast.get("content_sha256") != artifact_hash(locked_forecast):
        raise MultiweekChallengerError("locked forecast hash mismatch")
    base = deepcopy(dict(base_input))
    forecast = {
        str(row["player_id"]): row for row in locked_forecast["players"]
    }
    if set(forecast) != {str(row["player_id"]) for row in base["players"]}:
        raise MultiweekChallengerError("forecast and solver markets differ")
    multipliers = config["fixture_projection"]["difficulty_multiplier"]
    cutoff = str(locked_forecast["cutoff"])
    result: list[dict[str, Any]] = []
    for week in fixture_weeks:
        players: list[dict[str, Any]] = []
        for source in base["players"]:
            row = deepcopy(dict(source))
            player = forecast[str(row["player_id"])]
            components = _fixture_components(
                club_id=str(row["club_id"]),
                fixtures=week["fixtures"],
                season=str(base["season"]),
                multipliers=multipliers,
            )
            minutes = (
                float(player["expected_minutes"])
                / max(1, int(player.get("fixture_count", 1)))
            )
            rate = float(player["posterior_points_per_90"])
            if int(week["gameweek"]) == int(base["gameweek"]):
                # The executable week's input must be byte-for-byte equivalent
                # in decision meaning to the already reviewed one-week market.
                row["expected_points"] = float(source["expected_points"])
                row["expected_minutes"] = float(source.get("expected_minutes", 0.0))
                row["fixture_count"] = int(source.get("fixture_count", len(components)))
            else:
                row["expected_points"] = round(
                    sum(
                        rate * minutes / 90.0 * item["multiplier"]
                        for item in components
                    ),
                    4,
                )
                row["expected_minutes"] = round(minutes * len(components), 1)
                row["fixture_count"] = len(components)
            row["horizon_fixture_components"] = components
            players.append(row)
        result.append(
            {
                "gameweek": int(week["gameweek"]),
                "cutoff": cutoff,
                "feature_state_sha256": feature_state_sha256,
                "schedule_provenance": deepcopy(dict(week["schedule_provenance"])),
                "players": players,
            }
        )
    return result


def run_historical_multiweek_challenger(
    *,
    base_input_path: Path,
    locked_forecast_path: Path,
    fixture_episode_paths: Sequence[Path],
    config_path: Path,
    rules_path: Path,
) -> dict[str, Any]:
    base = json.loads(base_input_path.read_text(encoding="utf-8"))
    forecast = json.loads(locked_forecast_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("content_sha256") != artifact_hash(config):
        raise MultiweekChallengerError("policy config hash mismatch")
    fixture_weeks = []
    for path in fixture_episode_paths:
        observed = json.loads(path.read_text(encoding="utf-8"))
        fixture_weeks.append(
            {
                "gameweek": int(observed["gameweek"]),
                "fixtures": observed["fixtures"],
                "schedule_provenance": {
                    "source_path": path.as_posix(),
                    "observed_dataset_hash": observed["dataset_hash"],
                    "historical_point_in_time_snapshot_available": False,
                },
            }
        )
    feature_hashes = {
        str(row["feature_state_sha256"]) for row in base["players"]
    }
    if len(feature_hashes) != 1:
        raise MultiweekChallengerError("base input has ambiguous feature lineage")
    horizon = build_same_cutoff_horizon(
        base_input=base,
        locked_forecast=forecast,
        fixture_weeks=fixture_weeks,
        feature_state_sha256=next(iter(feature_hashes)),
        config=config,
    )
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    rules_hash = ruleset_sha256(rules_path)
    plan = plan_multiweek(
        SolverInput.from_dict(base),
        horizon,
        config=config,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    report = {
        "schema_version": "1.0",
        "report_id": (
            f"multiweek:{base['season']}:gw{int(base['gameweek']):02d}"
        ),
        "exploratory_only": True,
        "promotion_eligible": False,
        "reason_not_promotion_eligible": (
            "historical point-in-time full fixture schedule snapshots are absent; "
            "future fixture fields are reconstructed from later stripped episodes"
        ),
        "policy_config_sha256": config["content_sha256"],
        "forecast_sha256": forecast["content_sha256"],
        "horizon": horizon,
        "plan": plan,
    }
    report["content_sha256"] = multiweek_report_hash(report)
    if plan.get("content_sha256") != multiweek_plan_hash(plan):
        raise MultiweekChallengerError("multiweek plan hash mismatch")
    return report


def score_historical_first_action(
    report: Mapping[str, Any],
    *,
    state_path: Path,
    solver_input_path: Path,
    manifest_path: Path,
    hidden_outcome_path: Path,
    identity_map_path: Path,
    shared_context_path: Path,
    canonical_plan_path: Path,
    canonical_outcome_path: Path,
    rules_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Freeze and score only the executable action against the canonical outcome."""
    result = deepcopy(dict(report))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    solver_input = json.loads(solver_input_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hidden = json.loads(hidden_outcome_path.read_text(encoding="utf-8"))
    identity = json.loads(identity_map_path.read_text(encoding="utf-8"))
    shared = json.loads(shared_context_path.read_text(encoding="utf-8"))
    canonical_plan = json.loads(canonical_plan_path.read_text(encoding="utf-8"))
    canonical = json.loads(canonical_outcome_path.read_text(encoding="utf-8"))
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    rules_hash = ruleset_sha256(rules_path)
    plan = validate_and_freeze_plan(
        episode_id=str(manifest["episode_id"]),
        policy_arm=str(state["policy_arm"]),
        state=state,
        candidate=result["plan"]["executable_action"],
        decision_market=solver_input["players"],
        active_chip=None,
        frozen_at=str(manifest["deadline"]),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    identity_index = {
        str(row["fpl_player_id"]): str(row["canonical_id"])
        for row in identity["players"]
    }
    outcome = score_revealed_outcome(
        plan,
        hidden,
        revealed_at=str(canonical["revealed_at"]),
        rules=rules,
        ruleset_sha256=rules_hash,
        player_identity_map=identity_index,
        identity_map_sha256=str(shared["identity_map_sha256"]),
    )
    challenger_net = int(outcome["gross_points"]) - int(plan["finance"]["hit_cost"])
    canonical_net = int(canonical["gross_points"]) - int(
        canonical_plan["finance"]["hit_cost"]
    )
    result.pop("content_sha256", None)
    result["first_action_evaluation"] = {
        "comparison_type": "realised_isolated_same_starting_state",
        "canonical_plan_sha256": canonical_plan["content_sha256"],
        "challenger_plan_sha256": plan["content_sha256"],
        "canonical_gross_points": int(canonical["gross_points"]),
        "challenger_gross_points": int(outcome["gross_points"]),
        "canonical_net_points": canonical_net,
        "challenger_net_points": challenger_net,
        "net_points_delta": challenger_net - canonical_net,
        "tail_executed": False,
    }
    result["content_sha256"] = multiweek_report_hash(result)
    return result, plan, outcome
