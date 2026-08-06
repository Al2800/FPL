"""Persist ADR-0010 agent traces as JSONL beside Gameweek Decision Records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACES_DIR = ROOT / "reports" / "traces"


class AgentTraceError(ValueError):
    """Raised when an agent run cannot be written as a JSONL trace."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_agent_trace(
    run_result: Mapping[str, Any],
    *,
    traces_dir: Path | None = None,
) -> Path:
    """Append one sealed agent-arm result as a JSONL event under ``traces_dir``.

    The path matches ``trace_path`` declared on the in-memory result
    (``reports/traces/{run_id}.jsonl``) when using the default directory.
    """

    run_id = str(run_result.get("run_id") or "").strip()
    if not run_id:
        raise AgentTraceError("agent run requires run_id")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise AgentTraceError("run_id must be a single path segment")
    destination = Path(traces_dir) if traces_dir is not None else DEFAULT_TRACES_DIR
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{run_id}.jsonl"
    observed_at = None
    trace = run_result.get("trace")
    if isinstance(trace, Mapping):
        observed_at = trace.get("observed_at")
    event = {
        "schema_version": "agent-trace-jsonl-v1",
        "event": "agent_arm_result",
        "run_id": run_id,
        "arm": run_result.get("arm"),
        "status": run_result.get("status"),
        "content_sha256": run_result.get("content_sha256"),
        "observed_at": observed_at or _utc_now(),
        "trace": dict(trace) if isinstance(trace, Mapping) else None,
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        )
    return path
