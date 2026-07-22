"""FPL endpoint snapshotter — immutable raw captures with Section 10.1 metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

from src.ingestion.acquisition import acquire_http
from src.ingestion.registry import assert_collectable, load_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "data" / "raw" / "fpl"
SOURCE_ID = "fpl-official-endpoints"

DEFAULT_PATHS = [
    "/api/bootstrap-static/",
    "/api/fixtures/",
]


def snapshot_endpoint(
    client: httpx.Client,
    *,
    base_url: str,
    path: str,
    out_dir: Path,
    registry_version: str,
    timeout: float = 30.0,
    observed_at: str | None = None,
) -> dict[str, object]:
    """Capture one FPL endpoint through the source-neutral acquisition boundary."""

    url = base_url.rstrip("/") + path
    safe_name = path.strip("/").replace("/", "_") or "root"
    return acquire_http(
        client,
        source_id=SOURCE_ID,
        url=url,
        out_dir=out_dir,
        artifact_name=f"{safe_name}.json",
        registry_version=registry_version,
        observed_at=observed_at,
        timeout=timeout,
    )


def run_snapshot(
    *,
    out_dir: Path | None = None,
    paths: list[str] | None = None,
    base_url: str = "https://fantasy.premierleague.com",
) -> list[dict[str, object]]:
    source = assert_collectable(SOURCE_ID)
    registry = load_registry()
    registry_version = str(registry.get("registry_version", "unknown"))
    out = out_dir or DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    targets = paths or DEFAULT_PATHS

    results: list[dict[str, object]] = []
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
            digest = str(meta["content_hash_sha256"])
            print(f"{meta['request_url']} -> HTTP {status} hash={digest[:12]}...")
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
