"""Tests for the parameterised agent-fork dispatcher (ticket 12)."""

from __future__ import annotations

import pytest

from scripts.run_agent_fork import build_child_argv, parse_gameweeks, runner_for


def test_parse_gameweeks_ranges_and_lists() -> None:
    assert parse_gameweeks("12") == [12]
    assert parse_gameweeks("30-32") == [30, 31, 32]
    assert parse_gameweeks("12,15-17") == [12, 15, 16, 17]


def test_runner_routing() -> None:
    assert runner_for(12).name == "run_gw12_agent_fork.py"
    assert runner_for(25).name == "run_gw23_gw29_agent_forks.py"
    assert runner_for(38).name == "run_gw30_gw38_agent_forks.py"
    with pytest.raises(ValueError, match="no agent-fork runner"):
        runner_for(11)


def test_child_argv_injects_gameweek_except_gw12() -> None:
    gw12 = build_child_argv(12, ["--mode", "prepare"])
    assert "--gameweek" not in gw12
    assert gw12[-2:] == ["--mode", "prepare"]

    gw30 = build_child_argv(30, ["--mode", "prepare"])
    assert gw30[2:4] == ["--gameweek", "30"]
    assert "--mode" in gw30
