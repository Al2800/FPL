#!/usr/bin/env python3
"""Prepare or run the isolated GPT-5.6 Sol GW12 evidence fork."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from src.orchestration.agent_arm import build_hosted_request, run_agent_arm
from src.orchestration.agent_fork_adapter import (
    build_gw12_agent_host_bundle,
    run_isolated_agent_fork,
)
from src.orchestration.evidence_fork import _write_once


REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "evals/evidence-forks/2025-26/gw-12"
OUT = REPO / "reports/benchmarks/2025-26-agent-forks/gw-12/sol-v1"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _bundle() -> dict:
    return build_gw12_agent_host_bundle(
        evidence_bundle_path=EVAL / "evidence-bundle.json",
        canonical_root=REPO / "reports/benchmarks/2025-26",
        episode_root=REPO / "data/benchmark-v0/episodes/v2/2025-26",
        code_commit=_commit(),
    )


def _evidence_run(bundle: dict, response_path: Path) -> dict:
    return run_agent_arm(
        request=bundle["evidence_request"],
        hosted_response=_read(response_path),
        deterministic_candidate=bundle["deterministic_candidate"],
        code_commit=str(bundle["code_commit"]),
    )


def _challenger_request(bundle: dict, evidence_run: dict) -> dict:
    request = bundle["evidence_request"]
    return build_hosted_request(
        arm="evidence_challenger",
        run_id="gw12-sol-challenger-v1",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("prepare", "validate-evidence", "complete"),
        default="prepare",
    )
    parser.add_argument(
        "--evidence-response",
        type=Path,
        default=OUT / "evidence-hosted-response.json",
    )
    parser.add_argument(
        "--challenger-response",
        type=Path,
        default=OUT / "challenger-hosted-response.json",
    )
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    bundle = _bundle()
    _write_once(EVAL / "agent-host-bundle.json", bundle)
    if args.mode == "prepare":
        result = {
            "host_bundle": str(EVAL / "agent-host-bundle.json"),
            "request_sha256": bundle["evidence_request"]["rendered_input_sha256"],
        }
    else:
        evidence_run = _evidence_run(bundle, args.evidence_response)
        challenger_request = _challenger_request(bundle, evidence_run)
        _write_once(args.out / "evidence-run.json", evidence_run)
        _write_once(args.out / "challenger-request.json", challenger_request)
        if args.mode == "validate-evidence":
            result = {
                "evidence_status": evidence_run["status"],
                "challenger_request": str(args.out / "challenger-request.json"),
                "request_sha256": challenger_request["rendered_input_sha256"],
            }
        else:
            challenger_run = run_agent_arm(
                request=challenger_request,
                hosted_response=_read(args.challenger_response),
                deterministic_candidate=bundle["deterministic_candidate"],
                code_commit=str(bundle["code_commit"]),
                evidence_proposal=evidence_run,
            )
            result = run_isolated_agent_fork(
                host_bundle=bundle,
                evidence_run=evidence_run,
                challenger_run=challenger_run,
                canonical_root=REPO / "reports/benchmarks/2025-26",
                episode_root=REPO / "data/benchmark-v0/episodes/v2/2025-26",
                manual_fork_root=(
                    REPO
                    / "reports/benchmarks/2025-26-forks/gw-12/"
                    "retrospective-availability-v1"
                ),
                output_root=args.out,
            )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
