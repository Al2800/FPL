from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    live_evidence_hash,
    new_live_evidence_ledger,
)
from src.forecasting.live_faithful import artifact_hash
from src.orchestration.evidence_checkpoint_runner import (
    EvidenceCheckpointConflict,
    EvidenceCheckpointError,
    derive_deadline_checkpoints,
    new_checkpoint_head,
    run_evidence_checkpoint,
)


ROOT = Path(__file__).resolve().parents[2]
COVERAGE = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence-coverage.json").read_text()
)
EVIDENCE = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence.json").read_text()
)
REGISTRY = yaml.safe_load(
    (ROOT / "control/sources/source-registry.yaml").read_text()
)


_FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "candidate_boundary_fixture",
    ROOT / "tests/evidence/test_candidate_boundary_retrieval.py",
)
assert _FIXTURE_SPEC is not None and _FIXTURE_SPEC.loader is not None
_FIXTURE_MODULE = importlib.util.module_from_spec(_FIXTURE_SPEC)
_FIXTURE_SPEC.loader.exec_module(_FIXTURE_MODULE)
engine = _FIXTURE_MODULE.engine

def official_claim(
    claim_id: str,
    *,
    status: str,
    available_at: str,
) -> dict:
    return {
        "claim_id": claim_id,
        "source_id": "fpl-official-endpoints",
        "document_id": f"doc:{claim_id}",
        "source_url": "https://fantasy.premierleague.com/api/bootstrap-static/",
        "source_hash_sha256": hashlib.sha256(claim_id.encode()).hexdigest(),
        "claim_text": f"Official availability is {status}.",
        "claim_precision": "structured_fact",
        "claim_type": "player_availability",
        "value": {"status": status},
        "confidence": 1.0,
        "published_at": "2026-08-14T08:00:00Z",
        "observed_at": "2026-08-14T08:05:00Z",
        "available_at": available_at,
        "expires_at": "2026-08-15T08:06:00Z",
        "identity_bindings": [
            {
                "entity_type": "player_uid",
                "stable_id": "q1",
                "source_label": "q1",
                "match_status": "exact",
            }
        ],
        "decision_boundary_ids": [],
        "estimated_impact_points": 6.0,
        "supersedes_claim_ids": [],
    }


def capture_result(*claims: dict, status: str = "complete") -> dict:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    for row in claims:
        ledger = append_live_evidence_claim(
            ledger,
            row,
            source_registry=REGISTRY,
            config=EVIDENCE,
        )
    manifest = {
        "manifest_id": "acq:" + hashlib.sha256(status.encode()).hexdigest(),
        "content_hash_sha256": hashlib.sha256(b"bootstrap").hexdigest(),
        "acquisition_status": "success",
    }
    return {
        "status": status,
        "observed_at": "2026-08-14T10:00:00Z",
        "document_count": 1,
        "raw_claim_count": len(claims),
        "claim_count_added": len(claims),
        "observed_player_ids": ["q1"],
        "degraded_reasons": (
            [] if status == "complete" else ["fixtures_transport_error"]
        ),
        "endpoint_captures": [
            {
                "endpoint_id": "bootstrap-static",
                "status": "complete",
                "acquisition": manifest,
            },
            {
                "endpoint_id": "fixtures",
                "status": status,
                "acquisition": None if status != "complete" else manifest,
            },
        ],
        "ledger": ledger,
        "frozen_no_evidence_control_preserved": True,
        "account_writes": False,
    }


def run(
    tmp_path: Path,
    *,
    ledger: dict,
    adapter,
    expected_head_sha256: str,
    checkpoint_id: str = "T-48h",
    manual_observations: dict | None = None,
    manual_claims: dict | None = None,
) -> dict:
    solver_input, solver_output = engine()
    return run_evidence_checkpoint(
        season="2026-27",
        gameweek=1,
        checkpoint_id=checkpoint_id,
        decision_at="2026-08-14T10:00:00Z",
        current_ledger=ledger,
        solver_input=solver_input,
        solver_output=solver_output,
        coverage_config=COVERAGE,
        evidence_config=EVIDENCE,
        source_registry=REGISTRY,
        automated_adapters={"fpl-official-endpoints": adapter},
        manual_observations=manual_observations or {},
        manual_claims=manual_claims or {},
        expected_club_ids=["club:a", "club:b", "club:c", "club:d"],
        expected_player_ids=["p1", "p2", "p3", "q1", "q2"],
        accepted_adjustments=[],
        head_path=tmp_path / "head.json",
        checkpoint_dir=tmp_path / "checkpoints",
        expected_head_sha256=expected_head_sha256,
    )


