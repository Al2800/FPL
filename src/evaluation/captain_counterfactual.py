"""Captain-only frozen counterfactuals over the sealed historical replay."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.captaincy import choose_captain_pair
from src.orchestration.replay_payload_store import load_reviewed_payload
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import load_rules, ruleset_sha256


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_captain_challenger(
    *,
    reports_root: Path,
    episodes_root: Path,
    config: Mapping[str, Any],
    appearance_calibration: Mapping[str, Any],
    rules_path: Path,
) -> dict[str, Any]:
    """Score captain/vice alternatives with every other decision held fixed."""
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    episodes: list[dict[str, Any]] = []
    for gameweek in range(2, 39):
        report_dir = reports_root / f"gw-{gameweek:02d}"
        episode_dir = episodes_root / f"gw-{gameweek:02d}"
        state = _read(
            report_dir
            / "setup/arms/forecast_optimizer/starting-policy-state.json"
        )
        solver_input = load_reviewed_payload(
            report_dir
            / "setup/arms/forecast_optimizer/reviewed-engine-input.json",
            expected_kind="solver_input",
        )
        solver_output = load_reviewed_payload(
            report_dir
            / "setup/arms/forecast_optimizer/reviewed-engine-output.json",
            expected_kind="solver_output",
        )
        canonical_plan = _read(
            report_dir / "forecast_optimizer/validated-plan.json"
        )
        canonical_outcome = _read(
            report_dir / "forecast_optimizer/realised-outcome.json"
        )
        manifest = _read(episode_dir / "episode-manifest.json")
        hidden = _read(episode_dir / "hidden-outcome.json")
        identity = _read(episode_dir / "identity-map.json")
        shared = _read(report_dir / "shared-context.json")
        market = {
            str(row["player_id"]): row for row in solver_input["players"]
        }
        xi_ids = list(canonical_plan["lineup"]["starting_xi_ids"])
        selection = choose_captain_pair(
            [market[player_id] for player_id in xi_ids],
            config=config,
            appearance_calibration=appearance_calibration,
        )
        canonical_pair = next(
            row
            for row in selection["candidates"]
            if row["captain_id"] == canonical_plan["lineup"]["captain_id"]
            and row["vice_captain_id"]
            == canonical_plan["lineup"]["vice_captain_id"]
        )
        candidate = deepcopy(dict(solver_output["selected"]))
        candidate["lineup"] = deepcopy(dict(candidate["lineup"]))
        candidate["lineup"]["captain_id"] = selection["selected"]["captain_id"]
        candidate["lineup"]["vice_captain_id"] = selection["selected"][
            "vice_captain_id"
        ]
        plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=candidate,
            decision_market=solver_input["players"],
            active_chip=canonical_plan["active_chip"],
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
            revealed_at=str(canonical_outcome["revealed_at"]),
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=identity_index,
            identity_map_sha256=str(shared["identity_map_sha256"]),
        )
        gross_delta = int(outcome["gross_points"]) - int(
            canonical_outcome["gross_points"]
        )
        captain_delta = int(outcome["captain"]["extra_points"]) - int(
            canonical_outcome["captain"]["extra_points"]
        )
        if gross_delta != captain_delta:
            raise ValueError("captain-only counterfactual changed non-captain scoring")
        names = {
            player_id: str(row.get("web_name") or player_id)
            for player_id, row in market.items()
        }
        episodes.append(
            {
                "gameweek": gameweek,
                "canonical_plan_sha256": canonical_plan["content_sha256"],
                "challenger_plan_sha256": plan["content_sha256"],
                "fixed_squad_ids": sorted(
                    row["player_id"] for row in canonical_plan["squad_after"]
                ),
                "fixed_starting_xi_ids": sorted(xi_ids),
                "fixed_bench_ids": list(canonical_plan["lineup"]["bench_ids"]),
                "fixed_transfers": deepcopy(canonical_plan["transfers"]),
                "canonical_captain_id": canonical_plan["lineup"]["captain_id"],
                "canonical_captain_name": names[
                    canonical_plan["lineup"]["captain_id"]
                ],
                "canonical_vice_captain_id": canonical_plan["lineup"][
                    "vice_captain_id"
                ],
                "canonical_vice_captain_name": names[
                    canonical_plan["lineup"]["vice_captain_id"]
                ],
                "canonical_expected_captain_extra": canonical_pair[
                    "expected_captain_extra"
                ],
                "challenger": selection["selected"],
                "challenger_captain_name": names[
                    selection["selected"]["captain_id"]
                ],
                "challenger_vice_captain_name": names[
                    selection["selected"]["vice_captain_id"]
                ],
                "canonical_captain_extra": int(
                    canonical_outcome["captain"]["extra_points"]
                ),
                "challenger_captain_extra": int(
                    outcome["captain"]["extra_points"]
                ),
                "realised_points_delta": gross_delta,
            }
        )
    total_delta = sum(row["realised_points_delta"] for row in episodes)
    report = {
        "schema_version": "1.0",
        "report_id": "captain-v1-2025-26-frozen-counterfactual",
        "policy_config_sha256": config["content_sha256"],
        "appearance_calibration_sha256": appearance_calibration["content_sha256"],
        "comparison_type": "captain_only_realised_same_plan",
        "evaluation_gameweeks": len(episodes),
        "canonical_captain_extra_total": sum(
            row["canonical_captain_extra"] for row in episodes
        ),
        "challenger_captain_extra_total": sum(
            row["challenger_captain_extra"] for row in episodes
        ),
        "canonical_expected_captain_extra_total": round(
            sum(row["canonical_expected_captain_extra"] for row in episodes), 6
        ),
        "challenger_expected_captain_extra_total": round(
            sum(
                row["challenger"]["expected_captain_extra"] for row in episodes
            ),
            6,
        ),
        "realised_points_delta": total_delta,
        "locked_validation": deepcopy(config["locked_validation"]),
        "promotion_eligible": bool(config["locked_validation"]["promotion_eligible"]),
        "decision": (
            "promote" if config["locked_validation"]["promotion_eligible"] else "reject"
        ),
        "episodes": episodes,
    }
    report["content_sha256"] = artifact_hash(report)
    return report
