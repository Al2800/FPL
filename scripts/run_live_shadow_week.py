#!/usr/bin/env python3
"""Freeze and optionally reveal one advisory-only paired live-shadow week."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from src.orchestration.live_shadow import (
    LiveShadowError,
    freeze_live_shadow_week,
    reveal_live_shadow_week,
    write_shadow_artifact,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = ROOT / "control/rules/2026-27.yaml"
DEFAULT_POLICY = ROOT / "control/policies/live-shadow-candidate.json"


def _object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveShadowError(f"Unable to read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LiveShadowError(f"{label} must be a JSON object")
    return value


def run_bundle(
    *,
    bundle_path: Path,
    out_dir: Path,
    rules_path: Path,
    policy_path: Path,
) -> dict[str, Any]:
    """Run one pre-staged bundle without network, browser, or account access."""

    bundle = _object(bundle_path, "live-shadow bundle")
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    policy = _object(policy_path, "live-shadow policy")
    required = {
        "episode_manifest",
        "structured_context",
        "decision_market",
        "control_state",
        "evidence_state",
        "control_candidate",
        "evidence_baseline_candidate",
        "evidence_candidate",
        "evidence_capture",
        "frozen_at",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise LiveShadowError(
            "Live-shadow bundle missing fields: " + ", ".join(missing)
        )
    frozen = freeze_live_shadow_week(
        episode_manifest=bundle["episode_manifest"],
        structured_context=bundle["structured_context"],
        decision_market=bundle["decision_market"],
        control_state=bundle["control_state"],
        evidence_state=bundle["evidence_state"],
        control_candidate=bundle["control_candidate"],
        evidence_baseline_candidate=bundle["evidence_baseline_candidate"],
        evidence_candidate=bundle["evidence_candidate"],
        evidence_capture=bundle["evidence_capture"],
        agent_run=bundle.get("agent_run"),
        frozen_at=bundle["frozen_at"],
        rules=rules,
        ruleset_sha256=rules_hash,
        policy=policy,
        control_chip=bundle.get("control_chip"),
        evidence_baseline_chip=bundle.get("evidence_baseline_chip"),
        evidence_chip=bundle.get("evidence_chip"),
    )
    write_shadow_artifact(out_dir / "frozen-week.json", frozen)
    result: dict[str, Any] = {
        "status": "frozen",
        "frozen_week_sha256": frozen["content_sha256"],
        "account_writes": False,
    }
    outcomes = bundle.get("outcomes")
    if outcomes is not None:
        if not isinstance(outcomes, dict) or "next_market" not in bundle:
            raise LiveShadowError(
                "Reveal requires outcome objects and next_market"
            )
        revealed = reveal_live_shadow_week(
            frozen_week=frozen,
            control_state=bundle["control_state"],
            evidence_state=bundle["evidence_state"],
            control_outcome=outcomes["control"],
            evidence_baseline_outcome=outcomes["evidence_baseline"],
            evidence_actual_outcome=outcomes["evidence_actual"],
            decision_market=bundle["decision_market"],
            next_market=bundle["next_market"],
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        write_shadow_artifact(out_dir / "revealed-week.json", revealed)
        result.update(
            {
                "status": "revealed_and_transitioned",
                "revealed_week_sha256": revealed["content_sha256"],
                "effects": revealed["attribution"]["effects"],
            }
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    try:
        result = run_bundle(
            bundle_path=args.bundle,
            out_dir=args.out,
            rules_path=args.rules,
            policy_path=args.policy,
        )
    except (LiveShadowError, ValueError, KeyError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
