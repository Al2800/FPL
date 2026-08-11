"""Run the ICT feature ablation and seal the promotion decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.ict_ablation import load_ict_weight_policy, run_ict_ablation


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "reports" / "forecasting" / "ict-ablation-decision.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--pit-snapshot",
        action="append",
        default=[],
        type=Path,
        help="Optional cutoff-safe ICT lag snapshot path (repeatable)",
    )
    parser.add_argument(
        "--finalised-outcome",
        action="append",
        default=[],
        type=Path,
        help="Optional finalised outcome path (repeatable)",
    )
    args = parser.parse_args(argv)

    policy = load_ict_weight_policy(args.policy)
    decision = run_ict_ablation(
        policy_path=args.policy,
        pit_snapshot_paths=args.pit_snapshot,
        finalised_outcome_paths=args.finalised_outcome,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    md = args.out.with_suffix(".md")
    lines = [
        "# ICT feature ablation",
        "",
        f"Decision: `{decision['decision']}`",
        f"Promotion eligible: `{decision['promotion_eligible']}`",
        f"Reason: `{decision.get('reason')}`",
        f"Policy: `{policy['policy_id']}` (`{policy['content_sha256']}`)",
        f"Report hash: `{decision['content_sha256']}`",
        f"Frozen four-family prereg: `{decision['frozen_four_family_prereg']}`",
        "",
        "## Corpus gaps",
        "",
    ]
    for gap in decision["corpus"].get("gaps") or []:
        lines.append(f"- {gap}")
    if not decision["corpus"].get("gaps"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Live posture",
            "",
            "- live `player_events` / `live_faithful` projections remain ICT-free",
            "- candidate weights stay `live_active: false` until owner promotion",
            "- ICT is outside the frozen four optional_family_arms matrix",
            "",
            decision["notes"],
            "",
        ]
    )
    md.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(args.out)
    print(decision["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
