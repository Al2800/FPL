"""Write the sealed GW34 transfer-hit counterfactual outside canonical replay."""

from __future__ import annotations

from pathlib import Path

from src.evaluation.transfer_counterfactual import (
    evaluate_gw34_transfer_hit,
)
from src.optimisation.io import save_json


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    report = evaluate_gw34_transfer_hit(
        canonical_root=ROOT / "reports/benchmarks/2025-26",
        episode_root=ROOT / "data/benchmark-v0/episodes/v2/2025-26",
        transfer_config_path=(
            ROOT / "control/policies/transfer-horizon-v1.json"
        ),
        chip_config_path=ROOT / "control/policies/chip-v1.json",
    )
    output = (
        ROOT
        / "reports/benchmarks/2025-26-counterfactuals"
        / "gw-34/transfer-hit-evaluation.json"
    )
    save_json(output, report)
    print(
        f"wrote {output.relative_to(ROOT)}: "
        f"selected={report['transfer_hit_ladder']['selected']['candidate_id']}"
    )


if __name__ == "__main__":
    main()
