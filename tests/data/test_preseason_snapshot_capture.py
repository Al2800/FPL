"""Immutable 2026/27 preseason snapshot capture contracts."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from src.orchestration.preseason_snapshot import (
    PreseasonSnapshotConflict,
    PreseasonSnapshotError,
    admit_temporal_records,
    artifact_hash,
    capture_preseason_snapshot,
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
