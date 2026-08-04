#!/usr/bin/env python3
"""Evaluate capture freshness and optionally notify (ticket 04).

Offline by default: plans missed jobs from scheduler policy + bootstrap fixture
or live bootstrap path, compares source observations to registry max_staleness,
and exits non-zero when degraded.
"""

from __future__ import annotations

from datetime import datetime, timezone
import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.ingestion.registry import load_registry  # noqa: E402
from src.orchestration.deadline_capture_scheduler import (  # noqa: E402
    load_json_object,
    utc_timestamp,
)
from src.orchestration.freshness_monitor import (  # noqa: E402
    FreshnessMonitorError,
    evaluate_capture_freshness,
    notifier_from_environment,
)


def _load_optional_json(path: Path | None) -> Any:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO / "config" / "data_sources" / "2026-27-capture-scheduler.json",
    )
    parser.add_argument(
        "--bootstrap-fixture",
        type=Path,
        help="Offline bootstrap JSON (preferred for tests).",
    )
    parser.add_argument(
        "--bootstrap",
        type=Path,
        help="Bootstrap JSON path when not using --bootstrap-fixture.",
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="Scheduler state JSON (defaults to config state_path).",
    )
    parser.add_argument(
        "--source-observations",
        type=Path,
        help="JSON list of {source_id, observed_at} rows.",
    )
    parser.add_argument(
        "--prior-alerts",
        type=Path,
        help="JSON list of prior alert objects for recovery detection.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO / "control" / "sources" / "source-registry.yaml",
    )
    parser.add_argument("--now", help="ISO-8601 evaluation time (tests).")
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the freshness report JSON here.",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Emit via FPL_FRESHNESS_WEBHOOK_URL when set; otherwise no-op.",
    )
    args = parser.parse_args(argv)

    try:
        policy = load_json_object(args.config)
        bootstrap_path = args.bootstrap_fixture or args.bootstrap
        if bootstrap_path is None:
            raise FreshnessMonitorError(
                "Provide --bootstrap-fixture or --bootstrap"
            )
        bootstrap = load_json_object(bootstrap_path)
        state_path = args.state
        if state_path is None:
            state_path = REPO / str(policy.get("state_path", "data/live-shadow/scheduler/state.json"))
        if state_path.exists():
            state = load_json_object(state_path)
        else:
            state = {"terminal_job_ids": [], "updated_at": None}
        observations = _load_optional_json(args.source_observations) or []
        prior = _load_optional_json(args.prior_alerts) or []
        if not isinstance(observations, list) or not isinstance(prior, list):
            raise FreshnessMonitorError("observations and prior alerts must be JSON lists")
        registry = load_registry(args.registry)
        now = (
            utc_timestamp(args.now)
            if args.now
            else utc_timestamp(datetime.now(timezone.utc))
        )
        notifier = notifier_from_environment() if args.notify else None
        report = evaluate_capture_freshness(
            policy=policy,
            bootstrap=bootstrap,
            scheduler_state=state,
            now=now,
            registry_sources=list(registry.get("sources") or []),
            source_observations=observations,
            prior_alerts=prior,
            notifier=notifier,
        )
    except (FreshnessMonitorError, OSError, ValueError, KeyError) as exc:
        print(f"freshness check failed: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 1 if report["status"] == "degraded" else 0


if __name__ == "__main__":
    raise SystemExit(main())
