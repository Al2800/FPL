#!/usr/bin/env python3
"""Prepare and run sequential GW18-GW22 Sol evidence forks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import yaml

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
from src.forecasting.live_faithful import artifact_hash


REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "reports/benchmarks/2025-26"
EPISODES = REPO / "data/benchmark-v0/episodes/v2/2025-26"
AGENT_ROOT = REPO / "reports/benchmarks/2025-26-agent-forks"


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _output(gameweek: int, artifact_version: str = "sol-v1") -> Path:
    return AGENT_ROOT / f"gw-{gameweek:02d}/{artifact_version}"


def _state(gameweek: int, artifact_version: str = "sol-v1") -> dict:
    if artifact_version != "sol-v1":
        if gameweek == 20:
            return _read(_output(20, "sol-v1") / "starting-policy-state.json")
        if 21 <= gameweek <= 22:
            return _read(
                _output(gameweek - 1, artifact_version)
                / "next-policy-state.json"
            )
        raise ValueError(
            f"{artifact_version} supports only GW20-GW22"
        )
    if gameweek == 18:
        state, _ = derive_next_state_from_agent_fork(
            gameweek=17, canonical_root=CANONICAL, episode_root=EPISODES,
            fork_root=_output(17, artifact_version),
        )
        return state
    if 19 <= gameweek <= 22:
        return _read(
            _output(gameweek - 1, artifact_version)
            / "next-policy-state.json"
        )
    raise ValueError("Only GW18-GW22 are supported")


def _versioned_evidence_request(bundle: dict, artifact_version: str) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_agent",
        run_id=f"gw{bundle['gameweek']:02d}-sol-evidence-{artifact_version[-2:]}",
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


def _bundle(gameweek: int, artifact_version: str = "sol-v1") -> dict:
    state = _state(gameweek, artifact_version)
    solver_input = build_fork_solver_input(
        gameweek=gameweek, state=state, canonical_root=CANONICAL
    )
    manifest = _read(EPISODES / f"gw-{gameweek:02d}/episode-manifest.json")
    rules = yaml.safe_load(
        (EPISODES / f"gw-{gameweek:02d}/ruleset.yaml").read_text(encoding="utf-8")
    )
    candidate = solve(
        SolverInput.from_dict(solver_input), rules=rules,
        ruleset_sha256=str(manifest["ruleset"]["content_sha256"]),
    )["selected"]
    bundle = build_agent_host_bundle(
        gameweek=gameweek,
        evidence_bundle_path=REPO / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/evidence-bundle.json",
        canonical_root=CANONICAL, episode_root=EPISODES,
        solver_input=solver_input, deterministic_candidate=candidate,
        code_commit=_commit(),
    )
    if artifact_version != "sol-v1":
        bundle["experiment_id"] = (
            f"2025-26-gw{gameweek:02d}-sol-agent-fork-"
            f"{artifact_version[-2:]}"
        )
        bundle["evidence_request"] = _versioned_evidence_request(
            bundle, artifact_version
        )
        bundle["content_sha256"] = artifact_hash(bundle)
    return bundle


def _evidence_run(
    gameweek: int, bundle: dict, artifact_version: str = "sol-v1"
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
    bundle: dict, evidence_run: dict, artifact_version: str = "sol-v1"
) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_challenger",
        run_id=(
            f"gw{bundle['gameweek']:02d}-sol-challenger-"
            f"{artifact_version[-2:]}"
        ),
        episode_id=str(request["episode"]["episode_id"]),
        observed_episode_sha256=str(request["episode"]["observed_episode_sha256"]),
        snapshot_ids=list(request["episode"]["snapshot_ids"]),
        decision_at=str(request["episode"]["decision_at"]),
        ruleset_id=str(request["episode"]["ruleset_id"]),
        player_ids=list(request["player_ids"]),
        player_baselines=request["player_baselines"],
        evidence_documents=request["evidence_documents"],
        deterministic_candidate_sha256=str(request["deterministic_candidate_sha256"]),
        budget=request["budget"], evidence_proposal=evidence_run,
        evidence_mode=str(request["evidence_mode"]),
    )


def _prepare(gameweek: int, artifact_version: str = "sol-v1") -> dict:
    bundle = _bundle(gameweek, artifact_version)
    suffix = "" if artifact_version == "sol-v1" else f"-{artifact_version}"
    path = REPO / (
        f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/"
        f"agent-host-bundle{suffix}.json"
    )
    _write_once(path, bundle)
    return {"gameweek": gameweek, "host_bundle": str(path),
            "request_sha256": bundle["evidence_request"]["rendered_input_sha256"]}


def _validate_evidence(
    gameweek: int, artifact_version: str = "sol-v1"
) -> dict:
    bundle = _bundle(gameweek, artifact_version)
    evidence_run = _evidence_run(gameweek, bundle, artifact_version)
    request = _challenger_request(
        bundle, evidence_run, artifact_version
    )
    _write_once(
        _output(gameweek, artifact_version) / "evidence-run.json",
        evidence_run,
    )
    _write_once(
        _output(gameweek, artifact_version) / "challenger-request.json",
        request,
    )
    return {"gameweek": gameweek, "evidence_status": evidence_run["status"],
            "request_sha256": request["rendered_input_sha256"]}


def _complete_week(
    gameweek: int, artifact_version: str = "sol-v1"
) -> dict:
    bundle = _bundle(gameweek, artifact_version)
    evidence_run = _evidence_run(gameweek, bundle, artifact_version)
    request = _challenger_request(
        bundle, evidence_run, artifact_version
    )
    challenger_run = run_agent_arm(
        request=request,
        hosted_response=_read(
            _output(gameweek, artifact_version)
            / "challenger-hosted-response.json"
        ),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]), evidence_proposal=evidence_run,
    )
    _write_once(
        _output(gameweek, artifact_version) / "challenger-request.json",
        request,
    )
    comparison, _, _ = run_sequential_agent_fork_week(
        gameweek=gameweek,
        state=_state(gameweek, artifact_version),
        host_bundle=bundle,
        evidence_run=evidence_run, challenger_run=challenger_run,
        canonical_root=CANONICAL, episode_root=EPISODES,
        output_root=_output(gameweek, artifact_version),
        transition_to_next=gameweek < 22,
    )
    attribution = build_same_state_control_attribution(
        gameweek=gameweek,
        state=_state(gameweek, artifact_version),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        agent_output_root=_output(gameweek, artifact_version),
    )
    return {**comparison, "same_state_attribution": attribution}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("prepare", "validate-evidence", "complete-week", "complete"), default="prepare")
    parser.add_argument("--gameweek", type=int, choices=range(18, 23), default=18)
    parser.add_argument(
        "--artifact-version",
        choices=("sol-v1", "sol-v2", "sol-v3"),
        default="sol-v1",
    )
    args = parser.parse_args()
    if (
        args.mode != "complete"
        and args.artifact_version != "sol-v1"
        and args.gameweek < 20
    ):
        parser.error(
            f"{args.artifact_version} supports only GW20-GW22"
        )
    if args.mode == "prepare":
        result = _prepare(args.gameweek, args.artifact_version)
    elif args.mode == "validate-evidence":
        result = _validate_evidence(args.gameweek, args.artifact_version)
    elif args.mode == "complete-week":
        result = _complete_week(args.gameweek, args.artifact_version)
    else:
        first = 20 if args.artifact_version != "sol-v1" else 18
        result = {
            f"gw{gw}": _complete_week(gw, args.artifact_version)
            for gw in range(first, 23)
        }
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
