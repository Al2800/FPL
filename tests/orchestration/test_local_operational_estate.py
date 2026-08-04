"""Offline contracts for the local operational-estate audit and consolidation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.orchestration.local_operational_estate import (
    LocalOperationalEstateConflict,
    LocalOperationalEstateError,
    acknowledge_unavailable_artifacts,
    archive_operational_estate,
    audit_local_operational_estate,
    consolidate_retained_artifacts,
    copy_create_only,
    file_sha256,
    redact_secrets,
)


def _write(path: Path, body: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def _config(tmp_path: Path, **overrides: object) -> dict:
    active = tmp_path / "active"
    legacy = tmp_path / "legacy"
    active.mkdir()
    legacy.mkdir()
    config = {
        "schema_version": "1.0",
        "active_root": str(active),
        "legacy_roots": [str(legacy)],
        "preseason_manifest_path": "control/manifests/2026-27-preseason.json",
        "machine_manifest_path": "data/operational-state/machine-manifest.json",
        "acknowledgements_path": "data/operational-state/acknowledged-unavailable-artifacts.json",
        "retained_families": [
            {
                "id": "preseason-weekly-2026-07-30",
                "kind": "immutable_checkpoint",
                "relative_path": "data/snapshots/2026-27/preseason/weekly-2026-07-30",
            },
            {
                "id": "initial-squad-weekly-2026-07-30",
                "kind": "immutable_report",
                "relative_path": "reports/live/2026-27/initial-squad/weekly-2026-07-30",
            },
        ],
        "scheduled_tasks": [
            {
                "name": "FPL Deadline-Aware Capture",
                "expected_action_contains": [str(active), "run_deadline_capture_task.ps1"],
            }
        ],
        "secret_presence_checks": [
            {
                "id": "the_odds_api_key",
                "environment_variable": "THE_ODDS_API_KEY",
                "scope": "user",
            }
        ],
        "knowledge_runtime_config": "config/data_sources/2026-27-fpl-retrieval.json",
    }
    config.update(overrides)
    return config


def test_copy_create_only_copies_identical_and_refuses_conflict(tmp_path: Path) -> None:
    source = tmp_path / "source" / "file.bin"
    destination = tmp_path / "dest" / "file.bin"
    digest = _write(source, b"checkpoint-bytes")

    first = copy_create_only(source, destination)
    assert first["status"] == "copied"
    assert first["sha256"] == digest
    assert destination.read_bytes() == b"checkpoint-bytes"

    second = copy_create_only(source, destination)
    assert second["status"] == "identical_existing"
    assert second["sha256"] == digest

    _write(source, b"changed-bytes")
    with pytest.raises(LocalOperationalEstateConflict):
        copy_create_only(source, destination)
    assert destination.read_bytes() == b"checkpoint-bytes"


def test_consolidate_copies_missing_retained_artifacts_and_verifies_hashes(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    legacy = Path(config["legacy_roots"][0])
    active = Path(config["active_root"])
    relative = "data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json"
    digest = _write(legacy / relative, b'{"checkpoint_id":"weekly-2026-07-30"}\n')

    report = consolidate_retained_artifacts(config)
    copied = next(item for item in report["copies"] if item["relative_path"] == relative)
    assert copied["status"] == "copied"
    assert copied["sha256"] == digest
    assert file_sha256(active / relative) == digest
    assert (active / relative).read_bytes() == (legacy / relative).read_bytes()


def test_missing_reference_is_unavailable_until_acknowledged(tmp_path: Path) -> None:
    config = _config(tmp_path)
    active = Path(config["active_root"])
    manifest = {
        "checkpoints": {
            "weekly-2026-07-30": {
                "checkpoint_id": "weekly-2026-07-30",
                "manifest_path": "data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json",
                "manifest_sha256": "a" * 64,
            },
            "weekly-2026-07-31": {
                "checkpoint_id": "weekly-2026-07-31",
                "manifest_path": "data/snapshots/2026-27/preseason/weekly-2026-07-31/manifest.json",
                "manifest_sha256": "b" * 64,
            },
        }
    }
    manifest_path = active / "control" / "manifests" / "2026-27-preseason.json"
    _write(manifest_path, json.dumps(manifest).encode("utf-8"))

    audit = audit_local_operational_estate(
        config,
        task_query=lambda _name: {"present": False},
        environment={"THE_ODDS_API_KEY": "should-never-appear"},
        write_manifest=False,
    )
    refs = {item["checkpoint_id"]: item for item in audit["preseason_references"]}
    assert refs["weekly-2026-07-30"]["status"] == "unavailable_local_artifact"
    assert refs["weekly-2026-07-31"]["status"] == "unavailable_local_artifact"
    assert audit["exit_code"] != 0
    assert "should-never-appear" not in json.dumps(audit)

    acknowledge_unavailable_artifacts(
        config,
        [
            {
                "checkpoint_id": "weekly-2026-07-30",
                "manifest_path": refs["weekly-2026-07-30"]["manifest_path"],
                "manifest_sha256": "a" * 64,
                "reason": "fixture gap",
            },
            {
                "checkpoint_id": "weekly-2026-07-31",
                "manifest_path": refs["weekly-2026-07-31"]["manifest_path"],
                "manifest_sha256": "b" * 64,
                "reason": "fixture gap",
            },
        ],
    )
    def healthy_task(_name: str) -> dict:
        active = Path(config["active_root"])
        return {
            "present": True,
            "task_name": "FPL Deadline-Aware Capture",
            "status": "Ready",
            "last_result": 0,
            "task_to_run": f"powershell.exe -File {active}\\scripts\\run_deadline_capture_task.ps1",
        }

    acknowledged = audit_local_operational_estate(
        config,
        task_query=healthy_task,
        environment={},
        write_manifest=False,
    )
    assert all(
        item["status"] == "unavailable_local_artifact"
        and item["acknowledged"] is True
        for item in acknowledged["preseason_references"]
    )
    assert acknowledged["exit_code"] == 0


def test_scheduler_action_drift_is_visible_without_credentials(tmp_path: Path) -> None:
    config = _config(tmp_path)
    active = Path(config["active_root"])
    (active / "control" / "manifests").mkdir(parents=True)
    (active / "control" / "manifests" / "2026-27-preseason.json").write_text(
        json.dumps({"checkpoints": {}}),
        encoding="utf-8",
    )

    def query(name: str) -> dict:
        return {
            "present": True,
            "task_name": name,
            "status": "Ready",
            "last_result": 1,
            "task_to_run": (
                r"powershell.exe -File C:\Users\Alastair\FPL-pr-review\scripts\run_deadline_capture_task.ps1"
            ),
        }

    audit = audit_local_operational_estate(
        config,
        task_query=query,
        environment={},
        write_manifest=False,
    )
    task = audit["scheduled_tasks"][0]
    assert task["present"] is True
    assert task["targets_active_root"] is False
    assert task["action_drift"] is True
    assert task["last_result"] == 1
    assert audit["exit_code"] != 0


def test_secret_redaction_keeps_presence_only() -> None:
    payload = {
        "note": "key=super-secret-value",
        "nested": {"THE_ODDS_API_KEY": "abc123", "ok": True},
    }
    redacted = redact_secrets(
        payload,
        secret_values={"super-secret-value", "abc123"},
        environment_variable_names={"THE_ODDS_API_KEY"},
    )
    text = json.dumps(redacted)
    assert "super-secret-value" not in text
    assert "abc123" not in text
    assert redacted["nested"]["THE_ODDS_API_KEY"] == "[redacted-presence-only]"
    assert "[redacted]" in redacted["note"]


def test_backup_restore_hash_verification_refuses_differing_bytes(tmp_path: Path) -> None:
    config = _config(tmp_path)
    active = Path(config["active_root"])
    relative = "data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json"
    digest = _write(active / relative, b"archive-bytes\n")
    backup_root = tmp_path / "backup"

    archive = archive_operational_estate(config, backup_root=backup_root)
    assert archive["file_count"] == 1
    assert archive["files"][0]["sha256"] == digest
    assert file_sha256(backup_root / relative) == digest

    # Identical re-archive is accepted.
    again = archive_operational_estate(config, backup_root=backup_root)
    assert again["files"][0]["status"] == "identical_existing"

    # Differing destination fails closed and leaves original backup bytes.
    (active / relative).write_bytes(b"changed\n")
    with pytest.raises(LocalOperationalEstateConflict):
        archive_operational_estate(config, backup_root=backup_root)
    assert (backup_root / relative).read_bytes() == b"archive-bytes\n"


def test_resolvable_manifest_reference_matches_sealed_content_hash(tmp_path: Path) -> None:
    config = _config(tmp_path)
    active = Path(config["active_root"])
    body = {"checkpoint_id": "weekly-2026-07-30", "season": "2026-27"}
    sealed = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    path = active / "data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json"
    _write(
        path,
        (json.dumps({**body, "content_sha256": sealed}, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )
    index = {
        "checkpoints": {
            "weekly-2026-07-30": {
                "checkpoint_id": "weekly-2026-07-30",
                "manifest_path": "data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json",
                "manifest_sha256": sealed,
            }
        }
    }
    manifest_path = active / "control/manifests/2026-27-preseason.json"
    _write(manifest_path, json.dumps(index).encode("utf-8"))

    audit = audit_local_operational_estate(
        config,
        task_query=lambda _name: {
            "present": True,
            "task_name": "FPL Deadline-Aware Capture",
            "status": "Ready",
            "last_result": 0,
            "task_to_run": f"powershell.exe -File {active}\\scripts\\run_deadline_capture_task.ps1",
        },
        environment={},
        write_manifest=False,
    )
    assert audit["preseason_references"][0]["status"] == "resolved"
    assert audit["preseason_references"][0]["sha256"] == sealed
    assert audit["exit_code"] == 0
