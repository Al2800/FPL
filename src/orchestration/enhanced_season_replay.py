"""Resumable, non-canonical enhanced season replay with factorial controls."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.agent_fork_adapter import (
    build_fork_solver_input,
    build_same_state_control_attribution,
    run_sequential_agent_fork_week,
)
from src.orchestration.early_season_evidence_replay import (
    assert_reusable_baselines,
)
from src.orchestration.evidence_fork import (
    EvidenceForkError,
    _identity_index,
    _market_from_feature_state,
    _read,
    _sealed,
    _write_once,
)
from src.orchestration.policy_state import transition_policy_state
from src.orchestration.validated_plan import validate_and_freeze_plan


FIRST_GAMEWEEK = 1
REVIEW_TRANCHES = {
    1: 5,
    6: 10,
    11: 15,
    16: 20,
    21: 25,
    26: 30,
    31: 35,
    36: 38,
}
ARM_IDS = (
    "scout_structured",
    "optimized_structured",
    "scout_evidence",
    "optimized_evidence",
)


def _tree_hash(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(files)


def _validate_sealed(value: Mapping[str, Any], label: str) -> None:
    expected = value.get("content_sha256")
    if not isinstance(expected, str) or expected != artifact_hash(value):
        raise EvidenceForkError(f"{label} content hash mismatch")


def _relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _artifact_ref(path: Path, repo_root: Path) -> dict[str, Any]:
    value = _read(path)
    _validate_sealed(value, _relative(path, repo_root))
    return {
        "path": _relative(path, repo_root),
        "content_sha256": str(value["content_sha256"]),
    }


def _input_pack(
    *,
    gameweek: int,
    enhanced_input_root: Path,
    input_index: Mapping[str, Any],
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    indexed = {
        int(row["gameweek"]): dict(row)
        for row in input_index.get("packs", [])
    }
    if gameweek not in indexed:
        raise EvidenceForkError(f"Enhanced input index has no GW{gameweek}")
    entry = indexed[gameweek]
    path = enhanced_input_root / str(entry["path"])
    pack = _read(path)
    _validate_sealed(pack, f"GW{gameweek} enhanced input pack")
    if str(pack["content_sha256"]) != str(entry["content_sha256"]):
        raise EvidenceForkError(f"GW{gameweek} enhanced input index binding mismatch")
    if int(pack["gameweek"]) != gameweek:
        raise EvidenceForkError(f"GW{gameweek} enhanced input identity mismatch")
    availability = {
        str(row["family"]): str(row["status"])
        for row in pack["feature_availability"]
    }
    return pack, {
        **_artifact_ref(path, repo_root),
        "classification": str(pack["classification"]),
        "decision_cutoff": str(pack["decision_cutoff"]),
        "feature_availability": availability,
    }


def _later_artifact_version(gameweek: int) -> str:
    """Select the immutable completed hosted-artifact namespace."""
    accepted_versions = {
        20: "sol-v3",
        21: "sol-v3",
        22: "sol-v3",
        23: "sol-v2",
        25: "sol-v3",
        26: "sol-v3",
        30: "sol-v5",
        31: "sol-v3",
        33: "sol-v3",
    }
    return accepted_versions.get(gameweek, "sol-v1")

def _standard_arm_summary(
    *,
    gameweek: int,
    root: Path,
    policy_arm: str,
    repo_root: Path,
    evidence_decision: str,
) -> dict[str, Any]:
    arm_root = root / f"gw-{gameweek:02d}" / policy_arm
    plan_path = arm_root / "validated-plan.json"
    outcome_path = arm_root / "realised-outcome.json"
    transition_path = arm_root / "state-transition.json"
    next_state_path = arm_root / "next-policy-state.json"
    plan = _read(plan_path)
    outcome = _read(outcome_path)
    transition = _read(transition_path)
    next_state = _read(next_state_path)
    for label, value in (
        ("plan", plan),
        ("outcome", outcome),
        ("transition", transition),
        ("next state", next_state),
    ):
        _validate_sealed(value, f"GW{gameweek} {policy_arm} {label}")
    if plan.get("validation", {}).get("status") != "passed":
        raise EvidenceForkError(f"GW{gameweek} {policy_arm} plan is not valid")
    if len(plan["squad_after"]) != 15:
        raise EvidenceForkError(f"GW{gameweek} {policy_arm} squad is not a legal 15")
    if str(outcome["plan_sha256"]) != str(plan["content_sha256"]):
        raise EvidenceForkError(f"GW{gameweek} {policy_arm} outcome binding mismatch")
    if str(transition["next_state_sha256"]) != str(
        next_state["content_sha256"]
    ):
        raise EvidenceForkError(f"GW{gameweek} {policy_arm} transition binding mismatch")
    return {
        "weekly_net_points": int(transition["net_points"]),
        "cumulative_points": int(next_state["cumulative_points"]),
        "bank": float(next_state["bank"]),
        "free_transfers": int(next_state["free_transfers"]),
        "transfers": deepcopy(plan["transfers"]),
        "transfer_count": int(plan["finance"]["transfer_count"]),
        "hit_cost": int(transition["hit_cost"]),
        "active_chip": plan.get("active_chip"),
        "substitutions": deepcopy(outcome["substitutions"]),
        "captain_id": str(plan["lineup"]["captain_id"]),
        "evidence_decision": evidence_decision,
        "starting_state_sha256": str(plan["previous_state_sha256"]),
        "next_state_sha256": str(next_state["content_sha256"]),
        "artifacts": {
            "plan": _artifact_ref(plan_path, repo_root),
            "outcome": _artifact_ref(outcome_path, repo_root),
            "transition": _artifact_ref(transition_path, repo_root),
            "next_state": _artifact_ref(next_state_path, repo_root),
        },
    }


def _fork_arm_summary(
    *,
    gameweek: int,
    root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    plan_path = root / "validated-plan.json"
    outcome_path = root / "realised-outcome.json"
    transition_path = root / "state-transition.json"
    next_state_path = root / "next-policy-state.json"
    comparison_path = root / "comparison.json"
    attribution_path = root / "same-state-attribution.json"
    plan = _read(plan_path)
    outcome = _read(outcome_path)
    transition = _read(transition_path)
    next_state = _read(next_state_path)
    comparison = _read(comparison_path)
    attribution = _read(attribution_path)
    for label, value in (
        ("plan", plan),
        ("outcome", outcome),
        ("transition", transition),
        ("next state", next_state),
        ("comparison", comparison),
        ("same-state attribution", attribution),
    ):
        _validate_sealed(value, f"GW{gameweek} evidence fork {label}")
    if str(transition["next_state_sha256"]) != str(
        next_state["content_sha256"]
    ):
        raise EvidenceForkError(f"GW{gameweek} evidence fork transition mismatch")
    return {
        "weekly_net_points": int(transition["net_points"]),
        "cumulative_points": int(next_state["cumulative_points"]),
        "bank": float(next_state["bank"]),
        "free_transfers": int(next_state["free_transfers"]),
        "transfers": deepcopy(plan["transfers"]),
        "transfer_count": int(plan["finance"]["transfer_count"]),
        "hit_cost": int(transition["hit_cost"]),
        "active_chip": plan.get("active_chip"),
        "substitutions": deepcopy(outcome["substitutions"]),
        "captain_id": str(plan["lineup"]["captain_id"]),
        "evidence_decision": str(comparison["agent_decision"]),
        "same_state_evidence_delta": int(attribution["agent_evidence_delta"]),
        "starting_state_sha256": str(comparison["starting_state_sha256"]),
        "next_state_sha256": str(next_state["content_sha256"]),
        "artifacts": {
            "plan": _artifact_ref(plan_path, repo_root),
            "outcome": _artifact_ref(outcome_path, repo_root),
            "transition": _artifact_ref(transition_path, repo_root),
            "next_state": _artifact_ref(next_state_path, repo_root),
            "comparison": _artifact_ref(comparison_path, repo_root),
            "same_state_attribution": _artifact_ref(
                attribution_path, repo_root
            ),
        },
    }


def _owned_structured_arm_summary(
    *,
    gameweek: int,
    root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Summarise one structured week generated from an arm-owned state."""
    plan_path = root / "validated-plan.json"
    outcome_path = root / "realised-outcome.json"
    transition_path = root / "state-transition.json"
    next_state_path = root / "next-policy-state.json"
    plan = _read(plan_path)
    outcome = _read(outcome_path)
    transition = _read(transition_path)
    next_state = _read(next_state_path)
    for label, value in (
        ("plan", plan),
        ("outcome", outcome),
        ("transition", transition),
        ("next state", next_state),
    ):
        _validate_sealed(value, f"GW{gameweek} owned structured {label}")
    if plan.get("validation", {}).get("status") != "passed":
        raise EvidenceForkError(
            f"GW{gameweek} owned structured plan is not valid"
        )
    if str(outcome["plan_sha256"]) != str(plan["content_sha256"]):
        raise EvidenceForkError(
            f"GW{gameweek} owned structured outcome binding mismatch"
        )
    if str(transition["next_state_sha256"]) != str(
        next_state["content_sha256"]
    ):
        raise EvidenceForkError(
            f"GW{gameweek} owned structured transition binding mismatch"
        )
    return {
        "weekly_net_points": int(transition["net_points"]),
        "cumulative_points": int(next_state["cumulative_points"]),
        "bank": float(next_state["bank"]),
        "free_transfers": int(next_state["free_transfers"]),
        "transfers": deepcopy(plan["transfers"]),
        "transfer_count": int(plan["finance"]["transfer_count"]),
        "hit_cost": int(transition["hit_cost"]),
        "active_chip": plan.get("active_chip"),
        "substitutions": deepcopy(outcome["substitutions"]),
        "captain_id": str(plan["lineup"]["captain_id"]),
        "evidence_decision": "frozen_no_evidence",
        "starting_state_sha256": str(plan["previous_state_sha256"]),
        "next_state_sha256": str(next_state["content_sha256"]),
        "artifacts": {
            "plan": _artifact_ref(plan_path, repo_root),
            "outcome": _artifact_ref(outcome_path, repo_root),
            "transition": _artifact_ref(transition_path, repo_root),
            "next_state": _artifact_ref(next_state_path, repo_root),
        },
    }


