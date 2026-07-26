"""Run one additive same-cutoff historical multiweek challenger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestration.multiweek_challenger import (
    run_historical_multiweek_challenger,
    score_historical_first_action,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--gameweek", type=int, required=True)
    parser.add_argument("--horizon", type=int, default=4, choices=range(3, 7))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/benchmarks/2025-26-multiweek"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    gw = args.gameweek
    report = run_historical_multiweek_challenger(
        base_input_path=(
            root
            / f"reports/benchmarks/{args.season}/gw-{gw:02d}/setup/arms/"
            "forecast_optimizer/reviewed-engine-input.json"
        ),
        locked_forecast_path=(
            root
            / f"reports/benchmarks/{args.season}/gw-{gw:02d}/setup/"
            "shared-locked-forecast.json"
        ),
        fixture_episode_paths=[
            root
            / f"data/benchmark-v0/episodes/v1/{args.season}/gw-{week:02d}/observed.json"
            for week in range(gw, gw + args.horizon)
        ],
        config_path=root / "control/policies/transfer-horizon-v1.json",
        rules_path=root / f"control/rules/{args.season}.yaml",
    )
    canonical = root / f"reports/benchmarks/{args.season}/gw-{gw:02d}"
    episode = (
        root / f"data/benchmark-v0/episodes/v1/{args.season}/gw-{gw:02d}"
    )
    report, validated_plan, realised_outcome = score_historical_first_action(
        report,
        state_path=(
            canonical
            / "setup/arms/forecast_optimizer/starting-policy-state.json"
        ),
        solver_input_path=(
            canonical
            / "setup/arms/forecast_optimizer/reviewed-engine-input.json"
        ),
        manifest_path=episode / "episode-manifest.json",
        hidden_outcome_path=episode / "hidden-outcome.json",
        identity_map_path=episode / "identity-map.json",
        shared_context_path=canonical / "shared-context.json",
        canonical_plan_path=canonical / "forecast_optimizer/validated-plan.json",
        canonical_outcome_path=canonical / "forecast_optimizer/realised-outcome.json",
        rules_path=root / f"control/rules/{args.season}.yaml",
    )
    output_dir = root / args.output_root / f"gw-{gw:02d}"
    output = output_dir / "comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "validated-plan.json").write_text(
        json.dumps(validated_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "realised-outcome.json").write_text(
        json.dumps(realised_outcome, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": output.as_posix(),
                "status": report["plan"]["status"],
                "value": report["plan"]["value"],
                "search": report["plan"]["search"],
                "selected_transfers": report["plan"]["selected"]["transfers"],
                "first_action_evaluation": report["first_action_evaluation"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
