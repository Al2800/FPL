"""FPL endpoint snapshotter — immutable raw captures with Section 10.1 metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from src.ingestion.registry import assert_collectable, load_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "data" / "raw" / "fpl"
SOURCE_ID = "fpl-official-endpoints"

DEFAULT_PATHS = [
    "/api/bootstrap-static/",
    "/api/fixtures/",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _content_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _detect_schema(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "type": "object",
            "top_level_keys": sorted(payload.keys()),
            "n_keys": len(payload),
        }
    if isinstance(payload, list):
        sample_keys: list[str] = []
        if payload and isinstance(payload[0], dict):
            sample_keys = sorted(payload[0].keys())
        return {"type": "array", "length": len(payload), "item_keys_sample": sample_keys}
    return {"type": type(payload).__name__}


def snapshot_endpoint(
    client: httpx.Client,
    *,
    base_url: str,
    path: str,
    out_dir: Path,
    registry_version: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    observed_at = _utc_now()
    try:
        response = client.get(url, timeout=timeout)
        body = response.content
        status = response.status_code
        error = None
    except httpx.HTTPError as exc:
        body = b""
        status = 0
        error = str(exc)

    digest = _content_hash(body) if body else hashlib.sha256(b"").hexdigest()
    schema: dict[str, Any]
    parsed: Any = None
    if body and status == 200:
        try:
            parsed = json.loads(body)
            schema = _detect_schema(parsed)
        except json.JSONDecodeError:
            schema = {"type": "non_json", "bytes": len(body)}
    else:
        schema = {"type": "unavailable", "http_status": status, "error": error}

    stamp = observed_at.replace(":", "").replace("-", "")
    safe_name = path.strip("/").replace("/", "_") or "root"
    run_dir = out_dir / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    body_name = f"{safe_name}.json"
    meta_name = f"{safe_name}.meta.json"
    body_path = run_dir / body_name
    meta_path = run_dir / meta_name

    # Always retain the response (including failures) as operational evidence.
    body_path.write_bytes(body if body else b"")

    metadata = {
        "source_id": SOURCE_ID,
        "request_url": url,
        "http_status": status,
        "observed_at": observed_at,
        "content_hash_sha256": digest,
        "source_registry_version": registry_version,
        "schema_detection": schema,
        "error": error,
        "body_file": body_name,
        "bytes": len(body),
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def run_snapshot(
    *,
    out_dir: Path | None = None,
    paths: list[str] | None = None,
    base_url: str = "https://fantasy.premierleague.com",
) -> list[dict[str, Any]]:
    source = assert_collectable(SOURCE_ID)
    registry = load_registry()
    registry_version = str(registry.get("registry_version", "unknown"))
    out = out_dir or DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    targets = paths or DEFAULT_PATHS

    results: list[dict[str, Any]] = []
    with httpx.Client(headers={"User-Agent": "fpl-agentic-decision-lab/0.1 (private research)"}) as client:
        for path in targets:
            meta = snapshot_endpoint(
                client,
                base_url=base_url,
                path=path,
                out_dir=out,
                registry_version=registry_version,
            )
            results.append(meta)
            status = meta["http_status"]
            print(f"{meta['request_url']} -> HTTP {status} hash={meta['content_hash_sha256'][:12]}...")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot official FPL endpoints")
    parser.add_argument("--out", type=Path, default=None, help="Output directory under data/raw/fpl")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="API path to capture (repeatable). Defaults to bootstrap-static and fixtures.",
    )
    parser.add_argument("--base-url", default="https://fantasy.premierleague.com")
    args = parser.parse_args(argv)
    try:
        run_snapshot(out_dir=args.out, paths=args.paths, base_url=args.base_url)
    except PermissionError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
