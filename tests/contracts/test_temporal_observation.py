"""Contract tests for point-in-time-safe temporal observations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.data.temporal import (
    TemporalPolicyError,
    TemporalValidationError,
    normalise_observation,
    observations_as_of,
)

REPO = Path(__file__).resolve().parents[2]


def _observation(**overrides):
    value = {
        "source_id": "fpl-official-endpoints",
        "field_name": "selected_by_percent",
        "entity_id": "player:bukayo-saka",
        "source_record_id": "bootstrap-static:1",
        "observed_at": "2026-08-14T10:00:00+01:00",
        "ingested_at": "2026-08-14T09:00:30Z",
        "value": 31.4,
    }
    value.update(overrides)
    return value


def test_envelope_is_schema_valid_timezone_aware_and_content_addressed():
    first = normalise_observation(_observation())
    second = normalise_observation(dict(reversed(list(_observation().items()))))
    schema = json.loads(
        (REPO / "control/schemas/data/temporal-observation.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(first)
    assert first["observed_at"] == "2026-08-14T09:00:00Z"
    assert first["available_at"] == "2026-08-14T09:00:30Z"
    assert first["observation_id"] == second["observation_id"]


@pytest.mark.parametrize("field", ["observed_at", "ingested_at"])
def test_required_system_times_reject_naive_values(field):
    with pytest.raises(TemporalValidationError, match="timezone"):
        normalise_observation(_observation(**{field: "2026-08-14T09:00:00"}))


def test_missing_publication_time_is_preserved_and_uses_named_conservative_policy():
    record = normalise_observation(
        _observation(
            field_name="player_news",
            published_at=None,
            observed_at="2026-08-14T09:00:00Z",
            ingested_at="2026-08-14T09:05:00Z",
            value="75% chance of playing",
        )
    )
    assert record["published_at"] is None
    assert record["available_at"] == "2026-08-14T09:05:00Z"
    assert record["policy_version"] == "1.0"


def test_post_cutoff_correction_cannot_change_earlier_view():
    original = normalise_observation(_observation(value=31.4))
    correction = normalise_observation(
        _observation(
            observed_at="2026-08-14T12:00:00Z",
            ingested_at="2026-08-14T12:01:00Z",
            effective_at="2026-08-14T08:00:00Z",
            value=30.9,
            correction_of=original["observation_id"],
        )
    )
    assert observations_as_of([correction, original], "2026-08-14T11:00:00Z") == [original]
    assert observations_as_of([original, correction], "2026-08-14T13:00:00Z") == [correction]


def test_cutoff_is_inclusive_and_result_is_input_order_independent():
    included = normalise_observation(_observation())
    other = normalise_observation(_observation(entity_id="player:other", value=2.0))
    cutoff = included["available_at"]
    assert observations_as_of([included, other], cutoff) == observations_as_of(
        [other, included], cutoff
    )
    assert {row["entity_id"] for row in observations_as_of([included, other], cutoff)} == {
        "player:bukayo-saka",
        "player:other",
    }


def test_unknown_source_field_policy_fails_closed():
    with pytest.raises(TemporalPolicyError, match="No availability policy"):
        normalise_observation(_observation(field_name="unregistered_prediction"))


def test_ingestion_cannot_precede_observation():
    with pytest.raises(TemporalValidationError, match="cannot precede"):
        normalise_observation(
            _observation(
                observed_at="2026-08-14T09:01:00Z",
                ingested_at="2026-08-14T09:00:00Z",
            )
        )
