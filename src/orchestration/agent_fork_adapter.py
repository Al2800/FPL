"""Deterministic bridge from proposal-only agent arms to an isolated GW12 fork."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.evidence.lifecycle import load_policy
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.agent_arm import build_hosted_request
from src.orchestration.evidence_fork import (
    EvidenceForkError,
    _identity_index,
    _read,
    _sealed,
    _write_once,
)
from src.orchestration.validated_plan import validate_and_freeze_plan


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "control/policies/evidence-adjustments.yaml"
EVIDENCE_MODE = "retrospective_published_before_deadline"


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(value for value in path.rglob("*") if value.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _document(source: Mapping[str, Any]) -> dict[str, Any]:
    document = {
        "document_id": f"document:{source['source_id']}",
        "source_id": str(source["source_id"]),
        "title": str(source["title"]),
        "published_at": str(source["published_at"]),
        "observed_at": str(source["captured_at"]),
        "available_at": str(source["captured_at"]),
        "passages": {
            f"passage:{source['claim_id']}": str(source["citation_excerpt"])
        },
    }
    document["content_sha256"] = artifact_hash(document)
    return document


def build_gw12_agent_host_bundle(
    *,
    evidence_bundle_path: Path,
    canonical_root: Path,
    episode_root: Path,
    code_commit: str,
) -> dict[str, Any]:
    """Build the exact observed-only input for the two hosted roles."""
    reconstructed = _read(evidence_bundle_path)
    if reconstructed.get("evidence_mode") != EVIDENCE_MODE:
        raise EvidenceForkError("GW12 agent fork requires the retrospective evidence mode")
    episode = episode_root / "gw-12"
    manifest = _read(episode / "episode-manifest.json")
    if reconstructed.get("decision_cutoff") != manifest.get("deadline"):
        raise EvidenceForkError("Evidence cutoff does not match the GW12 episode")
    arm = canonical_root / "gw-12/setup/arms/evidence_agent"
    solver_input = _read(arm / "reviewed-engine-input.json")
    solver_output = _read(arm / "reviewed-engine-output.json")
    player_ids = sorted(str(row["player_id"]) for row in reconstructed["sources"])
    indexed = {str(row["player_id"]): row for row in solver_input["players"]}
    if any(player_id not in indexed for player_id in player_ids):
        raise EvidenceForkError("Evidence player is absent from the frozen market")
    baselines = {
        player_id: {
            "expected_minutes": float(indexed[player_id]["expected_minutes"]),
            "start_probability": float(indexed[player_id]["start_probability"]),
        }
        for player_id in player_ids
    }
    documents = [_document(source) for source in reconstructed["sources"]]
    candidate = deepcopy(dict(solver_output["selected"]))
    request = build_hosted_request(
        arm="evidence_agent",
        run_id="gw12-sol-evidence-v1",
        episode_id=str(manifest["episode_id"]),
        observed_episode_sha256=str(
            manifest["observed"]["feature_snapshot_ref"]["content_sha256"]
        ),
        snapshot_ids=list(manifest["observed"]["snapshot_ids"]),
        decision_at=str(manifest["deadline"]),
        ruleset_id=str(manifest["ruleset"]["ruleset_id"]),
        player_ids=player_ids,
        player_baselines=baselines,
        evidence_documents=documents,
        deterministic_candidate_sha256=artifact_hash(candidate),
        budget={
            "wall_clock_ms": 120_000,
            "tool_calls": 0,
            "input_tokens": 20_000,
            "output_tokens": 4_000,
            "total_tokens": 24_000,
            "cost": {"currency": "GBP", "amount": 0.0},
        },
        evidence_mode=EVIDENCE_MODE,
    )
    result = {
        "schema_version": "1.0",
        "experiment_id": "2025-26-gw12-sol-agent-fork-v1",
        "evidence_mode": EVIDENCE_MODE,
        "case_selection": str(reconstructed["case_selection"]),
        "code_commit": code_commit,
        "episode": {
            "episode_id": str(manifest["episode_id"]),
            "decision_cutoff": str(manifest["deadline"]),
            "observed_episode_sha256": str(
                manifest["observed"]["feature_snapshot_ref"]["content_sha256"]
            ),
            "snapshot_ids": list(manifest["observed"]["snapshot_ids"]),
            "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            "ruleset_sha256": str(manifest["ruleset"]["content_sha256"]),
        },
        "player_baselines": baselines,
        "evidence_documents": documents,
        "deterministic_candidate": candidate,
        "evidence_request": request,
        "limitations": [
            "sources_recovered_after_historical_decision",
            "case_selected_after_outcome_was_known",
            "subscription_subagent_is_an_experimental_host_surface",
            "not_eligible_for_headline_agent_performance",
        ],
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _fallback(
    solver_input: Mapping[str, Any], reason: str, evidence_run: Mapping[str, Any] | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    audit = _sealed(
        {
            "schema_version": "1.0",
            "policy_id": "agent-fork-adapter-v1",
            "policy_sha256": hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),
            "applied": False,
            "fallback_reason": reason,
            "evidence_run_sha256": (
                evidence_run.get("content_sha256") if evidence_run else None
            ),
            "adjustments": [],
        }
    )
    return deepcopy(dict(solver_input)), audit


def apply_agent_adjustments(
    solver_input: Mapping[str, Any],
    evidence_run: Mapping[str, Any],
    challenger_run: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply only independently unopposed, policy-safe reductions."""
    if evidence_run.get("content_sha256") != artifact_hash(evidence_run):
        return _fallback(solver_input, "evidence_run_hash_mismatch", evidence_run)
    if challenger_run.get("content_sha256") != artifact_hash(challenger_run):
        return _fallback(solver_input, "challenger_run_hash_mismatch", evidence_run)
    if evidence_run.get("status") != "completed":
        return _fallback(solver_input, "evidence_run_not_completed", evidence_run)
    if challenger_run.get("status") != "completed":
        return _fallback(solver_input, "challenger_run_not_completed", evidence_run)
    proposal = evidence_run.get("validated_output")
    review = challenger_run.get("validated_output")
    if not isinstance(proposal, Mapping) or not isinstance(review, Mapping):
        return _fallback(solver_input, "missing_validated_output", evidence_run)
    if review.get("proposal_sha256") != proposal.get("content_sha256"):
        return _fallback(solver_input, "challenger_proposal_binding_mismatch", evidence_run)
    gate = review.get("approval_gate", {})
    if (
        gate.get("requires_human_review")
        or gate.get("force_rerun")
        or gate.get("confidence_downgraded")
        or gate.get("unresolved_challenges")
    ):
        return _fallback(solver_input, "challenger_gate_blocked", evidence_run)
    proposals = list(proposal.get("proposed_adjustments", []))
    expected = {str(row.get("adjustment_id")) for row in proposals}
    unopposed = set(review.get("unopposed_proposed_adjustment_ids", []))
    if expected != unopposed:
        return _fallback(solver_input, "challenger_did_not_unoppose_every_adjustment", evidence_run)
    if not proposals:
        return _fallback(solver_input, "no_agent_adjustments", evidence_run)
    players = {str(row["player_id"]): row for row in solver_input["players"]}
    if len({str(row.get("player_uid")) for row in proposals}) != len(proposals):
        return _fallback(solver_input, "multiple_adjustments_for_player", evidence_run)

    policy = load_policy()
    adjusted = deepcopy(dict(solver_input))
    adjusted_players = {str(row["player_id"]): row for row in adjusted["players"]}
    applied: list[dict[str, Any]] = []
    for proposal_row in proposals:
        player_id = str(proposal_row.get("player_uid"))
        target = str(proposal_row.get("target"))
        if player_id not in players or target not in {
            "expected_minutes",
            "start_probability",
        }:
            return _fallback(solver_input, "unsupported_player_or_target", evidence_run)
        before_value = float(proposal_row["before_value"])
        after_value = float(proposal_row["after_value"])
        canonical_before = float(players[player_id][target])
        if before_value != canonical_before or after_value > before_value:
            return _fallback(solver_input, "baseline_mismatch_or_projection_increase", evidence_run)
        if target == "start_probability" and before_value - after_value > float(
            policy["thresholds"]["max_start_probability_delta"]
        ):
            return _fallback(solver_input, "start_probability_delta_exceeds_policy", evidence_run)
        row = adjusted_players[player_id]
        before = {
            "status": row.get("status"),
            "start_probability": float(row["start_probability"]),
            "expected_minutes": float(row["expected_minutes"]),
            "expected_points": float(row["expected_points"]),
        }
        ratio = after_value / before_value if before_value else 0.0
        row["start_probability"] = round(before["start_probability"] * ratio, 4)
        row["expected_minutes"] = round(before["expected_minutes"] * ratio, 1)
        row["expected_points"] = round(before["expected_points"] * ratio, 2)
        if row["expected_minutes"] == 0:
            row["status"] = "i"
        row["evidence_adjustment_ids"] = [str(proposal_row["adjustment_id"])]
        applied.append(
            {
                "adjustment_id": str(proposal_row["adjustment_id"]),
                "player_id": player_id,
                "target": target,
                "before": before,
                "after": {
                    "status": row.get("status"),
                    "start_probability": float(row["start_probability"]),
                    "expected_minutes": float(row["expected_minutes"]),
                    "expected_points": float(row["expected_points"]),
                },
                "ratio": ratio,
                "confidence": float(proposal_row["confidence"]),
                "claim_ids": list(proposal_row["signal_ids"]),
            }
        )
    audit = _sealed(
        {
            "schema_version": "1.0",
            "policy_id": "agent-fork-adapter-v1",
            "policy_sha256": hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),
            "applied": True,
            "fallback_reason": None,
            "evidence_run_sha256": str(evidence_run["content_sha256"]),
            "challenger_run_sha256": str(challenger_run["content_sha256"]),
            "adjustments": applied,
        }
    )
    return adjusted, audit


