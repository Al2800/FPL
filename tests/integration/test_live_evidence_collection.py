from __future__ import annotations

import json
from pathlib import Path

import httpx

from src.evidence.live_evidence_ledger import live_evidence_hash
from src.ingestion.live_evidence_collector import capture_official_fpl_evidence


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
            ]
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
