"""Triage a news-capture artifact into a verification shortlist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ingestion.news_triage import (  # noqa: E402
    load_triage_policy,
    triage_impact_summary,
    triage_news_capture,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--impact-out", type=Path, default=None)
    args = parser.parse_args(argv)

    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    policy = load_triage_policy(args.policy)
    triage = triage_news_capture(capture, policy=policy)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(triage, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    impact = triage_impact_summary(triage)
    impact_path = args.impact_out or args.out.with_name(
        args.out.stem + "-impact.json"
    )
    impact_path.write_text(
        json.dumps(impact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    md = args.out.with_suffix(".md")
    lines = [
        "# News capture triage",
        "",
        f"- capture_id: `{triage.get('capture_id')}`",
        f"- candidates: `{triage.get('candidate_count')}`",
        f"- shortlist: `{triage.get('shortlist_count')}`",
        f"- demoted: `{triage.get('demoted_candidate_count')}`",
        f"- topics: `{triage.get('topic_counts')}`",
        f"- strategy relevance: `{impact.get('strategy_relevance')}`",
        "",
        "## Shortlist",
        "",
    ]
    for row in triage.get("shortlist") or []:
        lines.append(
            f"- score `{row['triage_score']}` | `{row['source_class']}` | "
            f"`{row['club_id']}` | {row['title'][:120]}"
        )
        lines.append(f"  - url: {row['url']}")
        demote_bits = []
        if row.get("stale_year_hits"):
            demote_bits.append(f"years={row['stale_year_hits']}")
        if row.get("historical_manager_hits"):
            demote_bits.append(f"managers={row['historical_manager_hits']}")
        demote = f"; demoted ({', '.join(demote_bits)})" if demote_bits else ""
        lines.append(
            f"  - topics: {', '.join(row.get('topic_hits') or []) or 'none'}; "
            f"verify: {row['verification_status']}{demote}"
        )
    lines.extend(["", triage.get("notes") or "", ""])
    md.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(args.out)
    print(f"shortlist={triage['shortlist_count']}")
    print(json.dumps(impact["strategy_relevance"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
