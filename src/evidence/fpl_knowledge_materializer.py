"""Build a derived, additive SQLite/FTS index over immutable FPL evidence.

The FPL ledger and acquisition manifests remain authoritative.  This module
never fetches, alters or stores raw source captures: it indexes only already
admitted derived claim text plus the provenance needed to cite it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

from src.evidence.live_evidence_ledger import validate_live_evidence_ledger
from src.forecasting.live_faithful import artifact_hash


class FPLKnowledgeMaterializationError(ValueError):
    """Raised when an input cannot safely enter the derived FPL index."""


class FPLKnowledgeMaterializationConflict(FPLKnowledgeMaterializationError):
    """Raised when a materialisation identity is partially or inconsistently stored."""


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise FPLKnowledgeMaterializationError(f"{field} must be a SHA-256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise FPLKnowledgeMaterializationError(
            f"{field} must be a SHA-256 hex string"
        ) from exc
    return value


def _validate_context(context: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    context_id = context.get("context_id")
    content_sha256 = context.get("content_sha256")
    status = context.get("status")
    required_status = str(config["materialization"]["required_context_status"])
    if not isinstance(context_id, str) or not context_id:
        raise FPLKnowledgeMaterializationError("approved context requires context_id")
    _sha256(content_sha256, "approved context content_sha256")
    if status != required_status:
        raise FPLKnowledgeMaterializationError("approved context status is required")
    if artifact_hash(context) != content_sha256:
        raise FPLKnowledgeMaterializationError("approved context content hash mismatch")
    return {
        "context_id": context_id,
        "content_sha256": content_sha256,
        "status": status,
    }


def _manifest_bindings(
    manifests: Sequence[Mapping[str, Any]], config: Mapping[str, Any]
) -> list[dict[str, str]]:
    if not manifests:
        raise FPLKnowledgeMaterializationError("at least one acquisition manifest is required")
    expected_status = str(config["materialization"]["accepted_manifest_status"])
    bindings: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for manifest in manifests:
        manifest_id = manifest.get("manifest_id")
        source_id = manifest.get("source_id")
        source_hash = manifest.get("source_hash_sha256")
        content_hash = manifest.get("content_sha256")
        status = manifest.get("status")
        if not isinstance(manifest_id, str) or not manifest_id:
            raise FPLKnowledgeMaterializationError("manifest_id is required")
        if not isinstance(source_id, str) or not source_id:
            raise FPLKnowledgeMaterializationError("manifest source_id is required")
        _sha256(source_hash, "manifest source_hash_sha256")
        _sha256(content_hash, "manifest content_sha256")
        if status != expected_status:
            raise FPLKnowledgeMaterializationError("manifest is not accepted")
        if artifact_hash(manifest) != content_hash:
            raise FPLKnowledgeMaterializationError("manifest content hash mismatch")
        key = (source_id, source_hash)
        if key in seen:
            raise FPLKnowledgeMaterializationError("duplicate manifest source binding")
        seen.add(key)
        bindings.append(
            {
                "manifest_id": manifest_id,
                "source_id": source_id,
                "source_hash_sha256": source_hash,
                "content_sha256": content_hash,
            }
        )
    return sorted(bindings, key=lambda item: (item["source_id"], item["source_hash_sha256"]))


def _materialization_identity(
    ledger: Mapping[str, Any], manifests: Sequence[Mapping[str, str]], context: Mapping[str, str]
) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": "1.0",
            "ledger_id": str(ledger["ledger_id"]),
            "ledger_sha256": str(ledger["content_sha256"]),
            "manifest_content_sha256": [item["content_sha256"] for item in manifests],
            "approved_context_id": str(context["context_id"]),
            "approved_context_sha256": str(context["content_sha256"]),
            "index_schema": "fpl-evidence-fts-v1",
        }
    )


def _initialise(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS fpl_materializations (
            materialization_sha256 TEXT PRIMARY KEY,
            identity_json TEXT NOT NULL,
            ledger_id TEXT NOT NULL,
            ledger_sha256 TEXT NOT NULL,
            approved_context_id TEXT NOT NULL,
            approved_context_sha256 TEXT NOT NULL,
            claim_count INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fpl_claims (
            materialization_sha256 TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            manifest_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_hash_sha256 TEXT NOT NULL,
            source_authority TEXT NOT NULL,
            source_url TEXT NOT NULL,
            document_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            claim_text TEXT NOT NULL,
            value_json TEXT NOT NULL,
            confidence REAL NOT NULL,
            published_at TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            available_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            supersedes_json TEXT NOT NULL,
            identity_bindings_json TEXT NOT NULL,
            decision_boundary_ids_json TEXT NOT NULL,
            quarantine_json TEXT NOT NULL,
            PRIMARY KEY(materialization_sha256, claim_id),
            FOREIGN KEY(materialization_sha256)
                REFERENCES fpl_materializations(materialization_sha256)
        );
        CREATE TABLE IF NOT EXISTS fpl_claim_entities (
            materialization_sha256 TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            stable_id TEXT NOT NULL,
            PRIMARY KEY(materialization_sha256, claim_id, entity_type, stable_id),
            FOREIGN KEY(materialization_sha256, claim_id)
                REFERENCES fpl_claims(materialization_sha256, claim_id)
        );
        CREATE INDEX IF NOT EXISTS fpl_claims_temporal
            ON fpl_claims(materialization_sha256, available_at, expires_at);
        CREATE INDEX IF NOT EXISTS fpl_claims_authority
            ON fpl_claims(materialization_sha256, source_authority);
        CREATE INDEX IF NOT EXISTS fpl_claim_entities_scope
            ON fpl_claim_entities(materialization_sha256, entity_type, stable_id);
        CREATE VIRTUAL TABLE IF NOT EXISTS fpl_claims_fts USING fts5(
            materialization_sha256 UNINDEXED,
            claim_id UNINDEXED,
            claim_text
        );
        """
    )


