"""Seal the ADR-0023 horizon comparison from the 2025/26 GW34 hit-gate replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.optimisation.chip_distributional_ev import (
    build_horizon_comparison_from_transfer_hit_evaluation,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    REPO
    / "reports/benchmarks/2025-26-counterfactuals/gw-34/transfer-hit-evaluation.json"
)
DEFAULT_OUT = (
    REPO / "reports/optimisation/chip-horizon-policy-comparison-2025-26-gw34.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    evaluation = json.loads(args.source.read_text(encoding="utf-8"))
    comparison = build_horizon_comparison_from_transfer_hit_evaluation(evaluation)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(args.out)
    print(comparison["content_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
