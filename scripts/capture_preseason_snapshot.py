#!/usr/bin/env python3
"""Capture an immutable 2026/27 preseason checkpoint.

Example:
  python scripts/capture_preseason_snapshot.py \\
    --season 2026-27 \\
    --checkpoint-id launch \\
    --deadline 2026-08-21T17:30:00Z \\
    --output-root data/snapshots/2026-27/preseason
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import httpx

from src.ingestion.acquisition import utc_now
from src.ingestion.registry import assert_collectable, load_registry
from src.ingestion.snapshot_fpl import DEFAULT_PATHS, SOURCE_ID, snapshot_endpoint
from src.orchestration.preseason_snapshot import (
    PreseasonSnapshotConflict,
    PreseasonSnapshotError,
    capture_preseason_snapshot,
)  # noqa: F401 — PreseasonSnapshotConflict used in except clause

DEFAULT_OUT = REPO_ROOT / "data" / "snapshots" / "2026-27" / "preseason"
USER_AGENT = "fpl-agentic-decision-lab/0.1 (private read-only research)"


def _fetch_official(path: str, *, out_dir: Path, observed_at: str | None) -> bytes:
    assert_collectable(SOURCE_ID)
    registry = load_registry()
    registry_version = str(registry.get("registry_version", "unknown"))
    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        meta = snapshot_endpoint(
            client,
            base_url="https://fantasy.premierleague.com",
            path=path,
            out_dir=out_dir / "_live_fetch",
            registry_version=registry_version,
            observed_at=observed_at,
        )
    if meta.get("acquisition_status") != "success":
        raise PreseasonSnapshotError(
            f"Mandatory official fetch failed for {path}: {meta.get('acquisition_status')}"
        )
    stamp = str(meta["observed_at"]).replace(":", "").replace("-", "")
    body_path = out_dir / "_live_fetch" / stamp / str(meta["body_file"])
    return body_path.read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture an immutable 2026/27 preseason checkpoint"
    )
    parser.add_argument("--season", required=True)
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--deadline", required=True, help="Official GW1 deadline ISO-8601")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUT,
        help="Root directory for immutable preseason checkpoints",
    )
    parser.add_argument("--observed-at", default=None)
    parser.add_argument("--bootstrap-file", type=Path, default=None)
    parser.add_argument("--fixtures-file", type=Path, default=None)
    parser.add_argument("--rules-path", type=Path, default=None)
    parser.add_argument("--config-path", type=Path, default=None)
    parser.add_argument("--index-manifest-path", type=Path, default=None)
    parser.add_argument("--predecessor-checkpoint-hash", default=None)
    parser.add_argument("--code-commit", default=None)
    parser.add_argument("--availability-artifact", type=Path, default=None)
    parser.add_argument("--availability-sidecar", type=Path, default=None)
    parser.add_argument("--transfers-artifact", type=Path, default=None)
    parser.add_argument("--transfers-sidecar", type=Path, default=None)
    parser.add_argument("--set-pieces-artifact", type=Path, default=None)
    parser.add_argument("--set-pieces-sidecar", type=Path, default=None)
    parser.add_argument("--promoted-priors-artifact", type=Path, default=None)
    parser.add_argument("--promoted-priors-sidecar", type=Path, default=None)
    parser.add_argument("--world-cup-priors-artifact", type=Path, default=None)
    parser.add_argument("--world-cup-priors-sidecar", type=Path, default=None)
    parser.add_argument("--odds-artifact", type=Path, default=None)
    parser.add_argument("--odds-sidecar", type=Path, default=None)
    parser.add_argument("--ratings-artifact", type=Path, default=None)
    parser.add_argument("--ratings-sidecar", type=Path, default=None)
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Refuse live fetches; require --bootstrap-file and --fixtures-file",
    )
    args = parser.parse_args(argv)

    optional = {
        "availability_role_evidence": args.availability_artifact,
        "transfers_and_signings": args.transfers_artifact,
        "set_pieces": args.set_pieces_artifact,
        "promoted_team_priors": args.promoted_priors_artifact,
        "world_cup_return_fatigue": args.world_cup_priors_artifact,
        "licensed_odds": args.odds_artifact,
        "player_ratings": args.ratings_artifact,
    }
    optional_sidecars = {
        "availability_role_evidence": args.availability_sidecar,
        "transfers_and_signings": args.transfers_sidecar,
        "set_pieces": args.set_pieces_sidecar,
        "promoted_team_priors": args.promoted_priors_sidecar,
        "world_cup_return_fatigue": args.world_cup_priors_sidecar,
        "licensed_odds": args.odds_sidecar,
        "player_ratings": args.ratings_sidecar,
    }

    bootstrap_body = None
    fixtures_body = None
    bootstrap_fetcher = None
    fixtures_fetcher = None
    try:
        if args.bootstrap_file is not None:
            bootstrap_body = args.bootstrap_file.read_bytes()
        if args.fixtures_file is not None:
            fixtures_body = args.fixtures_file.read_bytes()
        if bootstrap_body is None or fixtures_body is None:
            if args.no_network:
                raise PreseasonSnapshotError(
                    "Mandatory official state is missing: bootstrap and fixtures are required"
                )
            output_root = args.output_root
            if bootstrap_body is None:
                bootstrap_fetcher = lambda: _fetch_official(
                    DEFAULT_PATHS[0],
                    out_dir=output_root,
                    observed_at=args.observed_at,
                )
            if fixtures_body is None:
                fixtures_fetcher = lambda: _fetch_official(
                    DEFAULT_PATHS[1],
                    out_dir=output_root,
                    observed_at=args.observed_at,
                )

        manifest = capture_preseason_snapshot(
            season=args.season,
            checkpoint_id=args.checkpoint_id,
            deadline=args.deadline,
            output_root=args.output_root,
            observed_at=args.observed_at or utc_now(),
            bootstrap_body=bootstrap_body,
            fixtures_body=fixtures_body,
            bootstrap_fetcher=bootstrap_fetcher,
            fixtures_fetcher=fixtures_fetcher,
            rules_path=args.rules_path,
            config_path=args.config_path,
            index_manifest_path=args.index_manifest_path,
            predecessor_checkpoint_hash=args.predecessor_checkpoint_hash,
            code_commit=args.code_commit,
            optional_artifacts=optional,
            optional_sidecars=optional_sidecars,
        )
    except (PreseasonSnapshotError, PreseasonSnapshotConflict, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(
        {
            "checkpoint_id": manifest["checkpoint_id"],
            "status": manifest["status"],
            "content_sha256": manifest["content_sha256"],
            "request_sha256": manifest["request_sha256"],
            "source_gaps": manifest["source_gaps"],
            "artifact_root": manifest["artifact_root"],
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