def write_head(path: Path, head: dict) -> None:
    path.write_text(json.dumps(head, indent=2, sort_keys=True) + "\n")


def test_deadline_schedule_uses_exact_official_event_timestamp() -> None:
    schedule = derive_deadline_checkpoints(
        {
            "events": [
                {
                    "id": 1,
                    "deadline_time": "2026-08-21T17:30:00Z",
                }
            ]
        },
        gameweek=1,
    )

    assert schedule == {
        "T-48h": "2026-08-19T17:30:00Z",
        "T-24h": "2026-08-20T17:30:00Z",
        "T-8h": "2026-08-21T09:30:00Z",
        "T-2h": "2026-08-21T15:30:00Z",
        "final_pre_deadline": "2026-08-21T17:25:00Z",
    }


def test_restart_is_idempotent_and_stale_different_writer_is_refused(
    tmp_path: Path,
) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)
    calls = 0

    def adapter() -> dict:
        nonlocal calls
        calls += 1
        return capture_result(
            official_claim(
                "official-v1", status="doubtful",
                available_at="2026-08-14T08:06:00Z",
            )
        )

    first = run(
        tmp_path,
        ledger=ledger,
        adapter=adapter,
        expected_head_sha256=head["content_sha256"],
    )
    assert calls == 1
    assert first["content_sha256"] == artifact_hash(first)
    assert first["bindings"]["packet_sha256"] == artifact_hash(first["packet"])
    assert first["bindings"]["coverage_audit_sha256"] == artifact_hash(
        first["coverage_audit"]
    )

    second = run(
        tmp_path,
        ledger=first["ledger_after"],
        adapter=adapter,
        expected_head_sha256=head["content_sha256"],
    )
    assert second == first
    assert calls == 1

    solver_input, solver_output = engine()
    solver_input = deepcopy(solver_input)
    solver_input["gameweek"] = 2
    with pytest.raises(EvidenceCheckpointConflict, match="stale checkpoint head"):
        run_evidence_checkpoint(
            season="2026-27",
            gameweek=2,
            checkpoint_id="T-48h",
            decision_at="2026-08-14T10:00:00Z",
            current_ledger=first["ledger_after"],
            solver_input=solver_input,
            solver_output=solver_output,
            coverage_config=COVERAGE,
            evidence_config=EVIDENCE,
            source_registry=REGISTRY,
            automated_adapters={
                "fpl-official-endpoints": lambda: pytest.fail(
                    "stale writer called adapter"
                )
            },
            manual_observations={},
            manual_claims={},
            expected_club_ids=[],
            expected_player_ids=[],
            accepted_adjustments=[],
            head_path=tmp_path / "head.json",
            checkpoint_dir=tmp_path / "checkpoints",
            expected_head_sha256=head["content_sha256"],
        )


def test_new_same_source_claim_supersedes_prior_subject(tmp_path: Path) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    ledger = append_live_evidence_claim(
        ledger,
        official_claim(
            "official-v1",
            status="doubtful",
            available_at="2026-08-14T08:06:00Z",
        ),
        source_registry=REGISTRY,
        config=EVIDENCE,
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)

    result = run(
        tmp_path,
        ledger=ledger,
        adapter=lambda: capture_result(
            official_claim(
                "official-v2",
                status="available",
                available_at="2026-08-14T09:06:00Z",
            )
        ),
        expected_head_sha256=head["content_sha256"],
    )

    claims = {row["claim_id"]: row for row in result["ledger_after"]["claims"]}
    assert claims["official-v2"]["supersedes_claim_ids"] == ["official-v1"]
    assert [row["claim_id"] for row in result["evidence_view"]["accepted"]] == [
        "official-v2"
    ]
    assert [
        row["claim_id"]
        for row in result["evidence_view"]["excluded"]["superseded"]
    ] == ["official-v1"]


