from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from src.evidence.fpl_evidence_retrieval import (
    FPLEvidenceRetrievalError,
    agent_visible_fpl_packet,
    measure_fpl_retrieval_latency,
    retrieve_fpl_evidence_packet,
)
from src.evidence.fpl_knowledge_materializer import (
    FPLKnowledgeMaterializationError,
    materialize_fpl_evidence_index,
)
from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    live_evidence_hash,
    new_live_evidence_ledger,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL_CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-fpl-retrieval.json").read_text(
        encoding="utf-8"
    )
)
EVIDENCE_CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence.json").read_text(
        encoding="utf-8"
    )
)
REGISTRY = yaml.safe_load(
    (ROOT / "control/sources/source-registry.yaml").read_text(encoding="utf-8")
)


def _claim(
    claim_id: str,
    *,
    player_id: str = "player:2026-27:1",
    text: str = "The player is fit and expected to train.",
    published_at: str = "2026-08-14T08:00:00Z",
    observed_at: str = "2026-08-14T08:05:00Z",
    available_at: str = "2026-08-14T08:06:00Z",
    expires_at: str = "2026-08-15T08:06:00Z",
    supersedes: list[str] | None = None,
) -> dict:
    return {
        "claim_id": claim_id,
        "source_id": "official-club-communications",
        "document_id": f"document:{claim_id}",
        "source_url": f"https://club.example/{claim_id}",
        "source_hash_sha256": hashlib.sha256(claim_id.encode()).hexdigest(),
        "claim_text": text,
        "claim_precision": "derived_claim",
        "claim_type": "player_availability",
        "value": {"status": "available"},
        "confidence": 0.8,
        "published_at": published_at,
        "observed_at": observed_at,
        "available_at": available_at,
        "expires_at": expires_at,
        "identity_bindings": [
            {
                "entity_type": "player_uid",
                "stable_id": player_id,
                "source_label": player_id,
                "match_status": "manual_verified",
            }
        ],
        "decision_boundary_ids": [f"availability:{player_id}"],
        "estimated_impact_points": 1.0,
        "supersedes_claim_ids": supersedes or [],
    }


def _append(ledger: dict, row: dict) -> dict:
    return append_live_evidence_claim(
        ledger, row, source_registry=REGISTRY, config=EVIDENCE_CONFIG
    )


def _seal(value: dict) -> dict:
    result = deepcopy(value)
    result["content_sha256"] = artifact_hash(result)
    return result


def _manifest_for(claim: dict) -> dict:
    return _seal(
        {
            "schema_version": "1.0",
            "manifest_id": f"manifest:{claim['claim_id']}",
            "source_id": claim["source_id"],
            "source_hash_sha256": claim["source_hash_sha256"],
            "status": "accepted",
        }
    )


def _context() -> dict:
    return _seal(
        {
            "context_id": "decision-context:2026-27:gw01",
            "status": "approved",
            "checkpoint_id": "T-24h",
        }
    )


def _ledger() -> dict:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    ledger = _append(
        ledger,
        _claim("old", text="The player remains doubtful."),
    )
    ledger = _append(
        ledger,
        _claim(
            "new",
            text="The player is fit after training.",
            observed_at="2026-08-14T08:19:00Z",
            available_at="2026-08-14T08:20:00Z",
            supersedes=["old"],
        ),
    )
    ledger = _append(
        ledger,
        _claim(
            "expired",
            text="Expired player status.",
            published_at="2026-08-14T08:23:00Z",
            observed_at="2026-08-14T08:24:00Z",
            available_at="2026-08-14T08:25:00Z",
            expires_at="2026-08-14T09:00:00Z",
        ),
    )
    ledger = _append(
        ledger,
        _claim(
            "other-player",
            player_id="player:2026-27:2",
            text="Different player is fit.",
            published_at="2026-08-14T08:30:00Z",
            observed_at="2026-08-14T08:31:00Z",
            available_at="2026-08-14T08:32:00Z",
        ),
    )
    ledger = _append(
        ledger,
        _claim(
            "untrusted",
            text="Untrusted player status.",
            published_at="2026-08-14T08:40:00Z",
            observed_at="2026-08-14T08:41:00Z",
            available_at="2026-08-14T08:42:00Z",
        ),
    )
    ledger = _append(
        ledger,
        _claim(
            "future",
            text="Future status update.",
            published_at="2026-08-14T11:00:00Z",
            observed_at="2026-08-14T11:01:00Z",
            available_at="2026-08-14T11:02:00Z",
            expires_at="2026-08-15T11:02:00Z",
        ),
    )
    changed = deepcopy(ledger)
    for row in changed["claims"]:
        if row["claim_id"] == "untrusted":
            row["source_rights"]["authority"] = "unknown"
    changed["content_sha256"] = live_evidence_hash(changed)
    return changed