def run_isolated_agent_fork(
    *,
    host_bundle: Mapping[str, Any],
    evidence_run: Mapping[str, Any],
    challenger_run: Mapping[str, Any],
    canonical_root: Path,
    episode_root: Path,
    manual_fork_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Apply reviewed proposals, freeze, then reveal and compare GW12."""
    canonical_gw = canonical_root / "gw-12"
    if canonical_gw.resolve() == output_root.resolve() or canonical_gw.resolve() in output_root.resolve().parents:
        raise EvidenceForkError("Agent fork output must be outside the canonical replay")
    canonical_before = _tree_hash(canonical_gw)
    episode = episode_root / "gw-12"
    manifest = _read(episode / "episode-manifest.json")
    arm = canonical_gw / "setup/arms/evidence_agent"
    state = _read(arm / "starting-policy-state.json")
    original_input = _read(arm / "reviewed-engine-input.json")
    adjusted_input, audit = apply_agent_adjustments(
        original_input, evidence_run, challenger_run
    )
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    solver_output = solve(
        SolverInput.from_dict(adjusted_input),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    candidate = deepcopy(dict(solver_output["selected"]))
    plan = validate_and_freeze_plan(
        episode_id=str(manifest["episode_id"]),
        policy_arm="evidence_agent",
        state=state,
        candidate=candidate,
        decision_market=adjusted_input["players"],
        active_chip=None,
        frozen_at=str(manifest["deadline"]),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    if plan.get("validation", {}).get("status") != "passed" or not plan.get("content_sha256"):
        raise EvidenceForkError("Hidden outcome access requires a frozen valid plan")

    hidden = _read(episode / "hidden-outcome.json")
    identity = _read(episode / "identity-map.json")
    shared = _read(canonical_gw / "shared-context.json")
    canonical_outcome = _read(canonical_gw / "evidence_agent/realised-outcome.json")
    outcome = score_revealed_outcome(
        plan,
        hidden,
        revealed_at=str(canonical_outcome["revealed_at"]),
        rules=rules,
        ruleset_sha256=rules_hash,
        player_identity_map=_identity_index(identity),
        identity_map_sha256=str(shared["identity_map_sha256"]),
    )
    manual = _read(manual_fork_root / "comparison.json")
    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in adjusted_input["players"]
    }
    canonical_after = _tree_hash(canonical_gw)
    if canonical_after != canonical_before:
        raise EvidenceForkError("Canonical GW12 changed during the agent fork")
    comparison = _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": str(host_bundle["experiment_id"]),
            "season": "2025-26",
            "gameweek": 12,
            "exploratory_only": True,
            "adapter_applied": bool(audit["applied"]),
            "canonical_gross_points": int(canonical_outcome["gross_points"]),
            "manual_fork_gross_points": int(manual["fork_gross_points"]),
            "agent_fork_gross_points": int(outcome["gross_points"]),
            "agent_vs_canonical_delta": int(outcome["gross_points"])
            - int(canonical_outcome["gross_points"]),
            "agent_vs_manual_delta": int(outcome["gross_points"])
            - int(manual["fork_gross_points"]),
            "selected_transfer_names": [
                {
                    "player_out": names[move["player_out_id"]],
                    "player_in": names[move["player_in_id"]],
                }
                for move in candidate["transfers"]
            ],
            "captain": names[candidate["lineup"]["captain_id"]],
            "hit_cost": int(candidate["hit_cost"]),
            "planning_objective": float(candidate["objective"]),
            "canonical_tree_sha256_before": canonical_before,
            "canonical_tree_sha256_after": canonical_after,
            "host_bundle_sha256": str(host_bundle["content_sha256"]),
            "evidence_run_sha256": str(evidence_run["content_sha256"]),
            "challenger_run_sha256": str(challenger_run["content_sha256"]),
            "adapter_audit_sha256": str(audit["content_sha256"]),
            "solver_input_sha256": fingerprint(adjusted_input),
            "solver_output_sha256": fingerprint(solver_output),
            "plan_sha256": str(plan["content_sha256"]),
            "limitations": list(host_bundle["limitations"]),
        }
    )
    _write_once(output_root / "host-bundle.json", host_bundle)
    _write_once(output_root / "evidence-run.json", evidence_run)
    _write_once(output_root / "challenger-run.json", challenger_run)
    _write_once(output_root / "adapter-audit.json", audit)
    _write_once(output_root / "adjusted-solver-input.json", adjusted_input)
    _write_once(
        output_root / "selected-candidate.json",
        _sealed(
            {
                "schema_version": "1.0",
                "candidate": candidate,
                "solver_output_sha256": fingerprint(solver_output),
            }
        ),
    )
    _write_once(output_root / "validated-plan.json", plan)
    _write_once(output_root / "realised-outcome.json", outcome)
    _write_once(output_root / "comparison.json", comparison)
    return comparison
