#!/usr/bin/env python3
"""Build deterministic ex-post claim-value ledgers from frozen replays."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.evaluation.claim_value_ledger import (
    build_agent_fork_ledger,
    build_enhanced_factorial_ledger,
    write_claim_value_report,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "reports" / "evaluation" / "claim-value"


def _summary(report: dict[str, Any], output: Path, written: bool) -> dict[str, Any]:
    return {
        "output": str(output),
        "written": written,
        "mode": report["mode"],
        "content_sha256": report["content_sha256"],
        "arms": report["rollups"]["arms"],
        "nonzero_paired_gameweeks_union": report["rollups"][
            "nonzero_paired_gameweeks_union"
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build read-only claim-value accounting reports"
    )
    parser.add_argument(
        "--mode",
        choices=("enhanced", "agent-fork", "all"),
        default="all",
    )
    parser.add_argument(
        "--enhanced-root",
        type=Path,
        default=ROOT / "reports" / "benchmarks" / "2025-26-enhanced",
    )
    parser.add_argument(
        "--early-evidence-root",
        type=Path,
        default=ROOT / "reports" / "benchmarks" / "2025-26-early-evidence",
    )
    parser.add_argument(
        "--agent-fork-root",
        type=Path,
        default=ROOT / "reports" / "benchmarks" / "2025-26-agent-forks",
    )
    parser.add_argument(
        "--episode-root",
        type=Path,
        default=(
            ROOT
            / "data"
            / "benchmark-v0"
            / "episodes"
            / "v1"
            / "2025-26"
        ),
        help="Sealed episode root supplying all-player post-match minutes",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    args = parser.parse_args()

    summaries: list[dict[str, Any]] = []
    if args.mode in {"enhanced", "all"}:
        report = build_enhanced_factorial_ledger(
            enhanced_root=args.enhanced_root,
            early_evidence_root=args.early_evidence_root,
            episode_root=args.episode_root,
        )
        output = args.output_root / "2025-26-enhanced-v1.json"
        summaries.append(
            _summary(report, output, write_claim_value_report(output, report))
        )
    if args.mode in {"agent-fork", "all"}:
        report = build_agent_fork_ledger(
            agent_fork_root=args.agent_fork_root,
            episode_root=args.episode_root,
        )
        output = args.output_root / "2025-26-agent-fork-v1.json"
        summaries.append(
            _summary(report, output, write_claim_value_report(output, report))
        )
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
