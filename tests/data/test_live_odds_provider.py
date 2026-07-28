from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import httpx
import pytest

from src.forecasting.live_capture import build_live_forecast_capture
from src.ingestion.live_odds_provider import (
    LiveOddsProviderError,
    artifact_hash,
    capture_the_odds_api,
    write_immutable_json,
)
from src.ingestion.registry import load_registry


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (
        ROOT / "config/data_sources/2026-27-live-odds-provider.json"
    ).read_text(encoding="utf-8")
)

OBSERVED = "2026-08-20T17:30:00Z"
CUTOFF = "2026-08-21T17:30:00Z"


def payload() -> list[dict]:
    return [
        {
            "id": "event-1",
            "sport_key": "soccer_epl",
            "sport_title": "EPL",
            "commence_time": "2026-08-21T19:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Liverpool",
            "bookmakers": [
                {
                    "key": "williamhill",
                    "title": "William Hill",
                    "last_update": "2026-08-20T17:29:00Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "last_update": "2026-08-20T17:29:00Z",
                            "outcomes": [
                                {"name": "Arsenal", "price": 2.1},
                                {"name": "Draw", "price": 3.5},
                                {"name": "Liverpool", "price": 3.4},
                            ],
                        },
                        {
                            "key": "totals",
                            "last_update": "2026-08-20T17:28:00Z",
                            "outcomes": [
                                {"name": "Over", "price": 1.8, "point": 2.5},
                                {"name": "Under", "price": 2.0, "point": 2.5},
                            ],
                        },
                    ],
                }
            ],
        }
    ]


