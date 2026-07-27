"""Auditable GW2-GW11 evidence replay over isolated and carried policy states."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.agent_arm import build_hosted_request, run_agent_arm
from src.orchestration.agent_fork_adapter import (
    build_fork_solver_input,
    build_same_state_control_attribution,
    run_sequential_agent_fork_week,
)
from src.orchestration.early_season_actionability import (
    attach_actionability_to_request,
    build_actionability_assessment,
    enforce_actionability,
)
from src.orchestration.evidence_fork import EvidenceForkError, _read, _sealed, _write_once


EVIDENCE_MODE = "retrospective_published_before_deadline"
FIRST_GAMEWEEK = 2
LAST_GAMEWEEK = 11


def _tree_hash(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in path.rglob("*")
        if item.is_file() and item.name != "evidence-early-season.html"
    )
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(files)


def _document(candidate: Mapping[str, Any]) -> dict[str, Any]:
    evidence_id = str(candidate["evidence_id"])
    document = {
        "document_id": f"document:{evidence_id}",
        "source_id": str(candidate["source_id"]),
        "title": str(candidate["title"]),
        "published_at": str(candidate["published_at"]),
        "observed_at": str(candidate["observed_at"]),
        "available_at": str(candidate["available_at"]),
        "passages": {
            f"passage:{evidence_id}": str(candidate["citation_excerpt"]),
        },
    }
    document["content_sha256"] = artifact_hash(document)
    return document


def _manifest_entry(manifest: Mapping[str, Any], gameweek: int) -> dict[str, Any]:
    entries = {
        int(entry["gameweek"]): dict(entry)
        for entry in manifest.get("entries", [])
    }
    if gameweek not in entries:
        raise EvidenceForkError(f"Early-season manifest has no GW{gameweek}")
    entry = entries[gameweek]
    if entry.get("decision_type") != "weekly_management":
        raise EvidenceForkError(f"GW{gameweek} is not a weekly-management entry")
    if not entry.get("search_complete"):
        raise EvidenceForkError(f"GW{gameweek} research is incomplete")
    candidates = [
        row
        for row in entry.get("candidates", [])
        if row.get("admission_status") == "admitted_exploratory"
    ]
    if not candidates:
        raise EvidenceForkError(f"GW{gameweek} has no admitted evidence")
    entry["admitted_candidates"] = candidates
    return entry


def _candidate_player_ids(entry: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            str(player_id)
            for candidate in entry["admitted_candidates"]
            for player_id in candidate["player_ids"]
        }
    )


def build_early_host_bundle(
    *,
    gameweek: int,
    early_manifest: Mapping[str, Any],
    state: Mapping[str, Any],
    canonical_root: Path,
    episode_root: Path,
    code_commit: str,
) -> dict[str, Any]:
    """Build one observed-only evidence request from the frozen manifest."""
    if gameweek < FIRST_GAMEWEEK or gameweek > LAST_GAMEWEEK:
        raise EvidenceForkError("Early-season hosted bundles support GW2-GW11")
    entry = _manifest_entry(early_manifest, gameweek)
    episode = episode_root / f"gw-{gameweek:02d}"
    episode_manifest = _read(episode / "episode-manifest.json")
    if str(entry["decision_cutoff"]) != str(episode_manifest["deadline"]):
        raise EvidenceForkError("Evidence cutoff does not match the episode")
    if str(entry["episode_id"]) != str(episode_manifest["episode_id"]):
        raise EvidenceForkError("Evidence episode identity does not match the episode")

    solver_input = build_fork_solver_input(
        gameweek=gameweek,
        state=state,
        canonical_root=canonical_root,
    )
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    deterministic_candidate = solve(
        SolverInput.from_dict(solver_input),
        rules=rules,
        ruleset_sha256=str(episode_manifest["ruleset"]["content_sha256"]),
    )["selected"]
    indexed = {str(row["player_id"]): row for row in solver_input["players"]}
    player_ids = _candidate_player_ids(entry)
    missing = sorted(set(player_ids) - set(indexed))
    if missing:
        raise EvidenceForkError(
            "Evidence player is absent from the frozen market: " + ",".join(missing)
        )
    baselines = {
        player_id: {
            "expected_minutes": float(indexed[player_id]["expected_minutes"]),
            "start_probability": float(indexed[player_id]["start_probability"]),
        }
        for player_id in player_ids
    }
    documents = [_document(row) for row in entry["admitted_candidates"]]
    request = build_hosted_request(
        arm="evidence_agent",
        run_id=f"gw{gameweek:02d}-early-sol-evidence-v1",
        episode_id=str(episode_manifest["episode_id"]),
        observed_episode_sha256=str(
            episode_manifest["observed"]["feature_snapshot_ref"]["content_sha256"]
        ),
        snapshot_ids=list(episode_manifest["observed"]["snapshot_ids"]),
        decision_at=str(episode_manifest["deadline"]),
        ruleset_id=str(episode_manifest["ruleset"]["ruleset_id"]),
        player_ids=player_ids,
        player_baselines=baselines,
        evidence_documents=documents,
        deterministic_candidate_sha256=artifact_hash(deterministic_candidate),
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
    actionability = build_actionability_assessment(
        gameweek=gameweek, entry=entry
    )
    request = attach_actionability_to_request(request, actionability)
    value = {
        "schema_version": "1.0",
        "experiment_id": f"2025-26-gw{gameweek:02d}-early-evidence-v1",
        "gameweek": gameweek,
        "evidence_mode": EVIDENCE_MODE,
        "case_selection": "retrospective_boundary_targeted_not_preregistered",
        "code_commit": code_commit,
        "episode": {
            "episode_id": str(episode_manifest["episode_id"]),
            "decision_cutoff": str(episode_manifest["deadline"]),
            "observed_episode_sha256": str(entry["observed_episode_sha256"]),
            "ruleset_id": str(episode_manifest["ruleset"]["ruleset_id"]),
            "ruleset_sha256": str(
                episode_manifest["ruleset"]["content_sha256"]
            ),
        },
        "manifest_entry_sha256": str(entry["content_sha256"]),
        "starting_state_sha256": str(state["content_sha256"]),
        "player_baselines": baselines,
        "evidence_documents": documents,
        "deterministic_candidate": deepcopy(dict(deterministic_candidate)),
        "evidence_request": request,
        "actionability_assessment": actionability,
        "reuse_contract": {
            "allowed_between_isolated_and_longitudinal": True,
            "condition": "exact_player_baseline_equality",
            "decision_fields_excluded_from_agent_authority": [
                "transfers",
                "lineup",
                "captain",
                "chips",
            ],
        },
        "limitations": [
            "sources_recovered_after_historical_decision",
            "case_selected_after_outcome_was_known",
            "publication_precision_may_be_date_only_or_inferred",
            "not_eligible_for_headline_agent_performance",
            "subscription_subagent_is_an_experimental_host_surface",
        ],
    }
    value["content_sha256"] = artifact_hash(value)
    return value


def build_early_challenger_request(
    *,
    host_bundle: Mapping[str, Any],
    evidence_run: Mapping[str, Any],
) -> dict[str, Any]:
    request = host_bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_challenger",
        run_id=f"gw{int(host_bundle['gameweek']):02d}-early-sol-challenger-v1",
        episode_id=str(request["episode"]["episode_id"]),
        observed_episode_sha256=str(
            request["episode"]["observed_episode_sha256"]
        ),
        snapshot_ids=list(request["episode"]["snapshot_ids"]),
        decision_at=str(request["episode"]["decision_at"]),
        ruleset_id=str(request["episode"]["ruleset_id"]),
        player_ids=list(request["player_ids"]),
        player_baselines=request["player_baselines"],
        evidence_documents=request["evidence_documents"],
        deterministic_candidate_sha256=str(
            request["deterministic_candidate_sha256"]
        ),
        budget=request["budget"],
        evidence_proposal=evidence_run,
        evidence_mode=str(request["evidence_mode"]),
    )


def validate_hosted_pair(
    *,
    host_bundle: Mapping[str, Any],
    evidence_hosted_response: Mapping[str, Any],
    challenger_hosted_response: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence_run = run_agent_arm(
        request=host_bundle["evidence_request"],
        hosted_response=evidence_hosted_response,
        deterministic_candidate=host_bundle["deterministic_candidate"],
        code_commit=str(host_bundle["code_commit"]),
    )
    enforce_actionability(
        evidence_run=evidence_run,
        assessment=host_bundle["actionability_assessment"],
    )
    challenger_request = build_early_challenger_request(
        host_bundle=host_bundle,
        evidence_run=evidence_run,
    )
    challenger_run = run_agent_arm(
        request=challenger_request,
        hosted_response=challenger_hosted_response,
        deterministic_candidate=host_bundle["deterministic_candidate"],
        code_commit=str(host_bundle["code_commit"]),
        evidence_proposal=evidence_run,
    )
    return evidence_run, challenger_request, challenger_run


def assert_reusable_baselines(
    *,
    gameweek: int,
    state: Mapping[str, Any],
    host_bundle: Mapping[str, Any],
    canonical_root: Path,
) -> None:
    solver_input = build_fork_solver_input(
        gameweek=gameweek,
        state=state,
        canonical_root=canonical_root,
    )
    indexed = {str(row["player_id"]): row for row in solver_input["players"]}
    current = {
        player_id: {
            "expected_minutes": float(indexed[player_id]["expected_minutes"]),
            "start_probability": float(indexed[player_id]["start_probability"]),
        }
        for player_id in host_bundle["player_baselines"]
    }
    if current != host_bundle["player_baselines"]:
        raise EvidenceForkError(
            f"GW{gameweek} longitudinal baselines differ; hosted proposal cannot be reused"
        )


def run_early_season_replay(
    *,
    early_manifest: Mapping[str, Any],
    host_bundles: Mapping[int, Mapping[str, Any]],
    evidence_runs: Mapping[int, Mapping[str, Any]],
    challenger_runs: Mapping[int, Mapping[str, Any]],
    canonical_root: Path,
    episode_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Run isolated forks and an independent GW2-GW11 carried trajectory."""
    before_hash, before_count = _tree_hash(canonical_root)
    isolated: list[dict[str, Any]] = []
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        state = _read(
            canonical_root
            / f"gw-{gameweek:02d}/setup/arms/evidence_agent/starting-policy-state.json"
        )
        week_root = output_root / "isolated" / f"gw-{gameweek:02d}"
        comparison, _, _ = run_sequential_agent_fork_week(
            gameweek=gameweek,
            state=state,
            host_bundle=host_bundles[gameweek],
            evidence_run=evidence_runs[gameweek],
            challenger_run=challenger_runs[gameweek],
            canonical_root=canonical_root,
            episode_root=episode_root,
            output_root=week_root,
            transition_to_next=False,
        )
        attribution = build_same_state_control_attribution(
            gameweek=gameweek,
            state=state,
            canonical_root=canonical_root,
            episode_root=episode_root,
            agent_output_root=week_root,
        )
        isolated.append(
            {
                **comparison,
                "same_state_attribution": attribution,
            }
        )

    state = _read(
        canonical_root
        / "gw-02/setup/arms/evidence_agent/starting-policy-state.json"
    )
    longitudinal: list[dict[str, Any]] = []
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        assert_reusable_baselines(
            gameweek=gameweek,
            state=state,
            host_bundle=host_bundles[gameweek],
            canonical_root=canonical_root,
        )
        week_root = output_root / "longitudinal" / f"gw-{gameweek:02d}"
        comparison, successor, _ = run_sequential_agent_fork_week(
            gameweek=gameweek,
            state=state,
            host_bundle=host_bundles[gameweek],
            evidence_run=evidence_runs[gameweek],
            challenger_run=challenger_runs[gameweek],
            canonical_root=canonical_root,
            episode_root=episode_root,
            output_root=week_root,
            transition_to_next=True,
        )
        attribution = build_same_state_control_attribution(
            gameweek=gameweek,
            state=state,
            canonical_root=canonical_root,
            episode_root=episode_root,
            agent_output_root=week_root,
        )
        longitudinal.append(
            {
                **comparison,
                "same_state_attribution": attribution,
            }
        )
        if successor is None:
            raise EvidenceForkError("Longitudinal replay did not produce successor state")
        state = successor

    canonical_gw12 = _read(
        canonical_root
        / "gw-12/setup/arms/evidence_agent/starting-policy-state.json"
    )
    canonical_weeks = []
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        transition = _read(
            canonical_root
            / f"gw-{gameweek:02d}/evidence_agent/state-transition.json"
        )
        canonical_weeks.append(
            {
                "gameweek": gameweek,
                "net_points": int(transition["net_points"]),
                "next_state_sha256": str(
                    _read(
                        canonical_root
                        / f"gw-{gameweek:02d}/evidence_agent/next-policy-state.json"
                    )["content_sha256"]
                ),
            }
        )

    after_hash, after_count = _tree_hash(canonical_root)
    if (before_hash, before_count) != (after_hash, after_count):
        raise EvidenceForkError("Canonical replay changed during early-season fork")
    protocol = {
        "week_count": len(evidence_runs),
        "evidence_completed": sum(
            run["status"] == "completed" for run in evidence_runs.values()
        ),
        "challenger_completed": sum(
            run["status"] == "completed" for run in challenger_runs.values()
        ),
        "evidence_adjustment_weeks": sum(
            bool((run.get("validated_output") or {}).get("proposed_adjustments"))
            for run in evidence_runs.values()
        ),
        "evidence_abstention_weeks": sum(
            not bool((run.get("validated_output") or {}).get("proposed_adjustments"))
            for run in evidence_runs.values()
        ),
    }
    result = _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": "2025-26-early-season-evidence-replay-v1",
            "season": "2025-26",
            "start_gameweek": FIRST_GAMEWEEK,
            "terminal_gameweek": LAST_GAMEWEEK,
            "exploratory_only": True,
            "promotion_eligible": False,
            "manifest_sha256": str(early_manifest["content_sha256"]),
            "isolated_weeks": isolated,
            "longitudinal_weeks": longitudinal,
            "frozen_no_evidence_shadow": {
                "source": "accepted_canonical_evidence_agent_trajectory",
                "weeks": canonical_weeks,
                "net_points": sum(row["net_points"] for row in canonical_weeks),
            },
            "longitudinal_net_points": sum(
                int(
                    _read(
                        output_root
                        / "longitudinal"
                        / f"gw-{gameweek:02d}"
                        / "state-transition.json"
                    )["net_points"]
                )
                for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1)
            ),
            "gw12_bridge": {
                "canonical_state_sha256": str(canonical_gw12["content_sha256"]),
                "fork_state_sha256": str(state["content_sha256"]),
                "states_equal": state == canonical_gw12,
                "canonical_cumulative_points": int(
                    canonical_gw12["cumulative_points"]
                ),
                "fork_cumulative_points": int(state["cumulative_points"]),
                "cumulative_points_delta": int(state["cumulative_points"])
                - int(canonical_gw12["cumulative_points"]),
                "canonical_bank": float(canonical_gw12["bank"]),
                "fork_bank": float(state["bank"]),
                "bank_delta": float(state["bank"])
                - float(canonical_gw12["bank"]),
                "canonical_free_transfers": int(
                    canonical_gw12["free_transfers"]
                ),
                "fork_free_transfers": int(state["free_transfers"]),
                "squad_symmetric_difference": sorted(
                    {
                        str(row["player_id"])
                        for row in state["squad"]
                    }
                    ^ {
                        str(row["player_id"])
                        for row in canonical_gw12["squad"]
                    }
                ),
            },
            "protocol_metrics": protocol,
            "canonical_artifacts": {
                "file_count": before_count,
                "tree_sha256_before": before_hash,
                "tree_sha256_after": after_hash,
                "unchanged": True,
            },
            "limitations": [
                "retrospective_case_selection_can_overstate_evidence_value",
                "hosted_interpretation_is_reused_only_under_exact_baseline_equality",
                "canonical_no_evidence_shadow_is_frozen_not_recomputed",
                "gw12_bridge_is_reported_not_spliced_into_accepted_trajectory",
            ],
        }
    )
    _write_once(output_root / "early-season-summary.json", result)
    return result
