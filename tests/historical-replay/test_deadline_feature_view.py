"""Historical-replay tests for deadline-safe feature materialisation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.data.quality import evaluate_quality
from src.data.temporal import normalise_observation
from src.features.deadline_view import FeatureViewError, materialise_deadline_view

REPO = Path(__file__).resolve().parents[2]
CUTOFF = "2026-08-14T11:00:00Z"
FPL_SNAPSHOT = "a" * 64
RESULTS_SNAPSHOT = "c" * 64


def _observation(source_id, field_name, entity_id, value, observed_at="2026-08-14T09:00:00Z"):
    return normalise_observation(
        {
            "source_id": source_id,
            "field_name": field_name,
            "entity_id": entity_id,
            "source_record_id": f"{source_id}:{entity_id}",
            "observed_at": observed_at,
            "ingested_at": observed_at,
            "value": value,
        }
    )


def _identity(rate=1.0):
    return {
        "metrics": {
            "total": 100,
            "resolved": int(100 * rate),
            "review": 0,
            "unresolved": 100 - int(100 * rate),
            "match_rate": rate,
        }
    }


def _quality_report(
    source_id,
    records,
    snapshot_id,
    evaluated_at="2026-08-14T10:00:00Z",
    identity_rate=1.0,
):
    return evaluate_quality(
        source_id=source_id,
        records=records,
        evaluation_at=evaluated_at,
        acquisition_manifest={
            "manifest_id": snapshot_id,
            "source_id": source_id,
            "observed_at": records[0]["observed_at"],
            "acquisition_status": "success",
            "content_hash_sha256": "b" * 64,
        },
        actual_content_hash="b" * 64,
        identity_report=_identity(identity_rate),
        expected_entity_ids=[record["entity_id"] for record in records],
        mode="enforce",
    )


def _worked_inputs(include_fpl_fixture=True):
    ownership = _observation(
        "fpl-official-endpoints", "selected_by_percent", "player:a", 31.4
    )
    fpl_fixture = _observation(
        "fpl-official-endpoints",
        "fixture",
        "fixture:1",
        {"home": "team:a", "away": "team:b", "finished": True, "home_score": 2, "away_score": 1},
    )
    result = _observation(
        "football-data-co-uk",
        "match_result",
        "fixture:1",
        {"home": "team:a", "away": "team:b", "home_score": 2, "away_score": 1},
    )
    fpl_records = [ownership, fpl_fixture] if include_fpl_fixture else [ownership]
    observations = [*fpl_records, result]
    reports = [
        _quality_report("fpl-official-endpoints", fpl_records, FPL_SNAPSHOT),
        _quality_report("football-data-co-uk", [result], RESULTS_SNAPSHOT),
    ]
    snapshots = {
        **{record["observation_id"]: FPL_SNAPSHOT for record in fpl_records},
        result["observation_id"]: RESULTS_SNAPSHOT,
    }
    return observations, reports, snapshots


def _materialise(observations, reports, snapshots, expected_entities=None):
    return materialise_deadline_view(
        episode_id="episode:2026-27:gw1",
        cutoff=CUTOFF,
        observations=observations,
        quality_reports=reports,
        observation_snapshot_ids=snapshots,
        expected_entities=expected_entities
        or {
            "ownership_percent": ["player:a"],
            "fixture_state": ["fixture:1"],
            "external_match_result": ["fixture:1"],
        },
    )


def test_fpl_and_results_produce_schema_valid_stable_lineage_manifest():
    observations, reports, snapshots = _worked_inputs()
    first = _materialise(observations, reports, snapshots)
    second = _materialise(list(reversed(observations)), list(reversed(reports)), snapshots)
    schema = json.loads(
        (REPO / "control/schemas/data/feature-view-manifest.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(first)
    assert first["status"] == "complete"
    assert first["feature_view_id"] == second["feature_view_id"]
    assert len(first["features"]) == 3
    fixture = next(row for row in first["features"] if row["feature_name"] == "fixture_state")
    assert fixture["source_id"] == "fpl-official-endpoints"
    assert fixture["selection_method"] == "preferred_source"
    assert {row["snapshot_id"] for row in first["features"]} == {
        FPL_SNAPSHOT,
        RESULTS_SNAPSHOT,
    }
    assert {row["quality_mode"] for row in first["quality_reports"]} == {"enforce"}
    assert {row["quality_policy_version"] for row in first["quality_reports"]} == {"1.0"}


def test_missing_preferred_source_uses_explicit_fallback_and_records_degradation():
    observations, reports, snapshots = _worked_inputs(include_fpl_fixture=False)
    view = _materialise(
        observations,
        reports,
        snapshots,
        {
            "ownership_percent": ["player:a"],
            "fixture_state": ["fixture:1"],
        },
    )
    fixture = next(row for row in view["features"] if row["feature_name"] == "fixture_state")
    assert fixture["source_id"] == "football-data-co-uk"
    assert fixture["selection_method"] == "fallback_source"
    assert view["status"] == "degraded"
    assert view["degraded_features"][0]["reason"] == "fallback_source"


def test_missing_optional_feature_is_recorded_without_imputation():
    observations, reports, snapshots = _worked_inputs()
    view = _materialise(
        observations,
        reports,
        snapshots,
        {
            "ownership_percent": ["player:a"],
            "fixture_state": ["fixture:1"],
            "player_status": ["player:a"],
        },
    )
    assert not any(row["feature_name"] == "player_status" for row in view["features"])
    missing = next(row for row in view["degraded_features"] if row["feature_name"] == "player_status")
    assert missing["reason"] == "missing_optional_feature"
    assert missing["selected_source_id"] is None


def test_later_correction_and_quality_report_cannot_change_earlier_frozen_view():
    observations, reports, snapshots = _worked_inputs()
    original = _materialise(observations, reports, snapshots)
    correction = _observation(
        "fpl-official-endpoints",
        "selected_by_percent",
        "player:a",
        33.0,
        observed_at="2026-08-14T12:00:00Z",
    )
    later_snapshot = "d" * 64
    later_report = _quality_report(
        "fpl-official-endpoints",
        [correction],
        later_snapshot,
        evaluated_at="2026-08-14T12:30:00Z",
    )
    augmented = _materialise(
        [*observations, correction],
        [*reports, later_report],
        {**snapshots, correction["observation_id"]: later_snapshot},
    )
    assert augmented == original


def test_quarantined_conflicts_cannot_enter_view_but_safe_records_and_fallback_can():
    ownership = _observation(
        "fpl-official-endpoints", "selected_by_percent", "player:a", 31.4
    )
    first = _observation(
        "fpl-official-endpoints", "fixture", "fixture:1", {"home_score": 2, "away_score": 1}
    )
    conflict = _observation(
        "fpl-official-endpoints", "fixture", "fixture:1", {"home_score": 3, "away_score": 1}
    )
    result = _observation(
        "football-data-co-uk", "match_result", "fixture:1", {"home_score": 2, "away_score": 1}
    )
    fpl_report = _quality_report(
        "fpl-official-endpoints", [ownership, first, conflict], FPL_SNAPSHOT
    )
    result_report = _quality_report(
        "football-data-co-uk", [result], RESULTS_SNAPSHOT
    )
    snapshots = {
        ownership["observation_id"]: FPL_SNAPSHOT,
        first["observation_id"]: FPL_SNAPSHOT,
        conflict["observation_id"]: FPL_SNAPSHOT,
        result["observation_id"]: RESULTS_SNAPSHOT,
    }
    view = _materialise(
        [ownership, first, conflict, result],
        [fpl_report, result_report],
        snapshots,
        {"ownership_percent": ["player:a"], "fixture_state": ["fixture:1"]},
    )
    assert ownership["observation_id"] in view["included_observation_ids"]
    assert first["observation_id"] not in view["included_observation_ids"]
    assert conflict["observation_id"] not in view["included_observation_ids"]
    fixture = next(row for row in view["features"] if row["feature_name"] == "fixture_state")
    assert fixture["source_id"] == "football-data-co-uk"


def test_wholly_quarantined_required_source_fails_closed():
    observations, reports, snapshots = _worked_inputs()
    fpl_records = [row for row in observations if row["source_id"] == "fpl-official-endpoints"]
    blocked = _quality_report(
        "fpl-official-endpoints", fpl_records, FPL_SNAPSHOT, identity_rate=0.99
    )
    with pytest.raises(FeatureViewError, match="ownership_percent:player:a"):
        _materialise(
            observations,
            [blocked, reports[1]],
            snapshots,
            {"ownership_percent": ["player:a"], "fixture_state": ["fixture:1"]},
        )


def test_unknown_feature_scope_fails_closed_instead_of_being_ignored():
    observations, reports, snapshots = _worked_inputs()
    with pytest.raises(FeatureViewError, match="Unknown feature scopes"):
        _materialise(
            observations,
            reports,
            snapshots,
            {
                "ownership_percent": ["player:a"],
                "fixture_state": ["fixture:1"],
                "typo_feature": ["player:a"],
            },
        )


def test_equally_timed_competing_quality_reports_fail_as_ambiguous():
    observations, reports, snapshots = _worked_inputs()
    competing = dict(reports[0])
    competing["report_id"] = "e" * 64
    with pytest.raises(FeatureViewError, match="Ambiguous quality reports"):
        _materialise(observations, [*reports, competing], snapshots)


def test_unrelated_quality_report_cannot_change_the_requested_view():
    observations, reports, snapshots = _worked_inputs()
    original = _materialise(observations, reports, snapshots)
    unrelated = dict(reports[0])
    unrelated["source_id"] = "unrelated-source"
    unrelated["report_id"] = "f" * 64
    augmented = _materialise(observations, [*reports, unrelated], snapshots)
    assert augmented == original
