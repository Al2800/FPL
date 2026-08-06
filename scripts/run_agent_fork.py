#!/usr/bin/env python3
"""Parameterised agent-fork dispatcher (ticket 12 / ADR-0026 Option A).

Routes ``--gws`` ranges to the existing per-range runners so committed fork
fixtures remain byte-identical. Does not move orchestration packages.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]

# Inclusive gameweek ranges → existing specialised runners.
RANGE_RUNNERS: tuple[tuple[int, int, str], ...] = (
    (12, 12, "run_gw12_agent_fork.py"),
    (13, 14, "run_gw13_gw14_agent_forks.py"),
    (15, 17, "run_gw15_gw17_agent_forks.py"),
    (18, 22, "run_gw18_gw22_agent_forks.py"),
    (23, 29, "run_gw23_gw29_agent_forks.py"),
    (30, 38, "run_gw30_gw38_agent_forks.py"),
)


def parse_gameweeks(spec: str) -> list[int]:
    """Parse ``12``, ``30-38``, or ``12,15-17`` into sorted unique gameweeks."""

    values: set[int] = set()
    for part in spec.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            left, right = token.split("-", 1)
            start, end = int(left), int(right)
            if end < start:
                raise ValueError(f"invalid gameweek range: {token}")
            values.update(range(start, end + 1))
        else:
            values.add(int(token))
    if not values:
        raise ValueError("no gameweeks provided")
    return sorted(values)


def runner_for(gameweek: int) -> Path:
    for start, end, name in RANGE_RUNNERS:
        if start <= gameweek <= end:
            return REPO / "scripts" / name
    raise ValueError(f"no agent-fork runner registered for GW{gameweek}")


def build_child_argv(gameweek: int, passthrough: list[str]) -> list[str]:
    """Build argv for the specialised runner, injecting --gameweek when needed."""

    script = runner_for(gameweek)
    argv = [sys.executable, str(script), *passthrough]
    # GW12 runner has no --gameweek flag; later ranges require it.
    if gameweek != 12 and "--gameweek" not in passthrough:
        # Insert after script path / before mode flags when possible.
        argv[2:2] = ["--gameweek", str(gameweek)]
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--gws",
        required=True,
        help="Gameweek list/ranges, e.g. 12 or 30-38 or 12,18-22",
    )
    parser.add_argument(
        "runner_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the specialised runner (use -- to separate)",
    )
    args = parser.parse_args(argv)
    passthrough = list(args.runner_args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    try:
        gameweeks = parse_gameweeks(args.gws)
    except ValueError as exc:
        parser.error(str(exc))

    exit_code = 0
    for gameweek in gameweeks:
        child = build_child_argv(gameweek, passthrough)
        print("+", " ".join(child), flush=True)
        completed = subprocess.run(child, cwd=REPO, check=False)
        if completed.returncode != 0:
            exit_code = completed.returncode
            break
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
