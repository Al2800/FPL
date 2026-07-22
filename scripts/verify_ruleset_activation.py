"""Print deterministic activation evidence for one or two FPL rulesets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.scoring.rules_loader import (
    build_ruleset_activation,
    load_rules,
    ruleset_semantic_diff,
    ruleset_sha256,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail closed unless each FPL ruleset can safely drive season state."
    )
    parser.add_argument(
        "rulesets",
        nargs="+",
        type=Path,
        help="One activation candidate, or two candidates for a semantic diff.",
    )
    parser.add_argument(
        "--compatibility-policy",
        type=Path,
        help="Optional JSON array of reviewed inherited-rule approvals.",
    )
    return parser


def _approvals(path: Path | None) -> list[dict]:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("Compatibility policy must be a JSON array of objects")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if len(args.rulesets) > 2:
        raise SystemExit("Provide at most two rulesets")
    approvals = _approvals(args.compatibility_policy)
    loaded: list[tuple[dict, str]] = []
    activations = []
    for path in args.rulesets:
        rules = load_rules(path)
        digest = ruleset_sha256(path)
        mode = (
            "historical_replay"
            if rules.get("meta", {}).get("replay_status") == "validated"
            else "live"
        )
        activations.append(
            build_ruleset_activation(
                rules,
                digest,
                mode=mode,
                compatibility_policy=approvals,
            )
        )
        loaded.append((rules, digest))
    semantic_diff = None
    if len(loaded) == 2:
        semantic_diff = ruleset_semantic_diff(
            loaded[0][0], loaded[0][1], loaded[1][0], loaded[1][1]
        )
    payload = {
        "schema_version": "1.0",
        "activations": activations,
        "semantic_diff": semantic_diff,
    }
    print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False))
    return 0 if all(report["activatable"] for report in activations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
