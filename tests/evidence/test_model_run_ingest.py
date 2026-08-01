"""Tests for hands-off model-run evidence admission."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from src.evidence.model_run_ingest import (
    ModelEvidenceRunError,
    ingest_model_evidence_run,
)
from src.ingestion.news_discovery import artifact_hash


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def _prompt(tmp_path: Path) -> tuple[str, str]:
    path = tmp_path / "prompt.md"
    path.write_text("model evidence prompt v1\n", encoding="utf-8")
    return str(path), _digest(path.read_bytes())


def _catalogue() -> dict:
    return {
        "schema_version": "1.0",
        "season": "2026-27",
        "sources": [
            {
                "club_id": "alpha",
                "club_name": "Alpha",
                "official_domain": "alpha.example",
            },
            {
                "club_id": "beta",
                "club_name": "Beta",
                "official_domain": "beta.example",
            },
        ],
    }


def _registry() -> dict:
    return {
        "sources": [
            {
                "source_id": "official-club-communications",
                "enabled": True,
                "licence_status": "restricted",
                "allowed_use": "private_analysis_citation_only",
                "model_run": {
                    "enabled": True,
                    "raw_content_retained": False,
                },
            }
        ]
    }


def _policy(minimum_watchlist_players: int = 1) -> dict:
    return {
        "sources": [
            {
                "source_id": "official-club-communications",
                "admitted": True,
                "admission_mode": "model_assisted_citation",
                "raw_content_retained": False,
            }
        ],
        "thresholds": {"minimum_claim_confidence": 0.55},
        "model_run": {
            "minimum_watchlist_players": minimum_watchlist_players,
            "fetch_timeout_seconds": 1,
            "max_source_bytes": 1000,
        },
    }


def _bootstrap() -> dict:
    return {
        "season": "2026-27",
        "elements": [
            {"id": 1, "team": 1, "web_name": "Alpha Player"},
            {"id": 2, "team": 2, "web_name": "Beta Player"},
        ],
    }


def _discovery(catalogue: dict, *, source_url: str = "https://alpha.example/news/1") -> dict:
    result = {
        "schema_version": "1.0",
        "discovery_id": "news-discovery:2026-27:2026-08-01T18:30:00Z",
        "season": "2026-27",
        "observed_at": "2026-08-01T18:30:00Z",
        "status": "complete",
        "coverage": [
            {"club_id": "alpha", "status": "searched", "result_count": 1},
            {"club_id": "beta", "status": "searched", "result_count": 0},
        ],
        "leads": [
            {
                "club_id": "alpha",
                "source_url": source_url,
                "published_at": "2026-08-01T12:00:00Z",
            }
        ],
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _run(tmp_path: Path, *, source_url: str = "https://alpha.example/news/1") -> dict:
    prompt_path, prompt_sha = _prompt(tmp_path)
    catalogue = _catalogue()
    catalogue_sha = _digest(
        json.dumps(catalogue, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    return {
        "schema_version": "model-evidence-run-v1",
        "run_id": "composer:2026-08-01T18:30:00Z",
        "model": {"id": "composer-2.5", "display_name": "Composer 2.5"},
        "prompt": {
            "path": prompt_path,
            "version": "test-v1",
            "sha256": prompt_sha,
        },
        "observed_at": "2026-08-01T18:30:00Z",
        "available_at": "2026-08-01T18:31:00Z",
        "bound_packet_sha256": "a" * 64,
        "discovery_sha256": _discovery(catalogue, source_url=source_url)[
            "content_sha256"
        ],
        "scope": {
            "catalogue_sha256": catalogue_sha,
            "searched_club_ids": ["alpha", "beta"],
            "watchlist_player_uids": [
                "player:2026-27:1",
                "player:2026-27:2",
            ],
            "watchlist_basis": "top packet candidates plus comparator players",
        },
        "coverage": {
            "alpha": {"status": "complete", "lead_count": 1},
            "beta": {"status": "empty", "lead_count": 0},
        },
        "claims": [
            {
                "claim_id": "candidate-alpha-1",
                "club_id": "alpha",
                "player_uid": "player:2026-27:1",
                "source_id": "official-club-communications",
                "source_url": source_url,
                "source_title": "Alpha training update",
                "claim_text": "Alpha Player returned to training after an illness.",
                "why_relevant": "This may change the player's GW1 minutes risk.",
                "claim_type": "availability",
                "status": "doubtful",
                "confidence": 0.72,
                "published_at": "2026-08-01T12:00:00Z",
                "expires_at": "2026-08-15T17:30:00Z",
                "decision_boundary_ids": ["player:2026-27:1:start"],
                "estimated_impact_points": 2.0,
            }
        ],
        "decision_trace": [
            {
                "boundary_id": "player:2026-27:1:start",
                "decision": "retain Alpha Player on the watchlist",
                "rationale": "The official training update keeps minutes uncertainty live.",
                "alternatives_rejected": ["treat status=a as a nailed start"],
                "supporting_claim_ids": ["candidate-alpha-1"],
                "conflicting_claim_ids": [],
                "confidence": 0.7,
                "falsifiers": ["confirmed full-team start"],
            }
        ],
    }


def test_model_run_admits_claim_and_retains_decision_trace(tmp_path: Path) -> None:
    run = _run(tmp_path)
    ledger, audit = ingest_model_evidence_run(
        run,
        None,
        source_registry=_registry(),
        policy=_policy(),
        catalogue=_catalogue(),
        bootstrap=_bootstrap(),
        discovery=_discovery(_catalogue()),
        fetcher=lambda _: _digest(b"official page body"),
        repo_root=tmp_path,
    )

    assert audit["status"] == "complete"
    assert len(audit["accepted_claim_ids"]) == 1
    assert audit["coverage"]["coverage_gaps"] == []
    assert audit["decision_trace"][0]["supporting_claim_ids"] == [
        audit["accepted_claim_ids"][0]
    ]
    assert ledger["claims"][0]["provenance"]["model_id"] == "composer-2.5"
    assert ledger["claims"][0]["provenance"]["source_document_hash_sha256"] == _digest(
        b"official page body"
    )
    assert "official page body" not in json.dumps(ledger)


def test_model_run_is_idempotent_for_same_source_version(tmp_path: Path) -> None:
    run = _run(tmp_path)
    first, first_audit = ingest_model_evidence_run(
        run,
        None,
        source_registry=_registry(),
        policy=_policy(),
        catalogue=_catalogue(),
        bootstrap=_bootstrap(),
        discovery=_discovery(_catalogue()),
        fetcher=lambda _: _digest(b"same body"),
        repo_root=tmp_path,
    )
    second, second_audit = ingest_model_evidence_run(
        run,
        first,
        source_registry=_registry(),
        policy=_policy(),
        catalogue=_catalogue(),
        bootstrap=_bootstrap(),
        discovery=_discovery(_catalogue()),
        fetcher=lambda _: _digest(b"same body"),
        repo_root=tmp_path,
    )

    assert len(first["claims"]) == len(second["claims"]) == 1
    assert second_audit["duplicate_claim_ids"] == first_audit["accepted_claim_ids"]
    assert second_audit["accepted_claim_ids"] == []


def test_non_official_url_is_rejected_without_fetch(tmp_path: Path) -> None:
    run = _run(tmp_path, source_url="https://social.example/post/1")
    calls: list[str] = []
    ledger, audit = ingest_model_evidence_run(
        run,
        None,
        source_registry=_registry(),
        policy=_policy(),
        catalogue=_catalogue(),
        bootstrap=_bootstrap(),
        discovery=_discovery(_catalogue(), source_url="https://social.example/post/1"),
        fetcher=lambda url: calls.append(url) or _digest(b"should not fetch"),
        repo_root=tmp_path,
    )

    assert ledger["claims"] == []
    assert calls == []
    assert audit["rejected_claims"][0]["reasons"] == [
        "source_url is outside the registered official catalogue: "
        "https://social.example/post/1"
    ]


def test_incomplete_broad_coverage_is_degraded_but_valid_claims_survive(
    tmp_path: Path,
) -> None:
    run = _run(tmp_path)
    run["scope"]["searched_club_ids"] = ["alpha"]
    run["coverage"].pop("beta")
    discovery = _discovery(_catalogue())
    discovery["coverage"][1]["status"] = "missing"
    discovery["content_sha256"] = artifact_hash(discovery)
    run["discovery_sha256"] = discovery["content_sha256"]
    _, audit = ingest_model_evidence_run(
        run,
        None,
        source_registry=_registry(),
        policy=_policy(),
        catalogue=_catalogue(),
        bootstrap=_bootstrap(),
        discovery=discovery,
        fetcher=lambda _: _digest(b"official page body"),
        repo_root=tmp_path,
    )

    assert audit["status"] == "degraded"
    assert audit["coverage"]["coverage_gaps"] == ["beta"]
    assert len(audit["accepted_claim_ids"]) == 1


def test_watchlist_is_broad_and_exact(tmp_path: Path) -> None:
    run = _run(tmp_path)
    run["scope"]["watchlist_player_uids"] = ["player:2026-27:999"]
    with pytest.raises(ModelEvidenceRunError, match="unknown player IDs"):
        ingest_model_evidence_run(
            run,
            None,
            source_registry=_registry(),
            policy=_policy(),
            catalogue=_catalogue(),
            bootstrap=_bootstrap(),
            discovery=_discovery(_catalogue()),
            fetcher=lambda _: _digest(b"official page body"),
            repo_root=tmp_path,
        )
