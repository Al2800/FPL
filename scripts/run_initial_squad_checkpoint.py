#!/usr/bin/env python3
"""Run an advisory-only initial-15 selection from one sealed preseason manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.orchestration.initial_squad_checkpoint import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_POLICY_PATH,
    InitialSquadCheckpointError,
    run_initial_squad_checkpoint,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a hash-bound, advisory-only FPL initial-squad checkpoint"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="Optional path only when it is byte-identical to the manifest-bound ruleset",
    )
    args = parser.parse_args(argv)
    try:
        checkpoint = run_initial_squad_checkpoint(
            manifest_path=args.manifest,
            output_root=args.output_root,
            policy_path=args.policy,
            rules_path=args.rules,
        )
    except (InitialSquadCheckpointError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "content_sha256": checkpoint["content_sha256"],
                "recommendation_sha256": checkpoint["recommendation_sha256"],
                "approval_status": checkpoint["approval_status"],
                "account_writes": checkpoint["account_writes"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
