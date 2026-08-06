"""Run the scheduled evidence/challenger overlay (ticket 11).

Offline modes:
  --force-timeout   inject a hosted timeout and degrade to the deterministic plan
  --t90m-now        treat ``now`` as inside the T-90m cutoff window

Hosted responses may be supplied as JSON files for unattended materialisation
without calling Codex from this process. Windows Scheduled Tasks invoke Codex
separately and write those response files for this script to validate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.orchestration.scheduled_agent_overlay import (
    load_overlay_policy,
    run_scheduled_overlay,
)


def _load(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deadline", required=True, help="ISO-8601 Gameweek deadline")
    parser.add_argument("--now", required=True, help="ISO-8601 wall clock")
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--deterministic-candidate", type=Path, required=True)
    parser.add_argument("--evidence-request", type=Path, default=None)
    parser.add_argument("--challenger-request", type=Path, default=None)
    parser.add_argument("--evidence-response", type=Path, default=None)
    parser.add_argument("--challenger-response", type=Path, default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--force-timeout", action="store_true")
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--traces-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    evidence_response = _load(args.evidence_response)
    challenger_response = _load(args.challenger_response)

    def invoke_evidence(_request: dict[str, Any]) -> dict[str, Any] | None:
        return evidence_response

    def invoke_challenger(_request: dict[str, Any]) -> dict[str, Any] | None:
        return challenger_response

    overlay = run_scheduled_overlay(
        deadline=args.deadline,
        now=args.now,
        evidence_request=_load(args.evidence_request),
        challenger_request=_load(args.challenger_request),
        deterministic_candidate=_load(args.deterministic_candidate) or {},
        code_commit=args.code_commit,
        policy=load_overlay_policy(args.policy) if args.policy else None,
        invoke_evidence=None if args.force_timeout else invoke_evidence,
        invoke_challenger=None if args.force_timeout else invoke_challenger,
        force_timeout=bool(args.force_timeout),
        checkpoint=args.checkpoint,
        traces_dir=args.traces_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Drop bulky nested runs from the on-disk summary when writing beside a GDR;
    # full runs remain available via trace JSONL + optional companion files.
    summary = {
        key: value
        for key, value in overlay.items()
        if key not in {"evidence_run", "challenger_run"}
    }
    summary["evidence_run_sha256"] = (
        None
        if overlay.get("evidence_run") is None
        else overlay["evidence_run"].get("content_sha256")
    )
    summary["challenger_run_sha256"] = (
        None
        if overlay.get("challenger_run") is None
        else overlay["challenger_run"].get("content_sha256")
    )
    args.out.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(args.out)
    print(overlay["status"])
    return 0 if overlay["status"] in {"completed", "timeout", "t90m_cutoff", "degraded", "absent"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