def client(
    *,
    status: int = 200,
    body: list[dict] | dict | None = None,
    request_counter: list[int] | None = None,
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request_counter is not None:
            request_counter.append(1)
        assert request.url.path == "/v4/sports/soccer_epl/odds"
        assert request.url.params["apiKey"] == "fixture-secret"
        assert request.url.params["regions"] == "uk"
        assert request.url.params["markets"] == "h2h,totals"
        return httpx.Response(
            status,
            json=payload() if body is None else body,
            headers={
                "x-requests-remaining": "498",
                "x-requests-used": "2",
                "x-requests-last": "2",
                "retry-after": "60" if status == 429 else "",
            },
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_capture_is_cutoff_safe_quota_bound_and_secret_free(
    tmp_path: Path,
) -> None:
    with client() as http:
        capture = capture_the_odds_api(
            http,
            season="2026-27",
            slot="T-24h",
            observed_at=OBSERVED,
            decision_cutoff=CUTOFF,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            api_key="fixture-secret",
            mode="fixture",
        )

    assert capture["status"] == "complete"
    assert capture["quota"] == {"last": 2, "remaining": 498, "used": 2}
    assert capture["snapshot"]["slot"] == "T-24h"
    assert capture["snapshot"]["lead_time_hours"] == 24.0
    assert len(capture["snapshot"]["payload"]["markets"]) == 2
    assert capture["snapshot"]["source_sha256"]
    assert capture["content_sha256"] == artifact_hash(capture)
    encoded = json.dumps(capture, sort_keys=True)
    assert "fixture-secret" not in encoded
    assert "apiKey" not in capture["acquisition"]["request_url"]
    assert capture["account_writes"] is False
    assert capture["authentication"] == "api_key_environment"


def test_snapshot_is_accepted_by_existing_live_forecast_contract(
    tmp_path: Path,
) -> None:
    with client() as http:
        capture = capture_the_odds_api(
            http,
            season="2026-27",
            slot="T-24h",
            observed_at=OBSERVED,
            decision_cutoff=CUTOFF,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            api_key="fixture-secret",
            mode="fixture",
        )
    forecast = build_live_forecast_capture(
        bootstrap={
            "events": [{"id": 1, "deadline_time": CUTOFF}],
            "teams": [],
            "elements": [],
        },
        bootstrap_manifest={"content_hash_sha256": "a" * 64},
        observed_at=OBSERVED,
        decision_cutoff=CUTOFF,
        launch_context=None,
        market_snapshots=[capture["snapshot"]],
        source_registry=load_registry(),
        freeze_launch=False,
    )
    assert forecast["market_evidence"]["snapshots"][0]["source_id"] == (
        "the-odds-api"
    )


def test_missing_secret_and_invalid_slot_refuse_before_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("THE_ODDS_API_KEY", raising=False)
    calls: list[int] = []
    with client(request_counter=calls) as http:
        with pytest.raises(LiveOddsProviderError, match="THE_ODDS_API_KEY"):
            capture_the_odds_api(
                http,
                season="2026-27",
                slot="T-24h",
                observed_at=OBSERVED,
                decision_cutoff=CUTOFF,
                raw_out_dir=tmp_path / "raw",
                config=CONFIG,
                mode="fixture",
            )
        with pytest.raises(LiveOddsProviderError, match="outside"):
            capture_the_odds_api(
                http,
                season="2026-27",
                slot="T-2h",
                observed_at=OBSERVED,
                decision_cutoff=CUTOFF,
                raw_out_dir=tmp_path / "raw",
                config=CONFIG,
                api_key="fixture-secret",
                mode="fixture",
            )
    assert calls == []


def test_rate_limit_degrades_and_preserves_retry_metadata(
    tmp_path: Path,
) -> None:
    with client(status=429, body={"error_code": "OUT_OF_USAGE_CREDITS"}) as http:
        capture = capture_the_odds_api(
            http,
            season="2026-27",
            slot="T-24h",
            observed_at=OBSERVED,
            decision_cutoff=CUTOFF,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            api_key="fixture-secret",
            mode="fixture",
        )
    assert capture["status"] == "degraded"
    assert capture["degraded_reasons"] == ["provider_http_429"]
    assert capture["retry_after_seconds"] == 60
    assert capture["snapshot"] is None
    assert capture["quota"]["remaining"] == 498


def test_missing_required_market_degrades_without_inventing_odds(
    tmp_path: Path,
) -> None:
    no_h2h = deepcopy(payload())
    no_h2h[0]["bookmakers"][0]["markets"] = [
        no_h2h[0]["bookmakers"][0]["markets"][1]
    ]
    with client(body=no_h2h) as http:
        capture = capture_the_odds_api(
            http,
            season="2026-27",
            slot="T-24h",
            observed_at=OBSERVED,
            decision_cutoff=CUTOFF,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            api_key="fixture-secret",
            mode="fixture",
        )
    assert capture["status"] == "degraded"
    assert capture["degraded_reasons"] == [
        "event:event-1:missing_required_market:h2h"
    ]
    assert capture["snapshot"] is not None
    assert all(
        row["market_key"] != "h2h"
        for row in capture["snapshot"]["payload"]["markets"]
    )


def test_immutable_writer_allows_identical_rerun_and_refuses_change(
    tmp_path: Path,
) -> None:
    path = tmp_path / "snapshot.json"
    value = {"content_sha256": "a" * 64}
    assert write_immutable_json(path, value) == "written"
    assert write_immutable_json(path, value) == "unchanged"
    with pytest.raises(FileExistsError, match="immutable"):
        write_immutable_json(path, {"content_sha256": "b" * 64})


@pytest.mark.parametrize(
    "slot,observed_at,expected_lead",
    [
        ("T-24h", "2026-08-20T17:30:00Z", 24.0),
        ("T-8h", "2026-08-21T09:30:00Z", 8.0),
        ("T-2h", "2026-08-21T15:30:00Z", 2.0),
        ("final", "2026-08-21T17:15:00Z", 0.25),
    ],
)
def test_each_capture_slot_builds_the_same_normalized_contract(
    tmp_path: Path, slot: str, observed_at: str, expected_lead: float
) -> None:
    with client() as http:
        capture = capture_the_odds_api(
            http,
            season="2026-27",
            slot=slot,
            observed_at=observed_at,
            decision_cutoff=CUTOFF,
            raw_out_dir=tmp_path / "raw",
            config=CONFIG,
            api_key="fixture-secret",
            mode="fixture",
        )
    assert capture["status"] == "complete"
    assert capture["snapshot"]["slot"] == slot
    assert capture["snapshot"]["lead_time_hours"] == expected_lead
