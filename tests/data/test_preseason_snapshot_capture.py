"""Immutable 2026/27 preseason snapshot capture contracts."""

from __future__ import annotations

import json
import os
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ingestion.registry import load_registry
from src.orchestration.preseason_snapshot import (
    PreseasonSnapshotConflict,
    PreseasonSnapshotError,
    _bind_optional_artifact,
    admit_temporal_records,
    artifact_hash,
    capture_preseason_snapshot,
    enforce_checkpoint_window,
    expected_deadline_schedule,
    validate_checkpoint_id,
)
from src.scoring.rules_loader import ruleset_sha256

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config/data_sources/2026-27-preseason.json"
RULES = REPO / "control/rules/2026-27.yaml"
DEADLINE = "2026-08-21T17:30:00Z"
OBSERVED = "2026-07-27T10:05:27Z"
COMMIT = "a" * 40


def _bootstrap() -> dict:
    return {
        "element_types": [{"id": 1}],
        "elements": [{"id": 1, "web_name": "Alpha"}],
        "events": [
            {
                "id": 1,
                "name": "Gameweek 1",
                "deadline_time": DEADLINE,
            }
        ],
        "teams": [{"id": 1, "name": "Alpha FC"}],
    }


def _fixtures() -> list:
    return [
        {
            "id": 1,
            "event": 1,
            "team_h": 1,
            "team_a": 2,
            "kickoff_time": "2026-08-21T19:00:00Z",
        }
    ]


def _bodies() -> tuple[bytes, bytes]:
    return (
        json.dumps(_bootstrap(), sort_keys=True).encode("utf-8"),
        json.dumps(_fixtures(), sort_keys=True).encode("utf-8"),
    )


def test_checkpoint_ids_and_deadline_schedule() -> None:
    for checkpoint_id in (
        "launch",
        "weekly-2026-08-03",
        "T-48h",
        "T-24h",
        "T-8h",
        "T-2h",
        "final",
    ):
        assert validate_checkpoint_id(checkpoint_id, deadline=DEADLINE) == checkpoint_id
    with pytest.raises(PreseasonSnapshotError):
        validate_checkpoint_id("daily_preseason", deadline=DEADLINE)
    with pytest.raises(PreseasonSnapshotError):
        validate_checkpoint_id("weekly-2026-13-40", deadline=DEADLINE)

    schedule = expected_deadline_schedule(_bootstrap())
    assert schedule == {
        "T-48h": "2026-08-19T17:30:00Z",
        "T-24h": "2026-08-20T17:30:00Z",
        "T-8h": "2026-08-21T09:30:00Z",
        "T-2h": "2026-08-21T15:30:00Z",
        "final": "2026-08-21T17:25:00Z",
    }


def test_records_at_or_after_deadline_are_quarantined() -> None:
    result = admit_temporal_records(
        [
            {"id": "ok", "available_at": "2026-08-21T17:29:59Z"},
            {"id": "exact", "available_at": DEADLINE},
            {"id": "late", "available_at": "2026-08-21T17:30:01Z"},
            {"id": "missing"},
        ],
        deadline=DEADLINE,
    )
    assert result["admitted_count"] == 1
    assert result["quarantined_count"] == 3
    reasons = {row["reason"] for row in result["quarantined"]}
    assert "available_at_at_or_after_deadline" in reasons
    assert "missing_available_at" in reasons