def resolve_fpl_knowledge_profile(
    config: Mapping[str, Any], *, environ: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Resolve the reusable knowledge profile without opening any database."""

    runtime = config.get("knowledge_runtime")
    if not isinstance(runtime, Mapping):
        raise FPLKnowledgeMaterializationError("retrieval config requires knowledge_runtime")
    package_path = Path(str(runtime.get("tools_kb_path", ""))).resolve(strict=False)
    if not package_path.is_dir():
        raise FPLKnowledgeMaterializationError("configured knowledge runtime is unavailable")
    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))
    try:
        from kb.service import resolve_runtime_project_profile
    except ImportError as exc:
        raise FPLKnowledgeMaterializationError("knowledge runtime profile resolver is unavailable") from exc
    profile = resolve_runtime_project_profile(
        str(runtime.get("profile_id", "")),
        environ=dict(environ) if environ is not None else None,
    )
    if profile is None:
        raise FPLKnowledgeMaterializationError("FPL profile must be explicitly selected")
    return {
        "profile_id": profile.profile_id,
        "root": str(profile.root),
        "intake_dir": str(profile.intake_dir),
        "evidence_db": str(profile.evidence_db),
        "profile_path": str(profile.profile_path),
    }


def materialize_fpl_evidence_index(
    *,
    ledger: Mapping[str, Any],
    acquisition_manifests: Sequence[Mapping[str, Any]],
    approved_context: Mapping[str, Any],
    config: Mapping[str, Any],
    database_path: str | Path,
) -> dict[str, Any]:
    """Index an immutable FPL ledger additively; raw inputs are read-only."""

    validate_live_evidence_ledger(ledger)
    if ledger.get("season") != config.get("season"):
        raise FPLKnowledgeMaterializationError("ledger season does not match retrieval config")
    manifests = _manifest_bindings(acquisition_manifests, config)
    context = _validate_context(approved_context, config)
    manifest_by_source = {
        (item["source_id"], item["source_hash_sha256"]): item for item in manifests
    }
    claims = list(ledger["claims"])
    rows: list[dict[str, Any]] = []
    for claim in claims:
        source_id = str(claim["source_id"])
        source_hash = str(claim["source_hash_sha256"])
        manifest = manifest_by_source.get((source_id, source_hash))
        if manifest is None:
            raise FPLKnowledgeMaterializationError(
                f"claim source is not bound by an accepted manifest: {claim['claim_id']}"
            )
        rows.append(
            {
                "claim": deepcopy(dict(claim)),
                "manifest": manifest,
            }
        )
    identity = _materialization_identity(ledger, manifests, context)
    materialization_sha256 = identity["content_sha256"]
    target = Path(database_path).resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    try:
        _initialise(connection)
        existing = connection.execute(
            "SELECT identity_json, claim_count FROM fpl_materializations WHERE materialization_sha256=?",
            (materialization_sha256,),
        ).fetchone()
        if existing is not None:
            indexed_claim_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM fpl_claims WHERE materialization_sha256=?",
                    (materialization_sha256,),
                ).fetchone()[0]
            )
            indexed_fts_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM fpl_claims_fts WHERE materialization_sha256=?",
                    (materialization_sha256,),
                ).fetchone()[0]
            )
            if (
                existing[0] != _canonical(identity)
                or int(existing[1]) != len(rows)
                or indexed_claim_count != len(rows)
                or indexed_fts_count != len(rows)
            ):
                raise FPLKnowledgeMaterializationConflict(
                    "materialization identity already has inconsistent derived rows"
                )
            return {
                "status": "unchanged",
                "database_path": str(target),
                "materialization_sha256": materialization_sha256,
                "claim_count": len(rows),
                "ledger_sha256": ledger["content_sha256"],
                "approved_context_sha256": context["content_sha256"],
            }
        with connection:
            connection.execute(
                """INSERT INTO fpl_materializations(
                    materialization_sha256, identity_json, ledger_id, ledger_sha256,
                    approved_context_id, approved_context_sha256, claim_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    materialization_sha256,
                    _canonical(identity),
                    ledger["ledger_id"],
                    ledger["content_sha256"],
                    context["context_id"],
                    context["content_sha256"],
                    len(rows),
                ),
            )
            for row in sorted(rows, key=lambda item: str(item["claim"]["claim_id"])):
                claim = row["claim"]
                manifest = row["manifest"]
                authority = str(claim.get("source_rights", {}).get("authority", "unknown"))
                connection.execute(
                    """INSERT INTO fpl_claims VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )""",
                    (
                        materialization_sha256,
                        claim["claim_id"],
                        manifest["manifest_id"],
                        claim["source_id"],
                        claim["source_hash_sha256"],
                        authority,
                        claim["source_url"],
                        claim["document_id"],
                        claim["claim_type"],
                        claim["claim_text"],
                        _canonical(claim["value"]),
                        claim["confidence"],
                        claim["published_at"],
                        claim["observed_at"],
                        claim["available_at"],
                        claim["expires_at"],
                        _canonical({"items": claim["supersedes_claim_ids"]}),
                        _canonical({"items": claim["identity_bindings"]}),
                        _canonical({"items": claim["decision_boundary_ids"]}),
                        _canonical(claim["quarantine"]),
                    ),
                )
                connection.execute(
                    "INSERT INTO fpl_claims_fts VALUES (?, ?, ?)",
                    (materialization_sha256, claim["claim_id"], claim["claim_text"]),
                )
                for binding in claim["identity_bindings"]:
                    connection.execute(
                        "INSERT INTO fpl_claim_entities VALUES (?, ?, ?, ?)",
                        (
                            materialization_sha256,
                            claim["claim_id"],
                            binding["entity_type"],
                            binding["stable_id"],
                        ),
                    )
    finally:
        connection.close()
    return {
        "status": "created",
        "database_path": str(target),
        "materialization_sha256": materialization_sha256,
        "claim_count": len(rows),
        "ledger_sha256": ledger["content_sha256"],
        "approved_context_sha256": context["content_sha256"],
    }
