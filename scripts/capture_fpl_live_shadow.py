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

from src.forecasting.live_capture import (
    LiveForecastCaptureError,
    build_live_forecast_capture,
)
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


def _write_immutable_bytes(path: Path, value: bytes) -> None:
    if path.exists():
        if path.read_bytes() != value:
            raise FileExistsError(f"Refusing to overwrite immutable input: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
        value = json.loads(body)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveForecastCaptureError(f"Unable to read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LiveForecastCaptureError(f"{label} must be a JSON object")
    return value, body


def _bootstrap_payload(out_dir: Path, observed_at: str, endpoints: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    endpoint = next(
        (
            value
            for value in endpoints
            if str(value.get("request_url", "")).endswith("/api/bootstrap-static/")
        ),
        None,
    )
    if endpoint is None or endpoint.get("acquisition_status") != "success":
        raise LiveForecastCaptureError(
            "Official bootstrap must succeed before forecast inputs can be captured"
        )
    path = out_dir / _stamp(observed_at) / str(endpoint["body_file"])
    payload, _ = _load_object(path, "official bootstrap")
    return payload, endpoint


def _decision_cutoff(bootstrap: dict[str, Any], observed_at: str) -> str:
    upcoming = sorted(
        str(value["deadline_time"])
        for value in bootstrap.get("events", [])
        if value.get("deadline_time") and str(value["deadline_time"]) > observed_at
    )
    if not upcoming:
        raise LiveForecastCaptureError(
            "No future official FPL deadline is available; pass --decision-cutoff"
        )
    return upcoming[0]


def capture_live_shadow(
    *,
    out_dir: Path = DEFAULT_OUT,
    base_url: str = DEFAULT_BASE_URL,
    paths: list[str] | None = None,
    observed_at: str | None = None,
    decision_cutoff: str | None = None,
    launch_context_path: Path | None = None,
    market_snapshot_paths: list[Path] | None = None,
    freeze_launch: bool = False,
    timeout: float = 30.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Capture public endpoints with no authentication or execution capability."""

    assert_collectable(SOURCE_ID)
    registry = load_registry()
    registry_version = str(registry.get("registry_version", "unknown"))
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
    forecast_ref: dict[str, Any] | None = None
    if not failures:
        bootstrap, bootstrap_manifest = _bootstrap_payload(out_dir, observed, endpoints)
        launch_context: dict[str, Any] | None = None
        run_dir = out_dir / _stamp(observed)
        if launch_context_path is not None:
            launch_context, launch_body = _load_object(
                launch_context_path, "launch context"
            )
            _write_immutable_bytes(
                run_dir / "forecast-inputs" / "launch-context.json", launch_body
            )
        market_snapshots: list[dict[str, Any]] = []
        for index, path in enumerate(market_snapshot_paths or [], start=1):
            snapshot, body = _load_object(path, f"market snapshot {index}")
            market_snapshots.append(snapshot)
            _write_immutable_bytes(
                run_dir / "forecast-inputs" / f"market-{index:02d}.json", body
            )
        try:
            forecast_capture = build_live_forecast_capture(
                bootstrap=bootstrap,
                bootstrap_manifest=bootstrap_manifest,
                observed_at=observed,
                decision_cutoff=decision_cutoff or _decision_cutoff(bootstrap, observed),
                launch_context=launch_context,
                market_snapshots=market_snapshots,
                source_registry=registry,
                freeze_launch=freeze_launch,
            )
        except LiveForecastCaptureError as exc:
            explicitly_requested = bool(
                decision_cutoff
                or launch_context_path
                or market_snapshot_paths
                or freeze_launch
            )
            if explicitly_requested:
                raise
            forecast_ref = {
                "body_file": None,
                "content_sha256": None,
                "status": "degraded",
                "reason": str(exc),
            }
        else:
            forecast_path = run_dir / "forecast-input-capture.json"
            _write_immutable_json(forecast_path, forecast_capture)
            forecast_ref = {
                "body_file": forecast_path.name,
                "content_sha256": forecast_capture["content_sha256"],
                "status": (
                    "degraded"
                    if forecast_capture["degraded_features"]
                    else "complete"
                ),
            }
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
        "forecast_input_capture": forecast_ref,
    }
    run_dir = out_dir / _stamp(observed)
    _write_immutable_json(run_dir / "capture-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--decision-cutoff")
    parser.add_argument("--launch-context", type=Path)
    parser.add_argument("--market-snapshot", action="append", type=Path, default=[])
    parser.add_argument("--freeze-launch", action="store_true")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        summary = capture_live_shadow(
            out_dir=args.out,
            base_url=args.base_url,
            paths=args.paths,
            decision_cutoff=args.decision_cutoff,
            launch_context_path=args.launch_context,
            market_snapshot_paths=args.market_snapshot,
            freeze_launch=args.freeze_launch,
            timeout=args.timeout,
        )
    except (PermissionError, FileExistsError, LiveForecastCaptureError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
