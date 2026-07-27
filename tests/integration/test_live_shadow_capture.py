"""Offline tests for public, immutable FPL live-shadow capture."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator

from scripts.capture_fpl_live_shadow import capture_live_shadow
from src.orchestration.live_shadow import (
    LiveShadowError,
    build_unstructured_evidence_capture,
    shadow_hash,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SCHEMA = ROOT / "control" / "schemas" / "data" / "source-snapshot-manifest.json"
OBSERVED_AT = "2026-07-22T12:00:00Z"


def _client(*, fixtures_status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        if request.url.path == "/api/bootstrap-static/":
            return httpx.Response(
                200,
                json={"elements": [{"id": 1}], "events": [{"id": 1}]},
                request=request,
            )
        if request.url.path == "/api/fixtures/":
            return httpx.Response(
                fixtures_status,
                json=[{"id": 1}] if fixtures_status == 200 else {"detail": "unavailable"},
                request=request,
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_complete_capture_is_immutable_and_schema_valid(tmp_path: Path) -> None:
    with _client() as client:
        first = capture_live_shadow(
            out_dir=tmp_path,
            base_url="https://example.test",
            observed_at=OBSERVED_AT,
            client=client,
        )
        second = capture_live_shadow(
            out_dir=tmp_path,
            base_url="https://example.test",
            observed_at=OBSERVED_AT,
            client=client,
        )

    assert first == second
    assert first["status"] == "complete"
    assert first["capture_id"] == second["capture_id"]
    assert first["endpoint_count"] == 2
    assert first["failure_count"] == 0
    assert first["execution_mode"] == "no_execution"
    assert first["browser_actions"] is False
    assert first["account_writes"] is False
    assert first["authentication"] == "none"
    assert first["unstructured_evidence_capture"]["status"] == "degraded"

    validator = Draft202012Validator(json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8")))
    run_dir = tmp_path / "20260722T120000Z"
    validator.validate(json.loads((run_dir / "api_bootstrap-static.meta.json").read_text()))
    validator.validate(json.loads((run_dir / "api_fixtures.meta.json").read_text()))
    assert json.loads((run_dir / "capture-summary.json").read_text()) == first


def test_partial_endpoint_failure_is_persisted_and_explicit(tmp_path: Path) -> None:
    with _client(fixtures_status=503) as client:
        result = capture_live_shadow(
            out_dir=tmp_path,
            base_url="https://example.test",
            observed_at=OBSERVED_AT,
            client=client,
        )

    assert result["status"] == "partial_failure"
    assert result["failure_count"] == 1
    assert result["failures"][0]["http_status"] == 503
    assert result["failures"][0]["acquisition_status"] == "http_error"
    assert result["endpoints"][0]["acquisition_status"] == "success"
    assert result["endpoints"][1]["acquisition_status"] == "http_error"


def test_capture_paths_are_public_read_only_endpoints(tmp_path: Path) -> None:
    with _client() as client:
        result = capture_live_shadow(
            out_dir=tmp_path,
            base_url="https://example.test",
            observed_at=OBSERVED_AT,
            client=client,
        )

    urls = [endpoint["request_url"] for endpoint in result["endpoints"]]
    assert urls == [
        "https://example.test/api/bootstrap-static/",
        "https://example.test/api/fixtures/",
    ]
    assert all("/my-team/" not in url and "/transfers/" not in url for url in urls)


def _evidence_registry(*, enabled: bool = True) -> dict:
    return {
        "sources": [
            {
                "source_id": "fixture-club-news",
                "enabled": enabled,
                "licence_status": "restricted",
                "allowed_use": "private_analysis",
                "attribution": "Fixture club",
            }
        ]
    }


def _snapshot() -> dict:
    content = "The player will be assessed before the match."
    return {
        "source_id": "fixture-club-news",
        "document_id": "fixture-document-1",
        "url": "https://club.example/news/1",
        "title": "Team update",
        "published_at": "2026-07-22T08:00:00Z",
        "observed_at": "2026-07-22T08:05:00Z",
        "available_at": "2026-07-22T08:06:00Z",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "raw_file": "forecast-inputs/evidence-01.json",
    }


def test_unstructured_capture_has_exact_timestamps_source_hash_and_degraded_empty():
    cutoff = "2026-07-22T10:00:00Z"
    admitted = build_unstructured_evidence_capture(
        snapshots=[_snapshot()],
        source_registry=_evidence_registry(),
        decision_cutoff=cutoff,
    )
    assert admitted["content_sha256"] == shadow_hash(admitted)
    assert admitted["status"] == "complete"
    row = admitted["snapshots"][0]
    assert {
        "published_at",
        "observed_at",
        "available_at",
        "content_sha256",
        "snapshot_id",
    } <= set(row)

    degraded = build_unstructured_evidence_capture(
        snapshots=[],
        source_registry=_evidence_registry(),
        decision_cutoff=cutoff,
    )
    assert degraded["status"] == "degraded"
    assert degraded["snapshots"] == []
    assert degraded["degraded_reasons"] == [
        "no_governed_unstructured_evidence_available"
    ]


def test_unstructured_capture_refuses_late_disabled_and_hash_changed_evidence():
    late = _snapshot()
    late["available_at"] = "2026-07-22T10:00:01Z"
    with pytest.raises(LiveShadowError, match="after decision cutoff"):
        build_unstructured_evidence_capture(
            snapshots=[late],
            source_registry=_evidence_registry(),
            decision_cutoff="2026-07-22T10:00:00Z",
        )

    with pytest.raises(LiveShadowError, match="disabled"):
        build_unstructured_evidence_capture(
            snapshots=[_snapshot()],
            source_registry=_evidence_registry(enabled=False),
            decision_cutoff="2026-07-22T10:00:00Z",
        )

    changed = _snapshot()
    changed["content"] += " Changed."
    with pytest.raises(LiveShadowError, match="hash mismatch"):
        build_unstructured_evidence_capture(
            snapshots=[changed],
            source_registry=_evidence_registry(),
            decision_cutoff="2026-07-22T10:00:00Z",
        )
