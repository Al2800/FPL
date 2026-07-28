#!/usr/bin/env python3
"""Run an approved, bounded tranche of the enhanced 2025/26 season replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.enhanced_season_replay import (
    run_enhanced_season_replay,
)


REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-gameweek", type=int, default=1)
    parser.add_argument("--stop-gameweek", type=int, required=True)
    args = parser.parse_args()
    result = run_enhanced_season_replay(
        start_gameweek=args.start_gameweek,
        stop_gameweek=args.stop_gameweek,
        repo_root=REPO,
        canonical_root=REPO / "reports/benchmarks/2025-26",
        optimized_seed_root=(
            REPO / "reports/benchmarks/2025-26-gw1-seed-counterfactual"
        ),
        scout_evidence_root=(
            REPO / "reports/benchmarks/2025-26-early-evidence"
        ),
        enhanced_input_root=REPO / "evals/episodes/enhanced/2025-26",
        episode_root=REPO / "data/benchmark-v0/episodes/v2/2025-26",
        evidence_bundle_root=REPO / "evals/evidence-forks/2025-26",
        later_evidence_root=(
            REPO / "reports/benchmarks/2025-26-agent-forks"
        ),
        output_root=REPO / "reports/benchmarks/2025-26-enhanced",
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
