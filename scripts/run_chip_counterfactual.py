#!/usr/bin/env python3
"""Generate the sealed 2025/26 GW31 chip-policy evaluation."""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.chip_counterfactual import evaluate_gw31_chip_policy


REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    report = evaluate_gw31_chip_policy(
        canonical_root=REPO / "reports" / "benchmarks" / "2025-26",
        episode_root=(
            REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
        ),
        config_path=REPO / "control" / "policies" / "chip-v1.json",
    )
    output = (
        REPO
        / "reports"
        / "benchmarks"
        / "2025-26-counterfactuals"
        / "gw-31"
        / "evaluation.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    output.write_text(text, encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
