"""Line-ups/minutes reconcile and degraded-family contracts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.ingestion.lineups_minutes import (
    LineupsMinutesError,
    admit_raw_provider_snapshot,
    artifact_hash,
    capture_provider_snapshot_or_degrade,
    degraded_lineups_family,
    provider_credential_status,
    reconcile_lineups_minutes,
    source_snapshot_hash,
    verify_snapshot_integrity,
    write_immutable_json,
)

ROOT = Path(__file__).parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-lineups-minutes.json").read_text(
        encoding="utf-8"
    )
)


def _approved_config(*, min_started_xi: int = 2, min_admitted: int = 2) -> dict:
    cfg = deepcopy(CONFIG)
    cfg["selected_provider"] = "api-football"
    for item in cfg["providers"]:
        if item["provider_id"] == "api-football":
            item["registry_enabled"] = True
            item["rights_approved"] = True
            item["owner_approved"] = True
    cfg["admission"]["min_started_xi"] = min_started_xi
    cfg["admission"]["min_admitted_players"] = min_admitted
    return cfg


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


def _raw_snapshot() -> dict:
    return {
        "schema_version": "1.0",
        "provider_id": "api-football",
        "provider_fixture_id": "fx1",
        "source_id": "api-football",
        "source_version": "fixture-v1",
        "acquisition_status": "success",
        "observed_at": "2026-08-20T10:00:00Z",
        "available_at": "2026-08-20T10:00:00Z",
        "players": [
            {"provider_player_id": "p1", "started": True, "minutes": 90},
            {"provider_player_id": "p2", "started": True, "minutes": 90},
        ],
    }


def _sealed_snapshot() -> dict:
    return admit_raw_provider_snapshot(
        _raw_snapshot(),
        expected_provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
    )


def test_reconciles_explicit_aliases_and_seals_artifact() -> None:
    snapshot = _sealed_snapshot()
    result = reconcile_lineups_minutes(
        snapshot,
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=_approved_config(),
        cutoff="2026-08-20T12:00:00Z",
    )
    assert result["status"] == "complete"
    assert result["players"][0]["status"] == "admitted"
    assert result["available_at"] == "2026-08-20T10:00:00Z"
    assert result["source_sha256"] == snapshot["content_sha256"]
    assert result["content_sha256"] == artifact_hash(result)


def _reseal(snapshot: dict) -> dict:
    body = {
        key: deepcopy(value)
        for key, value in snapshot.items()
        if key not in {"content_sha256", "source_sha256"}
    }
    with_source = {**body, "source_sha256": source_snapshot_hash(body)}
    return {**with_source, "content_sha256": artifact_hash(with_source)}

def test_disagreement_unmapped_and_after_cutoff_do_not_admit() -> None:
    changed = _reseal({**_sealed_snapshot(), "players": [
        {"provider_player_id": "p1", "started": True, "minutes": 88},
        {"provider_player_id": "p2", "started": True, "minutes": 90},
    ]})
    result = reconcile_lineups_minutes(
        changed,
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=_approved_config(),
        cutoff="2026-08-20T12:00:00Z",
    )
    assert result["players"][0]["status"] == "quarantined"
    assert result["quality"]["quarantined_player_count"] == 1

    late = _reseal({**_sealed_snapshot(), "observed_at": "2026-08-20T13:00:00Z"})
    with pytest.raises(LineupsMinutesError, match="after cutoff"):
        reconcile_lineups_minutes(
            late,
            fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
            aliases=ALIASES,
            config=_approved_config(),
            cutoff="2026-08-20T12:00:00Z",
        )

    unknown = _reseal({**_sealed_snapshot(), "players": [
        {"provider_player_id": "unknown", "started": True, "minutes": 90},
        {"provider_player_id": "p2", "started": True, "minutes": 90},
    ]})
    gaps = reconcile_lineups_minutes(
        unknown,
        fpl_minutes={"fixture:1": {"102": 90}},
        aliases=ALIASES,
        config=_approved_config(min_started_xi=1, min_admitted=1),
        cutoff="2026-08-20T12:00:00Z",
    )["quality"]["gaps"]
    assert "unmapped_provider_player:unknown" in gaps


def test_immutable_write(tmp_path: Path) -> None:
    value = reconcile_lineups_minutes(
        _sealed_snapshot(),
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=_approved_config(),
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

    calls: list[str] = []

    def fetch(**kwargs):
        calls.append("called")
        raise RuntimeError("should not fetch")

    # Even with credentials, null selected_provider must not fetch.
    degraded = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ={"API_FOOTBALL_KEY": "secret"},
        fetch=fetch,
    )
    assert calls == []
    assert degraded["status"] == "degraded"
    assert degraded["reason"] == "no_provider_selected"
    assert degraded["baseline_unchanged"] is True
    assert degraded["quality"]["retry_scheduled"] is False
    assert degraded["players"] == []


def test_timeout_rate_limit_and_outage_degrade_without_retry() -> None:
    environ = {"API_FOOTBALL_KEY": "secret-not-logged"}
    cfg = _approved_config()

    def boom_timeout(**kwargs):
        raise TimeoutError("slow")

    timeout = capture_provider_snapshot_or_degrade(
        config=cfg,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ=environ,
        fetch=boom_timeout,
    )
    assert timeout["reason"] == "timeout"

    limited = capture_provider_snapshot_or_degrade(
        config=cfg,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ=environ,
        fetch=lambda **kwargs: {
            "schema_version": "1.0",
            "http_status": 429,
            "acquisition_status": "http_error",
        },
    )
    assert limited["reason"] == "rate_limited"

    outage = capture_provider_snapshot_or_degrade(
        config=cfg,
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
    assert CONFIG["trial_status"]["blocker_bead"] == "FPL-eah"
    assert CONFIG["minutes_tolerance"] == 1
    assert CONFIG["admission"]["min_started_xi"] == 11


def test_fetch_never_called_for_null_disabled_or_unapproved_provider() -> None:
    calls: list[str] = []

    def fetch(**kwargs):
        calls.append(kwargs["provider_id"])
        return _raw_snapshot()

    # 1) null selection
    out = capture_provider_snapshot_or_degrade(
        config=CONFIG,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ={"API_FOOTBALL_KEY": "x"},
        fetch=fetch,
    )
    assert out["reason"] == "no_provider_selected"
    assert calls == []

    # 2) selected but registry disabled
    cfg = deepcopy(CONFIG)
    cfg["selected_provider"] = "api-football"
    for item in cfg["providers"]:
        if item["provider_id"] == "api-football":
            item["registry_enabled"] = False
            item["rights_approved"] = True
            item["owner_approved"] = True
    out = capture_provider_snapshot_or_degrade(
        config=cfg,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ={"API_FOOTBALL_KEY": "x"},
        fetch=fetch,
    )
    assert out["reason"] == "provider_not_enabled"
    assert calls == []

    # 3) selected + enabled but rights unapproved
    cfg = deepcopy(CONFIG)
    cfg["selected_provider"] = "api-football"
    for item in cfg["providers"]:
        if item["provider_id"] == "api-football":
            item["registry_enabled"] = True
            item["rights_approved"] = False
            item["owner_approved"] = True
    out = capture_provider_snapshot_or_degrade(
        config=cfg,
        provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
        environ={"API_FOOTBALL_KEY": "x"},
        fetch=fetch,
    )
    assert out["reason"] == "rights_unapproved"
    assert calls == []


def test_capture_timestamps_and_hash_layers_are_independent() -> None:
    raw = _raw_snapshot()

    with pytest.raises(LineupsMinutesError, match="must equal capture"):
        admit_raw_provider_snapshot(
            raw,
            expected_provider_id="api-football",
            observed_at="2026-08-20T10:01:00Z",
        )

    available_after_observed = {
        **raw,
        "available_at": "2026-08-20T10:01:00Z",
    }
    with pytest.raises(LineupsMinutesError, match="must not be after"):
        admit_raw_provider_snapshot(
            available_after_observed,
            expected_provider_id="api-football",
            observed_at="2026-08-20T10:00:00Z",
        )

    raw["source_sha256"] = source_snapshot_hash(raw)
    admitted = admit_raw_provider_snapshot(
        raw,
        expected_provider_id="api-football",
        observed_at="2026-08-20T10:00:00Z",
    )
    assert admitted["source_sha256"] == source_snapshot_hash(admitted)
    assert admitted["content_sha256"] == artifact_hash(admitted)
    verify_snapshot_integrity(admitted)

    source_tampered = dict(admitted)
    source_tampered["source_sha256"] = "0" * 64
    source_tampered["content_sha256"] = artifact_hash(source_tampered)
    with pytest.raises(LineupsMinutesError, match="source_sha256 mismatch"):
        verify_snapshot_integrity(source_tampered)

    envelope_tampered = dict(admitted)
    envelope_tampered["content_sha256"] = "f" * 64
    with pytest.raises(LineupsMinutesError, match="content hash mismatch"):
        verify_snapshot_integrity(envelope_tampered)

def test_malformed_hash_mismatch_and_incomplete_xi() -> None:
    cfg = _approved_config(min_started_xi=11, min_admitted=11)

    # Malformed: started as string "false" must not be truthy / must reject
    bad = _raw_snapshot()
    bad["players"][0]["started"] = "false"
    admitted = admit_raw_provider_snapshot(
        bad, expected_provider_id="api-football", observed_at="2026-08-20T10:00:00Z"
    )
    with pytest.raises(LineupsMinutesError, match="boolean"):
        reconcile_lineups_minutes(
            admitted,
            fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
            aliases=ALIASES,
            config=_approved_config(min_started_xi=2, min_admitted=2),
            cutoff="2026-08-20T12:00:00Z",
        )

    # Hash mismatch on reconcile
    snap = _sealed_snapshot()
    tampered = dict(snap)
    tampered["content_sha256"] = "0" * 64
    with pytest.raises(LineupsMinutesError, match="content hash mismatch"):
        reconcile_lineups_minutes(
            tampered,
            fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
            aliases=ALIASES,
            config=cfg,
            cutoff="2026-08-20T12:00:00Z",
        )

    # Incomplete XI: two started players cannot satisfy min_started_xi=11
    incomplete = reconcile_lineups_minutes(
        _sealed_snapshot(),
        fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
        aliases=ALIASES,
        config=cfg,
        cutoff="2026-08-20T12:00:00Z",
    )
    assert incomplete["status"] == "degraded"
    assert incomplete["quality"]["started_count"] == 2
    assert incomplete["quality"]["min_started_xi"] == 11

    # Unselected provider refused at reconcile
    with pytest.raises(LineupsMinutesError, match="unselected/unapproved"):
        reconcile_lineups_minutes(
            _sealed_snapshot(),
            fpl_minutes={"fixture:1": {"101": 90, "102": 90}},
            aliases=ALIASES,
            config=CONFIG,
            cutoff="2026-08-20T12:00:00Z",
        )

    # Hash mismatch on admit
    raw = _raw_snapshot()
    raw["content_sha256"] = "b" * 64
    with pytest.raises(LineupsMinutesError, match="content hash mismatch"):
        admit_raw_provider_snapshot(
            raw,
            expected_provider_id="api-football",
            observed_at="2026-08-20T10:00:00Z",
        )
