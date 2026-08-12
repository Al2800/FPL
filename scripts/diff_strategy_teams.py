"""CLI: diff the two most recent daily strategy briefing teams.

Auto mode picks the two latest date-named briefings
(reports/strategy-research/YYYY-MM-DD.md); explicit --current/--previous
paths override. Writes a committed markdown diff next to the briefings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.reporting.strategy_team_diff import (  # noqa: E402
    TeamDiffError,
    diff_teams,
    parse_briefing_team,
    render_team_diff,
)

_DATE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def _latest_two(briefing_root: Path) -> tuple[Path, Path]:
    dated = sorted(
        path
        for path in briefing_root.glob("*.md")
        if _DATE_NAME_RE.match(path.name)
    )
    if len(dated) < 2:
        raise SystemExit("need at least two date-named briefings to diff")
    return dated[-1], dated[-2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, default=None)
    parser.add_argument("--previous", type=Path, default=None)
    parser.add_argument(
        "--briefing-root",
        type=Path,
        default=ROOT / "reports" / "strategy-research",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if args.current and args.previous:
        current_path, previous_path = args.current, args.previous
    elif args.current or args.previous:
        parser.error("--current and --previous must be provided together")
    else:
        current_path, previous_path = _latest_two(args.briefing_root)

    try:
        current = parse_briefing_team(
            current_path.read_text(encoding="utf-8")
        )
        previous = parse_briefing_team(
            previous_path.read_text(encoding="utf-8")
        )
    except TeamDiffError as error:
        print(json.dumps({"status": "degraded", "error": str(error)}))
        return 1

    diff = diff_teams(current, previous)
    markdown = render_team_diff(
        diff,
        current,
        previous,
        current_label=current_path.stem,
        previous_label=previous_path.stem,
    )
    out_path = args.out or (
        args.briefing_root / "diffs" / f"{current_path.stem}-team-diff.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "current": str(current_path),
                "previous": str(previous_path),
                "out": str(out_path),
                "unchanged": diff["unchanged"],
                "players_in": [row["player"] for row in diff["players_in"]],
                "players_out": [row["player"] for row in diff["players_out"]],
                "captain_changed": diff["captain_changed"],
                "chip_path_changed": diff["chip_path_changed"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
