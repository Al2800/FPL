#!/usr/bin/env python3
"""Prepare and run the sequential GW13/GW14 Sol evidence forks."""

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
    build_same_state_control_attribution,
    build_agent_host_bundle,
    build_fork_solver_input,
    derive_gw13_state_from_gw12_agent_fork,
    run_sequential_agent_fork_week,
)
from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
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


def _output(gameweek: int) -> Path:
    return AGENT_ROOT / f"gw-{gameweek:02d}/sol-v1"


def _state(gameweek: int) -> dict:
    if gameweek == 13:
        state, _ = derive_gw13_state_from_gw12_agent_fork(
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            gw12_fork_root=AGENT_ROOT / "gw-12/sol-v1",
        )
        return state
    if gameweek == 14:
        return _read(_output(13) / "next-policy-state.json")
    raise ValueError("Only GW13 and GW14 are supported")


def _bundle(gameweek: int) -> dict:
    state = _state(gameweek)
    solver_input = build_fork_solver_input(
        gameweek=gameweek, state=state, canonical_root=CANONICAL
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
    return build_agent_host_bundle(
        gameweek=gameweek,
        evidence_bundle_path=(
            REPO
            / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/evidence-bundle.json"
        ),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        solver_input=solver_input,
        deterministic_candidate=candidate,
        code_commit=_commit(),
    )


def _evidence_run(gameweek: int, bundle: dict) -> dict:
    return run_agent_arm(
        request=bundle["evidence_request"],
        hosted_response=_read(_output(gameweek) / "evidence-hosted-response.json"),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
    )


def _challenger_request(bundle: dict, evidence_run: dict) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_challenger",
        run_id=f"gw{bundle['gameweek']:02d}-sol-challenger-v1",
        episode_id=str(request["episode"]["episode_id"]),
        observed_episode_sha256=str(request["episode"]["observed_episode_sha256"]),
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


def _prepare(gameweek: int) -> dict:
    bundle = _bundle(gameweek)
    path = (
        REPO
        / f"evals/evidence-forks/2025-26/gw-{gameweek:02d}/agent-host-bundle.json"
    )
    _write_once(path, bundle)
    return {
        "gameweek": gameweek,
        "host_bundle": str(path),
        "request_sha256": bundle["evidence_request"]["rendered_input_sha256"],
    }


def _validate_evidence(gameweek: int) -> dict:
    bundle = _bundle(gameweek)
    evidence_run = _evidence_run(gameweek, bundle)
    request = _challenger_request(bundle, evidence_run)
    _write_once(_output(gameweek) / "evidence-run.json", evidence_run)
    _write_once(_output(gameweek) / "challenger-request.json", request)
    return {
        "gameweek": gameweek,
        "evidence_status": evidence_run["status"],
        "request_sha256": request["rendered_input_sha256"],
    }


def _complete_week(gameweek: int) -> dict:
    bundle = _bundle(gameweek)
    evidence_run = _evidence_run(gameweek, bundle)
    request = _challenger_request(bundle, evidence_run)
    challenger_run = run_agent_arm(
        request=request,
        hosted_response=_read(_output(gameweek) / "challenger-hosted-response.json"),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
        evidence_proposal=evidence_run,
    )
    _write_once(_output(gameweek) / "challenger-request.json", request)
    comparison, _, _ = run_sequential_agent_fork_week(
        gameweek=gameweek,
        state=_state(gameweek),
        host_bundle=bundle,
        evidence_run=evidence_run,
        challenger_run=challenger_run,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=_output(gameweek),
        transition_to_next=gameweek == 13,
    )
    attribution = build_same_state_control_attribution(
        gameweek=gameweek,
        state=_state(gameweek),
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        agent_output_root=_output(gameweek),
    )
    comparison = {**comparison, "same_state_attribution": attribution}
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("prepare", "validate-evidence", "complete-week", "complete"),
        default="prepare",
    )
    parser.add_argument("--gameweek", type=int, choices=(13, 14), default=13)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = _prepare(args.gameweek)
    elif args.mode == "validate-evidence":
        result = _validate_evidence(args.gameweek)
    elif args.mode == "complete-week":
        result = _complete_week(args.gameweek)
    else:
        result = {"gw13": _complete_week(13), "gw14": _complete_week(14)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
