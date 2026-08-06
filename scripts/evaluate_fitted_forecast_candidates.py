"""Evaluate preregistered fitted forecast candidates (ticket 17)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.forecasting.fitted_candidates import (
    evaluate_preregistered_families,
    load_preregistration,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "reports" / "forecasting" / "fitted-candidates-evaluation.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prereg", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    prereg = load_preregistration(args.prereg) if args.prereg else load_preregistration()
    report = evaluate_preregistered_families(prereg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    md = args.out.with_suffix(".md")
    minutes = report["families"]["expected_minutes"]
    lines = [
        "# Fitted forecast candidates evaluation",
        "",
        f"Report hash: `{report['content_sha256']}`",
        "",
        f"Fit seasons: {', '.join(report['fit_seasons'])}",
        f"Locked validation: {report['locked_validation_season']}",
        f"Any promoted: {report['any_promoted']}",
        "",
        "## expected_minutes",
        "",
        f"- candidate: `{minutes['candidate_id']}`",
        f"- promotion_eligible: `{minutes['promotion_eligible']}`",
        f"- baseline Brier: {minutes['baseline_metrics']['brier']:.5f}",
        f"- candidate Brier: {minutes['candidate_metrics']['brier']:.5f}",
        f"- baseline minutes MAE: {minutes['baseline_metrics']['minutes_mae']:.3f}",
        f"- candidate minutes MAE: {minutes['candidate_metrics']['minutes_mae']:.3f}",
        f"- reason: {minutes.get('reason_not_promoted') or 'promoted'}",
        "",
        report["notes"],
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(args.out)
    print(report["content_sha256"])
    print("any_promoted", report["any_promoted"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
