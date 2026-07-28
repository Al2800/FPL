from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from src.evidence.live_evidence_ledger import live_evidence_hash
from src.ingestion.live_evidence_collector import (
    LiveEvidenceCollectionError,
    capture_official_fpl_evidence,
)


REPO = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (REPO / "config/data_sources/2026-27-evidence.json").read_text(
        encoding="utf-8"
    )
)
OBSERVED = "2026-08-14T12:00:00Z"


def client(*, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/bootstrap-static/"
        payload = {
            "elements": [
                {
                    "id": 1,
                    "code": 101,
                    "web_name": "Player One",
                    "status": "d",
                    "news": "Hamstring issue - 50% chance of playing",
                    "news_added": "2026-08-14T10:00:00Z",
                    "chance_of_playing_this_round": 50,
                    "chance_of_playing_next_round": 75,
                },
                {
                    "id": 2,
                    "code": 102,
                    "web_name": "Player Two",
                    "status": "i",
                    "news": "Awaiting assessment",
                    "news_added": None,
                    "chance_of_playing_this_round": 0,
                    "chance_of_playing_next_round": 25,
                },
                {
                    "id": 3,
                    "code": 103,
                    "web_name": "Player Three",
                    "status": "a",
                    "news": "",
                    "news_added": None,
                    "chance_of_playing_this_round": None,
                    "chance_of_playing_next_round": None,
                },
            ],
            "events": [],
            "teams": [],
            "element_types": [],
        }
        return httpx.Response(status, json=payload, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_official_fpl_collection_is_immutable_deduplicated_and_gap_explicit(
    tmp_path: Path,
) -> None:
    with client() as http:
        first = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
        )
        second = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            previous_ledger=first["ledger"],
        )

    assert first["status"] == "complete"
    assert first["claim_count_added"] == 1
    assert second["claim_count_added"] == 0
    assert second["ledger"] == first["ledger"]
    assert first["content_sha256"] == live_evidence_hash(first)
    assert first["gaps"] == [
        "player:2:news_missing_exact_publication_time"
    ]
    row = first["ledger"]["claims"][0]
    assert row["source_id"] == "fpl-official-endpoints"
    assert row["source_rights"]["admission_mode"] == "automated_snapshot"
    assert row["identity_bindings"][0]["entity_type"] == "fpl_code"
    assert first["account_writes"] is False
    assert first["authentication"] == "none"
    run_dir = tmp_path / "raw" / "20260814T120000Z"
    assert (run_dir / "bootstrap-static.json").exists()
    assert (run_dir / "bootstrap-static.meta.json").exists()


def test_official_fpl_http_failure_degrades_without_claims(
    tmp_path: Path,
) -> None:
    with client(status=503) as http:
        capture = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
        )
    assert capture["status"] == "degraded"
    assert capture["degraded_reasons"] == ["official_fpl_http_error"]
    assert capture["ledger"]["claims"] == []
    assert capture["account_writes"] is False


