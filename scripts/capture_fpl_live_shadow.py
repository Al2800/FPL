#!/usr/bin/env python3
"""Capture public official FPL state as immutable live-shadow evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx

from src.ingestion.acquisition import utc_now
from src.ingestion.registry import assert_collectable, load_registry
from src.ingestion.snapshot_fpl import DEFAULT_PATHS, SOURCE_ID, snapshot_endpoint

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "live-shadow" / "fpl"
DEFAULT_BASE_URL = "https://fantasy.premierleague.com"
USER_AGENT = "fpl-agentic-decision-lab/0.1 (private read-only research)"


def _stamp(observed_at: str) -> str:
    return observed_at.replace(":", "").replace("-", "")


def _write_immutable_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(f"Refusing to overwrite immutable capture summary: {path}")
        return
    path.write_bytes(encoded)


def capture_live_shadow(
    *,
    out_dir: Path = DEFAULT_OUT,
    base_url: str = DEFAULT_BASE_URL,
    paths: list[str] | None = None,
    observed_at: str | None = None,
    timeout: float = 30.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Capture public endpoints with no authentication or execution capability."""

    assert_collectable(SOURCE_ID)
    registry_version = str(load_registry().get("registry_version", "unknown"))
    observed = observed_at or utc_now()
    targets = list(paths or DEFAULT_PATHS)
    out_dir.mkdir(parents=True, exist_ok=True)

    owns_client = client is None
    active_client = client or httpx.Client(headers={"User-Agent": USER_AGENT})
    try:
        endpoints = [
            snapshot_endpoint(
                active_client,
                base_url=base_url,
                path=path,
                out_dir=out_dir,
                registry_version=registry_version,
                timeout=timeout,
                observed_at=observed,
            )
            for path in targets
        ]
    finally:
        if owns_client:
            active_client.close()

    failures = [
        {
            "request_url": endpoint["request_url"],
            "acquisition_status": endpoint["acquisition_status"],
            "http_status": endpoint["http_status"],
            "failure": endpoint["failure"],
        }
        for endpoint in endpoints
        if endpoint["acquisition_status"] != "success"
    ]
    stable_identity = {
        "source_id": SOURCE_ID,
        "observed_at": observed,
        "endpoint_manifest_ids": [endpoint["manifest_id"] for endpoint in endpoints],
    }
    capture_id = hashlib.sha256(
        json.dumps(stable_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    summary: dict[str, Any] = {
        "capture_version": "1.0",
        "capture_id": capture_id,
        "source_id": SOURCE_ID,
        "source_registry_version": registry_version,
        "observed_at": observed,
        "status": "partial_failure" if failures else "complete",
        "execution_mode": "no_execution",
        "browser_actions": False,
        "account_writes": False,
        "authentication": "none",
        "endpoint_count": len(endpoints),
        "failure_count": len(failures),
        "failures": failures,
        "endpoints": endpoints,
    }
    run_dir = out_dir / _stamp(observed)
    _write_immutable_json(run_dir / "capture-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        summary = capture_live_shadow(
            out_dir=args.out,
            base_url=args.base_url,
            paths=args.paths,
            timeout=args.timeout,
        )
    except (PermissionError, FileExistsError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
