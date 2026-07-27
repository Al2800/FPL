from __future__ import annotations

import json
from pathlib import Path

import httpx

from src.ingestion.live_evidence_collector import capture_official_fpl_evidence


REPO = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (REPO / "config/data_sources/2026-27-evidence.json").read_text(
        encoding="utf-8"
    )
)


def test_unrelated_bootstrap_change_does_not_duplicate_unchanged_news(
    tmp_path: Path,
) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={
                "elements": [
                    {
                        "id": 1,
                        "code": 101,
                        "web_name": "Player One",
                        "status": "d",
                        "news": "Hamstring issue",
                        "news_added": "2026-08-14T10:00:00Z",
                        "chance_of_playing_this_round": 50,
                        "chance_of_playing_next_round": 75,
                    }
                ],
                "events": [{"id": 1, "unrelated_revision": request_count}],
            },
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = capture_official_fpl_evidence(
            client,
            season="2026-27",
            observed_at="2026-08-14T12:00:00Z",
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
        )
        second = capture_official_fpl_evidence(
            client,
            season="2026-27",
            observed_at="2026-08-14T13:00:00Z",
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            base_url="https://example.test",
            mode="fixture",
            previous_ledger=first["ledger"],
        )

    assert (
        first["acquisition"]["content_hash_sha256"]
        != second["acquisition"]["content_hash_sha256"]
    )
    assert first["claim_count_added"] == 1
    assert second["claim_count_added"] == 0
    assert second["ledger"] == first["ledger"]
