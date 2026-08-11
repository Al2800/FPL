"""Run the set-piece role effect ablation and seal the promotion decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.set_piece_ablation import (
    load_set_piece_weight_policy,
    run_set_piece_ablation,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "reports" / "forecasting" / "set-piece-ablation-decision.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--pit-ledger",
        action="append",
        default=[],
        type=Path,
        help="Optional cutoff-safe ledger path (repeatable)",
    )
    parser.add_argument(
        "--finalised-outcome",
        action="append",
        default=[],
        type=Path,
        help="Optional finalised outcome path (repeatable)",
    )
    args = parser.parse_args(argv)

    # Seal policy file hash into the loaded object for the report.
    policy = load_set_piece_weight_policy(args.policy)
    decision = run_set_piece_ablation(
        policy_path=args.policy,
        pit_ledger_paths=args.pit_ledger,
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
        "# Set-piece role effect ablation",
        "",
        f"Decision: `{decision['decision']}`",
        f"Promotion eligible: `{decision['promotion_eligible']}`",
        f"Reason: `{decision.get('reason')}`",
        f"Policy: `{policy['policy_id']}` (`{policy['content_sha256']}`)",
        f"Report hash: `{decision['content_sha256']}`",
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
            "- `effect_weights` remain `null` on live feature payloads",
            "- candidate weights stay `live_active: false` until owner promotion",
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
