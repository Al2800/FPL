#!/usr/bin/env python3
"""Read-only audit of the local FPL operational estate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.orchestration.local_operational_estate import (  # noqa: E402
    LocalOperationalEstateError,
    audit_local_operational_estate,
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
        "--json-out",
        type=Path,
        default=None,
        help="Optional extra copy of the machine manifest (still gitignored if under data/).",
    )
    args = parser.parse_args(argv)

    try:
        config = load_estate_config(args.config)
        manifest = audit_local_operational_estate(config, write_manifest=True)
    except LocalOperationalEstateError as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(
        {
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
            "secret_presence": manifest["secret_presence"],
        },
        indent=2,
        sort_keys=True,
    ))
    return int(manifest["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
