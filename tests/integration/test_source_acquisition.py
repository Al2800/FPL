"""Offline integration tests for the immutable acquisition contract."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.ingestion.acquisition import acquire_fixture, acquire_http
from src.ingestion.snapshot_fpl import snapshot_endpoint

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "control" / "schemas" / "data" / "source-snapshot-manifest.json"


def _validate(manifest: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)


def test_registered_disabled_source_can_run_from_fixture(tmp_path: Path):
    fixture = tmp_path / "matches.json"
    fixture.write_text('[{"id": 1}]\n', encoding="utf-8")

    manifest = acquire_fixture(
        source_id="football-data-org",
        fixture_path=fixture,
        origin="fixture://football-data-org/matches",
        out_dir=tmp_path / "raw",
        observed_at="2026-07-22T09:00:00Z",
    )

    _validate(manifest)
    assert manifest["acquisition_mode"] == "fixture"
    assert manifest["acquisition_status"] == "success"
    assert list((tmp_path / "raw").rglob("matches.json"))[0].read_bytes() == fixture.read_bytes()


def test_disabled_source_is_rejected_before_http_client_is_called(tmp_path: Path):
    class BombClient:
        called = False

        def get(self, url: str, *, timeout: float):
            self.called = True
            raise AssertionError("network boundary should not be reached")

    client = BombClient()
    try:
        acquire_http(
            client,
            source_id="football-data-org",
            url="https://api.football-data.org/v4/competitions/PL",
            out_dir=tmp_path,
            artifact_name="competition.json",
        )
        assert False, "expected PermissionError"
    except PermissionError:
        pass
    assert client.called is False


def test_identical_fixture_has_stable_content_and_manifest_identity(tmp_path: Path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text('{"value": 7}\n', encoding="utf-8")

    first = acquire_fixture(
        source_id="statsbomb-open",
        fixture_path=fixture,
        origin="fixture://statsbomb-open/event",
        out_dir=tmp_path / "raw",
        observed_at="2026-07-22T09:00:00Z",
    )
    second = acquire_fixture(
        source_id="statsbomb-open",
        fixture_path=fixture,
        origin="fixture://statsbomb-open/event",
        out_dir=tmp_path / "raw",
        observed_at="2026-07-22T10:00:00Z",
    )

    assert first["content_identity"] == second["content_identity"]
    assert first["manifest_id"] == second["manifest_id"]


def test_different_bytes_cannot_overwrite_same_snapshot_path(tmp_path: Path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text('{"value": 1}\n', encoding="utf-8")
    kwargs = {
        "source_id": "statsbomb-open",
        "fixture_path": fixture,
        "origin": "fixture://statsbomb-open/event",
        "out_dir": tmp_path / "raw",
        "observed_at": "2026-07-22T09:00:00Z",
    }
    acquire_fixture(**kwargs)
    fixture.write_text('{"value": 2}\n', encoding="utf-8")

    with pytest.raises(FileExistsError, match="immutable artefact"):
        acquire_fixture(**kwargs)


def test_fpl_snapshot_interface_uses_source_neutral_manifest(tmp_path: Path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"events": [], "elements": []})
    )
    with httpx.Client(transport=transport) as client:
        manifest = snapshot_endpoint(
            client,
            base_url="https://fantasy.premierleague.com",
            path="/api/bootstrap-static/",
            out_dir=tmp_path,
            registry_version="test-registry",
            observed_at="2026-07-22T09:00:00Z",
        )

    _validate(manifest)
    assert str(manifest["request_url"]).endswith("/api/bootstrap-static/")
    assert manifest["http_status"] == 200
    assert manifest["body_file"] == "api_bootstrap-static.json"
    assert manifest["schema_detection"]["top_level_keys"] == ["elements", "events"]
    persisted = json.loads(list(tmp_path.rglob("api_bootstrap-static.meta.json"))[0].read_text())
    assert persisted == manifest


def test_http_failure_retains_body_and_structured_evidence(tmp_path: Path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(503, content=b"temporarily unavailable")
    )
    with httpx.Client(transport=transport) as client:
        manifest = snapshot_endpoint(
            client,
            base_url="https://fantasy.premierleague.com",
            path="/api/fixtures/",
            out_dir=tmp_path,
            registry_version="test-registry",
            observed_at="2026-07-22T09:00:00Z",
        )

    _validate(manifest)
    assert manifest["acquisition_status"] == "http_error"
    assert manifest["failure"] == {
        "category": "http",
        "type": "HTTPStatus",
        "message": "HTTP 503",
    }
    assert list(tmp_path.rglob("api_fixtures.json"))[0].read_bytes() == b"temporarily unavailable"


def test_transport_failure_is_persisted_without_raising(tmp_path: Path):
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        manifest = snapshot_endpoint(
            client,
            base_url="https://fantasy.premierleague.com",
            path="/api/fixtures/",
            out_dir=tmp_path,
            registry_version="test-registry",
            observed_at="2026-07-22T09:00:00Z",
        )

    _validate(manifest)
    assert manifest["acquisition_status"] == "transport_error"
    assert manifest["http_status"] == 0
    assert manifest["bytes"] == 0
    assert manifest["failure"]["category"] == "transport"
