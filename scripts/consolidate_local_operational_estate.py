#!/usr/bin/env python3
"""Create-only consolidation and optional archive of local operational evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.local_operational_estate import (  # noqa: E402
    LocalOperationalEstateConflict,
    LocalOperationalEstateError,
    acknowledge_unavailable_artifacts,
    archive_operational_estate,
    audit_local_operational_estate,
    consolidate_retained_artifacts,
    load_estate_config,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO / "config" / "operations" / "local-operational-estate.json",
    )
    parser.add_argument(
        "--acknowledge-unavailable",
        action="store_true",
        help=(
            "After consolidation, acknowledge any still-missing preseason "
            "references as unavailable_local_artifact (never reconstructs bytes)."
        ),
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional private backup root for create-only archive + hash manifest.",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip the post-consolidation audit (not recommended).",
    )
    args = parser.parse_args(argv)

    try:
        config = load_estate_config(args.config)
        consolidation = consolidate_retained_artifacts(config)
        print(json.dumps({"consolidation": {
            "copied_count": consolidation["copied_count"],
            "identical_count": consolidation["identical_count"],
            "missing_families": consolidation["missing_families"],
            "copies": [
                {
                    "relative_path": item["relative_path"],
                    "status": item["status"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                }
                for item in consolidation["copies"]
            ],
        }}, indent=2, sort_keys=True))

        if args.acknowledge_unavailable:
            audit = audit_local_operational_estate(config, write_manifest=False)
            to_ack = [
                {
                    "checkpoint_id": item["checkpoint_id"],
                    "manifest_path": item["manifest_path"],
                    "manifest_sha256": item.get("expected_sha256"),
                    "reason": "unavailable_on_active_and_legacy_roots",
                }
                for item in audit["preseason_references"]
                if item["status"] == "unavailable_local_artifact" and not item.get("acknowledged")
            ]
            if to_ack:
                ack = acknowledge_unavailable_artifacts(config, to_ack)
                print(json.dumps({"acknowledgements": {
                    "count": len(ack["artifacts"]),
                    "artifacts": [
                        {
                            "checkpoint_id": item.get("checkpoint_id"),
                            "manifest_path": item.get("manifest_path"),
                            "status": item.get("status"),
                        }
                        for item in ack["artifacts"]
                    ],
                }}, indent=2, sort_keys=True))

        archive_report = None
        if args.archive_root is not None:
            archive_report = archive_operational_estate(config, backup_root=args.archive_root)
            print(json.dumps({"archive": {
                "backup_root": archive_report["backup_root"],
                "file_count": archive_report["file_count"],
                "manifest_path": archive_report["manifest_path"],
                "manifest_status": archive_report["manifest_status"],
                "files": [
                    {
                        "relative_path": item["relative_path"],
                        "status": item["status"],
                        "sha256": item["sha256"],
                    }
                    for item in archive_report["files"]
                ],
            }}, indent=2, sort_keys=True))

        if args.skip_audit:
            return 0

        manifest = audit_local_operational_estate(config, write_manifest=True)
        print(json.dumps({"audit": {
            "exit_code": manifest["exit_code"],
            "machine_manifest_path": manifest.get("machine_manifest_path"),
            "preseason_references": [
                {
                    "checkpoint_id": item["checkpoint_id"],
                    "status": item["status"],
                    "acknowledged": item.get("acknowledged"),
                    "sha256": item.get("sha256"),
                }
                for item in manifest["preseason_references"]
            ],
            "scheduled_tasks": [
                {
                    "name": item["name"],
                    "present": item["present"],
                    "targets_active_root": item["targets_active_root"],
                    "action_drift": item["action_drift"],
                    "last_result": item["last_result"],
                }
                for item in manifest["scheduled_tasks"]
            ],
        }}, indent=2, sort_keys=True))
        return int(manifest["exit_code"])
    except LocalOperationalEstateConflict as exc:
        print(f"consolidation refused: {exc}", file=sys.stderr)
        return 4
    except LocalOperationalEstateError as exc:
        print(f"consolidation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
