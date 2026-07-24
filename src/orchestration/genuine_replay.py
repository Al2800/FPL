"""Chronological, checkpointed replay over immutable historical episodes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.replay_adapter import build_replay_solver_input
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.historical_feature_state import (
    build_feature_state,
    feature_state_hash,
)
from src.orchestration.policy_state import (
    POLICY_ARMS,
    initialise_policy_states,
    transition_policy_state,
)
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.reporting.decision_record import build_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256


class GenuineReplayError(ValueError):
    """Raised when a historical checkpoint cannot be reproduced safely."""


TRANSFER_VALUE_POLICY = "expected_hit_avoidance_v1"
PROBABILITY_EXTRA_TRANSFER_NEEDED = 0.5
FUTURE_TRANSFER_DISCOUNT = 0.9
REPO = Path(__file__).resolve().parents[2]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GenuineReplayError(f"Required replay artefact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GenuineReplayError(f"Replay artefact must be an object: {path}")
    return value


def _load_observed_episode(directory: Path) -> dict[str, dict[str, Any]]:
    bundle = {
        "manifest": _read_json(directory / "episode-manifest.json"),
        "observed": _read_json(directory / "observed.json"),
        "identity": _read_json(directory / "identity-map.json"),
    }
    manifest = bundle["manifest"]
    if manifest["observed"]["feature_snapshot_ref"]["content_sha256"] != _stable_hash(
        bundle["observed"]
    ):
        raise GenuineReplayError("Observed partition hash differs from manifest")
    identity_hash = _stable_hash(bundle["identity"])
    if bundle["observed"]["identity_map_ref"]["content_sha256"] != identity_hash:
        raise GenuineReplayError("Identity-map hash differs from observed partition")
    rules_path = directory / "ruleset.yaml"
    if ruleset_sha256(rules_path) != manifest["ruleset"]["content_sha256"]:
        raise GenuineReplayError("Ruleset hash differs from manifest")
    bundle["rules"] = load_rules(rules_path)
    return bundle


def _load_episode(directory: Path) -> dict[str, dict[str, Any]]:
    bundle = _load_observed_episode(directory)
    bundle["hidden"] = _read_json(directory / "hidden-outcome.json")
    if bundle["manifest"]["hidden_outcome_ref"][
        "content_sha256"
    ] != _stable_hash(bundle["hidden"]):
        raise GenuineReplayError("Hidden outcome hash differs from manifest")
    return bundle


def _market(feature_state: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for player in feature_state["players"]:
        quote = player.get("quote") or {}
        if "now_cost" not in quote:
            continue
        player_id = str(player["player_id"])
        result[player_id] = {
            "player_id": player_id,
            "position": str(player["position"]),
            "club_id": str(player["club_id"]),
            "now_cost": round(float(quote["now_cost"]), 1),
            "expected_points": round(
                float(player["projection"]["expected_points"]), 2
            ),
            "status": "a",
        }
    return result


def _identity_index(identity_map: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in identity_map["players"]:
        source = str(row["fpl_player_id"])
        target = str(row["canonical_id"])
        if source in result or target in result.values():
            raise GenuineReplayError("Player identity map is not one-to-one")
        result[source] = target
    return result


def _reveal_time(hidden: Mapping[str, Any], fallback: str) -> str:
    kickoffs = [
        datetime.fromisoformat(str(row["kickoff_time"]).replace("Z", "+00:00"))
        for row in hidden.get("fixtures", [])
        if row.get("kickoff_time")
    ]
    if not kickoffs:
        return fallback
    return (max(kickoffs) + timedelta(hours=4)).isoformat().replace("+00:00", "Z")


def _gw1_candidate(seed: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    initial = seed["initial_plan"]
    squad = {str(row["player_id"]): row for row in state["squad"]}
    xi_ids = [str(player_id) for player_id in initial["starting_xi_ids"]]
    formation_counts = Counter(squad[player_id]["position"] for player_id in xi_ids)
    return {
        "strategy": "controlled_official_scout_seed",
        "transfers": [],
        "bank_after": float(state["bank"]),
        "hit_cost": 0,
        "lineup": {
            "formation": {
                position: int(formation_counts[position])
                for position in ("DEF", "MID", "FWD")
            },
            "starting_xi_ids": xi_ids,
            "bench_ids": [str(player_id) for player_id in initial["bench_ids"]],
            "captain_id": str(initial["captain_id"]),
            "vice_captain_id": str(initial["vice_captain_id"]),
        },
    }


def _decision_record(
    *,
    manifest: Mapping[str, Any],
    feature_state: Mapping[str, Any],
    state: Mapping[str, Any],
    plan: Mapping[str, Any],
    outcome: Mapping[str, Any],
    transition: Mapping[str, Any],
    seed: Mapping[str, Any],
) -> dict[str, Any]:
    names = {
        str(row["player_id"]): str(row["web_name"])
        for row in seed["squad"]
    }
    recommendation = {
        "strategy": "controlled_official_scout_seed",
        "objective": 0.0,
        "captain_name": names[plan["lineup"]["captain_id"]],
        "vice_captain_name": names[plan["lineup"]["vice_captain_id"]],
        "validated_plan_sha256": plan["content_sha256"],
    }
    return build_decision_record(
        {
            "record_id": (
                f"gdr:{manifest['season']}:gw{manifest['gameweek']:02d}:"
                f"{state['policy_arm']}"
            ),
            "gameweek": int(manifest["gameweek"]),
            "season": str(manifest["season"]),
            "fixture_id": str(manifest["episode_id"]),
            "decision_cutoff": str(manifest["cutoff"]),
            "deadline": str(manifest["deadline"]),
            "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            "validated_plan": deepcopy(dict(plan)),
            "data_quality": "Degraded structured replay; governed official GW1 seed",
            "degraded": True,
            "manager_state": {
                "bank": state["bank"],
                "free_transfers": state["free_transfers"],
                "chips_available": list(state["chips_available"]),
                "squad_player_ids": [
                    row["player_id"] for row in state["squad"]
                ],
            },
            "projections_summary": {
                "n_players": len(feature_state["players"]),
                "model_versions": [
                    feature_state["lineage"]["model_version"]
                ],
                "principal_uncertainty": (
                    "GW1 uses the pre-deadline official Scout plan because no "
                    "completed prior Gameweek exists"
                ),
            },
            "candidate_plans": [
                {
                    "strategy": "controlled_official_scout_seed",
                    "objective": 0.0,
                    "hit_cost": 0,
                    "transfers": [],
                }
            ],
            "recommendation": recommendation,
            "baseline_comparison": {
                "do_nothing_objective": 0.0,
                "recommended_objective": 0.0,
                "expected_advantage": 0.0,
                "notes": "All arms share the governed GW1 seed; divergence begins GW2",
            },
            "alternatives": {"conservative": None, "aggressive": None},
            "evidence": {
                "supporting_claim_ids": [
                    source["source_url"] for source in seed["evidence"]
                ],
                "conflicting_claim_ids": [],
                "conflict_ids": [],
                "proposed_adjustment_ids": [],
            },
            "validation": {
                "squad": {"ok": True},
                "lineup": {"ok": True},
                "chips_ok": True,
                "validated_plan_sha256": plan["content_sha256"],
            },
            "approval": {
                "status": "approved",
                "approver": "controlled_seed_policy",
                "notes": "Published pre-deadline official Scout seed",
            },
            "execution": {
                "mode": "dry_run",
                "notes": "Historical replay; no external account action",
            },
            "outcome": {
                "points": outcome["gross_points"],
                "notes": "Official hidden outcome revealed after plan freeze",
                "finalised_at": outcome["revealed_at"],
            },
            "retrospective": {
                "process_notes": "GW1 controlled shared-seed checkpoint",
                "lessons": list(feature_state["limitations"]),
                "metrics": {
                    "gross_points": outcome["gross_points"],
                    "net_points": transition["net_points"],
                    "substitutions": len(outcome["substitutions"]),
                },
            },
            "confidence": "Controlled seed; no statistical GW1 projection",
            "principal_uncertainty": (
                "Historical seed is an official editorial benchmark, not a "
                "reconstructed manager account"
            ),
            "observed_at": str(manifest["cutoff"]),
            "available_at": str(manifest["cutoff"]),
            "finalised_at": str(outcome["revealed_at"]),
            "provenance": {
                "source_ids": [
                    "benchmark-v0-observed",
                    "premier-league-official-editorial",
                ],
                "transformation_version": "genuine-replay-v1",
                "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            },
        },
        validate=True,
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise GenuineReplayError(
                f"Existing replay artefact differs; refusing overwrite: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _policy_brief(
    *,
    arm: str,
    manifest: Mapping[str, Any],
    state: Mapping[str, Any],
    feature_state: Mapping[str, Any],
    solver_input_sha256: str,
    solver_output_sha256: str,
    solver_output: Mapping[str, Any],
) -> dict[str, Any]:
    selected = solver_output["selected"]
    no_transfer = solver_output["plans"]["no_transfer"]
    common = {
        "schema_version": "1.0",
        "policy_arm": arm,
        "season": manifest["season"],
        "gameweek": manifest["gameweek"],
        "episode_id": manifest["episode_id"],
        "status": "prepared_awaiting_policy_proposal",
        "outcome_access": "sealed_not_loaded",
        "proposal_frozen": False,
        "starting_state_sha256": state["content_sha256"],
        "observed_sha256": manifest["observed"]["feature_snapshot_ref"][
            "content_sha256"
        ],
        "feature_state_sha256": feature_state["content_sha256"],
        "solver_input_sha256": solver_input_sha256,
        "solver_output_sha256": solver_output_sha256,
        "shared_engine_baseline": {
            "selected_strategy": selected["strategy"],
            "objective": selected["objective"],
            "immediate_objective": selected.get(
                "immediate_objective", selected["objective"]
            ),
            "transfer_option_value": selected.get("transfer_option_value", 0.0),
            "transfers": selected["transfers"],
            "lineup": selected["lineup"],
            "no_transfer_objective": no_transfer["objective"],
            "candidate_count": solver_output["n_candidates"],
        },
    }
    policies = {
        "naive_baseline": {
            "execution_mode": "deterministic",
            "decision_rule": (
                "Use the engine's no-transfer lineup and bank available "
                "transfers; never inspect agent evidence."
            ),
            "proposed_source": "shared_engine_baseline.no_transfer",
            "fallback": None,
            "review_gate": "confirm_naive_rule_before_freeze",
        },
        "forecast_optimizer": {
            "execution_mode": "deterministic",
            "decision_rule": (
                "Use the highest expected-points legal plan in the declared "
                "candidate pool."
            ),
            "proposed_source": "shared_engine_baseline.selected",
            "fallback": None,
            "review_gate": "inspect_selected_plan_before_freeze",
        },
        "evidence_agent": {
            "execution_mode": "degraded_historical_evidence",
            "decision_rule": (
                "Receive the identical engine baseline and permit only cited, "
                "pre-deadline evidence adjustments."
            ),
            "proposed_source": "awaiting_bounded_agent_run",
            "fallback": "shared_engine_baseline.selected",
            "review_gate": "decide_admissible_gw2_evidence_before_agent_run",
        },
        "evidence_challenger": {
            "execution_mode": "degraded_historical_evidence",
            "decision_rule": (
                "Review the evidence-agent proposal against the same engine "
                "baseline and evidence cutoff; record accept, amend or reject."
            ),
            "proposed_source": "awaiting_agent_then_challenger",
            "fallback": "shared_engine_baseline.selected",
            "review_gate": "decide_admissible_gw2_evidence_before_agent_run",
        },
        "human_decision": {
            "execution_mode": "historical_record_required",
            "decision_rule": (
                "Use only a demonstrably pre-deadline recorded human choice "
                "from this observed episode."
            ),
            "proposed_source": "unavailable_pending_historical_record",
            "fallback": None,
            "review_gate": (
                "exclude_or_mark_missing; do_not_reconstruct_with_hindsight"
            ),
        },
    }
    common["policy"] = policies[arm]
    common["content_sha256"] = fingerprint(common)
    return common


def prepare_historical_gameweek(
    *,
    season: str,
    gameweek: int,
    episode_root: Path,
    previous_checkpoint_dir: Path,
    output_root: Path,
    code_commit: str,
) -> dict[str, Any]:
    """Prepare a sealed policy workspace without reading the outcome payload."""

    if gameweek < 2:
        raise GenuineReplayError(
            "Historical setup requires a completed predecessor Gameweek"
        )
    if len(code_commit) != 40:
        raise GenuineReplayError("code_commit must be a full 40-character Git SHA")

    current = _load_observed_episode(episode_root / f"gw-{gameweek:02d}")
    manifest = current["manifest"]
    if manifest["season"] != season or manifest["gameweek"] != gameweek:
        raise GenuineReplayError("Episode root does not contain requested Gameweek")

    if gameweek == 2:
        gw1 = _load_observed_episode(episode_root / "gw-01")
        seed_path = (
            REPO
            / "control"
            / "seeds"
            / season
            / "official-scout-gw1.json"
        )
        seed = _read_json(seed_path)
        previous_feature = build_feature_state(
            episode_manifest=gw1["manifest"],
            observed=gw1["observed"],
            identity_map=gw1["identity"],
            seed=seed,
        )
    else:
        previous_feature = _read_json(
            previous_checkpoint_dir / "setup" / "shared-feature-state.json"
        )
        if previous_feature.get("content_sha256") != feature_state_hash(
            previous_feature
        ):
            raise GenuineReplayError(
                "Previous checkpoint feature-state hash mismatch"
            )
    feature_current = build_feature_state(
        episode_manifest=manifest,
        observed=current["observed"],
        identity_map=current["identity"],
        previous_state=previous_feature,
    )

    previous_summary = _read_json(previous_checkpoint_dir / "run-summary.json")
    if previous_summary["next_feature_state_sha256"] != feature_current[
        "content_sha256"
    ]:
        raise GenuineReplayError(
            "Feature state differs from the prior checkpoint handoff"
        )

    rules = current["rules"]
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    states: dict[str, dict[str, Any]] = {}
    inputs: dict[str, dict[str, Any]] = {}
    input_hashes: set[str] = set()
    for arm in POLICY_ARMS:
        state = _read_json(
            previous_checkpoint_dir / arm / "next-policy-state.json"
        )
        expected_hash = previous_summary["arms"][arm]["next_state_sha256"]
        if state["content_sha256"] != expected_hash:
            raise GenuineReplayError(
                f"Opening state differs from prior summary for {arm}"
            )
        if state["policy_arm"] != arm or state["gameweek"] != gameweek:
            raise GenuineReplayError(f"Opening state identity mismatch for {arm}")
        solver_input = build_replay_solver_input(
            feature_state=feature_current,
            policy_state=state,
            max_transfers=3,
            transfer_value_policy=TRANSFER_VALUE_POLICY,
            probability_extra_transfer_needed=(
                PROBABILITY_EXTRA_TRANSFER_NEEDED
            ),
            future_transfer_discount=FUTURE_TRANSFER_DISCOUNT,
        )
        input_value = solver_input.as_dict()
        states[arm] = state
        inputs[arm] = input_value
        input_hashes.add(fingerprint(input_value))
    input_sha256 = {arm: fingerprint(inputs[arm]) for arm in POLICY_ARMS}
    output_cache: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    for arm in POLICY_ARMS:
        input_hash = input_sha256[arm]
        if input_hash not in output_cache:
            output_cache[input_hash] = solve(
                SolverInput.from_dict(inputs[arm]),
                rules=rules,
                ruleset_sha256=rules_hash,
            )
        outputs[arm] = output_cache[input_hash]
    output_sha256 = {arm: fingerprint(outputs[arm]) for arm in POLICY_ARMS}
    shared_engine = len(input_hashes) == 1
    engine_output = outputs[POLICY_ARMS[0]]

    setup_dir = output_root / f"gw-{gameweek:02d}" / "setup"
    _write_json(setup_dir / "shared-feature-state.json", feature_current)
    if shared_engine:
        _write_json(
            setup_dir / "shared-engine-input.json", inputs[POLICY_ARMS[0]]
        )
        _write_json(setup_dir / "shared-engine-output.json", engine_output)
    brief_hashes: dict[str, str] = {}
    for arm in POLICY_ARMS:
        arm_dir = setup_dir / "arms" / arm
        _write_json(arm_dir / "engine-input.json", inputs[arm])
        _write_json(arm_dir / "engine-output.json", outputs[arm])
        brief = _policy_brief(
            arm=arm,
            manifest=manifest,
            state=states[arm],
            feature_state=feature_current,
            solver_input_sha256=input_sha256[arm],
            solver_output_sha256=output_sha256[arm],
            solver_output=outputs[arm],
        )
        _write_json(arm_dir / "starting-policy-state.json", states[arm])
        _write_json(arm_dir / "decision-brief.json", brief)
        brief_hashes[arm] = brief["content_sha256"]

    selected = engine_output["selected"]
    no_transfer = engine_output["plans"]["no_transfer"]
    history_gameweeks = sorted(
        {
            int(row["gameweek"])
            for player in feature_current["players"]
            for row in player["history"]
        }
    )
    cold_start_blocked = len(history_gameweeks) < 3
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "status": (
            "prepared_review_blocked"
            if cold_start_blocked
            else "prepared_not_frozen"
        ),
        "season": season,
        "gameweek": gameweek,
        "episode_id": manifest["episode_id"],
        "code_commit": code_commit,
        "outcome_access": "sealed_not_loaded",
        "contains_hidden_outcome": False,
        "contains_validated_plan": False,
        "contains_state_transition": False,
        "observed_sha256": manifest["observed"]["feature_snapshot_ref"][
            "content_sha256"
        ],
        "feature_state_sha256": feature_current["content_sha256"],
        "ruleset": deepcopy(manifest["ruleset"]),
        "shared_engine_input": shared_engine,
        "solver_input_sha256": (
            input_sha256[POLICY_ARMS[0]] if shared_engine else input_sha256
        ),
        "solver_output_sha256": (
            output_sha256[POLICY_ARMS[0]] if shared_engine else output_sha256
        ),
        "candidate_count": engine_output["n_candidates"],
        "projection_diagnostics": {
            "model_version": feature_current["lineage"]["model_version"],
            "completed_history_gameweeks": history_gameweeks,
            "history_gameweek_count": len(history_gameweeks),
            "configured_rolling_window": 3,
            "maximum_player_expected_points": max(
                float(player["projection"]["expected_points"])
                for player in feature_current["players"]
            ),
            "cold_start_risk": (
                "severe_single_gameweek_outcome_chasing"
                if cold_start_blocked
                else "rolling_window_populated"
            ),
            "freeze_recommendation": (
                "blocked_pending_prior_or_shrinkage_policy"
                if cold_start_blocked
                else "eligible_for_policy_review"
            ),
        },
        "engine_selected": {
            "objective": selected["objective"],
            "immediate_objective": selected.get(
                "immediate_objective", selected["objective"]
            ),
            "transfer_option_value": selected.get("transfer_option_value", 0.0),
            "transfers": selected["transfers"],
            "lineup": selected["lineup"],
        },
        "engine_no_transfer": {
            "objective": no_transfer["objective"],
            "immediate_objective": no_transfer.get(
                "immediate_objective", no_transfer["objective"]
            ),
            "transfer_option_value": no_transfer.get(
                "transfer_option_value", 0.0
            ),
            "transfers": no_transfer["transfers"],
            "lineup": no_transfer["lineup"],
        },
        "policy_brief_sha256": brief_hashes,
        "review_gates": [
            "resolve early-season projection prior and shrinkage policy",
            "confirm naive no-transfer policy",
            "inspect forecast-optimiser transfer and lineup",
            "define admissible pre-deadline historical evidence",
            "decide treatment of unavailable historical human choice",
        ],
        "limitations": feature_current["limitations"],
    }
    summary["content_sha256"] = fingerprint(summary)
    _write_json(setup_dir / "setup-summary.json", summary)
    return summary


def _load_reviewed_gw2_setup(
    setup_dir: Path,
    *,
    previous_summary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    feature_state = _read_json(setup_dir / "shared-feature-state.json")
    solver_input = _read_json(setup_dir / "shared-option-value-engine-input.json")
    solver_output = _read_json(setup_dir / "shared-option-value-engine-output.json")
    comparison = _read_json(setup_dir / "forecast-option-value-comparison.json")
    review = _read_json(setup_dir / "transfer-option-value-review.json")
    if feature_state.get("content_sha256") != feature_state_hash(feature_state):
        raise GenuineReplayError("Reviewed GW2 feature-state hash mismatch")
    if (
        feature_state["content_sha256"]
        != previous_summary["next_feature_state_sha256"]
    ):
        raise GenuineReplayError(
            "Reviewed GW2 feature state differs from the GW1 handoff"
        )
    if comparison.get("content_sha256") != artifact_hash(comparison):
        raise GenuineReplayError("Reviewed GW2 comparison hash mismatch")
    if review.get("content_sha256") != artifact_hash(review):
        raise GenuineReplayError("Reviewed GW2 policy-review hash mismatch")
    if review.get("comparison_sha256") != comparison["content_sha256"]:
        raise GenuineReplayError("GW2 review does not bind the comparison")
    lineage = comparison.get("lineage", {})
    if lineage.get("solver_input_sha256") != fingerprint(solver_input):
        raise GenuineReplayError("Reviewed GW2 solver-input hash mismatch")
    if lineage.get("solver_output_sha256") != fingerprint(solver_output):
        raise GenuineReplayError("Reviewed GW2 solver-output hash mismatch")
    if solver_input.get("transfer_value_policy") != TRANSFER_VALUE_POLICY:
        raise GenuineReplayError("Reviewed GW2 transfer-value policy mismatch")
    if solver_input.get("probability_extra_transfer_needed") != (
        PROBABILITY_EXTRA_TRANSFER_NEEDED
    ):
        raise GenuineReplayError("Reviewed GW2 transfer-need probability mismatch")
    if solver_input.get("future_transfer_discount") != FUTURE_TRANSFER_DISCOUNT:
        raise GenuineReplayError("Reviewed GW2 transfer discount mismatch")
    if review.get("assessment", {}).get("policy_is_fitted_on_gw2") is not False:
        raise GenuineReplayError("Reviewed GW2 policy provenance is not admissible")
    if any(
        artifact.get(flag) is not False
        for artifact in (comparison, review)
        for flag in (
            "contains_hidden_outcome",
            "contains_validated_plan",
            "contains_state_transition",
        )
    ):
        raise GenuineReplayError("Reviewed GW2 setup crosses the freeze boundary")
    return feature_state, solver_input, solver_output


def _load_reviewed_gameweek_setup(
    setup_dir: Path,
    *,
    season: str,
    gameweek: int,
    previous_summary: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    """Load a reviewed setup without weakening the legacy GW2 contract."""
    if gameweek == 2:
        feature_state, solver_input, solver_output = _load_reviewed_gw2_setup(
            setup_dir,
            previous_summary=previous_summary,
        )
        states = {
            arm: _read_json(
                setup_dir / "arms" / arm / "starting-policy-state.json"
            )
            for arm in POLICY_ARMS
        }
        return (
            feature_state,
            states,
            {arm: deepcopy(solver_input) for arm in POLICY_ARMS},
            {arm: deepcopy(solver_output) for arm in POLICY_ARMS},
        )

    feature_state = _read_json(setup_dir / "shared-feature-state.json")
    forecast = _read_json(setup_dir / "shared-locked-forecast.json")
    summary = _read_json(setup_dir / "forecast-review-summary.json")
    if feature_state.get("content_sha256") != feature_state_hash(feature_state):
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} feature-state hash mismatch"
        )
    if (
        feature_state["content_sha256"]
        != previous_summary["next_feature_state_sha256"]
    ):
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} feature state differs from the prior handoff"
        )
    if summary.get("content_sha256") != artifact_hash(summary):
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} setup-summary hash mismatch"
        )
    if summary.get("season") != season or summary.get("gameweek") != gameweek:
        raise GenuineReplayError(
            f"Reviewed setup is not {season} GW{gameweek}"
        )
    if summary.get("feature_state_sha256") != feature_state["content_sha256"]:
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} summary does not bind the feature state"
        )
    if summary.get("forecast_sha256") != artifact_hash(forecast):
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} summary does not bind the forecast"
        )
    if any(
        summary.get(flag) is not False
        for flag in (
            "contains_hidden_outcome",
            "contains_validated_plan",
            "contains_state_transition",
        )
    ):
        raise GenuineReplayError(
            f"Reviewed GW{gameweek} setup crosses the freeze boundary"
        )

    states: dict[str, dict[str, Any]] = {}
    solver_inputs: dict[str, dict[str, Any]] = {}
    solver_outputs: dict[str, dict[str, Any]] = {}
    for arm in POLICY_ARMS:
        arm_dir = setup_dir / "arms" / arm
        state = _read_json(arm_dir / "starting-policy-state.json")
        solver_input = _read_json(arm_dir / "reviewed-engine-input.json")
        solver_output = _read_json(arm_dir / "reviewed-engine-output.json")
        review = _read_json(arm_dir / "forecast-plan-review.json")
        arm_summary = summary.get("arms", {}).get(arm, {})
        if review.get("content_sha256") != artifact_hash(review):
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} plan-review hash mismatch for {arm}"
            )
        if state.get("content_sha256") != arm_summary.get("state_sha256"):
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} state hash mismatch for {arm}"
            )
        if state.get("policy_arm") != arm or state.get("gameweek") != gameweek:
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} state identity mismatch for {arm}"
            )
        if review.get("state_sha256") != state["content_sha256"]:
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} review does not bind state for {arm}"
            )
        if review.get("feature_state_sha256") != feature_state["content_sha256"]:
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} review does not bind features for {arm}"
            )
        if review.get("forecast_sha256") != summary["forecast_sha256"]:
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} review does not bind forecast for {arm}"
            )
        if review.get("lineage", {}).get(
            "solver_input_sha256"
        ) != fingerprint(solver_input):
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} solver-input hash mismatch for {arm}"
            )
        if review.get("lineage", {}).get(
            "solver_output_sha256"
        ) != fingerprint(solver_output):
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} solver-output hash mismatch for {arm}"
            )
        if arm_summary.get("review_sha256") != review["content_sha256"]:
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} summary review mismatch for {arm}"
            )
        if any(
            review.get(flag) is not False
            for flag in (
                "contains_hidden_outcome",
                "contains_validated_plan",
                "contains_state_transition",
            )
        ):
            raise GenuineReplayError(
                f"Reviewed GW{gameweek} arm crosses the freeze boundary: {arm}"
            )
        states[arm] = state
        solver_inputs[arm] = solver_input
        solver_outputs[arm] = solver_output
    return feature_state, states, solver_inputs, solver_outputs


def _load_outcomes_after_all_plans_freeze(
    episode_dir: Path,
    *,
    frozen_plans: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if set(frozen_plans) != set(POLICY_ARMS):
        raise GenuineReplayError(
            "Hidden outcome access requires one frozen plan for every policy arm"
        )
    if any(
        plan.get("validation", {}).get("status") != "passed"
        or not plan.get("content_sha256")
        or not plan.get("frozen_at")
        for plan in frozen_plans.values()
    ):
        raise GenuineReplayError(
            "Hidden outcome access requires validated, frozen policy plans"
        )
    return _load_episode(episode_dir)


def _replay_strategy(arm: str) -> str:
    return {
        "naive_baseline": "do_nothing_bank_transfers",
        "forecast_optimizer": "live_faithful_option_value",
        "evidence_agent": "structured_fallback_no_admissible_evidence",
        "evidence_challenger": (
            "structured_fallback_no_admissible_challenger_evidence"
        ),
        "human_decision": "structured_fallback_no_recorded_human_choice",
    }[arm]


def select_policy_candidate(
    arm: str, solver_output: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the reviewed candidate that the policy arm will actually freeze."""
    if arm not in POLICY_ARMS:
        raise GenuineReplayError(f"Unknown replay policy arm: {arm}")
    candidate = (
        solver_output["plans"]["no_transfer"]
        if arm == "naive_baseline"
        else solver_output["selected"]
    )
    return deepcopy(dict(candidate))


