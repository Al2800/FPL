"""Content-addressed solver payload store for historical replay setup."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, Mapping

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint


PayloadKind = Literal["solver_input", "solver_output"]
REF_SCHEMA_VERSION = "1.0"
PAYLOAD_STORE_SCHEMA_VERSION = "1.0"
REF_KINDS = {"solver_input_ref", "solver_output_ref"}
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REVIEWED_FILENAMES = {
    "reviewed-engine-input.json": "solver_input",
    "reviewed-engine-output.json": "solver_output",
}


class ReplayPayloadStoreError(ValueError):
    """Raised when a replay payload store contract is violated."""


def is_payload_ref(value: Mapping[str, Any]) -> bool:
    return str(value.get("kind", "")) in REF_KINDS


def _subdir_for_kind(kind: PayloadKind) -> str:
    return "solver-input" if kind == "solver_input" else "solver-output"


def _reviewed_filename(kind: PayloadKind) -> str:
    return (
        "reviewed-engine-input.json"
        if kind == "solver_input"
        else "reviewed-engine-output.json"
    )


def _kind_from_ref_kind(ref_kind: str) -> PayloadKind:
    if ref_kind == "solver_input_ref":
        return "solver_input"
    if ref_kind == "solver_output_ref":
        return "solver_output"
    raise ReplayPayloadStoreError(f"Unknown payload ref kind: {ref_kind}")


def _kind_from_path(path: Path) -> PayloadKind:
    try:
        return _REVIEWED_FILENAMES[path.name]  # type: ignore[return-value]
    except KeyError as exc:
        raise ReplayPayloadStoreError(
            f"Cannot infer payload kind from path name: {path.name}"
        ) from exc


def validate_payload_digest(digest: str, *, field: str = "payload_sha256") -> str:
    """Reject non-canonical digests before any filesystem access."""

    if not isinstance(digest, str):
        raise ReplayPayloadStoreError(f"{field} must be a string")
    if "/" in digest or "\\" in digest or ".." in digest or digest != digest.lower():
        raise ReplayPayloadStoreError(
            f"{field} must be a lowercase 64-hex digest without path components"
        )
    if not _DIGEST_RE.fullmatch(digest):
        raise ReplayPayloadStoreError(
            f"{field} must be a lowercase 64-hex digest, got {digest!r}"
        )
    return digest


def payload_path(setup_dir: Path, kind: PayloadKind, payload_sha256: str) -> Path:
    digest = validate_payload_digest(payload_sha256)
    return setup_dir / "payloads" / _subdir_for_kind(kind) / f"{digest}.json"


def _write_immutable_json(path: Path, value: dict[str, Any]) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ReplayPayloadStoreError(
                f"Refusing to overwrite sealed replay payload: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReplayPayloadStoreError(f"Required replay payload is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReplayPayloadStoreError(f"Replay payload must be an object: {path}")
    return value


def store_payload_once(setup_dir: Path, kind: PayloadKind, value: dict[str, Any]) -> str:
    """Persist one solver payload under its content hash, writing at most once."""

    payload_sha256 = fingerprint(value)
    _write_immutable_json(payload_path(setup_dir, kind, payload_sha256), value)
    return payload_sha256


def build_payload_ref(kind: PayloadKind, payload_sha256: str) -> dict[str, Any]:
    """Build a self-sealed reference envelope for a stored payload."""

    digest = validate_payload_digest(payload_sha256)
    ref: dict[str, Any] = {
        "schema_version": REF_SCHEMA_VERSION,
        "kind": f"{kind}_ref",
        "payload_sha256": digest,
    }
    ref["content_sha256"] = artifact_hash(ref)
    return ref


def validate_payload_ref(
    raw: Mapping[str, Any],
    *,
    expected_kind: PayloadKind,
) -> str:
    """Validate a reference envelope and return its target payload digest."""

    if not is_payload_ref(raw):
        raise ReplayPayloadStoreError(
            f"Expected payload reference kind for {expected_kind}, "
            f"got {raw.get('kind')!r}"
        )
    if str(raw.get("schema_version")) != REF_SCHEMA_VERSION:
        raise ReplayPayloadStoreError(
            f"Unsupported payload ref schema_version: {raw.get('schema_version')!r}"
        )
    ref_kind = str(raw["kind"])
    actual_kind = _kind_from_ref_kind(ref_kind)
    if actual_kind != expected_kind:
        raise ReplayPayloadStoreError(
            f"Payload ref kind mismatch: expected {expected_kind}_ref, got {ref_kind}"
        )
    # Reject legacy dual-meaning content_sha256-as-target without payload_sha256.
    if "payload_sha256" not in raw:
        raise ReplayPayloadStoreError(
            "Payload ref must include payload_sha256 (target digest); "
            "content_sha256 is reserved for the reference self-hash"
        )
    digest = validate_payload_digest(str(raw["payload_sha256"]))
    if "content_sha256" not in raw:
        raise ReplayPayloadStoreError("Payload ref must be self-sealed with content_sha256")
    if str(raw["content_sha256"]) != artifact_hash(raw):
        raise ReplayPayloadStoreError("Payload ref content_sha256 mismatch")
    closed = set(raw) - {"schema_version", "kind", "payload_sha256", "content_sha256"}
    if closed:
        raise ReplayPayloadStoreError(
            f"Payload ref contains unexpected fields: {sorted(closed)}"
        )
    return digest


def _setup_dir_for_arm(arm_dir: Path) -> Path:
    return arm_dir.parent.parent


def _verify_manifest_entry(
    setup_dir: Path,
    kind: PayloadKind,
    payload_sha256: str,
) -> None:
    manifest_path = setup_dir / "payloads" / "manifest.json"
    if not manifest_path.exists():
        raise ReplayPayloadStoreError(
            f"Payload store manifest missing while resolving ref under {setup_dir}"
        )
    manifest = _read_json(manifest_path)
    if str(manifest.get("schema_version")) != PAYLOAD_STORE_SCHEMA_VERSION:
        raise ReplayPayloadStoreError(
            f"Unsupported payload store manifest schema: {manifest.get('schema_version')!r}"
        )
    if str(manifest.get("content_sha256")) != artifact_hash(manifest):
        raise ReplayPayloadStoreError("Payload store manifest content_sha256 mismatch")
    key = "solver_inputs" if kind == "solver_input" else "solver_outputs"
    entries = manifest.get(key)
    if not isinstance(entries, list) or payload_sha256 not in entries:
        raise ReplayPayloadStoreError(
            f"Payload {payload_sha256} for {kind} is not listed in store manifest"
        )


def resolve_payload_ref(
    raw: Mapping[str, Any],
    *,
    setup_dir: Path,
    expected_kind: PayloadKind,
    verify_manifest: bool = True,
) -> dict[str, Any]:
    """Resolve one validated reference envelope to its stored payload."""

    digest = validate_payload_ref(raw, expected_kind=expected_kind)
    if verify_manifest:
        _verify_manifest_entry(setup_dir, expected_kind, digest)
    stored = _read_json(payload_path(setup_dir, expected_kind, digest))
    actual = fingerprint(stored)
    if actual != digest:
        raise ReplayPayloadStoreError(
            f"Stored {expected_kind} hash mismatch: expected {digest}, got {actual}"
        )
    return stored


def load_reviewed_payload(
    path: Path,
    *,
    expected_kind: PayloadKind | None = None,
    verify_manifest: bool = True,
) -> dict[str, Any]:
    """Load an inline or referenced reviewed solver payload.

    This is the single entry point for all production/evaluation consumers.
    """

    kind = expected_kind or _kind_from_path(path)
    raw = _read_json(path)
    if not is_payload_ref(raw):
        return raw
    # Arm layout: <setup>/arms/<arm>/reviewed-engine-*.json
    setup_dir = path.parent.parent.parent
    return resolve_payload_ref(
        raw,
        setup_dir=setup_dir,
        expected_kind=kind,
        verify_manifest=verify_manifest,
    )


def resolve_reviewed_payload(
    arm_dir: Path,
    kind: PayloadKind,
    *,
    verify_manifest: bool = True,
) -> dict[str, Any]:
    """Load an inline or referenced reviewed solver payload for one arm."""

    return load_reviewed_payload(
        arm_dir / _reviewed_filename(kind),
        expected_kind=kind,
        verify_manifest=verify_manifest,
    )


def write_arm_payload_ref(
    arm_dir: Path,
    kind: PayloadKind,
    payload_sha256: str,
) -> None:
    """Write one arm-level reference to a content-addressed solver payload."""

    _write_immutable_json(
        arm_dir / _reviewed_filename(kind),
        build_payload_ref(kind, payload_sha256),
    )


def build_store_manifest(
    *,
    input_hashes: set[str],
    output_hashes: set[str],
) -> dict[str, Any]:
    for digest in sorted(input_hashes | output_hashes):
        validate_payload_digest(digest)
    manifest: dict[str, Any] = {
        "schema_version": PAYLOAD_STORE_SCHEMA_VERSION,
        "solver_inputs": sorted(input_hashes),
        "solver_outputs": sorted(output_hashes),
        "unique_solver_inputs": len(input_hashes),
        "unique_solver_outputs": len(output_hashes),
    }
    manifest["content_sha256"] = artifact_hash(manifest)
    return manifest


def write_store_manifest(
    setup_dir: Path,
    *,
    input_hashes: set[str],
    output_hashes: set[str],
) -> dict[str, Any]:
    manifest = build_store_manifest(
        input_hashes=input_hashes,
        output_hashes=output_hashes,
    )
    _write_immutable_json(setup_dir / "payloads" / "manifest.json", manifest)
    return manifest
