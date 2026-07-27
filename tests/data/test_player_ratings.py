"""Player ratings are immutable, cutoff-safe and isolated from the baseline."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.capture_player_ratings import main as capture_main
from src.ingestion.registry import get_source
from src.ingestion.player_ratings import (
    PlayerRatingError,
    artifact_hash,
    build_player_rating_feature_payload,
    build_player_rating_ledger,
    normalise_player_rating_snapshot,
)


SOURCE_HASH = "a" * 64
ROWS = [
    {
        "source_player_id": "sb-11",
        "player_name": "Player One",
        "team_name": "Alpha",
        "rating": 7.25,
    },
    {
        "source_player_id": "sb-12",
        "player_name": "Player Two",
        "team_name": "Alpha",
        "rating": 6.5,
    },
]
IDENTITIES = {"sb-11": 101, "sb-12": 102}
ROOT = Path(__file__).resolve().parents[2]


def _snapshot(
    *,
    rows: list[dict] | None = None,
    identity_map: dict | None = None,
    source_hash: str = SOURCE_HASH,
    observed_at: str = "2026-08-20T09:00:00Z",
    available_at: str = "2026-08-20T09:01:00Z",
    decision_cutoff: str = "2026-08-21T17:30:00Z",
    published_at: str | None = None,
    max_age_hours: int = 720,
) -> dict:
    return normalise_player_rating_snapshot(
        rows if rows is not None else ROWS,
        source_id="statsbomb-open",
        source_sha256=source_hash,
        origin="local://statsbomb-open/derived-player-ratings.json",
        methodology_id="transparent-event-rating",
        methodology_version="1.0.0",
        observed_at=observed_at,
        available_at=available_at,
        decision_cutoff=decision_cutoff,
        identity_map=identity_map if identity_map is not None else IDENTITIES,
        published_at=published_at,
        max_age_hours=max_age_hours,
    )


def test_snapshot_is_deterministic_identity_resolved_and_self_hashed() -> None:
    first = _snapshot()
    second = _snapshot(rows=deepcopy(ROWS), identity_map=dict(IDENTITIES))
    assert first == second
    assert first["status"] == "complete"
    assert first["admitted_count"] == 2
    assert first["quarantined_count"] == 0
    assert first["quarantine_rate"] == 0.0
    assert [row["official_player_id"] for row in first["ratings"]] == [101, 102]
    assert first["content_sha256"] == artifact_hash(first)
    assert first["collection_mode"] == "pre_acquired_local_rows_no_network_fetch"
    assert first["published_at"] is None
    assert first["effective_at"] is None
    assert first["finalised_at"] is None


def test_source_governance_matches_the_sealed_ablation() -> None:
    config = json.loads(
        (
            ROOT / "config/data_sources/2026-27-player-ratings.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (
            ROOT / "control/manifests/2026-27-player-ratings.json"
        ).read_text(encoding="utf-8")
    )
    preregistration = json.loads(
        (
            ROOT
            / "reports/forecasting/2026-27-preregistration/preregistration.json"
        ).read_text(encoding="utf-8")
    )
    source = get_source(config["selected_source_id"])
    allowed = preregistration["candidate_families"]["player_ratings"][
        "allowed_source_ids"
    ]
    assert config["selected_source_id"] in allowed
    assert source["enabled"] is True
    assert source["licence_status"] == "restricted"
    assert "method_prototyping" in source["allowed_use"]
    assert source["activation_approval"]["terms"] == "approved"
    assert source["activation_approval"]["cost"] == "approved_zero"
    assert manifest["selected_source_id"] == config["selected_source_id"]
    assert manifest["current_live_coverage"] == "unavailable_not_verified"


def test_unresolved_or_ambiguous_identities_quarantine_without_name_guessing() -> None:
    unresolved = _snapshot(identity_map={"sb-11": 101})
    assert unresolved["status"] == "degraded"
    assert unresolved["admitted_count"] == 1
    assert unresolved["quarantined_count"] == 1
    assert unresolved["quarantine_rate"] == 0.5
    assert unresolved["quarantine"][0]["reason"] == "unresolved_player_identity"
    assert unresolved["identity_policy"] == (
        "explicit_mapping_only_never_name_guessing"
    )

    unrelated_alias = _snapshot(
        identity_map={"sb-11": 101, "sb-12": 102, "unused-alias": 101}
    )
    assert unrelated_alias["status"] == "complete"
    assert unrelated_alias["quarantined_count"] == 0

    ambiguous = _snapshot(identity_map={"sb-11": 101, "sb-12": 101})
    assert ambiguous["admitted_count"] == 0
    assert {
        row["reason"] for row in ambiguous["quarantine"]
    } == {"ambiguous_official_identity_mapping"}


def test_bad_values_unauthorised_sources_and_late_rows_fail_closed() -> None:
    bad = deepcopy(ROWS)
    bad[0]["rating"] = 11
    snapshot = _snapshot(rows=bad)
    assert snapshot["admitted_count"] == 1
    assert snapshot["quarantine"][0]["reason"] == "invalid_rating"

    with pytest.raises(PlayerRatingError, match="not approved"):
        normalise_player_rating_snapshot(
            ROWS,
            source_id="commercial-epl-event-data",
            source_sha256=SOURCE_HASH,
            origin="local://commercial/ratings.json",
            methodology_id="provider-rating",
            methodology_version="1",
            observed_at="2026-08-20T09:00:00Z",
            available_at="2026-08-20T09:01:00Z",
            decision_cutoff="2026-08-21T17:30:00Z",
            identity_map=IDENTITIES,
        )
    with pytest.raises(PlayerRatingError, match="strictly before"):
        _snapshot(
            observed_at="2026-08-21T17:30:00Z",
            available_at="2026-08-21T17:30:00Z",
        )
    with pytest.raises(PlayerRatingError, match="cannot be before"):
        _snapshot(
            observed_at="2026-08-20T09:00:00Z",
            available_at="2026-08-20T08:59:59Z",
        )
    with pytest.raises(PlayerRatingError, match="published_at cannot be after"):
        _snapshot(published_at="2026-08-20T09:01:01Z")


def test_ledger_excludes_future_supersedes_and_expires() -> None:
    first = _snapshot(max_age_hours=48)
    changed_rows = deepcopy(ROWS)
    changed_rows[0]["rating"] = 8.0
    later = _snapshot(
        rows=changed_rows,
        source_hash="b" * 64,
        observed_at="2026-08-21T09:00:00Z",
        available_at="2026-08-21T09:01:00Z",
        decision_cutoff="2026-08-22T17:30:00Z",
        max_age_hours=48,
    )
    before = build_player_rating_ledger(
        [first, later], as_of="2026-08-20T12:00:00Z"
    )
    assert before["excluded_future_snapshot_ids"] == [later["content_sha256"]]
    assert next(
        row for row in before["ratings"] if row["official_player_id"] == 101
    )["rating"] == 7.25

    after = build_player_rating_ledger(
        [first, later], as_of="2026-08-21T12:00:00Z"
    )
    latest = next(
        row for row in after["ratings"] if row["official_player_id"] == 101
    )
    assert latest["rating"] == 8.0
    assert latest["superseded_snapshot_ids"] == [first["content_sha256"]]

    expired = build_player_rating_ledger(
        [first, later], as_of="2026-08-23T09:01:00Z"
    )
    assert expired["status"] == "degraded"
    assert expired["ratings"] == []
    assert len(expired["expired"]) == 2


def test_missing_or_expired_ratings_degrade_to_exact_baseline_contract() -> None:
    empty = build_player_rating_ledger(
        [], as_of="2026-08-20T12:00:00Z"
    )
    payload = build_player_rating_feature_payload(empty)
    assert payload["status"] == "degraded"
    assert payload["ratings"] == []
    assert payload["effect_weights"] is None
    assert payload["fallback"] == "byte_identical_baseline"
    assert payload["content_sha256"] == artifact_hash(payload)

    ready = build_player_rating_feature_payload(
        build_player_rating_ledger(
            [_snapshot()], as_of="2026-08-20T12:00:00Z"
        )
    )
    assert ready["status"] == "shadow_ready"
    assert ready["fallback"] is None
    assert ready["effect_weights"] is None
    assert [row["official_player_id"] for row in ready["ratings"]] == [101, 102]


def test_hash_tampering_and_duplicate_source_rows_fail_closed() -> None:
    changed = _snapshot()
    changed["admitted_count"] += 1
    with pytest.raises(PlayerRatingError, match="content hash mismatch"):
        build_player_rating_ledger(
            [changed], as_of="2026-08-20T12:00:00Z"
        )
    duplicate = ROWS + [deepcopy(ROWS[0])]
    with pytest.raises(PlayerRatingError, match="duplicate source_player_id"):
        _snapshot(rows=duplicate)


def test_local_capture_cli_is_idempotent_and_refuses_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    envelope = {
        "source_id": "statsbomb-open",
        "source_sha256": SOURCE_HASH,
        "origin": "local://statsbomb-open/derived-player-ratings.json",
        "methodology": {
            "methodology_id": "transparent-event-rating",
            "version": "1.0.0",
        },
        "observed_at": "2026-08-20T09:00:00Z",
        "available_at": "2026-08-20T09:01:00Z",
        "decision_cutoff": "2026-08-21T17:30:00Z",
        "identity_map": IDENTITIES,
        "rows": ROWS,
    }
    source = tmp_path / "input.json"
    out = tmp_path / "snapshot.json"
    source.write_text(json.dumps(envelope), encoding="utf-8")

    assert capture_main(["--input", str(source), "--out", str(out)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "written"
    assert capture_main(["--input", str(source), "--out", str(out)]) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "unchanged"
    assert second["content_sha256"] == first["content_sha256"]
    assert hashlib.sha256(out.read_bytes()).hexdigest()

    envelope["rows"][0]["rating"] = 9.0
    source.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(PlayerRatingError, match="refusing to overwrite"):
        capture_main(["--input", str(source), "--out", str(out)])