def endpoint_client(
    requests: list[httpx.Request],
    *,
    drift_path: str | None = None,
    rate_limit_path: str | None = None,
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "GET"
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        path = request.url.path
        if path == rate_limit_path:
            return httpx.Response(
                429,
                json={"detail": "rate limited"},
                headers={"retry-after": "120"},
                request=request,
            )
        if path == "/api/bootstrap-static/":
            payload = {
                "elements": [],
                "events": [],
                "teams": [],
                "element_types": [],
            }
        elif path == "/api/fixtures/":
            payload = [
                {
                    "id": 1,
                    "event": 1,
                    "kickoff_time": "2026-08-14T19:00:00Z",
                    "team_h": 1,
                    "team_a": 2,
                }
            ]
            if path == drift_path:
                payload[0].pop("team_a")
        elif path.startswith("/api/element-summary/"):
            payload = {"fixtures": [], "history": [], "history_past": []}
        elif path == "/api/event/3/live/":
            payload = {"elements": []}
        else:
            raise AssertionError(f"unexpected endpoint: {path}")
        return httpx.Response(200, json=payload, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_t24_endpoint_plan_is_bounded_read_only_and_reproducible(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    kwargs = {
        "season": "2026-27",
        "observed_at": OBSERVED,
        "raw_out_dir": tmp_path / "raw",
        "config": CONFIG,
        "base_url": "https://example.test",
        "mode": "fixture",
        "checkpoint_id": "T-24h",
        "player_ids": [2, 1, 2],
    }
    with endpoint_client(requests) as http:
        first = capture_official_fpl_evidence(http, **kwargs)
        second = capture_official_fpl_evidence(
            http, previous_ledger=first["ledger"], **kwargs
        )

    expected = [
        "/api/bootstrap-static/",
        "/api/fixtures/",
        "/api/element-summary/1/",
        "/api/element-summary/2/",
    ]
    assert [request.url.path for request in requests] == expected * 2
    assert first["status"] == "complete"
    assert first["request_count_planned"] == 4
    assert first["request_count_attempted"] == 4
    assert first["document_count"] == 4
    assert [row["endpoint_id"] for row in first["endpoint_captures"]] == [
        "bootstrap-static",
        "fixtures",
        "element-summary",
        "element-summary",
    ]
    assert [
        row["acquisition"]["manifest_id"]
        for row in first["endpoint_captures"]
    ] == [
        row["acquisition"]["manifest_id"]
        for row in second["endpoint_captures"]
    ]
    assert second["ledger"] == first["ledger"]
    assert second["claim_count_added"] == 0


def test_post_match_requests_only_explicit_gameweek_live_endpoint(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    with endpoint_client(requests) as http:
        capture = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            checkpoint_id="post_match",
            gameweek=3,
        )
    assert [request.url.path for request in requests] == [
        "/api/event/3/live/"
    ]
    assert capture["status"] == "complete"
    assert capture["acquisition"] is None
    assert capture["endpoint_captures"][0]["endpoint_id"] == "event-live"


def test_schema_drift_retains_raw_capture_and_degrades_visibly(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    with endpoint_client(requests, drift_path="/api/fixtures/") as http:
        capture = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            checkpoint_id="T-24h",
        )
    fixture = next(
        row for row in capture["endpoint_captures"]
        if row["endpoint_id"] == "fixtures"
    )
    assert capture["status"] == "degraded"
    assert fixture["status"] == "degraded"
    assert fixture["degraded_reasons"] == [
        "schema_drift:sample_missing_fields:team_a"
    ]
    assert fixture["acquisition"]["acquisition_status"] == "success"
    assert list((tmp_path / "raw").rglob("fixtures.json"))


def test_rate_limit_stops_remaining_plan_and_records_retry_after(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    with endpoint_client(requests, rate_limit_path="/api/fixtures/") as http:
        capture = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at=OBSERVED,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            checkpoint_id="T-24h",
            player_ids=[1],
        )
    assert [request.url.path for request in requests] == [
        "/api/bootstrap-static/",
        "/api/fixtures/",
    ]
    assert capture["status"] == "degraded"
    assert capture["request_count_planned"] == 3
    assert capture["request_count_attempted"] == 2
    assert capture["retry_after_seconds"] == 120
    assert capture["endpoint_captures"][2]["status"] == "not_attempted"
    assert capture["endpoint_captures"][2]["degraded_reasons"] == [
        "rate_limit_stop"
    ]


def test_explicit_player_limit_refuses_before_network(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []
    with endpoint_client(requests) as http:
        with pytest.raises(LiveEvidenceCollectionError, match="maximum"):
            capture_official_fpl_evidence(
                http,
                season="2026-27",
                observed_at=OBSERVED,
                raw_out_dir=tmp_path / "raw",
                config=CONFIG,
                base_url="https://example.test",
                mode="fixture",
                checkpoint_id="T-24h",
                player_ids=list(range(1, 42)),
            )
    assert requests == []
