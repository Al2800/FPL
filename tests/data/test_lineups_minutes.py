"""Line-ups/minutes reconcile and degraded-family contracts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.ingestion.lineups_minutes import (
    LineupsMinutesError,
    artifact_hash,
    capture_provider_snapshot_or_degrade,
    degraded_lineups_family,
    provider_credential_status,
    reconcile_lineups_minutes,
    write_immutable_json,
)

ROOT = Path(__file__).parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-lineups-minutes.json").read_text(
        encoding="utf-8"
    )
)
ALIASES = {
    "aliases": [
        {
            "entity_type": "fixture",
            "provider_id": "api-football",
            "provider_entity_id": "fx1",
            "fpl_entity_id": "fixture:1",
        },
        {
            "entity_type": "player",
            "provider_id": "api-football",
            "provider_entity_id": "p1",
            "fpl_entity_id": "101",
        },
        {
            "entity_type": "player",
            "provider_id": "api-football",
            "provider_entity_id": "p2",
            "fpl_entity_id": "102",
        },
    ]
}
SNAPSHOT = {
    "provider_id": "api-football",
    "provider_fixture_id": "fx1",
    "source_id": "api-football",
    "source_version": "fixture-v1",
    "source_sha256": "a" * 64,
    "observed_at": "2026-08-20T10:00:00Z",
    "available_at": "2026-08-20T10:00:00Z",
    "players": [
        {"provider_player_id": "p1", "started": True, "minutes": 90},
        {"provider_player_id": "p2", "started": True, "minutes": 90},
    ],
}


def test_reconciles_explicit_aliases_and_seals_artifact() -> None:
    result = reconcile_lineups_minutes(
        SNAPSHOT,
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=CONFIG,
        cutoff="2026-08-20T12:00:00Z",
    )
    assert result["status"] == "complete"
    assert result["players"][0]["status"] == "admitted"
    assert result["available_at"] == "2026-08-20T10:00:00Z"
    assert result["source_sha256"] == "a" * 64
    assert result["content_sha256"] == artifact_hash(result)


def test_disagreement_unmapped_and_after_cutoff_do_not_admit() -> None:
    changed = deepcopy(SNAPSHOT)
    changed["players"][0]["minutes"] = 88
    result = reconcile_lineups_minutes(
        changed,
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=CONFIG,
        cutoff="2026-08-20T12:00:00Z",
    )
    assert result["players"][0]["status"] == "quarantined"
    assert result["quality"]["quarantined_player_count"] == 1

    late = deepcopy(SNAPSHOT)
    late["observed_at"] = "2026-08-20T13:00:00Z"
    with pytest.raises(LineupsMinutesError, match="after cutoff"):
        reconcile_lineups_minutes(
            late,
            fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
            aliases=ALIASES,
            config=CONFIG,
            cutoff="2026-08-20T12:00:00Z",
        )

    unknown = deepcopy(SNAPSHOT)
    unknown["players"][0]["provider_player_id"] = "unknown"
    gaps = reconcile_lineups_minutes(
        unknown,
        fpl_minutes={"fixture:1": {"102": 90}},
        aliases=ALIASES,
        config=CONFIG,
        cutoff="2026-08-20T12:00:00Z",
    )["quality"]["gaps"]
    assert "unmapped_provider_player:unknown" in gaps


def test_immutable_write(tmp_path: Path) -> None:
    value = reconcile_lineups_minutes(
        SNAPSHOT,
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=CONFIG,
        cutoff="2026-08-20T12:00:00Z",
    )
    target = tmp_path / "a.json"
    assert write_immutable_json(target, value) == "created"
    assert write_immutable_json(target, value) == "identical"
    value = dict(value)
    value["status"] = "x"
    with pytest.raises(FileExistsError):
        write_immutable_json(target, value)


def test_missing_credential_degrades_without_network() -> None:
    status = provider_credential_status(CONFIG, environ={})
    assert status["any_candidate_credential_present"] is False
    assert all(row["value_redacted"] is True for row in status["providers"])

    degraded = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ={},
        fetch=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("should not fetch")),
    )
    assert degraded["status"] == "degraded"
    assert degraded["reason"] == "missing_credential"
    assert degraded["baseline_unchanged"] is True
    assert degraded["quality"]["retry_scheduled"] is False
    assert degraded["players"] == []


def test_timeout_rate_limit_and_outage_degrade_without_retry() -> None:
    environ = {"API_FOOTBALL_KEY": "secret-not-logged"}

    def boom_timeout(**kwargs):
        raise TimeoutError("slow")

    timeout = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ=environ,
        fetch=boom_timeout,
    )
    assert timeout["reason"] == "timeout"

    limited = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ=environ,
        fetch=lambda **kwargs: {"http_status": 429, "acquisition_status": "http_error"},
    )
    assert limited["reason"] == "rate_limited"

    outage = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ=environ,
        fetch=lambda **kwargs: (_ for _ in ()).throw(ConnectionError("down")),
    )
    assert outage["reason"] == "provider_outage"

    with pytest.raises(LineupsMinutesError, match="retry"):
        degraded_lineups_family(
            reason="timeout",
            observed_at="2026-08-20T10:00:00Z",
            retry_scheduled=True,
        )


def test_config_records_access_gated_trial_and_null_provider() -> None:
    assert CONFIG["selected_provider"] is None
    assert CONFIG["trial_status"]["fixtures_measured"] == 0
    assert CONFIG["trial_status"]["blocker_bead"] == "FPL-lpm"
    assert CONFIG["minutes_tolerance"] == 1
