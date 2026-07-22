"""Offline tests for public, immutable FPL live-shadow capture."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from scripts.capture_fpl_live_shadow import capture_live_shadow

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
