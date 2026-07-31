from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import httpx
import pytest

from src.evidence.availability_ledger import (
    new_availability_ledger,
    synchronise_availability_from_live_evidence,
)
from src.evidence.live_evidence_ledger import (
    LiveEvidenceLedgerError,
    live_evidence_hash,
    project_live_evidence,
)
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


def changing_client(snapshots: list[dict]) -> httpx.Client:
    index = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal index
        assert request.url.path == "/api/bootstrap-static/"
        payload = snapshots[min(index, len(snapshots) - 1)]
        index += 1
        return httpx.Response(200, json=payload, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def availability_snapshot(
    *,
    player_one: dict,
    player_two: dict | None = None,
) -> dict:
    second = player_two or {
        "id": 2,
        "code": 102,
        "web_name": "Player Two",
        "status": "d",
        "news": "Knock reported",
        "news_added": "2026-08-14T11:00:00Z",
        "chance_of_playing_this_round": 50,
        "chance_of_playing_next_round": 75,
    }
    return {
        "elements": [player_one, second],
        "events": [],
        "teams": [],
        "element_types": [],
    }


def player_uid(row: dict) -> str:
    return next(
        binding["stable_id"]
        for binding in row["identity_bindings"]
        if binding["entity_type"] == "player_uid"
    )


def test_changed_official_status_chains_and_reaches_availability_bridge(
    tmp_path: Path,
) -> None:
    first_payload = availability_snapshot(
        player_one={
            "id": 1,
            "code": 101,
            "web_name": "Player One",
            "status": "i",
            "news": "Injury confirmed",
            "news_added": "2026-08-14T11:00:00Z",
            "chance_of_playing_this_round": 0,
            "chance_of_playing_next_round": 25,
        }
    )
    second_payload = availability_snapshot(
        player_one={
            "id": 1,
            "code": 101,
            "web_name": "Player One",
            "status": "d",
            "news": "Doubtful after assessment",
            "news_added": "2026-08-14T12:00:00Z",
            "chance_of_playing_this_round": 50,
            "chance_of_playing_next_round": 75,
        }
    )
    third_payload = availability_snapshot(
        player_one={
            "id": 1,
            "code": 101,
            "web_name": "Player One",
            "status": "a",
            "news": "Returned to training",
            "news_added": "2026-08-14T13:00:00Z",
            "chance_of_playing_this_round": None,
            "chance_of_playing_next_round": None,
        }
    )

    with changing_client([first_payload, second_payload, third_payload]) as http:
        first = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at="2026-08-14T12:00:00Z",
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
        )
        second = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at="2026-08-14T13:00:00Z",
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            previous_ledger=first["ledger"],
        )
        third = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at="2026-08-14T14:00:00Z",
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            previous_ledger=second["ledger"],
        )

    first_claims = {
        row["claim_id"]: row for row in first["ledger"]["claims"]
    }
    second_claims = {
        row["claim_id"]: row for row in second["ledger"]["claims"]
    }
    third_claims = {
        row["claim_id"]: row for row in third["ledger"]["claims"]
    }
    player_one_ids = [
        claim_id
        for claim_id, row in third_claims.items()
        if player_uid(row) == "player:2026-27:1"
    ]
    assert len(player_one_ids) == 3
    first_id = next(
        claim_id
        for claim_id, row in first_claims.items()
        if player_uid(row) == "player:2026-27:1"
    )
    second_id = next(
        claim_id
        for claim_id, row in second_claims.items()
        if player_uid(row) == "player:2026-27:1"
        and claim_id != first_id
    )
    third_id = next(
        claim_id
        for claim_id in third_claims
        if player_uid(third_claims[claim_id]) == "player:2026-27:1"
        and claim_id not in {first_id, second_id}
    )
    assert second_claims[second_id]["supersedes_claim_ids"] == [first_id]
    assert third_claims[third_id]["supersedes_claim_ids"] == [second_id]

    view = project_live_evidence(
        third["ledger"], decision_at="2026-08-14T15:00:00Z"
    )
    assert [row["claim_id"] for row in view["accepted"]] == sorted(
        [third_id]
        + [
            claim_id
            for claim_id, row in third_claims.items()
            if player_uid(row) == "player:2026-27:2"
        ]
    )
    assert not view["conflicts"]
    assert {row["claim_id"] for row in view["excluded"]["superseded"]} == {
        first_id,
        second_id,
    }

    persistent = new_availability_ledger(
        season="2026-27", created_at="2026-08-14T12:00:00Z"
    )
    persistent, first_audit = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=first["ledger"],
        decision_at="2026-08-14T12:30:00Z",
    )
    persistent, second_audit = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=second["ledger"],
        decision_at="2026-08-14T13:30:00Z",
    )
    persistent, third_audit = synchronise_availability_from_live_evidence(
        persistent,
        live_evidence_ledger=third["ledger"],
        decision_at="2026-08-14T14:30:00Z",
    )
    assert first_id in first_audit["appended_claim_ids"]
    assert second_id in second_audit["appended_claim_ids"]
    assert third_id in third_audit["appended_claim_ids"]
    persistent_player_one = [
        row
        for row in persistent["claims"]
        if row["player_uid"] == "player:2026-27:1"
    ]
    assert [row["status"] for row in persistent_player_one] == [
        "unavailable",
        "doubtful",
        "available",
    ]
    assert persistent_player_one[-1]["supersedes_claim_ids"] == [second_id]


def test_tampered_official_predecessor_and_out_of_order_capture_fail_closed(
    tmp_path: Path,
) -> None:
    first_payload = availability_snapshot(
        player_one={
            "id": 1,
            "code": 101,
            "web_name": "Player One",
            "status": "i",
            "news": "Injury confirmed",
            "news_added": "2026-08-14T11:00:00Z",
            "chance_of_playing_this_round": 0,
            "chance_of_playing_next_round": 25,
        }
    )
    changed_payload = availability_snapshot(
        player_one={
            "id": 1,
            "code": 101,
            "web_name": "Player One",
            "status": "a",
            "news": "Returned to training",
            "news_added": "2026-08-14T12:00:00Z",
            "chance_of_playing_this_round": None,
            "chance_of_playing_next_round": None,
        }
    )
    with changing_client([first_payload]) as http:
        first = capture_official_fpl_evidence(
            http,
            season="2026-27",
            observed_at="2026-08-14T12:00:00Z",
            raw_out_dir=tmp_path / "raw-first",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
        )

    tampered = deepcopy(first["ledger"])
    tampered["claims"][0]["source_hash_sha256"] = "bad"
    tampered["content_sha256"] = live_evidence_hash(tampered)
    with changing_client([changed_payload]) as http:
        with pytest.raises(LiveEvidenceLedgerError, match="source_hash_sha256|source hash"):
            capture_official_fpl_evidence(
                http,
                season="2026-27",
                observed_at="2026-08-14T13:00:00Z",
                raw_out_dir=tmp_path / "raw-tampered",
                config=CONFIG,
                base_url="https://example.test",
                mode="fixture",
                previous_ledger=tampered,
            )

    with changing_client([changed_payload]) as http:
        with pytest.raises(LiveEvidenceCollectionError, match="out of order"):
            capture_official_fpl_evidence(
                http,
                season="2026-27",
                observed_at="2026-08-14T11:00:00Z",
                raw_out_dir=tmp_path / "raw-order",
                config=CONFIG,
                base_url="https://example.test",
                mode="fixture",
                previous_ledger=first["ledger"],
            )


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