def _run_owned_structured_week(
    *,
    gameweek: int,
    state: Mapping[str, Any],
    canonical_root: Path,
    episode_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Solve, validate, reveal, and transition a no-evidence owned state."""
    episode = episode_root / f"gw-{gameweek:02d}"
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    solver_input = build_fork_solver_input(
        gameweek=gameweek,
        state=state,
        canonical_root=canonical_root,
    )
    solver_output = solve(
        SolverInput.from_dict(solver_input),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    candidate = deepcopy(dict(solver_output["selected"]))
    plan = validate_and_freeze_plan(
        episode_id=str(manifest["episode_id"]),
        policy_arm=str(state["policy_arm"]),
        state=state,
        candidate=candidate,
        decision_market=solver_input["players"],
        active_chip=None,
        frozen_at=str(manifest["deadline"]),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    if plan.get("validation", {}).get("status") != "passed":
        raise EvidenceForkError(
            f"GW{gameweek} structured plan must pass before outcome reveal"
        )
    canonical_gw = canonical_root / f"gw-{gameweek:02d}"
    canonical_outcome = _read(
        canonical_gw / "evidence_agent/realised-outcome.json"
    )
    outcome = score_revealed_outcome(
        plan,
        _read(episode / "hidden-outcome.json"),
        revealed_at=str(canonical_outcome["revealed_at"]),
        rules=rules,
        ruleset_sha256=rules_hash,
        player_identity_map=_identity_index(
            _read(episode / "identity-map.json")
        ),
        identity_map_sha256=str(
            _read(canonical_gw / "shared-context.json")["identity_map_sha256"]
        ),
    )
    next_market = solver_input["players"]
    if gameweek < 38:
        next_feature = _read(
            canonical_root
            / f"gw-{gameweek + 1:02d}/setup/shared-feature-state.json"
        )
        next_market = _market_from_feature_state(next_feature)
    successor, transition = transition_policy_state(
        state,
        plan,
        outcome,
        decision_market=solver_input["players"],
        next_market=next_market,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    for name, value in (
        ("starting-policy-state.json", state),
        ("solver-input.json", solver_input),
        ("solver-output.json", solver_output),
        ("validated-plan.json", plan),
        ("realised-outcome.json", outcome),
        ("state-transition.json", transition),
        ("next-policy-state.json", successor),
    ):
        _write_once(output_root / name, value)
    return successor


def _bind_frozen_host_proposal(
    *,
    gameweek: int,
    arm_id: str,
    state: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Label reuse of a frozen interpretation on an exact-baseline arm."""
    limitations = list(source_bundle.get("limitations", []))
    for value in (
        "frozen_hosted_interpretation_reused_on_exact_player_baselines",
        "hosted_run_original_candidate_may_differ_from_application_candidate",
    ):
        if value not in limitations:
            limitations.append(value)
    result = {
        key: deepcopy(item)
        for key, item in source_bundle.items()
        if key != "content_sha256"
    }
    result["experiment_id"] = (
        f"2025-26-enhanced-gw{gameweek:02d}-{arm_id}-evidence-v1"
    )
    result["limitations"] = limitations
    result["replay_application"] = {
        "arm_id": arm_id,
        "starting_state_sha256": str(state["content_sha256"]),
        "source_host_bundle_sha256": str(source_bundle["content_sha256"]),
        "reuse_basis": (
            "Frozen evidence and challenger interpretations are decision-"
            "independent projection proposals; exact target-player baselines "
            "must match before application."
        ),
    }
    return _sealed(result)


def _state_from_arm_summary(
    summary: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    state = _read(repo_root / str(summary["artifacts"]["next_state"]["path"]))
    _validate_sealed(state, "enhanced arm successor state")
    if str(state["content_sha256"]) != str(summary["next_state_sha256"]):
        raise EvidenceForkError("Enhanced arm successor state binding mismatch")
    return state

def _effects(arms: Mapping[str, Mapping[str, Any]], field: str) -> dict[str, int]:
    scout_structured = int(arms["scout_structured"][field])
    optimized_structured = int(arms["optimized_structured"][field])
    scout_evidence = int(arms["scout_evidence"][field])
    optimized_evidence = int(arms["optimized_evidence"][field])
    evidence_scout = scout_evidence - scout_structured
    evidence_optimized = optimized_evidence - optimized_structured
    return {
        "seed_effect_without_evidence": optimized_structured - scout_structured,
        "seed_effect_with_evidence": optimized_evidence - scout_evidence,
        "evidence_effect_with_scout_seed": evidence_scout,
        "evidence_effect_with_optimized_seed": evidence_optimized,
        "seed_evidence_interaction": evidence_optimized - evidence_scout,
    }


def _assert_state_continuity(
    previous: Mapping[str, Mapping[str, Any]] | None,
    current: Mapping[str, Mapping[str, Any]],
) -> None:
    if previous is None:
        return
    for arm_id in ARM_IDS:
        if str(previous[arm_id]["next_state_sha256"]) != str(
            current[arm_id]["starting_state_sha256"]
        ):
            raise EvidenceForkError(
                f"{arm_id} state discontinuity between replay weeks"
            )


def _summarise_totals(
    weeks: list[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not weeks:
        raise EvidenceForkError("Enhanced replay totals require at least one week")
    return {
        arm_id: {
            "net_points": sum(
                int(week["arms"][arm_id]["weekly_net_points"])
                for week in weeks
            ),
            "terminal_cumulative_points": int(
                weeks[-1]["arms"][arm_id]["cumulative_points"]
            ),
            "transfer_count": sum(
                int(week["arms"][arm_id]["transfer_count"])
                for week in weeks
            ),
            "hit_cost": sum(
                int(week["arms"][arm_id]["hit_cost"])
                for week in weeks
            ),
            "chip_uses": sum(
                week["arms"][arm_id]["active_chip"] is not None
                for week in weeks
            ),
            "evidence_action_weeks": sum(
                week["arms"][arm_id]["evidence_decision"] == "applied"
                for week in weeks
            ),
        }
        for arm_id in ARM_IDS
    }


def _load_previous_tranche(
    *,
    start_gameweek: int,
    output_root: Path,
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]] | None]:
    if start_gameweek == FIRST_GAMEWEEK:
        return None, None
    previous_start = start_gameweek - 5
    previous_stop = start_gameweek - 1
    checkpoint = _read(
        output_root
        / f"checkpoints/gw-{previous_start:02d}-gw-{previous_stop:02d}.json"
    )
    _validate_sealed(checkpoint, "previous enhanced replay checkpoint")
    if (
        int(checkpoint["start_gameweek"]) != previous_start
        or int(checkpoint["stop_gameweek"]) != previous_stop
        or int(checkpoint["next_gameweek"]) != start_gameweek
        or checkpoint["status"] != "paused_for_review"
    ):
        raise EvidenceForkError("Previous enhanced checkpoint is not resumable")
    previous_week = _read(
        output_root
        / f"weeks/gw-{previous_stop:02d}/comparison.json"
    )
    _validate_sealed(previous_week, "previous enhanced terminal week")
    if int(previous_week["gameweek"]) != previous_stop:
        raise EvidenceForkError("Previous enhanced terminal week identity mismatch")
    return checkpoint, deepcopy(dict(previous_week["arms"]))

def run_enhanced_season_replay(
    *,
    start_gameweek: int,
    stop_gameweek: int,
    repo_root: Path,
    canonical_root: Path,
    optimized_seed_root: Path,
    scout_evidence_root: Path,
    enhanced_input_root: Path,
    episode_root: Path,
    evidence_bundle_root: Path,
    later_evidence_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Run one approved five-week enhanced replay tranche and stop hard."""
    expected_stop = REVIEW_TRANCHES.get(start_gameweek)
    if expected_stop is None:
        raise EvidenceForkError(
            "Enhanced replay can start only at an approved review boundary"
        )
    if stop_gameweek != expected_stop:
        raise EvidenceForkError(
            f"GW{start_gameweek}-GW{expected_stop} has a hard review stop "
            f"at GW{expected_stop}"
        )
    previous_checkpoint, previous_arms = _load_previous_tranche(
        start_gameweek=start_gameweek,
        output_root=output_root,
    )
    input_index = _read(enhanced_input_root / "input-index.json")
    _validate_sealed(input_index, "enhanced input index")
    canonical_before, canonical_count_before = _tree_hash(canonical_root)

    host_bundles: dict[int, dict[str, Any]] = {}
    evidence_runs: dict[int, dict[str, Any]] = {}
    challenger_runs: dict[int, dict[str, Any]] = {}
    for gameweek in range(max(2, start_gameweek), stop_gameweek + 1):
        if gameweek <= 11:
            bundle = _read(
                evidence_bundle_root
                / f"gw-{gameweek:02d}/agent-host-bundle-v2.json"
            )
            evidence = _read(
                scout_evidence_root
                / f"hosted/gw-{gameweek:02d}/evidence-run-v2.json"
            )
            challenger = _read(
                scout_evidence_root
                / f"hosted/gw-{gameweek:02d}/challenger-run-v2.json"
            )
        else:
            source_root = (
                later_evidence_root
                / f"gw-{gameweek:02d}/{_later_artifact_version(gameweek)}"
            )
            bundle = _read(source_root / "host-bundle.json")
            evidence = _read(source_root / "evidence-run.json")
            challenger = _read(source_root / "challenger-run.json")
        for label, value in (
            ("host bundle", bundle),
            ("evidence run", evidence),
            ("challenger run", challenger),
        ):
            _validate_sealed(value, f"GW{gameweek} {label}")
        host_bundles[gameweek] = bundle
        evidence_runs[gameweek] = evidence
        challenger_runs[gameweek] = challenger

    if start_gameweek == FIRST_GAMEWEEK:
        optimized_evidence_state = _read(
            optimized_seed_root
            / "gw-01/evidence_agent/next-policy-state.json"
        )
        state_label = "optimized evidence GW2 state"
    else:
        optimized_evidence_state = _read(
            output_root
            / "arms/optimized_evidence"
            / f"gw-{start_gameweek - 1:02d}/next-policy-state.json"
        )
        state_label = f"optimized evidence GW{start_gameweek} resume state"
    _validate_sealed(optimized_evidence_state, state_label)
    if previous_arms is not None and str(
        previous_arms["optimized_evidence"]["next_state_sha256"]
    ) != str(optimized_evidence_state["content_sha256"]):
        raise EvidenceForkError("Optimized evidence resume state binding mismatch")

    carried_states: dict[str, dict[str, Any]] = {}
    if start_gameweek > 11:
        if previous_arms is None:
            raise EvidenceForkError("Later enhanced tranche requires predecessor state")
        carried_states = {
            arm_id: _state_from_arm_summary(
                previous_arms[arm_id],
                repo_root=repo_root,
            )
            for arm_id in ARM_IDS
        }
    weeks: list[dict[str, Any]] = []
    for gameweek in range(start_gameweek, stop_gameweek + 1):
        _, input_ref = _input_pack(
            gameweek=gameweek,
            enhanced_input_root=enhanced_input_root,
            input_index=input_index,
            repo_root=repo_root,
        )
        if gameweek <= 11:
            scout_structured = _standard_arm_summary(
                gameweek=gameweek,
                root=canonical_root,
                policy_arm="forecast_optimizer",
                repo_root=repo_root,
                evidence_decision="frozen_no_evidence",
            )
            optimized_structured = _standard_arm_summary(
                gameweek=gameweek,
                root=optimized_seed_root,
                policy_arm="forecast_optimizer",
                repo_root=repo_root,
                evidence_decision="frozen_no_evidence",
            )
        else:
            structured_summaries: dict[str, dict[str, Any]] = {}
            for arm_id in ("scout_structured", "optimized_structured"):
                week_root = (
                    output_root / "arms" / arm_id / f"gw-{gameweek:02d}"
                )
                _run_owned_structured_week(
                    gameweek=gameweek,
                    state=carried_states[arm_id],
                    canonical_root=canonical_root,
                    episode_root=episode_root,
                    output_root=week_root,
                )
                structured_summaries[arm_id] = _owned_structured_arm_summary(
                    gameweek=gameweek,
                    root=week_root,
                    repo_root=repo_root,
                )
            scout_structured = structured_summaries["scout_structured"]
            optimized_structured = structured_summaries["optimized_structured"]

        if gameweek == 1:
            scout_evidence = _standard_arm_summary(
                gameweek=gameweek,
                root=canonical_root,
                policy_arm="evidence_agent",
                repo_root=repo_root,
                evidence_decision="not_applicable_seed_week",
            )
            optimized_evidence = _standard_arm_summary(
                gameweek=gameweek,
                root=optimized_seed_root,
                policy_arm="evidence_agent",
                repo_root=repo_root,
                evidence_decision="not_applicable_seed_week",
            )
            scout_evidence["same_state_evidence_delta"] = 0
            optimized_evidence["same_state_evidence_delta"] = 0
        elif gameweek <= 11:
            scout_evidence = _fork_arm_summary(
                gameweek=gameweek,
                root=(
                    scout_evidence_root
                    / f"longitudinal/gw-{gameweek:02d}"
                ),
                repo_root=repo_root,
            )
            assert_reusable_baselines(
                gameweek=gameweek,
                state=optimized_evidence_state,
                host_bundle=host_bundles[gameweek],
                canonical_root=canonical_root,
            )
            optimized_week_root = (
                output_root
                / "arms/optimized_evidence"
                / f"gw-{gameweek:02d}"
            )
            _, successor, _ = run_sequential_agent_fork_week(
                gameweek=gameweek,
                state=optimized_evidence_state,
                host_bundle=host_bundles[gameweek],
                evidence_run=evidence_runs[gameweek],
                challenger_run=challenger_runs[gameweek],
                canonical_root=canonical_root,
                episode_root=episode_root,
                output_root=optimized_week_root,
                transition_to_next=True,
            )
            build_same_state_control_attribution(
                gameweek=gameweek,
                state=optimized_evidence_state,
                canonical_root=canonical_root,
                episode_root=episode_root,
                agent_output_root=optimized_week_root,
            )
            if successor is None:
                raise EvidenceForkError(
                    f"GW{gameweek} optimized evidence produced no successor"
                )
            optimized_evidence = _fork_arm_summary(
                gameweek=gameweek,
                root=optimized_week_root,
                repo_root=repo_root,
            )
            optimized_evidence_state = successor
        else:
            evidence_summaries: dict[str, dict[str, Any]] = {}
            for arm_id in ("scout_evidence", "optimized_evidence"):
                state = carried_states[arm_id]
                assert_reusable_baselines(
                    gameweek=gameweek,
                    state=state,
                    host_bundle=host_bundles[gameweek],
                    canonical_root=canonical_root,
                )
                application_bundle = _bind_frozen_host_proposal(
                    gameweek=gameweek,
                    arm_id=arm_id,
                    state=state,
                    source_bundle=host_bundles[gameweek],
                )
                week_root = (
                    output_root / "arms" / arm_id / f"gw-{gameweek:02d}"
                )
                _, successor, _ = run_sequential_agent_fork_week(
                    gameweek=gameweek,
                    state=state,
                    host_bundle=application_bundle,
                    evidence_run=evidence_runs[gameweek],
                    challenger_run=challenger_runs[gameweek],
                    canonical_root=canonical_root,
                    episode_root=episode_root,
                    output_root=week_root,
                    transition_to_next=True,
                )
                build_same_state_control_attribution(
                    gameweek=gameweek,
                    state=state,
                    canonical_root=canonical_root,
                    episode_root=episode_root,
                    agent_output_root=week_root,
                )
                if successor is None:
                    raise EvidenceForkError(
                        f"GW{gameweek} {arm_id} produced no successor"
                    )
                evidence_summaries[arm_id] = _fork_arm_summary(
                    gameweek=gameweek,
                    root=week_root,
                    repo_root=repo_root,
                )
            scout_evidence = evidence_summaries["scout_evidence"]
            optimized_evidence = evidence_summaries["optimized_evidence"]

        arms = {
            "scout_structured": scout_structured,
            "optimized_structured": optimized_structured,
            "scout_evidence": scout_evidence,
            "optimized_evidence": optimized_evidence,
        }
        _assert_state_continuity(previous_arms, arms)
        week = _sealed(
            {
                "schema_version": "1.0",
                "experiment_id": "2025-26-enhanced-season-replay-v1",
                "classification": "exploratory_production_ineligible",
                "gameweek": gameweek,
                "enhanced_input": input_ref,
                "identical_input_binding": {
                    arm_id: str(input_ref["content_sha256"])
                    for arm_id in ARM_IDS
                },
                "arms": arms,
                "weekly_effects": _effects(arms, "weekly_net_points"),
                "cumulative_effects": _effects(arms, "cumulative_points"),
            }
        )
        _write_once(
            output_root / f"weeks/gw-{gameweek:02d}/comparison.json",
            week,
        )
        weeks.append(week)
        previous_arms = arms
        carried_states = {
            arm_id: _state_from_arm_summary(
                arms[arm_id],
                repo_root=repo_root,
            )
            for arm_id in ARM_IDS
        }
    canonical_after, canonical_count_after = _tree_hash(canonical_root)
    if (canonical_before, canonical_count_before) != (
        canonical_after,
        canonical_count_after,
    ):
        raise EvidenceForkError("Canonical replay changed during enhanced tranche")

    season_weeks: list[dict[str, Any]] = []
    for gameweek in range(FIRST_GAMEWEEK, stop_gameweek + 1):
        week = _read(
            output_root / f"weeks/gw-{gameweek:02d}/comparison.json"
        )
        _validate_sealed(week, f"enhanced GW{gameweek} comparison")
        season_weeks.append(week)
    tranche_totals = _summarise_totals(weeks)
    season_totals = _summarise_totals(season_weeks)

    season_complete = stop_gameweek == 38
    checkpoint_body: dict[str, Any] = {
        "schema_version": "1.0" if start_gameweek == 1 else "1.1",
        "experiment_id": "2025-26-enhanced-season-replay-v1",
        "classification": "exploratory_production_ineligible",
        "start_gameweek": start_gameweek,
        "stop_gameweek": stop_gameweek,
        "status": "completed" if season_complete else "paused_for_review",
        "input_index_sha256": str(input_index["content_sha256"]),
        "arms": list(ARM_IDS),
        "weeks": [
            {
                "gameweek": int(week["gameweek"]),
                "comparison_sha256": str(week["content_sha256"]),
            }
            for week in weeks
        ],
        "totals": season_totals,
        "terminal_effects": _effects(
            {arm_id: season_totals[arm_id] for arm_id in ARM_IDS},
            "terminal_cumulative_points",
        ),
        "canonical_artifacts": {
            "file_count": canonical_count_before,
            "tree_sha256_before": canonical_before,
            "tree_sha256_after": canonical_after,
            "unchanged": True,
        },
        "review_required_before_continuation": not season_complete,
        "limitations": [
            "retrospective_optimized_seed_is_production_ineligible",
            "historical_evidence_cases_are_not_preregistered",
            "enhanced_input_packs_include_explicit_degraded_and_exploratory_fallbacks",
            "odds_are_not_applied_to_the_structured_projection_in_this_tranche",
            "ratings_and_set_piece_inputs_are_unavailable_in_this_tranche",
        ],
    }
    if not season_complete:
        checkpoint_body["next_gameweek"] = stop_gameweek + 1
    if previous_checkpoint is not None:
        checkpoint_body["predecessor_checkpoint"] = {
            "path": (
                f"reports/benchmarks/2025-26-enhanced/checkpoints/"
                f"gw-{start_gameweek - 5:02d}-gw-{start_gameweek - 1:02d}.json"
            ),
            "content_sha256": str(previous_checkpoint["content_sha256"]),
        }
        checkpoint_body["tranche_totals"] = tranche_totals
        checkpoint_body["season_to_date_totals"] = season_totals
    checkpoint = _sealed(checkpoint_body)
    _write_once(
        output_root
        / f"checkpoints/gw-{start_gameweek:02d}-gw-{stop_gameweek:02d}.json",
        checkpoint,
    )
    return checkpoint
