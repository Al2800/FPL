"""Governed comparison and live-shadow nomination for FPL challengers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint
from src.optimisation.robust_objective import robust_solver_input
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import load_rules, ruleset_sha256


class ChallengerMatrixError(ValueError):
    """Raised when matrix evidence is missing, mutable, or internally unsafe."""


PROMOTION_RULE = {
    "rule_id": "live-shadow-promotion-v1",
    "target": "observation_only_live_shadow",
    "required_gates": [
        "configuration_integrity",
        "episode_integrity",
        "no_known_temporal_leakage",
        "locked_held_out_gate",
        "legal_replay",
        "deterministic_reproduction",
        "bounded_degradation",
        "control_fallback",
    ],
    "disqualifiers": [
        "failed_locked_gate",
        "retrospective_case_selection",
        "historical_schedule_provenance_gap",
        "missing_full_legal_replay",
    ],
    "tie_break_order": [
        "held_out_decision_quality",
        "full_replay_realised_net_points",
        "calibration",
        "lower_operational_cost",
        "challenger_id",
    ],
    "final_season_points_can_override_failed_gate": False,
}


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ChallengerMatrixError(f"required artifact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ChallengerMatrixError(f"artifact must be an object: {path}")
    return value


def _assert_content_hash(value: Mapping[str, Any], label: str) -> str:
    expected = value.get("content_sha256")
    if not isinstance(expected, str) or expected != artifact_hash(value):
        raise ChallengerMatrixError(f"{label} content hash mismatch")
    return expected


def _sealed(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def episode_bindings(
    *, reports_root: Path, episodes_root: Path, gameweeks: Sequence[int]
) -> list[dict[str, Any]]:
    """Bind every comparison row to the same observed and hidden episode bytes."""
    bindings: list[dict[str, Any]] = []
    for gameweek in gameweeks:
        shared = _read(reports_root / f"gw-{gameweek:02d}/shared-context.json")
        manifest = _read(episodes_root / f"gw-{gameweek:02d}/episode-manifest.json")
        if shared["episode_id"] != manifest["episode_id"]:
            raise ChallengerMatrixError(f"GW{gameweek} episode identity mismatch")
        bindings.append(
            {
                "gameweek": gameweek,
                "episode_id": manifest["episode_id"],
                "episode_manifest_sha256": fingerprint(manifest),
                "observed_sha256": shared["observed_sha256"],
                "hidden_outcome_sha256": shared["hidden_outcome_sha256"],
                "ruleset_sha256": shared["ruleset"]["content_sha256"],
            }
        )
    return bindings


def evaluate_robust_legal_replay(
    *,
    reports_root: Path,
    episodes_root: Path,
    config: Mapping[str, Any],
    rules_path: Path,
    gameweeks: Sequence[int] = tuple(range(2, 39)),
) -> dict[str, Any]:
    """Run an isolated, legal robust-selection comparison from canonical states."""
    config_hash = _assert_content_hash(config, "robust-selection config")
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    rows: list[dict[str, Any]] = []
    for gameweek in gameweeks:
        report_dir = reports_root / f"gw-{gameweek:02d}"
        episode_dir = episodes_root / f"gw-{gameweek:02d}"
        arm_setup = report_dir / "setup/arms/forecast_optimizer"
        state = _read(arm_setup / "starting-policy-state.json")
        raw_input = _read(arm_setup / "reviewed-engine-input.json")
        raw_output = _read(arm_setup / "reviewed-engine-output.json")
        forecast = _read(report_dir / "setup/shared-locked-forecast.json")
        canonical_plan = _read(report_dir / "forecast_optimizer/validated-plan.json")
        canonical_outcome = _read(
            report_dir / "forecast_optimizer/realised-outcome.json"
        )
        manifest = _read(episode_dir / "episode-manifest.json")
        hidden = _read(episode_dir / "hidden-outcome.json")
        identity = _read(episode_dir / "identity-map.json")
        shared = _read(report_dir / "shared-context.json")

        adjusted = robust_solver_input(
            raw_input,
            locked_forecast=forecast,
            config=config,
        )
        robust_output = solve(
            SolverInput.from_dict(adjusted),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        candidate = robust_output["selected"]
        plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=candidate,
            decision_market=raw_input["players"],
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
        canonical_net = int(canonical_outcome["gross_points"]) - int(
            canonical_plan["finance"]["hit_cost"]
        )
        challenger_net = int(outcome["gross_points"]) - int(
            plan["finance"]["hit_cost"]
        )
        rows.append(
            {
                "gameweek": gameweek,
                "episode_id": manifest["episode_id"],
                "episode_manifest_sha256": fingerprint(manifest),
                "observed_sha256": shared["observed_sha256"],
                "hidden_outcome_sha256": shared["hidden_outcome_sha256"],
                "raw_solver_input_sha256": fingerprint(raw_input),
                "robust_solver_input_sha256": fingerprint(adjusted),
                "canonical_plan_sha256": canonical_plan["content_sha256"],
                "challenger_plan_sha256": plan["content_sha256"],
                "same_transfers": (
                    canonical_plan["transfers"] == plan["transfers"]
                ),
                "same_starting_xi": (
                    canonical_plan["lineup"]["starting_xi_ids"]
                    == plan["lineup"]["starting_xi_ids"]
                ),
                "same_captain": (
                    canonical_plan["lineup"]["captain_id"]
                    == plan["lineup"]["captain_id"]
                ),
                "canonical_net_points": canonical_net,
                "challenger_net_points": challenger_net,
                "net_points_delta": challenger_net - canonical_net,
                "canonical_objective": raw_output["selected"]["objective"],
                "challenger_objective": candidate["objective"],
            }
        )
    return _sealed(
        {
            "schema_version": "1.0",
            "report_id": "robust-selection-full-legal-isolated-replay",
            "comparison_type": "same_episode_same_starting_state_isolated",
            "model_config_sha256": config_hash,
            "gameweeks": list(gameweeks),
            "episodes": rows,
            "summary": {
                "evaluation_gameweeks": len(rows),
                "changed_transfer_gameweeks": sum(
                    not row["same_transfers"] for row in rows
                ),
                "changed_lineup_gameweeks": sum(
                    not row["same_starting_xi"] for row in rows
                ),
                "changed_captain_gameweeks": sum(
                    not row["same_captain"] for row in rows
                ),
                "canonical_net_points": sum(
                    row["canonical_net_points"] for row in rows
                ),
                "challenger_net_points": sum(
                    row["challenger_net_points"] for row in rows
                ),
                "net_points_delta": sum(row["net_points_delta"] for row in rows),
            },
        }
    )


def apply_promotion_rule(rows: Sequence[Mapping[str, Any]]) -> str | None:
    """Return one shadow nominee; realised final points never rescue a failed gate."""
    eligible: list[Mapping[str, Any]] = []
    required = set(PROMOTION_RULE["required_gates"])
    disqualifiers = set(PROMOTION_RULE["disqualifiers"])
    for row in rows:
        gates = row.get("gates", {})
        blockers = set(row.get("disqualifiers", []))
        if blockers & disqualifiers:
            continue
        if not all(gates.get(gate) is True for gate in required):
            continue
        eligible.append(row)
    if not eligible:
        return None
    eligible.sort(
        key=lambda row: (
            -float(row["selection_metrics"]["held_out_decision_quality"]),
            -float(row["selection_metrics"]["full_replay_realised_net_points"]),
            -float(row["selection_metrics"]["calibration"]),
            float(row["selection_metrics"]["operational_cost"]),
            str(row["challenger_id"]),
        )
    )
    return str(eligible[0]["challenger_id"])


def validate_matrix_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Enforce the audit fields that make matrix rows comparable."""
    if not rows:
        raise ChallengerMatrixError("challenger matrix cannot be empty")
    for row in rows:
        if not isinstance(row.get("configuration_sha256"), str):
            raise ChallengerMatrixError("every row requires a configuration hash")
        bindings = row.get("episode_bindings")
        if not isinstance(bindings, list) or not bindings:
            raise ChallengerMatrixError("every row requires episode bindings")
        for binding in bindings:
            for key in (
                "episode_manifest_sha256",
                "observed_sha256",
                "hidden_outcome_sha256",
            ):
                if not isinstance(binding.get(key), str):
                    raise ChallengerMatrixError(
                        f"every episode binding requires {key}"
                    )


def build_live_shadow_candidate(
    *,
    nominee: str,
    rows: Sequence[Mapping[str, Any]],
    control_model_sha256: str,
) -> dict[str, Any]:
    selected = next(row for row in rows if row["challenger_id"] == nominee)
    return _sealed(
        {
            "schema_version": "1.0",
            "policy_id": "live-shadow-candidate-2026-27-v1",
            "mode": "observation_only_no_fpl_execution",
            "executable_policy": {
                "policy_id": "live-faithful-v1-control",
                "model_config_sha256": control_model_sha256,
            },
            "shadow_policy": {
                "challenger_id": nominee,
                "configuration_sha256": selected["configuration_sha256"],
            },
            "promotion_rule": PROMOTION_RULE,
            "fallback": {
                "policy_id": "live-faithful-v1-control",
                "on_timeout": True,
                "on_missing_inputs": True,
                "on_validation_failure": True,
            },
            "prohibitions": [
                "must_not_submit_actions_to_fpl",
                "must_not_delay_control_deadline",
                "must_not_train_on_live_outcomes_before_freeze",
            ],
        }
    )
