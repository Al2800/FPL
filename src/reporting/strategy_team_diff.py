"""Deterministic day-over-day diff of daily strategy briefing teams.

Parses the fixed briefing template sections (Recommended 15 table,
captain/vice line, bench order, chip path) and reports what changed
between two briefings. Pure text processing — no model involvement.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_TABLE_ROW_RE = re.compile(r"^\|\s*(GKP?|DEF|MID|FWD)\s*\|", re.IGNORECASE)
_CAPTAIN_RE = re.compile(r"^-\s*Captain\s*/\s*vice\s*:\s*(.+)$", re.IGNORECASE)
_BENCH_RE = re.compile(r"^-\s*Bench\s*(?:\([^)]*\))?\s*:\s*(.+)$", re.IGNORECASE)
_CHIP_RE = re.compile(r"^-\s*Chip path\s*:\s*(.+)$", re.IGNORECASE)
_PAREN_RE = re.compile(r"\([^)]*\)")


class TeamDiffError(ValueError):
    """Raised when a briefing cannot be parsed into a team."""


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("**", "").strip())


def _norm(name: str) -> str:
    return _clean(name).casefold()


def parse_briefing_team(text: str) -> dict[str, Any]:
    """Extract the recommended 15, captain/vice, bench order and chip path."""

    squad: dict[str, dict[str, Any]] = {}
    captain: str | None = None
    vice: str | None = None
    bench: list[str] = []
    chip_path: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if _TABLE_ROW_RE.match(stripped):
            cells = [_clean(cell) for cell in stripped.strip("|").split("|")]
            if len(cells) < 5 or not cells[1]:
                continue
            player = cells[1]
            squad[_norm(player)] = {
                "player": player,
                "pos": cells[0].upper().replace("GK", "GKP").replace("GKPP", "GKP"),
                "club": cells[2],
                "price": cells[3].replace("£", ""),
                "role": "bench" if "bench" in cells[4].casefold() else "XI",
            }
            continue
        match = _CAPTAIN_RE.match(stripped)
        if match and captain is None:
            names = _PAREN_RE.sub("", match.group(1))
            parts = [
                _clean(part.rstrip(".").strip())
                for part in names.split("/")
                if _clean(part)
            ]
            if parts:
                captain = parts[0]
            if len(parts) > 1:
                vice = parts[1]
            continue
        match = _BENCH_RE.match(stripped)
        if match and not bench:
            bench = [
                _clean(part.rstrip("."))
                for part in re.split(r"[;,]", match.group(1))
                if _clean(part)
            ]
            continue
        match = _CHIP_RE.match(stripped)
        if match and chip_path is None:
            chip_path = _clean(match.group(1))

    if len(squad) < 15:
        raise TeamDiffError(
            f"briefing table yielded {len(squad)} players; expected 15"
        )
    return {
        "squad": squad,
        "captain": captain,
        "vice": vice,
        "bench_order": bench,
        "chip_path": chip_path,
    }


def diff_teams(
    current: Mapping[str, Any],
    previous: Mapping[str, Any],
) -> dict[str, Any]:
    cur_squad: Mapping[str, Mapping[str, Any]] = current["squad"]
    prev_squad: Mapping[str, Mapping[str, Any]] = previous["squad"]
    added = sorted(set(cur_squad) - set(prev_squad))
    removed = sorted(set(prev_squad) - set(cur_squad))
    role_changes = [
        {
            "player": cur_squad[key]["player"],
            "from": prev_squad[key]["role"],
            "to": cur_squad[key]["role"],
        }
        for key in sorted(set(cur_squad) & set(prev_squad))
        if cur_squad[key]["role"] != prev_squad[key]["role"]
    ]

    def _changed(field: str) -> bool:
        cur = current.get(field)
        prev = previous.get(field)
        if cur is None or prev is None:
            return False
        if isinstance(cur, list):
            return [_norm(str(v)) for v in cur] != [_norm(str(v)) for v in prev]
        return _norm(str(cur)) != _norm(str(prev))

    return {
        "players_in": [dict(cur_squad[key]) for key in added],
        "players_out": [dict(prev_squad[key]) for key in removed],
        "role_changes": role_changes,
        "captain_changed": _changed("captain"),
        "vice_changed": _changed("vice"),
        "bench_order_changed": _changed("bench_order"),
        "chip_path_changed": _changed("chip_path"),
        "unchanged": (
            not added
            and not removed
            and not role_changes
            and not _changed("captain")
            and not _changed("vice")
            and not _changed("bench_order")
            and not _changed("chip_path")
        ),
    }


def render_team_diff(
    diff: Mapping[str, Any],
    current: Mapping[str, Any],
    previous: Mapping[str, Any],
    *,
    current_label: str,
    previous_label: str,
) -> str:
    lines = [
        f"# Team diff — {current_label} vs {previous_label}",
        "",
    ]
    if diff["unchanged"]:
        lines.append(
            "**No change**: same 15, roles, captain/vice, bench order and "
            "chip path as the previous briefing."
        )
    else:
        if diff["players_in"] or diff["players_out"]:
            lines.append("## Transfers (advisory)")
            lines.append("")
            for row in diff["players_in"]:
                lines.append(
                    f"- **In:** {row['player']} ({row['pos']}, {row['club']}, "
                    f"{row['price']}) — {row['role']}"
                )
            for row in diff["players_out"]:
                lines.append(
                    f"- **Out:** {row['player']} ({row['pos']}, {row['club']}, "
                    f"{row['price']}) — was {row['role']}"
                )
            lines.append("")
        if diff["role_changes"]:
            lines.append("## Role changes")
            lines.append("")
            for row in diff["role_changes"]:
                lines.append(f"- {row['player']}: {row['from']} → {row['to']}")
            lines.append("")
        lines.append("## Leadership and structure")
        lines.append("")
        lines.append(
            f"- Captain: {previous.get('captain') or 'unknown'} → "
            f"{current.get('captain') or 'unknown'}"
            + (" (changed)" if diff["captain_changed"] else " (unchanged)")
        )
        lines.append(
            f"- Vice: {previous.get('vice') or 'unknown'} → "
            f"{current.get('vice') or 'unknown'}"
            + (" (changed)" if diff["vice_changed"] else " (unchanged)")
        )
        bench_now = ", ".join(current.get("bench_order") or []) or "unknown"
        lines.append(
            f"- Bench order: {bench_now}"
            + (" (changed)" if diff["bench_order_changed"] else " (unchanged)")
        )
        lines.append(
            "- Chip path: "
            + ("**changed**" if diff["chip_path_changed"] else "unchanged")
        )
        if diff["chip_path_changed"]:
            lines.append(f"  - was: {previous.get('chip_path')}")
            lines.append(f"  - now: {current.get('chip_path')}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Advisory diff only: this compares recommended teams, not FPL",
            "  account state. Owner approval is still required for any entry.",
            "",
        ]
    )
    return "\n".join(lines)
