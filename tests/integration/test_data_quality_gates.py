"""Integration tests for staged data-quality decisions and scoped quarantine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.data.quality import (
    DataQualityError,
    QuarantinedDataError,
    evaluate_quality,
    require_admissible,
)
from src.data.temporal import normalise_observation

REPO = Path(__file__).resolve().parents[2]


def _record(entity_id: str = "player:a", value=10.0, **overrides):
    observation = {
        "source_id": "fpl-official-endpoints",
        "field_name": "selected_by_percent",
        "entity_id": entity_id,
        "source_record_id": entity_id,
        "observed_at": "2026-08-14T09:00:00Z",
        "ingested_at": "2026-08-14T09:00:30Z",
        "value": value,
    }
    observation.update(overrides)
    return normalise_observation(observation)


def _manifest(source_id: str = "fpl-official-endpoints", **overrides):
    manifest = {
        "manifest_id": "a" * 64,
        "source_id": source_id,
        "observed_at": "2026-08-14T09:00:00Z",
        "acquisition_status": "success",
        "content_hash_sha256": "b" * 64,
    }
    manifest.update(overrides)
    return manifest


def _identity(rate: float = 1.0):
    total = 100
    resolved = int(total * rate)
    return {
        "metrics": {
            "total": total,
            "resolved": resolved,
            "review": 0,
            "unresolved": total - resolved,
            "match_rate": rate,
        }
    }


def _evaluate(records, **overrides):
    values = {
        "source_id": "fpl-official-endpoints",
        "records": records,
        "evaluation_at": "2026-08-14T10:00:00Z",
        "acquisition_manifest": _manifest(),
        "actual_content_hash": "b" * 64,
        "identity_report": _identity(),
        "expected_entity_ids": [record["entity_id"] for record in records if record.get("entity_id")],
    }
    values.update(overrides)
    return evaluate_quality(**values)


def _check(report, check_id):
    return next(check for check in report["checks"] if check["check_id"] == check_id)


def test_healthy_report_is_schema_valid_and_order_independent():
    records = [_record("player:a"), _record("player:b")]
    first = _evaluate(records)
    second = _evaluate(list(reversed(records)))
    schema = json.loads(
        (REPO / "control/schemas/data/data-quality-report.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(first)
    assert first["recommended_disposition"] == "pass"
    assert first["enforced_disposition"] == "pass"
    assert first["report_id"] == second["report_id"]


def test_exact_duplicates_are_measured_and_collapsed_without_quarantine():
    record = _record()
    report = _evaluate([record, record], expected_entity_ids=["player:a"])
    assert report["metrics"]["exact_duplicate_count"] == 1
    assert report["metrics"]["exact_duplicate_rate"] == 0.5
    assert _check(report, "duplicates.exact")["status"] == "warn"
    assert report["recommended_disposition"] == "pass"
    assert report["admitted_observation_ids"] == [record["observation_id"]]


def test_equivalent_key_value_duplicates_collapse_without_being_quarantined():
    first = _record(source_record_id="capture:a")
    equivalent = _record(source_record_id="capture:b")
    report = _evaluate([equivalent, first], expected_entity_ids=["player:a"])
    kept = min(first["observation_id"], equivalent["observation_id"])
    assert report["metrics"]["exact_duplicate_count"] == 0
    assert report["metrics"]["equivalent_duplicate_count"] == 1
    assert report["metrics"]["deduplicated_record_count"] == 1
    assert report["metrics"]["quarantined_record_count"] == 0
    assert report["admitted_observation_ids"] == [kept]
    assert _check(report, "duplicates.equivalent")["status"] == "warn"


def test_conflicts_are_observed_shadowed_then_enforced_at_record_scope():
    first = _record("player:a", 10.0)
    conflict = _record("player:a", 11.0)
    safe = _record("player:b", 5.0)

    observe = _evaluate([first, conflict, safe], mode="observe_only")
    shadow = _evaluate([first, conflict, safe], mode="shadow")
    enforced = _evaluate([first, conflict, safe], mode="enforce")

    assert observe["recommended_disposition"] == "quarantine"
    assert observe["enforced_disposition"] == "pass"
    assert shadow["admissible"] is True
    assert all(not item["enforced"] for item in shadow["quarantine"])
    assert enforced["enforced_disposition"] == "quarantine"
    assert enforced["admitted_observation_ids"] == [safe["observation_id"]]
    assert enforced["admissible"] is True
    require_admissible(enforced, [safe["observation_id"]])
    with pytest.raises(QuarantinedDataError, match="quarantined"):
        require_admissible(enforced, [first["observation_id"]])


def test_bad_schema_quarantines_only_the_bad_record_when_a_safe_record_remains():
    bad = _record("player:a")
    del bad["field_name"]
    safe = _record("player:b")
    report = _evaluate([bad, safe], mode="enforce")
    assert report["metrics"]["schema_error_count"] == 1
    assert report["admitted_observation_ids"] == [safe["observation_id"]]
    assert report["admissible"] is True


def test_required_source_hash_mismatch_stops_the_snapshot_in_enforce_mode():
    record = _record()
    report = _evaluate([record], mode="enforce", actual_content_hash="c" * 64)
    assert _check(report, "acquisition.integrity")["status"] == "fail"
    assert report["recommended_disposition"] == "stop"
    assert report["enforced_disposition"] == "stop"
    assert report["admitted_observation_ids"] == []
    assert report["admissible"] is False


def test_freshness_and_coverage_are_measured_but_not_initially_hard_enforced():
    record = _record()
    report = _evaluate(
        [record],
        mode="enforce",
        evaluation_at="2026-08-15T10:00:00Z",
        expected_entity_ids=["player:a", "player:b"],
    )
    assert report["metrics"]["coverage_rate"] == 0.5
    assert report["metrics"]["staleness_seconds"] == 90000.0
    assert report["recommended_disposition"] == "quarantine"
    assert report["enforced_disposition"] == "pass"
    assert report["admissible"] is True


def test_identity_failure_is_a_hard_partition_gate_for_required_fpl_data():
    records = [_record("player:a"), _record("player:b")]
    report = _evaluate(records, mode="enforce", identity_report=_identity(0.99))
    assert _check(report, "identity.match_rate")["recommended_disposition"] == "quarantine"
    assert report["admitted_observation_ids"] == []
    assert report["admissible"] is False
    with pytest.raises(QuarantinedDataError, match="not admissible"):
        require_admissible(report)


def test_cross_source_disagreement_preserves_claim_lineage_and_degrades():
    record = _record()
    reconciliation = {
        "entity_id": "fixture:1",
        "field_name": "home_score",
        "claims": [
            {"source_id": "fpl-official-endpoints", "observation_id": "fpl-1", "value": 2},
            {"source_id": "football-data-co-uk", "observation_id": "fd-1", "value": 1},
        ],
    }
    report = _evaluate([record], reconciliations=[reconciliation], mode="enforce")
    assert report["recommended_disposition"] == "degrade"
    assert report["enforced_disposition"] == "pass"
    assert report["metrics"]["disagreement_rate"] == 1.0
    assert {
        claim["source_id"]: (claim["observation_id"], claim["value"])
        for claim in report["disagreements"][0]["claims"]
    } == {
        "fpl-official-endpoints": ("fpl-1", 2),
        "football-data-co-uk": ("fd-1", 1),
    }


def test_optional_source_failure_degrades_without_stopping_the_episode():
    record = normalise_observation(
        {
            "source_id": "football-data-co-uk",
            "field_name": "match_result",
            "entity_id": "fixture:1",
            "source_record_id": "row:1",
            "observed_at": "2026-08-14T09:00:00Z",
            "ingested_at": "2026-08-14T09:01:00Z",
            "value": {"home": 2, "away": 1},
        }
    )
    report = evaluate_quality(
        source_id="football-data-co-uk",
        records=[record],
        evaluation_at="2026-08-14T10:00:00Z",
        acquisition_manifest=_manifest(
            source_id="football-data-co-uk", acquisition_status="transport_error"
        ),
        identity_report=_identity(0.97),
        expected_entity_ids=["fixture:1", "fixture:2"],
        mode="enforce",
    )
    assert report["required_source"] is False
    assert report["recommended_disposition"] == "degrade"
    assert report["enforced_disposition"] == "pass"
    assert report["admissible"] is True


def test_unknown_source_has_no_permissive_default():
    with pytest.raises(DataQualityError, match="No data-quality policy"):
        evaluate_quality(
            source_id="unknown-source",
            records=[],
            evaluation_at="2026-08-14T10:00:00Z",
            acquisition_manifest=None,
        )
