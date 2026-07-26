"""Generate the sealed 2025/26 captain-only challenger report."""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.captain_counterfactual import evaluate_captain_challenger


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "control/policies/captain-v1.json").read_text(encoding="utf-8")
    )
    appearance = json.loads(
        (
            root / "control/models/appearance-distribution-v1.json"
        ).read_text(encoding="utf-8")
    )
    report = evaluate_captain_challenger(
        reports_root=root / "reports/benchmarks/2025-26",
        episodes_root=root / "data/benchmark-v0/episodes/v1/2025-26",
        config=config,
        appearance_calibration=appearance,
        rules_path=root / "control/rules/2025-26.yaml",
    )
    output = root / "reports/benchmarks/2025-26-captain/evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": output.as_posix(),
                "decision": report["decision"],
                "evaluation_gameweeks": report["evaluation_gameweeks"],
                "canonical_captain_extra_total": report[
                    "canonical_captain_extra_total"
                ],
                "challenger_captain_extra_total": report[
                    "challenger_captain_extra_total"
                ],
                "realised_points_delta": report["realised_points_delta"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
