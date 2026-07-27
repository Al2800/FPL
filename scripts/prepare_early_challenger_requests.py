#!/usr/bin/env python3
"""Validate early evidence outputs and seal their challenger requests."""

from __future__ import annotations

import json
from pathlib import Path

from src.orchestration.agent_arm import run_agent_arm
from src.orchestration.early_season_actionability import enforce_actionability
from src.orchestration.early_season_evidence_replay import (
    FIRST_GAMEWEEK,
    LAST_GAMEWEEK,
    build_early_challenger_request,
)
from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "evals/evidence-forks/2025-26"
OUTPUT = REPO / "reports/benchmarks/2025-26-early-evidence/hosted"


def main() -> int:
    rows = []
    for gameweek in range(FIRST_GAMEWEEK, LAST_GAMEWEEK + 1):
        bundle = _read(
            EVIDENCE
            / f"gw-{gameweek:02d}"
            / "agent-host-bundle-v2.json"
        )
        root = OUTPUT / f"gw-{gameweek:02d}"
        evidence = run_agent_arm(
            request=bundle["evidence_request"],
            hosted_response=_read(root / "evidence-hosted-response.json"),
            deterministic_candidate=bundle["deterministic_candidate"],
            code_commit=str(bundle["code_commit"]),
        )
        enforce_actionability(
            evidence_run=evidence,
            assessment=bundle["actionability_assessment"],
        )
        challenger = build_early_challenger_request(
            host_bundle=bundle,
            evidence_run=evidence,
        )
        _write_once(root / "evidence-run.json", evidence)
        _write_once(root / "challenger-request.json", challenger)
        rows.append(
            {
                "gameweek": gameweek,
                "adjustment_count": len(
                    evidence["validated_output"]["proposed_adjustments"]
                ),
                "challenger_request_sha256": challenger[
                    "rendered_input_sha256"
                ],
            }
        )
    print(json.dumps({"weeks": rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
