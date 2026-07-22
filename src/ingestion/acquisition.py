"""Source-neutral, governed persistence for immutable acquisition artefacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Protocol

import httpx

from src.ingestion.registry import assert_collectable, get_source, load_registry

AcquisitionMode = Literal["live", "fixture"]
AcquisitionStatus = Literal["success", "http_error", "transport_error"]


class HttpClient(Protocol):
    """Small client boundary used by live adapters and offline tests."""

    def get(self, url: str, *, timeout: float) -> httpx.Response: ...


def utc_now() -> str:
    """Return a seconds-resolution UTC timestamp suitable for snapshot paths."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def content_hash(body: bytes) -> str:
    """Return the content address used by raw and derived provenance."""

    return hashlib.sha256(body).hexdigest()


def detect_schema(body: bytes, *, available: bool, http_status: int | None) -> dict[str, Any]:
    """Record a bounded shape fingerprint without embedding the source payload."""

    if not available:
        return {"type": "unavailable", "http_status": http_status}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {"type": "non_json", "bytes": len(body)}
    if isinstance(payload, dict):
        return {
            "type": "object",
            "top_level_keys": sorted(payload.keys()),
            "n_keys": len(payload),
        }
    if isinstance(payload, list):
        sample_keys: list[str] = []
        if payload and isinstance(payload[0], dict):
            sample_keys = sorted(payload[0].keys())
        return {"type": "array", "length": len(payload), "item_keys_sample": sample_keys}
    return {"type": type(payload).__name__}


def assert_acquisition_allowed(
    source_id: str,
    mode: AcquisitionMode,
    *,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Gate network collection while allowing registered sources in fixture tests."""

    if mode == "live":
        return assert_collectable(source_id, registry_path)
    if mode == "fixture":
        return get_source(source_id, registry_path)
    raise ValueError(f"Unsupported acquisition mode: {mode}")


def _manifest_id(
    *,
    source_id: str,
    origin: str,
    digest: str,
    status: AcquisitionStatus,
    schema_detection: dict[str, Any],
) -> str:
    stable = json.dumps(
        {
            "source_id": source_id,
            "origin": origin,
            "content_hash_sha256": digest,
            "acquisition_status": status,
            "schema_detection": schema_detection,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _snapshot_stamp(observed_at: str) -> str:
    return observed_at.replace(":", "").replace("-", "")


def _validate_artifact_name(artifact_name: str) -> str:
    candidate = Path(artifact_name)
    if candidate.is_absolute() or candidate.name != artifact_name or artifact_name in {"", ".", ".."}:
        raise ValueError("artifact_name must be a single relative filename")
    return artifact_name


def _write_immutable(path: Path, body: bytes) -> None:
    if path.exists():
        if path.read_bytes() != body:
            raise FileExistsError(f"Refusing to overwrite immutable artefact: {path}")
        return
    path.write_bytes(body)


def record_acquisition(
    *,
    source_id: str,
    mode: AcquisitionMode,
    origin: str,
    body: bytes,
    out_dir: Path,
    artifact_name: str,
    status: AcquisitionStatus,
    registry_version: str | None = None,
    observed_at: str | None = None,
    http_status: int | None = None,
    request_url: str | None = None,
    failure: dict[str, str] | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Persist a raw body and manifest without allowing destructive overwrite."""

    assert_acquisition_allowed(source_id, mode, registry_path=registry_path)
    name = _validate_artifact_name(artifact_name)
    observed = observed_at or utc_now()
    version = registry_version
    if version is None:
        version = str(load_registry(registry_path).get("registry_version", "unknown"))

    digest = content_hash(body)
    schema = detect_schema(body, available=status == "success", http_status=http_status)
    manifest_id = _manifest_id(
        source_id=source_id,
        origin=origin,
        digest=digest,
        status=status,
        schema_detection=schema,
    )
    run_dir = out_dir / _snapshot_stamp(observed)
    run_dir.mkdir(parents=True, exist_ok=True)
    body_path = run_dir / name
    manifest_name = f"{Path(name).stem}.meta.json"
    manifest_path = run_dir / manifest_name
    _write_immutable(body_path, body)

    manifest: dict[str, Any] = {
        "manifest_version": "1.0",
        "manifest_id": manifest_id,
        "content_identity": f"sha256:{digest}",
        "source_id": source_id,
        "acquisition_mode": mode,
        "origin": origin,
        "observed_at": observed,
        "source_registry_version": version,
        "acquisition_status": status,
        "content_hash_sha256": digest,
        "bytes": len(body),
        "body_file": name,
        "schema_detection": schema,
        "http_status": http_status,
        "request_url": request_url,
        "error": failure["message"] if failure else None,
        "failure": failure,
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_immutable(manifest_path, encoded)
    return manifest


def acquire_http(
    client: HttpClient,
    *,
    source_id: str,
    url: str,
    out_dir: Path,
    artifact_name: str,
    registry_version: str | None = None,
    observed_at: str | None = None,
    timeout: float = 30.0,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Acquire an HTTP resource only after its live registry gate passes."""

    assert_acquisition_allowed(source_id, "live", registry_path=registry_path)
    failure: dict[str, str] | None = None
    try:
        response = client.get(url, timeout=timeout)
        body = response.content
        http_status = response.status_code
        status: AcquisitionStatus = "success" if http_status == 200 else "http_error"
        if status == "http_error":
            failure = {"category": "http", "type": "HTTPStatus", "message": f"HTTP {http_status}"}
    except httpx.HTTPError as exc:
        body = b""
        http_status = 0
        status = "transport_error"
        failure = {
            "category": "transport",
            "type": type(exc).__name__,
            "message": str(exc),
        }
    return record_acquisition(
        source_id=source_id,
        mode="live",
        origin=url,
        body=body,
        out_dir=out_dir,
        artifact_name=artifact_name,
        status=status,
        registry_version=registry_version,
        observed_at=observed_at,
        http_status=http_status,
        request_url=url,
        failure=failure,
        registry_path=registry_path,
    )


def acquire_fixture(
    *,
    source_id: str,
    fixture_path: Path,
    origin: str,
    out_dir: Path,
    artifact_name: str | None = None,
    observed_at: str | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Exercise a registered adapter from a local fixture without network access."""

    assert_acquisition_allowed(source_id, "fixture", registry_path=registry_path)
    body = fixture_path.read_bytes()
    return record_acquisition(
        source_id=source_id,
        mode="fixture",
        origin=origin,
        body=body,
        out_dir=out_dir,
        artifact_name=artifact_name or fixture_path.name,
        status="success",
        observed_at=observed_at,
        registry_path=registry_path,
    )
