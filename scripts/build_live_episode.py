#!/usr/bin/env python3
"""Build one immutable live-shadow episode from local governed inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.orchestration.episode_builder import LiveEpisodeError, build_live_episode
from src.orchestration.manager_state import ManagerStateError
from src.scoring.rules_activation import RulesetActivationError
from src.scoring.rules_loader import DEFAULT_RULES_PATH


def _load_policy(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load compatibility policy {path}: {exc}") from exc
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("compatibility policy must be a JSON array of objects")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-summary", type=Path, required=True)
    parser.add_argument("--manager-state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES_PATH)
    parser.add_argument("--code-commit")
    parser.add_argument(
        "--compatibility-policy",
        type=Path,
        help="Optional JSON array of governed compatibility decisions.",
    )
    args = parser.parse_args(argv)
    try:
        result = build_live_episode(
            capture_summary_path=args.capture_summary,
            manager_state_path=args.manager_state,
            out_dir=args.out,
            rules_path=args.rules,
            code_commit=args.code_commit,
            compatibility_policy=_load_policy(args.compatibility_policy),
        )
    except (
        FileExistsError,
        LiveEpisodeError,
        ManagerStateError,
        RulesetActivationError,
        ValueError,
    ) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