def test_manual_claim_requires_matching_real_citation(tmp_path: Path) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)

    with pytest.raises(EvidenceCheckpointError, match="source_hash_sha256"):
        run(
            tmp_path,
            ledger=ledger,
            adapter=lambda: capture_result(),
            expected_head_sha256=head["content_sha256"],
            manual_observations={
                "official_club_news": [
                    {
                        "document_id": "missing-hash",
                        "source_url": "https://club.example/news",
                        "observed_at": "2026-08-14T09:00:00Z",
                        "claim_count": 0,
                    }
                ]
            },
        )


def test_partial_failure_keeps_successful_claim_and_manifest(tmp_path: Path) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)

    result = run(
        tmp_path,
        ledger=ledger,
        adapter=lambda: capture_result(
            official_claim(
                "partial-v1",
                status="doubtful",
                available_at="2026-08-14T08:06:00Z",
            ),
            status="degraded",
        ),
        expected_head_sha256=head["content_sha256"],
    )

    assert result["status"] == "degraded"
    assert result["bindings"]["acquisition_manifest_ids"]
    assert result["bindings"]["claim_ids_added"] == ["partial-v1"]
    assert result["ledger_after"]["content_sha256"] != (
        result["bindings"]["ledger_before_sha256"]
    )
    assert result["frozen_no_evidence_control_preserved"] is True
    assert result["account_writes"] is False
    assert result["content_sha256"] == artifact_hash(result)


def test_approved_odds_sidecar_is_bound_without_becoming_a_claim(
    tmp_path: Path,
) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)
    solver_input, solver_output = engine()
    odds = {
        "schema_version": "1.0",
        "provider": "the-odds-api",
        "status": "complete",
        "degraded_reasons": [],
        "acquisition": {
            "manifest_id": "odds:manifest:1",
            "content_hash_sha256": hashlib.sha256(b"odds").hexdigest(),
            "acquisition_status": "success",
        },
        "snapshot": {"slot": "T-24h"},
        "account_writes": False,
    }
    odds["content_sha256"] = artifact_hash(odds)

    result = run_evidence_checkpoint(
        season="2026-27",
        gameweek=1,
        checkpoint_id="T-24h",
        decision_at="2026-08-14T10:00:00Z",
        current_ledger=ledger,
        solver_input=solver_input,
        solver_output=solver_output,
        coverage_config=COVERAGE,
        evidence_config=EVIDENCE,
        source_registry=REGISTRY,
        automated_adapters={
            "fpl-official-endpoints": lambda: capture_result()
        },
        supplemental_adapters={"the-odds-api": lambda: odds},
        manual_observations={},
        manual_claims={},
        expected_club_ids=[],
        expected_player_ids=[],
        accepted_adjustments=[],
        head_path=tmp_path / "head.json",
        checkpoint_dir=tmp_path / "checkpoints",
        expected_head_sha256=head["content_sha256"],
    )

    assert result["bindings"]["supplemental_capture_sha256"] == {
        "the-odds-api": odds["content_sha256"]
    }
    assert "odds:manifest:1" in result["bindings"][
        "acquisition_manifest_ids"
    ]

def test_reported_account_write_refuses_without_advancing_head(
    tmp_path: Path,
) -> None:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    head = new_checkpoint_head(
        season="2026-27", ledger_sha256=ledger["content_sha256"]
    )
    write_head(tmp_path / "head.json", head)

    def unsafe_adapter() -> dict:
        capture = capture_result()
        capture["account_writes"] = True
        return capture

    with pytest.raises(EvidenceCheckpointError, match="account write"):
        run(
            tmp_path,
            ledger=ledger,
            adapter=unsafe_adapter,
            expected_head_sha256=head["content_sha256"],
        )

    unchanged = json.loads((tmp_path / "head.json").read_text())
    assert unchanged == head
    assert not (tmp_path / "checkpoints").exists()