def _materialized(tmp_path: Path) -> tuple[dict, dict, Path]:
    ledger = _ledger()
    manifests = [_manifest_for(row) for row in ledger["claims"]]
    database = tmp_path / "fpl-evidence.sqlite"
    result = materialize_fpl_evidence_index(
        ledger=ledger,
        acquisition_manifests=manifests,
        approved_context=_context(),
        config=RETRIEVAL_CONFIG,
        database_path=database,
    )
    return ledger, result, database


def _request(database: Path, materialization_sha256: str, cutoff: str) -> dict:
    return {
        "database_path": database,
        "materialization_sha256": materialization_sha256,
        "decision_cutoff": cutoff,
        "entity_scope": {"player_ids": ["player:2026-27:1"]},
        "query_text": "player",
        "config": RETRIEVAL_CONFIG,
    }


def test_materialization_is_idempotent_and_inputs_remain_unchanged(
    tmp_path: Path,
) -> None:
    ledger = _ledger()
    manifests = [_manifest_for(row) for row in ledger["claims"]]
    context = _context()
    before = json.dumps({"ledger": ledger, "manifests": manifests, "context": context}, sort_keys=True)
    database = tmp_path / "fpl-evidence.sqlite"

    first = materialize_fpl_evidence_index(
        ledger=ledger,
        acquisition_manifests=manifests,
        approved_context=context,
        config=RETRIEVAL_CONFIG,
        database_path=database,
    )
    second = materialize_fpl_evidence_index(
        ledger=ledger,
        acquisition_manifests=manifests,
        approved_context=context,
        config=RETRIEVAL_CONFIG,
        database_path=database,
    )

    changed_ledger = _append(
        ledger,
        _claim(
            "rebuild",
            published_at="2026-08-14T12:00:00Z",
            observed_at="2026-08-14T12:01:00Z",
            available_at="2026-08-14T12:02:00Z",
        ),
    )
    rebuilt = materialize_fpl_evidence_index(
        ledger=changed_ledger,
        acquisition_manifests=manifests + [_manifest_for(changed_ledger["claims"][-1])],
        approved_context=context,
        config=RETRIEVAL_CONFIG,
        database_path=database,
    )

    assert first["status"] == "created"
    assert second["status"] == "unchanged"
    assert second["materialization_sha256"] == first["materialization_sha256"]
    assert rebuilt["status"] == "created"
    assert rebuilt["materialization_sha256"] != first["materialization_sha256"]
    assert json.dumps({"ledger": ledger, "manifests": manifests, "context": context}, sort_keys=True) == before


def test_materializer_rejects_unbound_or_tampered_immutable_inputs(
    tmp_path: Path,
) -> None:
    ledger = _ledger()
    manifests = [_manifest_for(row) for row in ledger["claims"]]
    tampered = deepcopy(manifests)
    tampered[0]["status"] = "rejected"

    with pytest.raises(FPLKnowledgeMaterializationError, match="not accepted"):
        materialize_fpl_evidence_index(
            ledger=ledger,
            acquisition_manifests=tampered,
            approved_context=_context(),
            config=RETRIEVAL_CONFIG,
            database_path=tmp_path / "index.sqlite",
        )
    with pytest.raises(FPLKnowledgeMaterializationError, match="not bound"):
        materialize_fpl_evidence_index(
            ledger=ledger,
            acquisition_manifests=manifests[:-1],
            approved_context=_context(),
            config=RETRIEVAL_CONFIG,
            database_path=tmp_path / "index.sqlite",
        )


