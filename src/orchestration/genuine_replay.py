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
from src.forecasting.replay_adapter import build_replay_solver_input
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.orchestration.historical_feature_state import build_feature_state
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

    if gameweek != 2:
        raise GenuineReplayError(
            "The reviewed setup boundary currently implements Gameweek 2 only"
        )
    if len(code_commit) != 40:
        raise GenuineReplayError("code_commit must be a full 40-character Git SHA")

    gw1 = _load_observed_episode(episode_root / "gw-01")
    current = _load_observed_episode(episode_root / f"gw-{gameweek:02d}")
    manifest = current["manifest"]
    if manifest["season"] != season or manifest["gameweek"] != gameweek:
        raise GenuineReplayError("Episode root does not contain requested Gameweek")

    seed_path = (
        Path(__file__).resolve().parents[2]
        / "control"
        / "seeds"
        / season
        / "official-scout-gw1.json"
    )
    seed = _read_json(seed_path)
    feature_gw1 = build_feature_state(
        episode_manifest=gw1["manifest"],
        observed=gw1["observed"],
        identity_map=gw1["identity"],
        seed=seed,
    )
    feature_current = build_feature_state(
        episode_manifest=manifest,
        observed=current["observed"],
        identity_map=current["identity"],
        previous_state=feature_gw1,
    )

    previous_summary = _read_json(previous_checkpoint_dir / "run-summary.json")
    if previous_summary["next_feature_state_sha256"] != feature_current[
        "content_sha256"
    ]:
        raise GenuineReplayError(
            "GW2 feature state differs from the prior checkpoint handoff"
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
                f"Opening state differs from GW1 summary for {arm}"
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
    if len(input_hashes) != 1:
        raise GenuineReplayError(
            "GW2 controlled arms do not have an identical engine input"
        )

    shared_input = inputs[POLICY_ARMS[0]]
    shared_input_sha256 = fingerprint(shared_input)
    engine_output = solve(
        build_replay_solver_input(
            feature_state=feature_current,
            policy_state=states[POLICY_ARMS[0]],
            max_transfers=3,
            transfer_value_policy=TRANSFER_VALUE_POLICY,
            probability_extra_transfer_needed=(
                PROBABILITY_EXTRA_TRANSFER_NEEDED
            ),
            future_transfer_discount=FUTURE_TRANSFER_DISCOUNT,
        ),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    engine_output_sha256 = fingerprint(engine_output)

    setup_dir = output_root / f"gw-{gameweek:02d}" / "setup"
    _write_json(setup_dir / "shared-feature-state.json", feature_current)
    _write_json(setup_dir / "shared-engine-input.json", shared_input)
    _write_json(setup_dir / "shared-engine-output.json", engine_output)
    brief_hashes: dict[str, str] = {}
    for arm in POLICY_ARMS:
        arm_dir = setup_dir / "arms" / arm
        brief = _policy_brief(
            arm=arm,
            manifest=manifest,
            state=states[arm],
            feature_state=feature_current,
            solver_input_sha256=shared_input_sha256,
            solver_output_sha256=engine_output_sha256,
            solver_output=engine_output,
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
        "shared_engine_input": True,
        "solver_input_sha256": shared_input_sha256,
        "solver_output_sha256": engine_output_sha256,
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


def run_historical_replay(
    *,
    season: str,
    episode_root: Path,
    output_root: Path,
    start_gameweek: int = 1,
    stop_after_gameweek: int,
    code_commit: str,
) -> dict[str, Any]:
    """Run one reviewed historical checkpoint; currently GW1 only."""
    if start_gameweek != 1 or stop_after_gameweek != 1:
        raise GenuineReplayError(
            "This reviewed checkpoint implements Gameweek 1 only"
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
