"""Content-addressed solver payload store for historical replay setup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Mapping

from src.optimisation.io import fingerprint


PayloadKind = Literal["solver_input", "solver_output"]
REF_SCHEMA_VERSION = "1.0"
PAYLOAD_STORE_SCHEMA_VERSION = "1.0"
REF_KINDS = {"solver_input_ref", "solver_output_ref"}


class ReplayPayloadStoreError(ValueError):
    """Raised when a replay payload store contract is violated."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def is_payload_ref(value: Mapping[str, Any]) -> bool:  # type: ignore[name-defined]
    return str(value.get("kind", "")) in REF_KINDS


def _subdir_for_kind(kind: PayloadKind) -> str:
    return "solver-input" if kind == "solver_input" else "solver-output"


def _reviewed_filename(kind: PayloadKind) -> str:
    return (
        "reviewed-engine-input.json"
        if kind == "solver_input"
        else "reviewed-engine-output.json"
    )


def payload_path(setup_dir: Path, kind: PayloadKind, content_sha256: str) -> Path:
    return (
        setup_dir
        / "payloads"
        / _subdir_for_kind(kind)
        / f"{content_sha256}.json"
    )


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

    content_sha256 = fingerprint(value)
    _write_immutable_json(payload_path(setup_dir, kind, content_sha256), value)
    return content_sha256


def build_payload_ref(kind: PayloadKind, content_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": REF_SCHEMA_VERSION,
        "kind": f"{kind}_ref",
        "content_sha256": content_sha256,
    }


def write_arm_payload_ref(
    arm_dir: Path,
    kind: PayloadKind,
    content_sha256: str,
) -> None:
    """Write one arm-level reference to a content-addressed solver payload."""

    _write_immutable_json(
        arm_dir / _reviewed_filename(kind),
        build_payload_ref(kind, content_sha256),
    )


def resolve_reviewed_payload(arm_dir: Path, kind: PayloadKind) -> dict[str, Any]:
    """Load an inline or referenced reviewed solver payload with hash validation."""

    artifact_path = arm_dir / _reviewed_filename(kind)
    raw = _read_json(artifact_path)
    if not is_payload_ref(raw):
        actual = fingerprint(raw)
        return raw

    expected = str(raw["content_sha256"])
    setup_dir = arm_dir.parent.parent
    stored = _read_json(payload_path(setup_dir, kind, expected))
    actual = fingerprint(stored)
    if actual != expected:
        raise ReplayPayloadStoreError(
            f"Stored {kind} hash mismatch for {artifact_path}: "
            f"expected {expected}, got {actual}"
        )
    return stored


def build_store_manifest(
    *,
    input_hashes: set[str],
    output_hashes: set[str],
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": PAYLOAD_STORE_SCHEMA_VERSION,
        "solver_inputs": sorted(input_hashes),
        "solver_outputs": sorted(output_hashes),
        "unique_solver_inputs": len(input_hashes),
        "unique_solver_outputs": len(output_hashes),
    }
    from src.forecasting.live_faithful import artifact_hash

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