def _replay_decision_record(
    *,
    manifest: Mapping[str, Any],
    feature_state: Mapping[str, Any],
    state: Mapping[str, Any],
    plan: Mapping[str, Any],
    outcome: Mapping[str, Any],
    transition: Mapping[str, Any],
    solver_input: Mapping[str, Any],
    solver_output: Mapping[str, Any],
) -> dict[str, Any]:
    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in solver_input["players"]
    }
    no_transfer = solver_output["plans"]["no_transfer"]
    strategy = _replay_strategy(str(state["policy_arm"]))
    recommended = select_policy_candidate(
        str(state["policy_arm"]), solver_output
    )
    selected_objective = float(recommended["objective"])
    no_transfer_objective = float(no_transfer["objective"])
    candidates = [
        {
            "strategy": f"{count}_transfers",
            "objective": float(candidate["objective"]),
            "hit_cost": int(candidate["hit_cost"]),
            "transfers": deepcopy(candidate["transfers"]),
        }
        for count, candidate in solver_output["best_by_transfer_count"].items()
    ]
    return build_decision_record(
        {
            "record_id": (
                f"gdr:{manifest['season']}:gw{manifest['gameweek']:02d}:"
                f"{state['policy_arm']}"
            ),
            "gameweek": int(manifest["gameweek"]),
            "season": str(manifest["season"]),
            "fixture_id": str(manifest["episode_id"]),
            "decision_cutoff": str(manifest["cutoff"]),
            "deadline": str(manifest["deadline"]),
            "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            "validated_plan": deepcopy(dict(plan)),
            "data_quality": (
                "Locked structured forecast; historical unstructured evidence "
                "and recorded human choice unavailable"
            ),
            "degraded": True,
            "manager_state": {
                "bank": state["bank"],
                "free_transfers": state["free_transfers"],
                "chips_available": list(state["chips_available"]),
                "squad_player_ids": [
                    row["player_id"] for row in state["squad"]
                ],
            },
            "projections_summary": {
                "n_players": len(solver_input["players"]),
                "model_versions": ["live-faithful-v1"],
                "principal_uncertainty": (
                    "Transfer flexibility uses an explicit expected-hit-"
                    "avoidance bridge rather than future player forecasts"
                ),
            },
            "candidate_plans": candidates,
            "recommendation": {
                "strategy": strategy,
                "objective": selected_objective,
                "captain_name": names[plan["lineup"]["captain_id"]],
                "vice_captain_name": names[
                    plan["lineup"]["vice_captain_id"]
                ],
                "validated_plan_sha256": plan["content_sha256"],
            },
            "baseline_comparison": {
                "do_nothing_objective": no_transfer_objective,
                "recommended_objective": selected_objective,
                "expected_advantage": round(
                    selected_objective - no_transfer_objective, 4
                ),
                "notes": (
                    "Planning objectives include the declared transfer-option "
                    "term; immediate objectives remain in the solver artefact"
                ),
            },
            "alternatives": {
                "conservative": deepcopy(
                    solver_output["best_by_transfer_count"].get("0")
                ),
                "aggressive": deepcopy(
                    solver_output["best_by_transfer_count"].get("2")
                ),
            },
            "evidence": {
                "supporting_claim_ids": [],
                "conflicting_claim_ids": [],
                "conflict_ids": [],
                "proposed_adjustment_ids": [],
            },
            "validation": {
                "squad": {"ok": True},
                "lineup": {"ok": True},
                "chips_ok": True,
                "validated_plan_sha256": plan["content_sha256"],
            },
            "approval": {
                "status": "approved",
                "approver": "reviewed_structured_replay_policy",
                "notes": (
                    "No post-deadline evidence; evidence/human arms use the "
                    "declared structured fallback"
                ),
            },
            "execution": {
                "mode": "dry_run",
                "notes": "Historical replay; no external account action",
            },
            "outcome": {
                "points": outcome["gross_points"],
                "notes": "Official hidden outcome revealed after all arm freezes",
                "finalised_at": outcome["revealed_at"],
            },
            "retrospective": {
                "process_notes": (
                    f"Reviewed GW{manifest['gameweek']} chronological checkpoint"
                ),
                "lessons": list(feature_state["limitations"]),
                "metrics": {
                    "gross_points": outcome["gross_points"],
                    "net_points": transition["net_points"],
                    "substitutions": len(outcome["substitutions"]),
                },
            },
            "confidence": "Locked structured forecast with explicit option-value policy",
            "principal_uncertainty": (
                "No admissible historical press, injury, odds, agent or human "
                "proposal was available for this checkpoint"
            ),
            "observed_at": str(manifest["cutoff"]),
            "available_at": str(manifest["cutoff"]),
            "finalised_at": str(outcome["revealed_at"]),
            "provenance": {
                "source_ids": [
                    "benchmark-v0-observed",
                    "live-faithful-v1-locked",
                    "expected-hit-avoidance-v1",
                ],
                "transformation_version": "genuine-replay-v2",
                "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            },
        },
        validate=True,
    )


def finalise_historical_gameweek(
    *,
    season: str,
    gameweek: int,
    episode_root: Path,
    output_root: Path,
    code_commit: str,
    reviewed_setup_dir: Path | None = None,
) -> dict[str, Any]:
    """Freeze, reveal, score and transition one reviewed checkpoint."""
    if len(code_commit) != 40:
        raise GenuineReplayError("code_commit must be a full 40-character Git SHA")
    if gameweek < 2:
        raise GenuineReplayError("Reviewed finalisation begins at GW2")
    previous_dir = output_root / f"gw-{gameweek - 1:02d}"
    previous_summary = _read_json(previous_dir / "run-summary.json")
    if previous_summary.get("next_state_gameweek") != gameweek:
        raise GenuineReplayError(
            f"GW{gameweek - 1} checkpoint does not hand off to GW{gameweek}"
        )
    setup_dir = reviewed_setup_dir or (
        REPO
        / "reports"
        / "benchmarks"
        / season
        / f"gw-{gameweek:02d}"
        / "setup"
    )
    feature_state, reviewed_states, solver_inputs, solver_outputs = (
        _load_reviewed_gameweek_setup(
            setup_dir,
            season=season,
            gameweek=gameweek,
            previous_summary=previous_summary,
        )
    )
    observed_episode = _load_observed_episode(
        episode_root / f"gw-{gameweek:02d}"
    )
    manifest = observed_episode["manifest"]
    if manifest["season"] != season or manifest["gameweek"] != gameweek:
        raise GenuineReplayError(
            f"Episode root does not contain requested GW{gameweek}"
        )
    rules = observed_episode["rules"]
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    decision_markets: dict[str, dict[str, dict[str, Any]]] = {}
    frozen_plans: dict[str, dict[str, Any]] = {}
    states: dict[str, dict[str, Any]] = {}
    for arm in POLICY_ARMS:
        solver_input = solver_inputs[arm]
        solver_output = solver_outputs[arm]
        if (
            solver_input.get("season") != season
            or solver_input.get("gameweek") != gameweek
        ):
            raise GenuineReplayError(
                f"Reviewed solver input is not {season} GW{gameweek} for {arm}"
            )
        state = reviewed_states[arm]
        if state["content_sha256"] != previous_summary["arms"][arm][
            "next_state_sha256"
        ]:
            raise GenuineReplayError(
                f"GW{gameweek} opening state hash mismatch for {arm}"
            )
        prior_state = _read_json(previous_dir / arm / "next-policy-state.json")
        if state != prior_state:
            raise GenuineReplayError(
                f"GW{gameweek} reviewed state differs from prior handoff for {arm}"
            )
        if state["policy_arm"] != arm or state["gameweek"] != gameweek:
            raise GenuineReplayError(
                f"GW{gameweek} opening state identity mismatch for {arm}"
            )
        if sorted(row["player_id"] for row in state["squad"]) != sorted(
            solver_input["squad_player_ids"]
        ):
            raise GenuineReplayError(f"Reviewed solver squad differs for {arm}")
        decision_market = {
            str(row["player_id"]): dict(row) for row in solver_input["players"]
        }
        candidate = select_policy_candidate(arm, solver_output)
        states[arm] = state
        decision_markets[arm] = decision_market
        frozen_plans[arm] = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=arm,
            state=state,
            candidate=candidate,
            decision_market=decision_market,
            active_chip=None,
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=rules_hash,
        )

    gameweek_dir = output_root / f"gw-{gameweek:02d}"
    for arm in POLICY_ARMS:
        arm_dir = gameweek_dir / arm
        _write_json(arm_dir / "policy-state-before.json", states[arm])
        _write_json(arm_dir / "validated-plan.json", frozen_plans[arm])

    revealed_episode = _load_outcomes_after_all_plans_freeze(
        episode_root / f"gw-{gameweek:02d}",
        frozen_plans=frozen_plans,
    )
    next_observed = _load_observed_episode(
        episode_root / f"gw-{gameweek + 1:02d}"
    )
    next_feature_state = build_feature_state(
        episode_manifest=next_observed["manifest"],
        observed=next_observed["observed"],
        identity_map=next_observed["identity"],
        previous_state=feature_state,
    )
    next_market = _market(next_feature_state)
    identity_hash = _stable_hash(revealed_episode["identity"])
    identity = _identity_index(revealed_episode["identity"])
    revealed_at = _reveal_time(
        revealed_episode["hidden"], str(manifest["created_at"])
    )
    arm_summaries: dict[str, Any] = {}
    action_hashes: set[str] = set()
    for arm in POLICY_ARMS:
        state = states[arm]
        plan = frozen_plans[arm]
        outcome = score_revealed_outcome(
            plan,
            revealed_episode["hidden"],
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=identity,
            identity_map_sha256=identity_hash,
        )
        successor, transition = transition_policy_state(
            state,
            plan,
            outcome,
            decision_market=decision_markets[arm],
            next_market=next_market,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        record = _replay_decision_record(
            manifest=manifest,
            feature_state=feature_state,
            state=state,
            plan=plan,
            outcome=outcome,
            transition=transition,
            solver_input=solver_inputs[arm],
            solver_output=solver_outputs[arm],
        )
        action_projection = {
            "transfers": plan["transfers"],
            "lineup": plan["lineup"],
            "active_chip": plan["active_chip"],
            "finance": plan["finance"],
        }
        action_hashes.add(fingerprint(action_projection))
        arm_dir = gameweek_dir / arm
        _write_json(arm_dir / "policy-state-before.json", state)
        _write_json(arm_dir / "validated-plan.json", plan)
        _write_json(arm_dir / "decision-record.json", record)
        _write_json(arm_dir / "realised-outcome.json", outcome)
        _write_json(arm_dir / "state-transition.json", transition)
        _write_json(arm_dir / "next-policy-state.json", successor)
        arm_summaries[arm] = {
            "strategy": _replay_strategy(arm),
            "plan_sha256": plan["content_sha256"],
            "outcome_sha256": outcome["content_sha256"],
            "transition_sha256": transition["content_sha256"],
            "next_state_sha256": successor["content_sha256"],
            "transfers": plan["finance"]["transfer_count"],
            "hit_cost": plan["finance"]["hit_cost"],
            "active_chip": plan["active_chip"],
            "captain_id": plan["lineup"]["captain_id"],
            "vice_captain_id": plan["lineup"]["vice_captain_id"],
            "substitutions": outcome["substitutions"],
            "gross_points": outcome["gross_points"],
            "net_points": transition["net_points"],
            "cumulative_points": successor["cumulative_points"],
            "bank": successor["bank"],
            "free_transfers": successor["free_transfers"],
        }

    input_hashes = {
        arm: fingerprint(solver_inputs[arm]) for arm in POLICY_ARMS
    }
    output_hashes = {
        arm: fingerprint(solver_outputs[arm]) for arm in POLICY_ARMS
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_mode": "genuine_historical_checkpoint",
        "season": season,
        "decisions_completed_through_gameweek": gameweek,
        "next_state_gameweek": gameweek + 1,
        "contains_next_gameweek_decision": False,
        "code_commit": code_commit,
        "episode_id": manifest["episode_id"],
        "observed_sha256": manifest["observed"]["feature_snapshot_ref"][
            "content_sha256"
        ],
        "hidden_outcome_sha256": manifest["hidden_outcome_ref"][
            "content_sha256"
        ],
        "identity_map_sha256": identity_hash,
        "ruleset": deepcopy(manifest["ruleset"]),
        "feature_state_sha256": feature_state["content_sha256"],
        "next_feature_state_sha256": next_feature_state["content_sha256"],
        "limitations": sorted(
            set(feature_state["limitations"])
            | {
                "No admissible historical unstructured evidence was reconstructed",
                "No recorded historical human decision was available",
                "Transfer option value is a bridge, not a multiweek player forecast",
            }
        ),
        "shared_action_count": len(action_hashes),
        "arms": arm_summaries,
    }
    if gameweek == 2:
        summary["reviewed_solver_input_sha256"] = next(iter(input_hashes.values()))
        summary["reviewed_solver_output_sha256"] = next(
            iter(output_hashes.values())
        )
    else:
        summary["reviewed_solver_input_sha256_by_arm"] = input_hashes
        summary["reviewed_solver_output_sha256_by_arm"] = output_hashes
    summary["content_sha256"] = fingerprint(summary)
    _write_json(gameweek_dir / "run-summary.json", summary)
    solver_lineage = (
        {
            "reviewed_solver_input_sha256": summary[
                "reviewed_solver_input_sha256"
            ],
            "reviewed_solver_output_sha256": summary[
                "reviewed_solver_output_sha256"
            ],
        }
        if gameweek == 2
        else {
            "reviewed_solver_input_sha256_by_arm": input_hashes,
            "reviewed_solver_output_sha256_by_arm": output_hashes,
        }
    )
    _write_json(
        gameweek_dir / "shared-context.json",
        {
            "episode_id": manifest["episode_id"],
            "observed_sha256": summary["observed_sha256"],
            "hidden_outcome_sha256": summary["hidden_outcome_sha256"],
            "identity_map_sha256": identity_hash,
            "ruleset": summary["ruleset"],
            "feature_state_sha256": summary["feature_state_sha256"],
            "next_feature_state_sha256": summary[
                "next_feature_state_sha256"
            ],
            "limitations": summary["limitations"],
            **solver_lineage,
        },
    )
    return summary


def finalise_historical_gameweek_two(
    *,
    season: str,
    episode_root: Path,
    output_root: Path,
    code_commit: str,
    reviewed_setup_dir: Path | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for the reviewed GW2 checkpoint."""
    return finalise_historical_gameweek(
        season=season,
        gameweek=2,
        episode_root=episode_root,
        output_root=output_root,
        code_commit=code_commit,
        reviewed_setup_dir=reviewed_setup_dir,
    )


def run_historical_replay(
    *,
    season: str,
    episode_root: Path,
    output_root: Path,
    start_gameweek: int = 1,
    stop_after_gameweek: int,
    code_commit: str,
) -> dict[str, Any]:
    """Run one explicitly reviewed historical checkpoint."""
    if start_gameweek == stop_after_gameweek and start_gameweek >= 2:
        return finalise_historical_gameweek(
            season=season,
            gameweek=start_gameweek,
            episode_root=episode_root,
            output_root=output_root,
            code_commit=code_commit,
        )
    if start_gameweek != 1 or stop_after_gameweek != 1:
        raise GenuineReplayError(
            "Reviewed checkpoints support exactly one Gameweek at a time"
        )
    if len(code_commit) != 40:
        raise GenuineReplayError("code_commit must be a full 40-character Git SHA")

    gw1_dir = episode_root / "gw-01"
    gw2_dir = episode_root / "gw-02"
    gw1 = _load_episode(gw1_dir)
    gw2 = _load_episode(gw2_dir)
    manifest = gw1["manifest"]
    if manifest["season"] != season or manifest["gameweek"] != 1:
        raise GenuineReplayError("Episode root does not contain requested GW1")
    seed_path = (
        Path(__file__).resolve().parents[2]
        / "control"
        / "seeds"
        / season
        / "official-scout-gw1.json"
    )
    seed = _read_json(seed_path)
    rules = gw1["rules"]
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    feature_gw1 = build_feature_state(
        episode_manifest=manifest,
        observed=gw1["observed"],
        identity_map=gw1["identity"],
        seed=seed,
    )
    feature_gw2 = build_feature_state(
        episode_manifest=gw2["manifest"],
        observed=gw2["observed"],
        identity_map=gw2["identity"],
        previous_state=feature_gw1,
    )
    states = initialise_policy_states(
        seed,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    decision_market = _market(feature_gw1)
    next_market = _market(feature_gw2)
    identity_hash = _stable_hash(gw1["identity"])
    identity = _identity_index(gw1["identity"])
    revealed_at = _reveal_time(
        gw1["hidden"], str(manifest["created_at"])
    )

    arm_summaries: dict[str, Any] = {}
    plans_by_action: set[str] = set()
    gameweek_dir = output_root / "gw-01"
    for arm in POLICY_ARMS:
        state = states[arm]
        candidate = _gw1_candidate(seed, state)
        plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=arm,
            state=state,
            candidate=candidate,
            decision_market=decision_market,
            active_chip=seed["initial_plan"]["active_chip"],
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        outcome = score_revealed_outcome(
            plan,
            gw1["hidden"],
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=identity,
            identity_map_sha256=identity_hash,
        )
        successor, transition = transition_policy_state(
            state,
            plan,
            outcome,
            decision_market=decision_market,
            next_market=next_market,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        record = _decision_record(
            manifest=manifest,
            feature_state=feature_gw1,
            state=state,
            plan=plan,
            outcome=outcome,
            transition=transition,
            seed=seed,
        )
        action_projection = {
            "transfers": plan["transfers"],
            "lineup": plan["lineup"],
            "active_chip": plan["active_chip"],
            "finance": plan["finance"],
        }
        plans_by_action.add(fingerprint(action_projection))
        arm_dir = gameweek_dir / arm
        _write_json(arm_dir / "policy-state-before.json", state)
        _write_json(arm_dir / "validated-plan.json", plan)
        _write_json(arm_dir / "decision-record.json", record)
        _write_json(arm_dir / "realised-outcome.json", outcome)
        _write_json(arm_dir / "state-transition.json", transition)
        _write_json(arm_dir / "next-policy-state.json", successor)
        arm_summaries[arm] = {
            "strategy": "controlled_official_scout_seed",
            "plan_sha256": plan["content_sha256"],
            "outcome_sha256": outcome["content_sha256"],
            "transition_sha256": transition["content_sha256"],
            "next_state_sha256": successor["content_sha256"],
            "transfers": plan["finance"]["transfer_count"],
            "hit_cost": plan["finance"]["hit_cost"],
            "active_chip": plan["active_chip"],
            "captain_id": plan["lineup"]["captain_id"],
            "vice_captain_id": plan["lineup"]["vice_captain_id"],
            "substitutions": outcome["substitutions"],
            "gross_points": outcome["gross_points"],
            "net_points": transition["net_points"],
            "cumulative_points": successor["cumulative_points"],
            "bank": successor["bank"],
            "free_transfers": successor["free_transfers"],
        }

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_mode": "genuine_historical_checkpoint",
        "season": season,
        "decisions_completed_through_gameweek": 1,
        "next_state_gameweek": 2,
        "contains_next_gameweek_decision": False,
        "code_commit": code_commit,
        "episode_id": manifest["episode_id"],
        "observed_sha256": manifest["observed"]["feature_snapshot_ref"][
            "content_sha256"
        ],
        "hidden_outcome_sha256": manifest["hidden_outcome_ref"][
            "content_sha256"
        ],
        "identity_map_sha256": identity_hash,
        "ruleset": deepcopy(manifest["ruleset"]),
        "feature_state_sha256": feature_gw1["content_sha256"],
        "next_feature_state_sha256": feature_gw2["content_sha256"],
        "limitations": sorted(
            set(feature_gw1["limitations"]) | set(seed["limitations"])
        ),
        "shared_action_count": len(plans_by_action),
        "arms": arm_summaries,
    }
    summary["content_sha256"] = fingerprint(summary)
    _write_json(gameweek_dir / "run-summary.json", summary)
    _write_json(
        gameweek_dir / "shared-context.json",
        {
            "episode_id": manifest["episode_id"],
            "observed_sha256": summary["observed_sha256"],
            "hidden_outcome_sha256": summary["hidden_outcome_sha256"],
            "identity_map_sha256": identity_hash,
            "ruleset": summary["ruleset"],
            "feature_state_sha256": summary["feature_state_sha256"],
            "next_feature_state_sha256": summary[
                "next_feature_state_sha256"
            ],
            "limitations": summary["limitations"],
        },
    )
    return summary
