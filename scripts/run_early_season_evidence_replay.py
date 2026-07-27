#!/usr/bin/env python3
"""Prepare, validate, and run the GW2-GW11 evidence counterfactuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from src.orchestration.early_season_evidence_replay import (
    FIRST_GAMEWEEK,
    LAST_GAMEWEEK,
    build_early_host_bundle,
    run_early_season_replay,
    validate_hosted_pair,
)
from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
CANONICAL = REPO / "reports/benchmarks/2025-26"
EPISODES = REPO / "data/benchmark-v0/episodes/v2/2025-26"
EVIDENCE = REPO / "evals/evidence-forks/2025-26"
OUTPUT = REPO / "reports/benchmarks/2025-26-early-evidence"


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _manifest() -> dict:
    return _read(EVIDENCE / "early-season-manifest.json")


def _canonical_state(gameweek: int) -> dict:
    return _read(
        CANONICAL
        / f"gw-{gameweek:02d}/setup/arms/evidence_agent/starting-policy-state.json"
    )


def _bundle_path(gameweek: int) -> Path:
    return EVIDENCE / f"gw-{gameweek:02d}/agent-host-bundle-v2.json"


def _response_root(gameweek: int) -> Path:
    return OUTPUT / "hosted" / f"gw-{gameweek:02d}"


def _prepare() -> dict:
    manifest = _manifest()
    rows = []
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        bundle = build_early_host_bundle(
            gameweek=gameweek,
            early_manifest=manifest,
            state=_canonical_state(gameweek),
            canonical_root=CANONICAL,
            episode_root=EPISODES,
            code_commit=_commit(),
        )
        _write_once(_bundle_path(gameweek), bundle)
        rows.append(
            {
                "gameweek": gameweek,
                "host_bundle": str(_bundle_path(gameweek)),
                "request_sha256": bundle["evidence_request"][
                    "rendered_input_sha256"
                ],
            }
        )
    return {"mode": "prepare", "weeks": rows}


def _validated_pairs() -> tuple[dict[int, dict], dict[int, dict], dict[int, dict]]:
    bundles: dict[int, dict] = {}
    evidence_runs: dict[int, dict] = {}
    challenger_runs: dict[int, dict] = {}
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        bundle = _read(_bundle_path(gameweek))
        root = _response_root(gameweek)
        evidence, challenger_request, challenger = validate_hosted_pair(
            host_bundle=bundle,
            evidence_hosted_response=_read(root / "evidence-hosted-response.json"),
            challenger_hosted_response=_read(
                root / "challenger-hosted-response-v2.json"
            ),
        )
        _write_once(root / "evidence-run-v2.json", evidence)
        _write_once(root / "challenger-request-v2.json", challenger_request)
        _write_once(root / "challenger-run-v2.json", challenger)
        bundles[gameweek] = bundle
        evidence_runs[gameweek] = evidence
        challenger_runs[gameweek] = challenger
    return bundles, evidence_runs, challenger_runs


def _validate() -> dict:
    _, evidence, challengers = _validated_pairs()
    return {
        "mode": "validate",
        "weeks": [
            {
                "gameweek": gameweek,
                "evidence_status": evidence[gameweek]["status"],
                "challenger_status": challengers[gameweek]["status"],
                "adjustment_count": len(
                    (evidence[gameweek].get("validated_output") or {}).get(
                        "proposed_adjustments", []
                    )
                ),
            }
            for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1)
        ],
    }


def _run() -> dict:
    bundles, evidence, challengers = _validated_pairs()
    return run_early_season_replay(
        early_manifest=_manifest(),
        host_bundles=bundles,
        evidence_runs=evidence,
        challenger_runs=challengers,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=OUTPUT,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("prepare", "validate", "run"),
        default="prepare",
    )
    args = parser.parse_args()
    if args.mode == "prepare":
        result = _prepare()
    elif args.mode == "validate":
        result = _validate()
    else:
        result = _run()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
