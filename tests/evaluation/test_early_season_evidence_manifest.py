"""Contract tests for the retrospective GW1-GW11 evidence inventory."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from src.evaluation.early_season_evidence_manifest import (
    EarlySeasonEvidenceManifestError,
    build_early_season_manifest,
    build_manifest_entry,
    validate_early_season_manifest,
    write_immutable_json,
)


def _episode(gameweek: int) -> dict:
    deadline = f"2025-08-{14 + gameweek:02d}T10:00:00Z"
    return {
        "season": "2025-26",
        "gameweek": gameweek,
        "deadline": deadline,
        "episode_id": f"episode:{gameweek}",
        "observed_episode_sha256": f"observed-{gameweek}",
        "ruleset_id": "2025-26-v1.0",
        "ruleset_sha256": "rules",
    }


def _candidate(gameweek: int, *, admitted: bool = True) -> dict:
    excerpt = f"Player update for GW{gameweek}."
    return {
        "evidence_id": f"evidence-gw{gameweek}",
        "source_registry_id": "official-club-communications",
        "source_id": f"club-update-gw{gameweek}",
        "url": f"https://club.example/gw-{gameweek}",
        "title": f"GW{gameweek} team update",
        "published_at": f"2025-08-{14 + gameweek:02d}T08:00:00Z",
        "published_at_precision": "minute",
        "observed_at": "2026-07-27T10:00:00Z",
        "available_at": "2026-07-27T10:00:00Z",
        "citation_excerpt": excerpt,
        "citation_excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
        "claim_summary": "A player availability update.",
        "player_ids": [f"player:2025-26:{gameweek}"],
        "boundary_ids": [f"gw{gameweek}-lineup"],
        "rights_status": "manual_citation_only",
        "admission_status": (
            "admitted_exploratory" if admitted else "excluded"
        ),
        "exclusion_reasons": [] if admitted else ["publication_time_ambiguous"],
    }


def _record(gameweek: int, *, with_candidate: bool = True) -> dict:
    candidates = [_candidate(gameweek)] if with_candidate else []
    return {
        "schema_version": "1.0",
        "season": "2025-26",
        "gameweek": gameweek,
        "decision_type": (
            "initial_squad_selection" if gameweek == 1 else "weekly_management"
        ),
        "researched_at": "2026-07-27T11:00:00Z",
        "research_method": "manual_boundary_targeted_web_research",
        "search_scope": ["official club communications"],
        "search_complete": with_candidate,
        "boundary_ids": [f"gw{gameweek}-lineup"],
        "completeness_status": "ready" if with_candidate else "abstain",
        "abstention_reason": (
            None if with_candidate else "no_cutoff_safe_source_recovered"
        ),
        "limitations": [],
        "candidates": candidates,
    }


def _index() -> dict:
    return {
        "season": "2025-26",
        "dataset_id": "benchmark-v0-2025-26",
        "dataset_hash": "dataset-hash",
        "episodes": [_episode(gameweek) for gameweek in range(1, 12)],
    }


def test_manifest_covers_all_weeks_and_reports_abstention() -> None:
    records = {
        gameweek: _record(gameweek, with_candidate=gameweek != 3)
        for gameweek in range(1, 12)
    }
    manifest = build_early_season_manifest(
        index=_index(), research_records=records
    )

    validate_early_season_manifest(manifest, index=_index())
    assert [entry["gameweek"] for entry in manifest["entries"]] == list(
        range(1, 12)
    )
    assert manifest["entries"][0]["decision_type"] == "initial_squad_selection"
    assert all(
        entry["decision_type"] == "weekly_management"
        for entry in manifest["entries"][1:]
    )
    assert manifest["production_eligible"] is False
    assert manifest["coverage"] == {
        "gameweek_count": 11,
        "candidate_count": 10,
        "admitted_count": 10,
        "excluded_count": 0,
        "abstained_gameweek_count": 1,
        "abstention_rate": 1 / 11,
        "admission_rate": 1.0,
        "search_complete_gameweek_count": 10,
    }


def test_rejects_late_publication_and_excerpt_hash_change() -> None:
    record = _record(2)
    record["candidates"][0]["published_at"] = "2025-08-16T10:00:01Z"
    with pytest.raises(
        EarlySeasonEvidenceManifestError, match="published after"
    ):
        build_manifest_entry(episode=_episode(2), research_record=record)

    record = _record(2)
    record["candidates"][0]["citation_excerpt"] += " Changed"
    with pytest.raises(EarlySeasonEvidenceManifestError, match="hash mismatch"):
        build_manifest_entry(episode=_episode(2), research_record=record)


def test_rejects_duplicate_claims_and_unexplained_exclusion() -> None:
    record = _record(4)
    duplicate = deepcopy(record["candidates"][0])
    duplicate["evidence_id"] = "different-id"
    record["candidates"].append(duplicate)
    with pytest.raises(EarlySeasonEvidenceManifestError, match="duplicate"):
        build_manifest_entry(episode=_episode(4), research_record=record)

    record = _record(4)
    record["candidates"][0]["admission_status"] = "excluded"
    with pytest.raises(
        EarlySeasonEvidenceManifestError, match="without an exclusion reason"
    ):
        build_manifest_entry(episode=_episode(4), research_record=record)


def test_rejects_gw1_weekly_label_and_episode_tampering() -> None:
    record = _record(1)
    record["decision_type"] = "weekly_management"
    with pytest.raises(
        EarlySeasonEvidenceManifestError, match="initial_squad_selection"
    ):
        build_manifest_entry(episode=_episode(1), research_record=record)

    records = {gameweek: _record(gameweek) for gameweek in range(1, 12)}
    manifest = build_early_season_manifest(
        index=_index(), research_records=records
    )
    tampered = deepcopy(manifest)
    tampered["entries"][4]["decision_cutoff"] = "2025-01-01T00:00:00Z"
    tampered["content_sha256"] = manifest["content_sha256"]
    with pytest.raises(EarlySeasonEvidenceManifestError, match="content hash"):
        validate_early_season_manifest(tampered, index=_index())


def test_immutable_writer_accepts_identical_and_refuses_change(
    tmp_path: Path,
) -> None:
    path = tmp_path / "manifest.json"
    value = {"content_sha256": "one", "value": 1}
    write_immutable_json(path, value)
    write_immutable_json(path, value)
    with pytest.raises(EarlySeasonEvidenceManifestError, match="overwrite"):
        write_immutable_json(path, {"content_sha256": "two", "value": 2})

