#!/usr/bin/env python3
"""Materialise the immutable GW1-GW38 enhanced replay input boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.evaluation.enhanced_replay_inputs import (
    EnhancedReplayInputError,
    build_enhanced_episode_pack,
    build_enhanced_index,
    canonical_input_tree_hash,
    write_immutable_json,
)
from src.ingestion.odds_snapshot import normalise_football_data_csv


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EPISODES = (
    REPO_ROOT / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
)
DEFAULT_DATASET = (
    REPO_ROOT / "control" / "manifests" / "datasets" / "benchmark-v0.json"
)
DEFAULT_EVIDENCE = REPO_ROOT / "evals" / "evidence-forks" / "2025-26"
DEFAULT_EARLY_EVIDENCE = DEFAULT_EVIDENCE / "early-season-manifest.json"
DEFAULT_CANDIDATE_POOL = (
    REPO_ROOT / "evals" / "seed-forks" / "2025-26" / "gw-01"
    / "candidate-pool.json"
)
DEFAULT_OUT = (
    REPO_ROOT / "evals" / "episodes" / "enhanced" / "2025-26"
)
DEFAULT_LOCAL_ODDS = (
    REPO_ROOT / "data" / "benchmark-v0" / "enhanced" / "2025-26"
    / "football-data-preclosing.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-root", type=Path, default=DEFAULT_EPISODES)
    parser.add_argument("--dataset-manifest", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument(
        "--early-evidence-manifest",
        type=Path,
        default=DEFAULT_EARLY_EVIDENCE,
    )
    parser.add_argument(
        "--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--local-odds-artifact", type=Path, default=DEFAULT_LOCAL_ODDS
    )
    parser.add_argument(
        "--without-odds",
        action="store_true",
        help="Emit explicit odds gaps without building the local comparator.",
    )
    return parser


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnhancedReplayInputError(f"cannot load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise EnhancedReplayInputError(f"JSON artifact must be an object: {path}")
    return value


def _repo_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _source_by_role(
    manifest: Mapping[str, Any], role: str
) -> Mapping[str, Any]:
    values = [
        row
        for row in manifest.get("sources", [])
        if row.get("dataset_role") == role
    ]
    if len(values) != 1:
        raise EnhancedReplayInputError(
            f"dataset manifest requires one {role} source"
        )
    return values[0]


def _build_odds_comparator(
    dataset: Mapping[str, Any],
    *,
    dataset_manifest_path: Path,
) -> dict[str, Any]:
    source = _source_by_role(dataset, "match_results")
    season_root = dataset_manifest_path.parents[3] / "data" / "benchmark-v0"
    # The committed manifest stores a path relative to data/benchmark-v0/<season>.
    source_path = (
        season_root
        / str(dataset["season"])
        / Path(str(source["local_artifact"]))
    )
    if not source_path.is_file():
        raise EnhancedReplayInputError(
            f"local Football-Data source is absent: {source_path}"
        )
    comparator = normalise_football_data_csv(
        source_path.read_bytes(),
        season=str(dataset["season"]),
        origin=str(source["origin"]),
        observed_at=str(source["observed_at"]),
        available_at=str(source["observed_at"]),
    )
    if comparator["source_sha256"] != source["content_hash_sha256"]:
        raise EnhancedReplayInputError(
            "local Football-Data bytes differ from frozen dataset manifest"
        )
    return comparator


def _evidence_map(
    *,
    evidence_root: Path,
    early_manifest_path: Path,
) -> dict[int, tuple[dict[str, Any], str]]:
    result: dict[int, tuple[dict[str, Any], str]] = {}
    early = _load(early_manifest_path)
    for index, entry in enumerate(early.get("entries", [])):
        gameweek = int(entry["gameweek"])
        result[gameweek] = (
            dict(entry),
            f"{_repo_ref(early_manifest_path)}#/entries/{index}",
        )
    for gameweek in range(12, 39):
        path = evidence_root / f"gw-{gameweek:02d}" / "evidence-bundle.json"
        if path.is_file():
            result[gameweek] = (_load(path), _repo_ref(path))
    return result


def _preflight_outputs(
    desired: Mapping[Path, Mapping[str, Any]],
) -> None:
    for path, value in desired.items():
        if not path.exists():
            continue
        expected = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        )
        if path.read_text(encoding="utf-8") != expected:
            raise EnhancedReplayInputError(
                f"refusing partial materialisation; immutable conflict: {path}"
            )


def materialise(args: argparse.Namespace) -> dict[str, Any]:
    dataset = _load(args.dataset_manifest)
    candidate_pool = _load(args.candidate_pool)
    evidence = _evidence_map(
        evidence_root=args.evidence_root,
        early_manifest_path=args.early_evidence_manifest,
    )
    comparator = (
        None
        if args.without_odds
        else _build_odds_comparator(
            dataset, dataset_manifest_path=args.dataset_manifest
        )
    )
    canonical_before, canonical_file_count = canonical_input_tree_hash(
        args.episode_root
    )

    packs: list[dict[str, Any]] = []
    desired: dict[Path, Mapping[str, Any]] = {}
    for gameweek in range(1, 39):
        directory = args.episode_root / f"gw-{gameweek:02d}"
        manifest_path = directory / "episode-manifest.json"
        observed_path = directory / "observed.json"
        identity_path = directory / "identity-map.json"
        evidence_value, evidence_ref = evidence.get(
            gameweek, (None, None)
        )
        pack = build_enhanced_episode_pack(
            manifest=_load(manifest_path),
            observed=_load(observed_path),
            identity_map=_load(identity_path),
            dataset_manifest=dataset,
            canonical_refs={
                "manifest": _repo_ref(manifest_path),
                "observed": _repo_ref(observed_path),
                "identity_map": _repo_ref(identity_path),
            },
            evidence_artifact=evidence_value,
            evidence_ref=evidence_ref,
            seed_candidate_pool=(
                candidate_pool if gameweek == 1 else None
            ),
            seed_candidate_ref=(
                _repo_ref(args.candidate_pool) if gameweek == 1 else None
            ),
            odds_comparator=comparator,
            odds_ref=(
                _repo_ref(args.local_odds_artifact)
                if comparator is not None
                else None
            ),
        )
        packs.append(pack)
        desired[
            args.out / f"gw-{gameweek:02d}" / "input-pack.json"
        ] = pack

    index = build_enhanced_index(
        packs,
        canonical_tree_sha256=canonical_before,
        canonical_file_count=canonical_file_count,
    )
    desired[args.out / "input-index.json"] = index
    if comparator is not None:
        desired[args.local_odds_artifact] = comparator
    _preflight_outputs(desired)

    statuses = {
        str(path): write_immutable_json(path, value)
        for path, value in desired.items()
    }
    canonical_after, after_count = canonical_input_tree_hash(args.episode_root)
    if (
        canonical_after != canonical_before
        or after_count != canonical_file_count
    ):
        raise EnhancedReplayInputError(
            "canonical input tree changed during materialisation"
        )
    return {
        "status": (
            "written"
            if any(value == "written" for value in statuses.values())
            else "unchanged"
        ),
        "episode_count": len(packs),
        "index_content_sha256": index["content_sha256"],
        "canonical_tree_sha256": canonical_before,
        "canonical_file_count": canonical_file_count,
        "odds_comparator": comparator is not None,
        "coverage_matrix": index["coverage_matrix"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    print(json.dumps(materialise(args), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
