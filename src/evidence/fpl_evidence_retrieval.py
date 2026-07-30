"""Deadline-bounded, entity-scoped retrieval over the derived FPL evidence index."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class FPLEvidenceRetrievalError(ValueError):
    """Raised when a retrieval request is missing a hard safety boundary."""


_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._'-]{1,}")
_SCOPE_FIELDS = {
    "player_ids": "player_uid",
    "team_ids": "team_uid",
    "club_ids": "club_uid",
    "fixture_ids": "fixture_uid",
}


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        raise FPLEvidenceRetrievalError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FPLEvidenceRetrievalError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise FPLEvidenceRetrievalError(f"{field} must include timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _scope(entity_scope: Mapping[str, Any] | None) -> dict[str, set[str]]:
    if not isinstance(entity_scope, Mapping):
        raise FPLEvidenceRetrievalError("entity_scope is required")
    result: dict[str, set[str]] = {}
    for field, entity_type in _SCOPE_FIELDS.items():
        values = entity_scope.get(field, [])
        if values is None:
            values = []
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not item.strip() for item in values
        ):
            raise FPLEvidenceRetrievalError(f"entity_scope.{field} must be a string list")
        if values:
            result.setdefault(entity_type, set()).update(item.strip() for item in values)
    if not result:
        raise FPLEvidenceRetrievalError("entity_scope requires at least one candidate/entity ID")
    return result


def _parse_items(value: str, field: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise FPLEvidenceRetrievalError(f"invalid indexed {field}") from exc
    items = parsed.get("items") if isinstance(parsed, dict) else None
    if not isinstance(items, list):
        raise FPLEvidenceRetrievalError(f"invalid indexed {field}")
    return items


def _rows(connection: sqlite3.Connection, materialization_sha256: str) -> list[dict[str, Any]]:
    connection.row_factory = sqlite3.Row
    records = connection.execute(
        "SELECT * FROM fpl_claims WHERE materialization_sha256=? ORDER BY claim_id",
        (materialization_sha256,),
    ).fetchall()
    if not records:
        raise FPLEvidenceRetrievalError("unknown materialization_sha256")
    output: list[dict[str, Any]] = []
    for record in records:
        row = dict(record)
        row["value"] = json.loads(row.pop("value_json"))
        row["supersedes_claim_ids"] = _parse_items(
            row.pop("supersedes_json"), "supersedes_claim_ids"
        )
        row["identity_bindings"] = _parse_items(
            row.pop("identity_bindings_json"), "identity_bindings"
        )
        row["decision_boundary_ids"] = _parse_items(
            row.pop("decision_boundary_ids_json"), "decision_boundary_ids"
        )
        try:
            row["quarantine"] = json.loads(row.pop("quarantine_json"))
        except json.JSONDecodeError as exc:
            raise FPLEvidenceRetrievalError("invalid indexed quarantine") from exc
        output.append(row)
    return output


def _lifecycle(
    rows: Sequence[Mapping[str, Any]], cutoff: datetime
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    known: list[dict[str, Any]] = []
    omitted = {
        "future_claim_ids": [],
        "superseded_claim_ids": [],
        "expired_claim_ids": [],
        "quarantined_claim_ids": [],
    }
    for source in rows:
        row = deepcopy(dict(source))
        times = [_timestamp(row[field], field)[1] for field in (
            "published_at", "observed_at", "available_at"
        )]
        if not all(item <= cutoff for item in times):
            omitted["future_claim_ids"].append(str(row["claim_id"]))
        else:
            known.append(row)
    effective_superseders = [
        row for row in known
        if not bool(row["quarantine"].get("quarantined"))
        and _timestamp(row["expires_at"], "expires_at")[1] > cutoff
    ]
    superseded_ids = {
        str(value)
        for row in effective_superseders
        for value in row["supersedes_claim_ids"]
    }
    current = []
    for row in known:
        claim_id = str(row["claim_id"])
        if claim_id in superseded_ids:
            omitted["superseded_claim_ids"].append(claim_id)
        else:
            current.append(row)
    active: list[dict[str, Any]] = []
    for row in current:
        claim_id = str(row["claim_id"])
        if _timestamp(row["expires_at"], "expires_at")[1] <= cutoff:
            omitted["expired_claim_ids"].append(claim_id)
        elif bool(row["quarantine"].get("quarantined")):
            omitted["quarantined_claim_ids"].append(claim_id)
        else:
            active.append(row)
    return active, {key: sorted(value) for key, value in omitted.items()}


def _in_scope(row: Mapping[str, Any], scope: Mapping[str, set[str]]) -> bool:
    return any(
        str(binding.get("entity_type")) in scope
        and str(binding.get("stable_id")) in scope[str(binding.get("entity_type"))]
        for binding in row["identity_bindings"]
    )


def _fts_scores(
    connection: sqlite3.Connection,
    *,
    materialization_sha256: str,
    claim_ids: Sequence[str],
    query_text: str,
) -> dict[str, float]:
    if not claim_ids:
        return {}
    tokens = list(dict.fromkeys(_TOKEN.findall(query_text.lower())))
    if not tokens:
        return {claim_id: 0.0 for claim_id in claim_ids}
    match = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
    result: dict[str, float] = {}
    # SQLite's parameter limit varies by build. Chunking retains deterministic
    # scores while ensuring hard lifecycle/scope filters have already run.
    for start in range(0, len(claim_ids), 800):
        batch = list(claim_ids[start : start + 800])
        placeholders = ",".join("?" for _ in batch)
        rows = connection.execute(
            f"""SELECT claim_id, -bm25(fpl_claims_fts) AS score
                FROM fpl_claims_fts
                WHERE materialization_sha256=?
                  AND claim_id IN ({placeholders})
                  AND fpl_claims_fts MATCH ?""",
            (materialization_sha256, *batch, match),
        ).fetchall()
        result.update({str(row[0]): round(float(row[1]), 8) for row in rows})
    return result


def _ranked_claim_view(row: Mapping[str, Any], score: float) -> dict[str, Any]:
    return {
        "claim_id": row["claim_id"],
        "manifest_id": row["manifest_id"],
        "source_id": row["source_id"],
        "source_hash_sha256": row["source_hash_sha256"],
        "source_authority": row["source_authority"],
        "source_url": row["source_url"],
        "document_id": row["document_id"],
        "claim_type": row["claim_type"],
        "claim_text": row["claim_text"],
        "value": row["value"],
        "confidence": float(row["confidence"]),
        "published_at": row["published_at"],
        "observed_at": row["observed_at"],
        "available_at": row["available_at"],
        "expires_at": row["expires_at"],
        "identity_bindings": row["identity_bindings"],
        "decision_boundary_ids": row["decision_boundary_ids"],
        "lexical_score": score,
    }


def _limit_ids(values: Sequence[str], maximum: int) -> list[str]:
    return sorted(values)[:maximum]


def retrieve_fpl_evidence_packet(
    *,
    database_path: str | Path,
    materialization_sha256: str,
    decision_cutoff: str,
    entity_scope: Mapping[str, Any] | None,
    query_text: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic, bounded cited packet for one decision cutoff."""

    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    scope = _scope(entity_scope)
    retrieval = config.get("retrieval")
    if not isinstance(retrieval, Mapping):
        raise FPLEvidenceRetrievalError("retrieval config is required")
    if not isinstance(query_text, str) or len(query_text) > int(retrieval["maximum_query_characters"]):
        raise FPLEvidenceRetrievalError("query_text exceeds configured limit")
    allowed_authorities = {str(item) for item in retrieval["allowed_authorities"]}
    if not allowed_authorities:
        raise FPLEvidenceRetrievalError("allowed_authorities is required")
    maximum_omissions = int(retrieval["omission_id_limit"])
    target = Path(database_path)
    connection = sqlite3.connect(f"{target.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows = _rows(connection, materialization_sha256)
        active, omissions = _lifecycle(rows, cutoff)
        authority_allowed = [
            row for row in active if str(row["source_authority"]) in allowed_authorities
        ]
        omissions["disallowed_source_claim_ids"] = _limit_ids(
            [str(row["claim_id"]) for row in active if row not in authority_allowed],
            maximum_omissions,
        )
        scoped = [row for row in authority_allowed if _in_scope(row, scope)]
        omissions["out_of_scope_claim_ids"] = _limit_ids(
            [str(row["claim_id"]) for row in authority_allowed if row not in scoped],
            maximum_omissions,
        )
        scores = _fts_scores(
            connection,
            materialization_sha256=materialization_sha256,
            claim_ids=[str(row["claim_id"]) for row in scoped],
            query_text=query_text,
        )
    finally:
        connection.close()

    lexical = [row for row in scoped if str(row["claim_id"]) in scores]
    omissions["lexical_no_match_claim_ids"] = _limit_ids(
        [str(row["claim_id"]) for row in scoped if row not in lexical],
        maximum_omissions,
    )
    authority_rank = {name: index for index, name in enumerate(sorted(allowed_authorities))}
    ranked = sorted(
        lexical,
        key=lambda row: (
            -scores[str(row["claim_id"])],
            authority_rank[str(row["source_authority"])],
            str(row["available_at"]),
            str(row["claim_id"]),
        ),
    )
    maximum_claims = int(retrieval["maximum_claims"])
    maximum_characters = int(retrieval["maximum_claim_characters"])
    selected: list[dict[str, Any]] = []
    characters = 0
    claim_budget: list[str] = []
    character_budget: list[str] = []
    for row in ranked:
        text_size = len(str(row["claim_text"]))
        if len(selected) >= maximum_claims:
            claim_budget.append(str(row["claim_id"]))
        elif characters + text_size > maximum_characters:
            character_budget.append(str(row["claim_id"]))
        else:
            selected.append(_ranked_claim_view(row, scores[str(row["claim_id"])]))
            characters += text_size
    omissions["claim_budget_claim_ids"] = _limit_ids(claim_budget, maximum_omissions)
    omissions["character_budget_claim_ids"] = _limit_ids(character_budget, maximum_omissions)
    for key, values in omissions.items():
        omissions[key] = _limit_ids(values, maximum_omissions)

    packet_body = {
        "schema_version": "1.0",
        "packet_id": f"fpl-evidence:{materialization_sha256}:{cutoff_text}",
        "status": "complete" if selected else "degraded",
        "degraded_reasons": [] if selected else ["no_retrieved_active_evidence"],
        "materialization_sha256": materialization_sha256,
        "decision_cutoff": cutoff_text,
        "entity_scope": {
            field: sorted(entity_scope.get(field, []))
            for field in _SCOPE_FIELDS
            if entity_scope.get(field)
        },
        "query_text": query_text,
        "evidence": selected,
        "limits": {
            "maximum_claims": maximum_claims,
            "maximum_claim_characters": maximum_characters,
            "selected_claims": len(selected),
            "selected_claim_characters": characters,
        },
        "context_contract": {
            "agent_visible_fields": [
                "schema_version", "packet_id", "status", "degraded_reasons",
                "materialization_sha256", "decision_cutoff", "entity_scope",
                "query_text", "evidence", "limits", "content_sha256",
            ],
            "host_audit_only_fields": ["retrieval_audit", "omitted"],
            "raw_source_text": "forbidden",
            "identical_packet_required_for_all_agent_arms": True,
            "frozen_no_evidence_control_required": True,
        },
        "retrieval_audit": {
            "ranking_method": str(retrieval["ranking_method"]),
            "semantic_dependency": str(retrieval["semantic_dependency"]),
            "hard_predicates_before_ranking": [
                "published_observed_available_at_cutoff",
                "supersession_expiry_quarantine",
                "source_authority",
                "entity_scope",
            ],
            "indexed_claim_count": len(rows),
            "active_claim_count": len(active),
            "authority_allowed_claim_count": len(authority_allowed),
            "scope_allowed_claim_count": len(scoped),
            "lexically_ranked_claim_count": len(lexical),
        },
        "omitted": omissions,
    }
    return _seal(packet_body)


def agent_visible_fpl_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Strip host audit/omission fields before an agent receives the packet."""

    if packet.get("content_sha256") != artifact_hash(packet):
        raise FPLEvidenceRetrievalError("packet content hash mismatch")
    allowed = set(packet["context_contract"]["agent_visible_fields"])
    return {key: deepcopy(value) for key, value in packet.items() if key in allowed}


def measure_fpl_retrieval_latency(
    *,
    runs: int,
    **request: Any,
) -> dict[str, float]:
    """Measure deterministic local retrieval latency without changing the index."""

    if runs < 1:
        raise FPLEvidenceRetrievalError("runs must be positive")
    durations: list[float] = []
    packet_hashes: set[str] = set()
    for _ in range(runs):
        started = time.perf_counter()
        packet = retrieve_fpl_evidence_packet(**request)
        durations.append((time.perf_counter() - started) * 1000)
        packet_hashes.add(str(packet["content_sha256"]))
    ordered = sorted(durations)

    def percentile(percent: float) -> float:
        position = (len(ordered) - 1) * percent
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        "runs": float(runs),
        "p50_ms": round(percentile(0.50), 3),
        "p95_ms": round(percentile(0.95), 3),
        "p99_ms": round(percentile(0.99), 3),
        "packet_hash_count": float(len(packet_hashes)),
    }