def test_cutoff_scope_authority_and_lifecycle_are_filtered_before_ranking(
    tmp_path: Path,
) -> None:
    _, materialization, database = _materialized(tmp_path)

    early = retrieve_fpl_evidence_packet(
        **_request(database, materialization["materialization_sha256"], "2026-08-14T08:15:00Z")
    )
    late = retrieve_fpl_evidence_packet(
        **_request(database, materialization["materialization_sha256"], "2026-08-14T10:00:00Z")
    )

    assert [row["claim_id"] for row in early["evidence"]] == ["old"]
    assert [row["claim_id"] for row in late["evidence"]] == ["new"]
    assert late["omitted"]["future_claim_ids"] == ["future"]
    assert late["omitted"]["superseded_claim_ids"] == ["old"]
    assert late["omitted"]["expired_claim_ids"] == ["expired"]
    assert late["omitted"]["disallowed_source_claim_ids"] == ["untrusted"]
    assert late["omitted"]["out_of_scope_claim_ids"] == ["other-player"]
    assert late["retrieval_audit"]["hard_predicates_before_ranking"][-2:] == [
        "source_authority",
        "entity_scope",
    ]


def test_missing_cutoff_or_candidate_scope_fails_closed(tmp_path: Path) -> None:
    _, materialization, database = _materialized(tmp_path)
    request = _request(database, materialization["materialization_sha256"], "")
    with pytest.raises(FPLEvidenceRetrievalError, match="decision_cutoff"):
        retrieve_fpl_evidence_packet(**request)
    request = _request(
        database, materialization["materialization_sha256"], "2026-08-14T10:00:00Z"
    )
    request["entity_scope"] = {}
    with pytest.raises(FPLEvidenceRetrievalError, match="entity_scope"):
        retrieve_fpl_evidence_packet(**request)


def test_packet_is_deterministic_cited_and_agent_view_hides_audit_text(
    tmp_path: Path,
) -> None:
    _, materialization, database = _materialized(tmp_path)
    request = _request(
        database, materialization["materialization_sha256"], "2026-08-14T10:00:00Z"
    )
    first = retrieve_fpl_evidence_packet(**request)
    second = retrieve_fpl_evidence_packet(**request)
    agent = agent_visible_fpl_packet(first)

    assert first["content_sha256"] == second["content_sha256"]
    assert first["evidence"][0]["source_hash_sha256"]
    assert first["evidence"][0]["claim_id"] == "new"
    assert "retrieval_audit" not in agent
    assert "omitted" not in agent
    assert "raw_content" not in json.dumps(first, sort_keys=True)


def _scale_materialized(tmp_path: Path, count: int = 256) -> tuple[dict, Path]:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    for index in range(count):
        ledger = _append(
            ledger,
            _claim(
                f"scale-{index:03d}",
                text=f"Player scale availability note {index}.",
            ),
        )
    manifests = [_manifest_for(row) for row in ledger["claims"]]
    database = tmp_path / "scale.sqlite"
    materialization = materialize_fpl_evidence_index(
        ledger=ledger,
        acquisition_manifests=manifests,
        approved_context=_context(),
        config=RETRIEVAL_CONFIG,
        database_path=database,
    )
    return materialization, database


def test_local_lexical_retrieval_latency_is_measured_and_hash_stable(
    tmp_path: Path,
) -> None:
    materialization, database = _scale_materialized(tmp_path)
    request = _request(
        database,
        materialization["materialization_sha256"],
        "2026-08-14T10:00:00Z",
    )
    request["query_text"] = "scale player availability"
    metrics = measure_fpl_retrieval_latency(runs=20, **request)

    assert metrics["packet_hash_count"] == 1.0
    assert metrics["p50_ms"] >= 0
    assert metrics["p95_ms"] < RETRIEVAL_CONFIG["retrieval"]["maximum_packet_latency_ms"]
    assert metrics["p99_ms"] >= metrics["p95_ms"]
