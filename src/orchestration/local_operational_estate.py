"""Create-only audit and consolidation for the local operational estate.

Distinguishes versioned Git definitions, gitignored operational evidence, and
machine registration/secrets that may only be checked for presence. Never
deletes, moves, rewrites differing bytes, regenerates missing historical
observations, or emits secret values.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "operations" / "local-operational-estate.json"

TaskQuery = Callable[[str], Mapping[str, Any]]


class LocalOperationalEstateError(ValueError):
    """Raised when the operational estate cannot be audited or consolidated safely."""


class LocalOperationalEstateConflict(LocalOperationalEstateError):
    """Raised when a create-only destination already holds different bytes."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_estate_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalOperationalEstateError(f"Cannot read estate config {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LocalOperationalEstateError(f"Estate config must be a JSON object: {config_path}")
    required = (
        "active_root",
        "legacy_roots",
        "preseason_manifest_path",
        "machine_manifest_path",
        "acknowledgements_path",
        "retained_families",
        "scheduled_tasks",
    )
    missing = [name for name in required if name not in payload]
    if missing:
        raise LocalOperationalEstateError(f"Estate config is missing {missing}")
    return payload


def _active_root(config: Mapping[str, Any]) -> Path:
    return Path(str(config["active_root"]))


def _legacy_roots(config: Mapping[str, Any]) -> list[Path]:
    return [Path(str(item)) for item in config["legacy_roots"]]


def _resolve_under(root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise LocalOperationalEstateError(f"Refusing unsafe relative path: {relative}")
    return root / relative_path


def copy_create_only(source: Path, destination: Path) -> dict[str, Any]:
    """Copy one file create-only. Identical destination bytes are accepted."""

    if not source.is_file():
        raise LocalOperationalEstateError(f"Source file is missing: {source}")
    source_hash = file_sha256(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file():
            raise LocalOperationalEstateConflict(
                f"Destination exists and is not a file: {destination}"
            )
        destination_hash = file_sha256(destination)
        if destination_hash != source_hash or destination.read_bytes() != source.read_bytes():
            raise LocalOperationalEstateConflict(
                f"Refusing to overwrite differing destination bytes: {destination}"
            )
        return {
            "status": "identical_existing",
            "source": str(source),
            "destination": str(destination),
            "sha256": source_hash,
            "bytes": destination.stat().st_size,
        }

    body = source.read_bytes()
    if hashlib.sha256(body).hexdigest() != source_hash:
        raise LocalOperationalEstateError(f"Source changed while reading: {source}")
    with destination.open("xb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    written_hash = file_sha256(destination)
    if written_hash != source_hash:
        raise LocalOperationalEstateError(
            f"Copied bytes do not match source hash for {destination}"
        )
    return {
        "status": "copied",
        "source": str(source),
        "destination": str(destination),
        "sha256": written_hash,
        "bytes": destination.stat().st_size,
    }


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*") if path.is_file())


def inventory_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "present": False,
            "file_count": 0,
            "bytes": 0,
            "latest_mtime_utc": None,
            "files": [],
        }
    files: list[dict[str, Any]] = []
    latest: float | None = None
    total = 0
    for file_path in _iter_files(path):
        stat = file_path.stat()
        total += stat.st_size
        latest = stat.st_mtime if latest is None else max(latest, stat.st_mtime)
        files.append(
            {
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(path)) if path.is_dir() else file_path.name,
                "bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "sha256": file_sha256(file_path),
            }
        )
    return {
        "path": str(path),
        "present": True,
        "file_count": len(files),
        "bytes": total,
        "latest_mtime_utc": (
            None
            if latest is None
            else datetime.fromtimestamp(latest, timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "files": files,
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalOperationalEstateError(f"Cannot read JSON {path}: {exc}") from exc


def _acknowledgements(config: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    path = _resolve_under(_active_root(config), str(config["acknowledgements_path"]))
    if not path.exists():
        return {}
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise LocalOperationalEstateError(f"Acknowledgements must be a JSON object: {path}")
    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise LocalOperationalEstateError(f"Acknowledgements artifacts must be a list: {path}")
    indexed: dict[str, dict[str, Any]] = {}
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        key = str(item.get("manifest_path") or item.get("checkpoint_id") or "")
        if key:
            indexed[key] = item
    return indexed


def acknowledge_unavailable_artifacts(
    config: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Record explicit historical gaps without inventing missing bytes."""

    active = _active_root(config)
    path = _resolve_under(active, str(config["acknowledgements_path"]))
    existing = _load_json(path) if path.exists() else {"schema_version": "1.0", "artifacts": []}
    if not isinstance(existing, dict):
        raise LocalOperationalEstateError(f"Acknowledgements must be a JSON object: {path}")
    current = list(existing.get("artifacts") or [])
    by_path = {
        str(item.get("manifest_path") or item.get("checkpoint_id")): dict(item)
        for item in current
        if isinstance(item, dict)
    }
    for artifact in artifacts:
        record = {
            "checkpoint_id": artifact.get("checkpoint_id"),
            "manifest_path": artifact.get("manifest_path"),
            "manifest_sha256": artifact.get("manifest_sha256"),
            "status": "unavailable_local_artifact",
            "reason": artifact.get("reason") or "operator_acknowledged_unavailable",
            "acknowledged_at": utc_now(),
        }
        key = str(record["manifest_path"] or record["checkpoint_id"])
        by_path[key] = record
    payload = {
        "schema_version": "1.0",
        "updated_at": utc_now(),
        "artifacts": sorted(by_path.values(), key=lambda item: str(item.get("manifest_path") or "")),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        # Acknowledgements are mutable operational state, but still refuse silent
        # truncation via a temporary replace rather than in-place rewrite of evidence.
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(body)
        temporary.replace(path)
    else:
        with path.open("xb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
    return payload


def redact_secrets(
    value: Any,
    *,
    secret_values: set[str] | None = None,
    environment_variable_names: set[str] | None = None,
) -> Any:
    """Remove secret values from nested structures; keep presence markers only."""

    secrets = {item for item in (secret_values or set()) if item}
    names = {item for item in (environment_variable_names or set()) if item}
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in names:
                result[str(key)] = "[redacted-presence-only]"
            else:
                result[str(key)] = redact_secrets(
                    item,
                    secret_values=secrets,
                    environment_variable_names=names,
                )
        return result
    if isinstance(value, list):
        return [
            redact_secrets(item, secret_values=secrets, environment_variable_names=names)
            for item in value
        ]
    if isinstance(value, str):
        redacted = value
        for secret in sorted(secrets, key=len, reverse=True):
            if secret and secret in redacted:
                redacted = redacted.replace(secret, "[redacted]")
        return redacted
    return value


def _secret_values_from_environment(
    config: Mapping[str, Any],
    environment: Mapping[str, str],
) -> set[str]:
    values: set[str] = set()
    for check in config.get("secret_presence_checks", []):
        name = str(check.get("environment_variable") or "")
        if name and environment.get(name):
            values.add(environment[name])
    return values


def _environment_variable_present(name: str, *, scope: str | None, environment: Mapping[str, str]) -> bool:
    if name and str(environment.get(name) or "").strip():
        return True
    if scope == "user" and os.name == "nt" and name:
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
            return bool(str(value or "").strip())
        except OSError:
            return False
    return False


def audit_secret_presence(
    config: Mapping[str, Any],
    *,
    environment: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    env = environment if environment is not None else os.environ
    results: list[dict[str, Any]] = []
    for check in config.get("secret_presence_checks", []):
        name = str(check.get("environment_variable") or "")
        scope = check.get("scope")
        present = _environment_variable_present(name, scope=str(scope) if scope else None, environment=env)
        results.append(
            {
                "id": check.get("id") or name,
                "environment_variable": name,
                "scope": scope,
                "present": present,
                "value": None,
            }
        )
    return results


def query_windows_scheduled_task(task_name: str) -> dict[str, Any]:
    """Query one Windows scheduled task without returning credentials."""

    completed = subprocess.run(
        ["schtasks", "/Query", "/TN", task_name, "/FO", "LIST", "/V"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "present": False,
            "task_name": task_name,
            "query_exit_code": completed.returncode,
        }
    fields: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        fields[key.strip()] = raw.strip()
    return {
        "present": True,
        "task_name": fields.get("TaskName", task_name),
        "status": fields.get("Status"),
        "last_run_time": fields.get("Last Run Time"),
        "next_run_time": fields.get("Next Run Time"),
        "last_result": _parse_last_result(fields.get("Last Result")),
        "task_to_run": fields.get("Task To Run"),
        "run_as_user": fields.get("Run As User"),
        "query_exit_code": 0,
    }


def _parse_last_result(value: str | None) -> int | str | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return value


def audit_scheduled_tasks(
    config: Mapping[str, Any],
    *,
    task_query: TaskQuery | None = None,
) -> list[dict[str, Any]]:
    active = str(_active_root(config))
    query = task_query or query_windows_scheduled_task
    results: list[dict[str, Any]] = []
    for expected in config.get("scheduled_tasks", []):
        name = str(expected["name"])
        observed = dict(query(name))
        action = str(observed.get("task_to_run") or "")
        expected_fragments = [str(item) for item in expected.get("expected_action_contains", [])]
        missing_fragments = [item for item in expected_fragments if item.lower() not in action.lower()]
        targets_active = active.lower() in action.lower() if action else False
        present = bool(observed.get("present"))
        last_result = observed.get("last_result")
        results.append(
            {
                "name": name,
                "present": present,
                "status": observed.get("status"),
                "last_run_time": observed.get("last_run_time"),
                "next_run_time": observed.get("next_run_time"),
                "last_result": last_result,
                "task_to_run": action or None,
                "targets_active_root": targets_active,
                "action_drift": (not present) or bool(missing_fragments) or (not targets_active),
                "missing_action_fragments": missing_fragments,
                "non_zero_last_result": present and last_result not in (0, "0", None),
            }
        )
    return results


def sealed_json_sha256(path: Path) -> tuple[str, str]:
    """Return (file_sha256, sealed content_sha256) for an immutable JSON artifact."""

    raw_hash = file_sha256(path)
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise LocalOperationalEstateError(f"Expected JSON object at {path}")
    declared = payload.get("content_sha256")
    body = {key: deepcopy(value) for key, value in payload.items() if key != "content_sha256"}
    recomputed = hashlib.sha256(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if isinstance(declared, str) and declared and declared != recomputed:
        raise LocalOperationalEstateError(
            f"Sealed JSON content_sha256 does not match recomputed digest: {path}"
        )
    return raw_hash, str(declared or recomputed)


def _classify_preseason_reference(
    *,
    checkpoint_id: str,
    manifest_path: str,
    expected_sha256: str | None,
    active: Path,
    acknowledgements: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    local_path = _resolve_under(active, manifest_path)
    acknowledged = bool(
        acknowledgements.get(manifest_path) or acknowledgements.get(checkpoint_id)
    )
    if not local_path.is_file():
        return {
            "checkpoint_id": checkpoint_id,
            "manifest_path": manifest_path,
            "expected_sha256": expected_sha256,
            "status": "unavailable_local_artifact",
            "acknowledged": acknowledged,
            "sha256": None,
            "file_sha256": None,
            "path": str(local_path),
        }
    file_digest, sealed_digest = sealed_json_sha256(local_path)
    if expected_sha256 and sealed_digest != expected_sha256:
        return {
            "checkpoint_id": checkpoint_id,
            "manifest_path": manifest_path,
            "expected_sha256": expected_sha256,
            "status": "hash_mismatch",
            "acknowledged": False,
            "sha256": sealed_digest,
            "file_sha256": file_digest,
            "path": str(local_path),
        }
    return {
        "checkpoint_id": checkpoint_id,
        "manifest_path": manifest_path,
        "expected_sha256": expected_sha256,
        "status": "resolved",
        "acknowledged": False,
        "sha256": sealed_digest,
        "file_sha256": file_digest,
        "path": str(local_path),
    }


def audit_preseason_references(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    active = _active_root(config)
    manifest_path = _resolve_under(active, str(config["preseason_manifest_path"]))
    if not manifest_path.is_file():
        raise LocalOperationalEstateError(f"Committed preseason manifest is missing: {manifest_path}")
    payload = _load_json(manifest_path)
    checkpoints = payload.get("checkpoints") if isinstance(payload, dict) else None
    if not isinstance(checkpoints, dict):
        raise LocalOperationalEstateError("Preseason manifest is missing checkpoints")
    acknowledgements = _acknowledgements(config)
    results: list[dict[str, Any]] = []
    for checkpoint_id, entry in sorted(checkpoints.items()):
        if not isinstance(entry, dict):
            continue
        results.append(
            _classify_preseason_reference(
                checkpoint_id=str(entry.get("checkpoint_id") or checkpoint_id),
                manifest_path=str(entry["manifest_path"]),
                expected_sha256=entry.get("manifest_sha256"),
                active=active,
                acknowledgements=acknowledgements,
            )
        )
    return results


def inventory_retained_families(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    active = _active_root(config)
    legacy_roots = _legacy_roots(config)
    families: list[dict[str, Any]] = []
    for family in config.get("retained_families", []):
        relative = str(family["relative_path"])
        active_inventory = inventory_path(_resolve_under(active, relative))
        legacy_inventories = [
            {
                "root": str(root),
                **inventory_path(_resolve_under(root, relative)),
            }
            for root in legacy_roots
        ]
        families.append(
            {
                "id": family.get("id"),
                "kind": family.get("kind"),
                "relative_path": relative,
                "active": active_inventory,
                "legacy": legacy_inventories,
            }
        )
    return families


def inventory_knowledge_runtime(config: Mapping[str, Any]) -> dict[str, Any]:
    active = _active_root(config)
    relative = config.get("knowledge_runtime_config")
    if not relative:
        return {"configured": False}
    path = _resolve_under(active, str(relative))
    if not path.is_file():
        return {"configured": True, "present": False, "path": str(path)}
    payload = _load_json(path)
    runtime = payload.get("knowledge_runtime") if isinstance(payload, dict) else None
    if not isinstance(runtime, dict):
        return {"configured": True, "present": True, "path": str(path), "paths": []}
    paths = []
    for key in ("overlay_path", "tools_kb_path"):
        candidate = runtime.get(key)
        if not candidate:
            continue
        candidate_path = Path(str(candidate))
        paths.append(
            {
                "key": key,
                "path": str(candidate_path),
                "present": candidate_path.exists(),
            }
        )
    return {
        "configured": True,
        "present": True,
        "path": str(path),
        "profile_id": runtime.get("profile_id"),
        "mode": runtime.get("mode"),
        "paths": paths,
    }


def consolidate_retained_artifacts(config: Mapping[str, Any]) -> dict[str, Any]:
    """Copy missing retained artifacts from legacy roots into the active root."""

    active = _active_root(config)
    legacy_roots = _legacy_roots(config)
    copies: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for family in config.get("retained_families", []):
        relative_root = str(family["relative_path"])
        source_root: Path | None = None
        for root in legacy_roots:
            candidate = _resolve_under(root, relative_root)
            if candidate.exists():
                source_root = candidate
                break
        if source_root is None:
            missing.append(
                {
                    "id": family.get("id"),
                    "relative_path": relative_root,
                    "status": "unavailable_local_artifact",
                }
            )
            continue
        for source_file in _iter_files(source_root):
            rel_from_family = source_file.relative_to(source_root)
            destination = _resolve_under(active, relative_root) / rel_from_family
            result = copy_create_only(source_file, destination)
            result["relative_path"] = str(Path(relative_root) / rel_from_family).replace("\\", "/")
            result["family_id"] = family.get("id")
            copies.append(result)
    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "active_root": str(active),
        "copies": copies,
        "missing_families": missing,
        "copied_count": sum(1 for item in copies if item["status"] == "copied"),
        "identical_count": sum(1 for item in copies if item["status"] == "identical_existing"),
    }


def archive_operational_estate(
    config: Mapping[str, Any],
    *,
    backup_root: Path,
) -> dict[str, Any]:
    """Create-only archive of retained active artifacts plus a hash manifest."""

    if backup_root.exists() and not backup_root.is_dir():
        raise LocalOperationalEstateError(f"Backup root must be a directory: {backup_root}")
    active = _active_root(config)
    files: list[dict[str, Any]] = []
    for family in config.get("retained_families", []):
        relative_root = str(family["relative_path"])
        source_root = _resolve_under(active, relative_root)
        for source_file in _iter_files(source_root):
            rel = source_file.relative_to(active)
            destination = backup_root / rel
            result = copy_create_only(source_file, destination)
            result["relative_path"] = str(rel).replace("\\", "/")
            files.append(result)

    manifest = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "active_root": str(active),
        "backup_root": str(backup_root),
        "file_count": len(files),
        "files": files,
    }
    manifest_path = backup_root / "operational-estate-archive-manifest.json"
    body = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if manifest_path.exists():
        if manifest_path.read_bytes() != body:
            # Manifest content changes with generated_at; compare file hashes only.
            existing = _load_json(manifest_path)
            existing_files = {
                item["relative_path"]: item["sha256"]
                for item in existing.get("files", [])
                if isinstance(item, dict)
            }
            current_files = {item["relative_path"]: item["sha256"] for item in files}
            if existing_files != current_files:
                raise LocalOperationalEstateConflict(
                    f"Archive manifest already records different file hashes: {manifest_path}"
                )
            return {
                **manifest,
                "manifest_path": str(manifest_path),
                "manifest_status": "identical_file_set",
            }
        return {**manifest, "manifest_path": str(manifest_path), "manifest_status": "identical_existing"}
    backup_root.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("xb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    return {**manifest, "manifest_path": str(manifest_path), "manifest_status": "copied"}


def _exit_code(
    *,
    references: Sequence[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
) -> int:
    for reference in references:
        status = reference.get("status")
        if status == "resolved":
            continue
        if status == "unavailable_local_artifact" and reference.get("acknowledged"):
            continue
        return 2
    for task in tasks:
        if (not task.get("present")) or task.get("action_drift"):
            return 3
    return 0


def audit_local_operational_estate(
    config: Mapping[str, Any],
    *,
    task_query: TaskQuery | None = None,
    environment: Mapping[str, str] | None = None,
    write_manifest: bool = True,
) -> dict[str, Any]:
    """Build the machine manifest for the active/legacy operational estate."""

    active = _active_root(config)
    env = dict(environment) if environment is not None else dict(os.environ)
    references = audit_preseason_references(config)
    tasks = audit_scheduled_tasks(config, task_query=task_query)
    secrets = audit_secret_presence(config, environment=env)
    families = inventory_retained_families(config)
    knowledge = inventory_knowledge_runtime(config)
    roots = {
        "active": {
            "path": str(active),
            "present": active.exists(),
        },
        "legacy": [
            {"path": str(root), "present": root.exists()} for root in _legacy_roots(config)
        ],
    }
    exit_code = _exit_code(references=references, tasks=tasks)
    manifest = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "active_root": str(active),
        "roots": roots,
        "retained_families": families,
        "preseason_references": references,
        "knowledge_runtime": knowledge,
        "scheduled_tasks": tasks,
        "secret_presence": secrets,
        "exit_code": exit_code,
        "git_restorable": [
            "scripts",
            "config",
            "control",
            "prompts",
            "schemas",
            "tests",
            "docs",
            "src",
        ],
        "local_only": [
            "data/**",
            "reports/live/**",
            "*.sqlite",
            "Windows Task Scheduler registration",
            "user environment secrets",
        ],
    }
    secret_values = _secret_values_from_environment(config, env)
    env_names = {
        str(item.get("environment_variable"))
        for item in config.get("secret_presence_checks", [])
        if item.get("environment_variable")
    }
    redacted = redact_secrets(
        manifest,
        secret_values=secret_values,
        environment_variable_names=env_names,
    )
    if write_manifest:
        output = _resolve_under(active, str(config["machine_manifest_path"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        body = (json.dumps(redacted, indent=2, sort_keys=True) + "\n").encode("utf-8")
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_bytes(body)
        temporary.replace(output)
        redacted = deepcopy(redacted)
        redacted["machine_manifest_path"] = str(output)
    return redacted