def test_identical_capture_is_idempotent(tmp_path: Path) -> None:
    bootstrap, fixtures = _bodies()
    kwargs = dict(
        season="2026-27",
        checkpoint_id="launch",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at=OBSERVED,
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
        update_index=True,
    )
    first = capture_preseason_snapshot(**kwargs)
    second = capture_preseason_snapshot(**kwargs)
    assert second == first
    assert first["content_sha256"] == artifact_hash(first)
    assert first["ruleset_sha256"] == ruleset_sha256(RULES)
    assert first["status"] == "degraded"
    assert "licensed_odds" in first["source_gaps"]
    manifest_path = tmp_path / "preseason" / "launch" / "manifest.json"
    assert manifest_path.read_bytes() == (
        json.dumps(first, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def test_changed_payload_fails_closed(tmp_path: Path) -> None:
    bootstrap, fixtures = _bodies()
    capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id="launch",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at=OBSERVED,
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
    )
    changed = json.dumps(
        {**_bootstrap(), "elements": [{"id": 2, "web_name": "Beta"}]},
        sort_keys=True,
    ).encode("utf-8")
    with pytest.raises(PreseasonSnapshotConflict):
        capture_preseason_snapshot(
            season="2026-27",
            checkpoint_id="launch",
            deadline=DEADLINE,
            output_root=tmp_path / "preseason",
            observed_at=OBSERVED,
            bootstrap_body=changed,
            fixtures_body=fixtures,
            rules_path=RULES,
            config_path=CONFIG,
            index_manifest_path=tmp_path / "index.json",
            code_commit=COMMIT,
        )


def test_missing_mandatory_official_state_writes_no_manifest(tmp_path: Path) -> None:
    output_root = tmp_path / "preseason"
    with pytest.raises(PreseasonSnapshotError, match="Mandatory official state"):
        capture_preseason_snapshot(
            season="2026-27",
            checkpoint_id="T-24h",
            deadline=DEADLINE,
            output_root=output_root,
            observed_at="2026-08-20T17:30:00Z",
            bootstrap_body=None,
            fixtures_body=None,
            rules_path=RULES,
            config_path=CONFIG,
            index_manifest_path=tmp_path / "index.json",
            code_commit=COMMIT,
            update_index=False,
        )
    assert not (output_root / "T-24h" / "manifest.json").exists()


def test_optional_family_degrades_explicitly_and_cli_succeeds(tmp_path: Path) -> None:
    bootstrap, fixtures = _bodies()
    bootstrap_path = tmp_path / "bootstrap.json"
    fixtures_path = tmp_path / "fixtures.json"
    bootstrap_path.write_bytes(bootstrap)
    fixtures_path.write_bytes(fixtures)
    odds = {
        "available_at": "2026-08-21T17:30:00Z",
        "slot": "T-24h",
        "quotes": [],
    }
    odds_path = tmp_path / "odds.json"
    odds_path.write_text(json.dumps(odds), encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)

    result = subprocess.run(
        [
            "python",
            str(REPO / "scripts/capture_preseason_snapshot.py"),
            "--season",
            "2026-27",
            "--checkpoint-id",
            "weekly-2026-08-03",
            "--deadline",
            DEADLINE,
            "--output-root",
            str(tmp_path / "preseason"),
            "--observed-at",
            "2026-08-03T12:00:00Z",
            "--bootstrap-file",
            str(bootstrap_path),
            "--fixtures-file",
            str(fixtures_path),
            "--rules-path",
            str(RULES),
            "--config-path",
            str(CONFIG),
            "--index-manifest-path",
            str(tmp_path / "index.json"),
            "--code-commit",
            COMMIT,
            "--odds-artifact",
            str(odds_path),
            "--no-network",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "degraded"
    assert "licensed_odds" in payload["source_gaps"]
    manifest = json.loads(
        (tmp_path / "preseason" / "weekly-2026-08-03" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    family = manifest["families"]["licensed_odds"]
    assert family["status"] == "degraded"
    assert family["counts"]["quarantined"] == 1
    assert "available_at_at_or_after_deadline" in family["reasons"]


def test_cli_missing_mandatory_exits_nonzero(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    result = subprocess.run(
        [
            "python",
            str(REPO / "scripts/capture_preseason_snapshot.py"),
            "--season",
            "2026-27",
            "--checkpoint-id",
            "final",
            "--deadline",
            DEADLINE,
            "--output-root",
            str(tmp_path / "preseason"),
            "--observed-at",
            "2026-08-21T17:25:00Z",
            "--code-commit",
            COMMIT,
            "--no-network",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1
    assert "Mandatory official state" in result.stderr
    assert not (tmp_path / "preseason" / "final" / "manifest.json").exists()


# ---------------------------------------------------------------------------
# Finding 1 — deadline-relative checkpoint label enforcement
# ---------------------------------------------------------------------------

def test_deadline_relative_late_capture_rejected(tmp_path: Path) -> None:
    """A T-48h capture observed at T-2h time must be rejected (cannot backfill)."""
    bootstrap, fixtures = _bodies()
    with pytest.raises(PreseasonSnapshotError, match="cannot be backfilled"):
        capture_preseason_snapshot(
            season="2026-27",
            checkpoint_id="T-48h",
            deadline=DEADLINE,
            output_root=tmp_path / "preseason",
            observed_at="2026-08-21T15:30:00Z",  # T-2h nominal
            bootstrap_body=bootstrap,
            fixtures_body=fixtures,
            rules_path=RULES,
            config_path=CONFIG,
            index_manifest_path=tmp_path / "index.json",
            code_commit=COMMIT,
            update_index=False,
        )
    assert not (tmp_path / "preseason" / "T-48h" / "manifest.json").exists()


def test_deadline_relative_correct_window_accepted(tmp_path: Path) -> None:
    """A T-48h capture observed at the nominal T-48h time is admitted."""
    bootstrap, fixtures = _bodies()
    manifest = capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id="T-48h",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at="2026-08-19T17:30:00Z",  # T-48h nominal
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
    )
    assert manifest["checkpoint_id"] == "T-48h"
    assert (tmp_path / "preseason" / "T-48h" / "manifest.json").exists()


def test_weekly_mislabelled_date_rejected(tmp_path: Path) -> None:
    """weekly-YYYY-MM-DD must match the UTC observation date."""
    bootstrap, fixtures = _bodies()
    with pytest.raises(PreseasonSnapshotError, match="does not match observation date"):
        capture_preseason_snapshot(
            season="2026-27",
            checkpoint_id="weekly-2026-08-03",
            deadline=DEADLINE,
            output_root=tmp_path / "preseason",
            observed_at="2026-08-04T12:00:00Z",  # wrong date — next day
            bootstrap_body=bootstrap,
            fixtures_body=fixtures,
            rules_path=RULES,
            config_path=CONFIG,
            index_manifest_path=tmp_path / "index.json",
            code_commit=COMMIT,
            update_index=False,
        )
    assert not (tmp_path / "preseason" / "weekly-2026-08-03" / "manifest.json").exists()


def test_enforce_checkpoint_window_unit() -> None:
    """Unit test for enforce_checkpoint_window covering all deadline-relative slots."""
    schedule = expected_deadline_schedule(_bootstrap())
    deadline_utc = datetime.fromisoformat(DEADLINE.replace("Z", "+00:00"))

    def utc(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    for cid in ("T-48h", "T-24h", "T-8h", "T-2h", "final"):
        nominal = utc(schedule[cid])
        enforce_checkpoint_window(cid, nominal, schedule, deadline_utc)

    with pytest.raises(PreseasonSnapshotError, match="cannot be backfilled"):
        enforce_checkpoint_window(
            "T-48h", utc(schedule["T-24h"]), schedule, deadline_utc
        )

    with pytest.raises(PreseasonSnapshotError, match="does not match observation date"):
        enforce_checkpoint_window(
            "weekly-2026-08-03",
            utc("2026-08-04T12:00:00Z"),
            schedule,
            deadline_utc,
        )


# ---------------------------------------------------------------------------
# Finding 2 — single-writer lock / atomic writers
# ---------------------------------------------------------------------------

def test_different_request_same_path_fails_closed(tmp_path: Path) -> None:
    """A second capture at the same checkpoint with a different request raises conflict."""
    bootstrap, fixtures = _bodies()
    base_kwargs: dict = dict(
        season="2026-27",
        checkpoint_id="launch",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
        update_index=False,
    )
    capture_preseason_snapshot(**base_kwargs, observed_at=OBSERVED)
    with pytest.raises(PreseasonSnapshotConflict):
        capture_preseason_snapshot(**base_kwargs, observed_at="2026-07-28T10:00:00Z")


def test_sequential_different_checkpoints_update_index(tmp_path: Path) -> None:
    """Two sequential captures at different checkpoint IDs both appear in the index."""
    bootstrap, fixtures = _bodies()
    index_path = tmp_path / "index.json"
    for cid, obs in (
        ("T-48h", "2026-08-19T17:30:00Z"),
        ("T-24h", "2026-08-20T17:30:00Z"),
    ):
        capture_preseason_snapshot(
            season="2026-27",
            checkpoint_id=cid,
            deadline=DEADLINE,
            output_root=tmp_path / "preseason",
            observed_at=obs,
            bootstrap_body=bootstrap,
            fixtures_body=fixtures,
            rules_path=RULES,
            config_path=CONFIG,
            index_manifest_path=index_path,
            code_commit=COMMIT,
        )
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert "T-48h" in index["checkpoints"]
    assert "T-24h" in index["checkpoints"]
    assert index["checkpoints"]["T-48h"]["manifest_sha256"]
    assert index["checkpoints"]["T-24h"]["manifest_sha256"]


# ---------------------------------------------------------------------------
# Finding 3 — optional inputs are immutable and in rerun conflict detection
# ---------------------------------------------------------------------------

def test_optional_artifact_content_change_raises_conflict(tmp_path: Path) -> None:
    """Changing an optional artifact's content at the same checkpoint raises conflict."""
    bootstrap, fixtures = _bodies()
    odds_v1 = {"available_at": "2026-08-19T12:00:00Z", "quotes": [{"player_id": 1}]}
    odds_v2 = {"available_at": "2026-08-19T12:00:00Z", "quotes": [{"player_id": 2}]}
    p1 = tmp_path / "odds_v1.json"
    p2 = tmp_path / "odds_v2.json"
    p1.write_text(json.dumps(odds_v1), encoding="utf-8")
    p2.write_text(json.dumps(odds_v2), encoding="utf-8")

    base: dict = dict(
        season="2026-27",
        checkpoint_id="T-48h",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at="2026-08-19T17:30:00Z",
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
    )
    capture_preseason_snapshot(**base, optional_artifacts={"licensed_odds": p1})
    with pytest.raises(PreseasonSnapshotConflict):
        capture_preseason_snapshot(**base, optional_artifacts={"licensed_odds": p2})


def test_optional_artifact_copied_content_addressably(tmp_path: Path) -> None:
    """An admitted optional artifact is copied into the checkpoint directory."""
    bootstrap, fixtures = _bodies()
    odds = {"available_at": "2026-08-19T12:00:00Z", "quotes": []}
    odds_path = tmp_path / "odds.json"
    odds_path.write_text(json.dumps(odds), encoding="utf-8")

    manifest = capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id="T-48h",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at="2026-08-19T17:30:00Z",
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
        optional_artifacts={"licensed_odds": odds_path},
    )
    family = manifest["families"]["licensed_odds"]
    assert family["status"] == "admitted"
    checkpoint_dir = tmp_path / "preseason" / "T-48h"
    copied = checkpoint_dir / family["artifact_path"]
    assert copied.exists(), f"Content-addressed copy not found: {copied}"
    assert family["artifact_sha256"]


def test_optional_artifact_absent_vs_provided_uses_different_request(tmp_path: Path) -> None:
    """Providing an optional artifact changes the request hash vs not providing it."""
    bootstrap, fixtures = _bodies()
    odds = {"available_at": "2026-08-19T12:00:00Z", "quotes": []}
    odds_path = tmp_path / "odds.json"
    odds_path.write_text(json.dumps(odds), encoding="utf-8")

    base: dict = dict(
        season="2026-27",
        checkpoint_id="T-48h",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at="2026-08-19T17:30:00Z",
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
    )
    m_without = capture_preseason_snapshot(**base)
    with pytest.raises(PreseasonSnapshotConflict):
        capture_preseason_snapshot(**base, optional_artifacts={"licensed_odds": odds_path})


# ---------------------------------------------------------------------------
# Finding 4 — optional-source provenance and temporal admission
# ---------------------------------------------------------------------------

def test_non_json_optional_without_sidecar_is_quarantined(tmp_path: Path) -> None:
    """A non-JSON optional artifact without a temporal sidecar degrades."""
    registry = load_registry()
    csv_path = tmp_path / "priors.csv"
    csv_path.write_text("player_id,prior\n1,0.5\n", encoding="utf-8")
    result = _bind_optional_artifact(
        family_id="promoted_team_priors",
        path=csv_path,
        deadline=DEADLINE,
        source_id="the-odds-api",
        missing_reason="optional_promoted_team_priors_not_supplied",
        checkpoint_dir=tmp_path / "ckpt",
        sidecar_path=None,
        registry=registry,
    )
    assert result["status"] == "degraded"
    assert "missing_temporal_sidecar_for_binary" in result["reasons"]
    assert result["counts"]["quarantined"] == 1


def test_non_json_optional_with_valid_sidecar_is_admitted(tmp_path: Path) -> None:
    """A non-JSON optional artifact with a valid temporal sidecar is admitted."""
    registry = load_registry()
    csv_path = tmp_path / "priors.csv"
    csv_path.write_text("player_id,prior\n1,0.5\n", encoding="utf-8")
    sidecar = {"available_at": "2026-07-01T00:00:00Z", "source": "manual"}
    sidecar_path = tmp_path / "priors_sidecar.json"
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
    result = _bind_optional_artifact(
        family_id="promoted_team_priors",
        path=csv_path,
        deadline=DEADLINE,
        source_id="the-odds-api",
        missing_reason="optional_promoted_team_priors_not_supplied",
        checkpoint_dir=tmp_path / "ckpt",
        sidecar_path=sidecar_path,
        registry=registry,
    )
    assert result["status"] == "admitted"
    assert result["counts"]["admitted"] == 1
    ckpt_copy = tmp_path / "ckpt" / result["artifact_path"]
    assert ckpt_copy.exists()


def test_non_object_records_explicitly_quarantined(tmp_path: Path) -> None:
    """Non-Mapping rows inside a records list are quarantined, not silently dropped."""
    registry = load_registry()
    payload = {
        "records": [
            {"available_at": "2026-07-01T00:00:00Z", "player_id": 1},
            "this_is_not_an_object",
            {"available_at": "2026-07-01T00:00:00Z", "player_id": 2},
        ]
    }
    art_path = tmp_path / "data.json"
    art_path.write_text(json.dumps(payload), encoding="utf-8")
    result = _bind_optional_artifact(
        family_id="player_ratings",
        path=art_path,
        deadline=DEADLINE,
        source_id="statsbomb-open",
        missing_reason="optional_player_ratings_not_supplied",
        checkpoint_dir=tmp_path / "ckpt",
        sidecar_path=None,
        registry=registry,
    )
    assert result["counts"]["input"] == 3
    assert result["counts"]["quarantined"] == 1
    assert result["counts"]["admitted"] == 2


def test_unregistered_source_id_degrades_optional_family(tmp_path: Path) -> None:
    """An optional artifact with an unregistered source ID degrades."""
    registry = load_registry()
    art_path = tmp_path / "data.json"
    art_path.write_text(
        json.dumps({"available_at": "2026-07-01T00:00:00Z", "data": []}),
        encoding="utf-8",
    )
    result = _bind_optional_artifact(
        family_id="player_ratings",
        path=art_path,
        deadline=DEADLINE,
        source_id="totally-nonexistent-source-xyz",
        missing_reason="not_supplied",
        checkpoint_dir=tmp_path / "ckpt",
        sidecar_path=None,
        registry=registry,
    )
    assert result["status"] == "degraded"
    assert any("source_not_collectable" in r for r in result["reasons"])
    assert result["registry_source_status"] == "unregistered"


def test_source_id_from_config_not_hardcoded(tmp_path: Path) -> None:
    """Optional source IDs come from config and carry registry_source_status."""
    bootstrap, fixtures = _bodies()
    odds = {"available_at": "2026-08-19T12:00:00Z", "quotes": []}
    odds_path = tmp_path / "odds.json"
    odds_path.write_text(json.dumps(odds), encoding="utf-8")

    manifest = capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id="T-48h",
        deadline=DEADLINE,
        output_root=tmp_path / "preseason",
        observed_at="2026-08-19T17:30:00Z",
        bootstrap_body=bootstrap,
        fixtures_body=fixtures,
        rules_path=RULES,
        config_path=CONFIG,
        index_manifest_path=tmp_path / "index.json",
        code_commit=COMMIT,
        optional_artifacts={"licensed_odds": odds_path},
    )
    odds_family = manifest["families"]["licensed_odds"]
    assert odds_family["source_id"] == "the-odds-api"
    assert "registry_source_status" in odds_family
