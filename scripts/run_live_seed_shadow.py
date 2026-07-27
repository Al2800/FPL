#!/usr/bin/env python3
"""Run the advisory 2026/27 initial-squad lab from local frozen inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.orchestration.live_seed_selection import (
    run_live_seed_selection,
    write_live_seed_artifact,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[1]


def _read(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an advisory-only FPL initial-squad shadow selection"
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=REPO / "control" / "policies" / "initial-squad-2026-27.json",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=REPO / "control" / "rules" / "2026-27.yaml",
    )
    parser.add_argument("--external-arms", type=Path)
    parser.add_argument("--rules-activation", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--selected-arm", default="robust")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    packet = _read(args.packet)
    policy = _read(args.policy)
    if packet is None or policy is None:
        raise ValueError("Packet and policy are required")
    rules = load_rules(args.rules)
    output = run_live_seed_selection(
        packet=packet,
        policy=policy,
        rules=rules,
        ruleset_sha256=ruleset_sha256(args.rules),
        external_arms=_read(args.external_arms),
        selected_arm=args.selected_arm,
        rules_activation=_read(args.rules_activation),
        approval=_read(args.approval),
    )
    write_live_seed_artifact(args.output, output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "selected_arm": output["selection"]["selected_arm"],
                "proposal_sha256": output["selection"]["proposal"][
                    "proposal_sha256"
                ],
                "approval_status": output["approval_gate"]["status"],
                "content_sha256": output["content_sha256"],
                "account_writes": output["account_writes"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
