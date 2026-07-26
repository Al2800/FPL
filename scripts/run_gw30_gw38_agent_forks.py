#!/usr/bin/env python3
"""Prepare and run the sequential GW30-GW38 Sol evidence trajectory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.agent_arm import build_hosted_request, run_agent_arm
from src.orchestration.agent_fork_adapter import (
    build_agent_host_bundle,
    build_fork_solver_input,
    build_same_state_control_attribution,
    derive_next_state_from_agent_fork,
    run_sequential_agent_fork_week,
)
from src.orchestration.evidence_fork import _read, _write_once


CANONICAL = REPO / "reports/benchmarks/2025-26"
EPISODES = REPO / "data/benchmark-v0/episodes/v2/2025-26"
AGENT_ROOT = REPO / "reports/benchmarks/2025-26-agent-forks"


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _output(gameweek: int, artifact_version: str) -> Path:
    return AGENT_ROOT / f"gw-{gameweek:02d}/{artifact_version}"


def _state(gameweek: int, previous_version: str) -> dict:
    if gameweek == 30:
        state, _ = derive_next_state_from_agent_fork(
            gameweek=29,
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            fork_root=_output(29, "sol-v1"),
        )
        return state
    if 31 <= gameweek <= 38:
        return _read(
            _output(gameweek - 1, previous_version)
            / "next-policy-state.json"
        )
    raise ValueError("Only GW30-GW38 are supported")


def _versioned_evidence_request(bundle: dict, artifact_version: str) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_agent",
        run_id=(
            f"gw{bundle['gameweek']:02d}-sol-evidence-"
            f"{artifact_version.removeprefix('sol-')}"
        ),
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
        evidence_mode=str(request["evidence_mode"]),
    )


def _bundle(
    gameweek: int, artifact_version: str, previous_version: str
) -> dict:
    state = _state(gameweek, previous_version)
    solver_input = build_fork_solver_input(
        gameweek=gameweek,
        state=state,
        canonical_root=CANONICAL,
    )
    manifest = _read(
        EPISODES / f"gw-{gameweek:02d}/episode-manifest.json"
    )
    rules = yaml.safe_load(
        (
            EPISODES / f"gw-{gameweek:02d}/ruleset.yaml"
        ).read_text(encoding="utf-8")
    )
    candidate = solve(
        SolverInput.from_dict(solver_input),
        rules=rules,
        ruleset_sha256=str(manifest["ruleset"]["content_sha256"]),
    )["selected"]
    bundle = build_agent_host_bundle(
        gameweek=gameweek,
        evidence_bundle_path=(
            REPO
            / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}"
            / "evidence-bundle.json"
        ),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        solver_input=solver_input,
        deterministic_candidate=candidate,
        code_commit=_commit(),
    )
    if artifact_version != "sol-v1":
        bundle["experiment_id"] = (
            f"2025-26-gw{gameweek:02d}-sol-agent-fork-"
            f"{artifact_version.removeprefix('sol-')}"
        )
        bundle["evidence_request"] = _versioned_evidence_request(
            bundle, artifact_version
        )
        bundle["content_sha256"] = artifact_hash(bundle)
    return bundle


def _evidence_run(
    gameweek: int, bundle: dict, artifact_version: str
) -> dict:
    return run_agent_arm(
        request=bundle["evidence_request"],
        hosted_response=_read(
            _output(gameweek, artifact_version)
            / "evidence-hosted-response.json"
        ),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
    )


def _challenger_request(
    bundle: dict, evidence_run: dict, artifact_version: str
) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_challenger",
        run_id=(
            f"gw{bundle['gameweek']:02d}-sol-challenger-"
            f"{artifact_version.removeprefix('sol-')}"
        ),
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


def _prepare(
    gameweek: int, artifact_version: str, previous_version: str
) -> dict:
    bundle = _bundle(gameweek, artifact_version, previous_version)
    suffix = "" if artifact_version == "sol-v1" else f"-{artifact_version}"
    path = (
        REPO
        / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}"
        / f"agent-host-bundle{suffix}.json"
    )
    _write_once(path, bundle)
    return {
        "gameweek": gameweek,
        "host_bundle": str(path),
        "request_sha256": bundle["evidence_request"][
            "rendered_input_sha256"
        ],
    }


def _validate_evidence(
    gameweek: int, artifact_version: str, previous_version: str
) -> dict:
    bundle = _bundle(gameweek, artifact_version, previous_version)
    evidence_run = _evidence_run(gameweek, bundle, artifact_version)
    _write_once(
        _output(gameweek, artifact_version) / "evidence-run.json",
        evidence_run,
    )
    if evidence_run["status"] != "completed":
        return {
            "gameweek": gameweek,
            "evidence_status": evidence_run["status"],
            "failure": evidence_run.get("trace", {}).get("failure"),
            "request_sha256": None,
        }
    request = _challenger_request(
        bundle, evidence_run, artifact_version
    )
    _write_once(
        _output(gameweek, artifact_version) / "challenger-request.json",
        request,
    )
    return {
        "gameweek": gameweek,
        "evidence_status": evidence_run["status"],
        "request_sha256": request["rendered_input_sha256"],
    }


def _validate_challenger(
    gameweek: int, artifact_version: str, previous_version: str
) -> dict:
    bundle = _bundle(gameweek, artifact_version, previous_version)
    evidence_run = _evidence_run(gameweek, bundle, artifact_version)
    request = _challenger_request(bundle, evidence_run, artifact_version)
    challenger_run = run_agent_arm(
        request=request,
        hosted_response=_read(
            _output(gameweek, artifact_version)
            / "challenger-hosted-response.json"
        ),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
        evidence_proposal=evidence_run,
    )
    _write_once(
        _output(gameweek, artifact_version) / "challenger-run.json",
        challenger_run,
    )
    return {
        "gameweek": gameweek,
        "challenger_status": challenger_run["status"],
        "failure_reason": challenger_run.get("failure_reason"),
    }


def _complete_week(
    gameweek: int, artifact_version: str, previous_version: str
) -> dict:
    state = _state(gameweek, previous_version)
    bundle = _bundle(gameweek, artifact_version, previous_version)
    evidence_run = _evidence_run(gameweek, bundle, artifact_version)
    request = _challenger_request(bundle, evidence_run, artifact_version)
    challenger_run = run_agent_arm(
        request=request,
        hosted_response=_read(
            _output(gameweek, artifact_version)
            / "challenger-hosted-response.json"
        ),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
        evidence_proposal=evidence_run,
    )
    if evidence_run["status"] != "completed":
        raise RuntimeError(
            "Refusing to score a non-completed evidence gate: "
            f"{evidence_run['status']}"
        )
    if challenger_run["status"] != "completed":
        raise RuntimeError(
            "Refusing to score a non-completed challenger gate: "
            f"{challenger_run['status']}"
        )
    _write_once(
        _output(gameweek, artifact_version) / "challenger-request.json",
        request,
    )
    comparison, _, _ = run_sequential_agent_fork_week(
        gameweek=gameweek,
        state=state,
        host_bundle=bundle,
        evidence_run=evidence_run,
        challenger_run=challenger_run,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=_output(gameweek, artifact_version),
        transition_to_next=gameweek < 38,
    )
    attribution = build_same_state_control_attribution(
        gameweek=gameweek,
        state=state,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        agent_output_root=_output(gameweek, artifact_version),
    )
    return {**comparison, "same_state_attribution": attribution}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=(
            "prepare",
            "validate-evidence",
            "validate-challenger",
            "complete-week",
        ),
        default="prepare",
    )
    parser.add_argument(
        "--gameweek", type=int, choices=range(30, 39), required=True
    )
    parser.add_argument("--artifact-version", default="sol-v1")
    parser.add_argument("--previous-version", default="sol-v1")
    args = parser.parse_args()
    if args.mode == "prepare":
        result = _prepare(
            args.gameweek, args.artifact_version, args.previous_version
        )
    elif args.mode == "validate-evidence":
        result = _validate_evidence(
            args.gameweek, args.artifact_version, args.previous_version
        )
    elif args.mode == "validate-challenger":
        result = _validate_challenger(
            args.gameweek, args.artifact_version, args.previous_version
        )
    else:
        result = _complete_week(
            args.gameweek, args.artifact_version, args.previous_version
        )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
