"""Tests for the day-over-day strategy team diff."""

from __future__ import annotations

import pytest

from src.reporting.strategy_team_diff import (
    TeamDiffError,
    diff_teams,
    parse_briefing_team,
    render_team_diff,
)


def _briefing(
    *,
    forward: str = "| FWD | Haaland | Man City | £15.5 | XI | Premium. |",
    captain_line: str = "- Captain / vice: B.Fernandes / Haaland (EP 6.37 vs 5.74).",
    bench_line: str = "- Bench (1→4): Dubravka; Xhaka; Diop; van Ewijk.",
    chip_line: str = "- Chip path: no chip in GW1; roll the free transfer.",
) -> str:
    rows = [
        "| GKP | Verbruggen | Brighton | £4.5 | XI | Starter. |",
        "| GKP | Dubravka | Spurs | £4.0 | bench | Enabler. |",
        "| DEF | Van Hecke | Spurs | £5.0 | XI | Core. |",
        "| DEF | Mitchell | Crystal Palace | £4.5 | XI | Core. |",
        "| DEF | Shaw | Man Utd | £4.5 | XI | Cheap. |",
        "| DEF | Diop | Ipswich | £4.0 | bench | Enabler. |",
        "| DEF | van Ewijk | Coventry | £4.0 | bench | Enabler. |",
        "| MID | B.Fernandes | Man Utd | £12.0 | XI | Captain. |",
        "| MID | Gibbs-White | Nott'm Forest | £8.0 | XI | Robust. |",
        "| MID | E.Le Fée | Sunderland | £6.0 | XI | Robust. |",
        "| MID | Wilson | Leeds | £6.5 | XI | Both arms. |",
        "| MID | Xhaka | Sunderland | £5.5 | bench | Fifth mid. |",
        forward,
        "| FWD | João Pedro | Chelsea | £7.5 | XI | Bridge. |",
        "| FWD | Thiago | Brentford | £8.0 | XI | Robust. |",
    ]
    return "\n".join(
        [
            "# Daily FPL strategy decision — test",
            "",
            chip_line,
            "",
            "## Recommended 15",
            "",
            "| pos | player | club | price | role (XI/bench) | why |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            captain_line,
            bench_line,
        ]
    )


def test_parse_briefing_team_extracts_all_sections() -> None:
    team = parse_briefing_team(_briefing())
    assert len(team["squad"]) == 15
    assert team["captain"] == "B.Fernandes"
    assert team["vice"] == "Haaland"
    assert team["bench_order"] == ["Dubravka", "Xhaka", "Diop", "van Ewijk"]
    assert team["chip_path"].startswith("no chip in GW1")
    assert team["squad"]["haaland"]["role"] == "XI"
    assert team["squad"]["dubravka"]["role"] == "bench"


def test_parse_tolerates_parenthesised_captain_and_gk_position() -> None:
    team = parse_briefing_team(
        _briefing(
            captain_line=(
                "- Captain / vice: Haaland (MCI vs BOU, H) / "
                "B.Fernandes (MUN vs HUL, A)"
            ),
        )
    )
    assert team["captain"] == "Haaland"
    assert team["vice"] == "B.Fernandes"


def test_parse_rejects_incomplete_table() -> None:
    with pytest.raises(TeamDiffError, match="expected 15"):
        parse_briefing_team("| FWD | Haaland | MCI | 15.5 | XI | x |")


def test_diff_identical_teams_reports_unchanged() -> None:
    team = parse_briefing_team(_briefing())
    diff = diff_teams(team, team)
    assert diff["unchanged"] is True
    rendered = render_team_diff(
        diff, team, team, current_label="today", previous_label="yesterday"
    )
    assert "**No change**" in rendered


def test_diff_reports_transfer_captaincy_and_chip_changes() -> None:
    previous = parse_briefing_team(_briefing())
    current = parse_briefing_team(
        _briefing(
            forward="| FWD | Isak | Newcastle | £13.5 | XI | Pivot. |",
            captain_line="- Captain / vice: Isak / B.Fernandes.",
            chip_line="- Chip path: Wildcard GW1 rebuild.",
        )
    )
    diff = diff_teams(current, previous)
    assert [row["player"] for row in diff["players_in"]] == ["Isak"]
    assert [row["player"] for row in diff["players_out"]] == ["Haaland"]
    assert diff["captain_changed"] is True
    assert diff["chip_path_changed"] is True
    assert diff["unchanged"] is False
    rendered = render_team_diff(
        diff,
        current,
        previous,
        current_label="today",
        previous_label="yesterday",
    )
    assert "**In:** Isak" in rendered
    assert "**Out:** Haaland" in rendered
    assert "B.Fernandes → Isak (changed)" in rendered
    assert "**changed**" in rendered


def test_diff_reports_role_changes() -> None:
    previous = parse_briefing_team(_briefing())
    current = parse_briefing_team(
        _briefing(
            forward="| FWD | Haaland | Man City | £15.5 | bench | Benched. |",
        )
    )
    diff = diff_teams(current, previous)
    assert diff["role_changes"] == [
        {"player": "Haaland", "from": "XI", "to": "bench"}
    ]
