#!/usr/bin/env python3
"""Build the sealed GW1-GW11 retrospective evidence inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from src.evaluation.early_season_evidence_manifest import (
    EarlySeasonEvidenceManifestError,
    build_early_season_manifest,
    write_immutable_json,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = (
    ROOT / "evals" / "episodes" / "structured" / "benchmark-v0-index-v2.json"
)
DEFAULT_EVIDENCE_ROOT = ROOT / "evals" / "evidence-forks" / "2025-26"


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EarlySeasonEvidenceManifestError(
            f"unable to read JSON {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise EarlySeasonEvidenceManifestError(f"{path} must contain an object")
    return value


def build_from_files(*, index_path: Path, evidence_root: Path) -> dict:
    index = _read(index_path)
    records = {
        gameweek: _read(
            evidence_root
            / f"gw-{gameweek:02d}"
            / "research-record.json"
        )
        for gameweek in range(1, 12)
    }
    manifest = build_early_season_manifest(
        index=index, research_records=records
    )
    for entry in manifest["entries"]:
        write_immutable_json(
            evidence_root
            / f"gw-{int(entry['gameweek']):02d}"
            / "manifest-entry.json",
            entry,
        )
    write_immutable_json(
        evidence_root / "early-season-manifest.json", manifest
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument(
        "--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT
    )
    args = parser.parse_args(argv)
    try:
        manifest = build_from_files(
            index_path=args.index, evidence_root=args.evidence_root
        )
    except EarlySeasonEvidenceManifestError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "manifest_id": manifest["manifest_id"],
                "content_sha256": manifest["content_sha256"],
                **manifest["coverage"],
                "production_eligible": manifest["production_eligible"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
