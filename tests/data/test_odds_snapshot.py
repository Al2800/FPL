"""Football-Data odds must remain deterministic and comparator-only."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.forecasting.live_capture import build_live_forecast_capture
from src.ingestion.odds_snapshot import (
    FootballDataOddsError,
    MARKET_SLOTS,
    artifact_hash,
    build_football_data_checkpoint_manifest,
    build_observed_live_snapshot,
    normalise_football_data_csv,
)
from src.ingestion.registry import load_registry


CSV = b"""Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A,PSH,PSD,PSA,AvgH,AvgD,AvgA
15/08/26,Alpha,Beta,4,1,H,2.00,4.00,4.00,2.10,3.80,3.70,2.05,3.90,3.80
16/08/26,Gamma,Delta,0,3,A,,,,1.80,3.60,5.00,1.82,3.55,4.90
17/08/26,Epsilon,Zeta,2,2,D,1.00,3.00,4.00,,,,,,
"""


def _comparator() -> dict:
    return normalise_football_data_csv(
        CSV,
        season="2026-27",
        origin="fixture://football-data/E0.csv",
        observed_at="2026-08-18T09:00:00+01:00",
        available_at="2026-08-18T09:05:00+01:00",
    )


def test_csv_is_normalised_without_outcomes_or_false_timing() -> None:
    result = _comparator()
    assert result["source_id"] == "football-data-co-uk"
    assert result["observed_at"] == "2026-08-18T08:00:00Z"
    assert result["available_at"] == "2026-08-18T08:05:00Z"
    assert result["match_count"] == 2
    assert result["rejected_count"] == 1
    assert result["matches"][0]["odds_family"] == "B365"
    assert result["matches"][1]["odds_family"] == "PS"
    assert all(
        sum(row["probabilities"].values()) == pytest.approx(1.0)
        for row in result["matches"]
    )
    assert all(
        row["timing_label"] == "source_scheduled_preclosing"
        and row["live_forecast_admissible"] is False
        for row in result["matches"]
    )
    forbidden = {"FTHG", "FTAG", "FTR", "result", "home_score", "away_score"}
    assert not any(forbidden & set(row) for row in result["matches"])
    assert result["content_sha256"] == artifact_hash(result)


def test_normalisation_is_deterministic_and_source_bound() -> None:
    first = _comparator()
    second = _comparator()
    assert second == first
    changed = normalise_football_data_csv(
        CSV.replace(b"2.00", b"2.01"),
        season="2026-27",
        origin="fixture://football-data/E0.csv",
        observed_at="2026-08-18T08:00:00Z",
        available_at="2026-08-18T08:05:00Z",
    )
    assert changed["source_sha256"] != first["source_sha256"]
    assert changed["content_sha256"] != first["content_sha256"]


def test_duplicate_fixture_and_bad_availability_fail_closed() -> None:
    duplicate = CSV + CSV.splitlines(keepends=True)[1]
    with pytest.raises(FootballDataOddsError, match="Duplicate"):
        normalise_football_data_csv(
            duplicate,
            season="2026-27",
            origin="fixture://duplicate.csv",
            observed_at="2026-08-18T08:00:00Z",
        )
    with pytest.raises(FootballDataOddsError, match="cannot be before"):
        normalise_football_data_csv(
            CSV,
            season="2026-27",
            origin="fixture://bad-time.csv",
            observed_at="2026-08-18T08:00:00Z",
            available_at="2026-08-18T07:59:59Z",
        )


def test_all_live_slots_degrade_and_comparator_is_hash_bound() -> None:
    comparator = _comparator()
    manifest = build_football_data_checkpoint_manifest(
        season="2026-27",
        decision_cutoff="2026-08-21T17:30:00Z",
        assessed_at="2026-08-18T08:05:00Z",
        comparator=comparator,
    )
    assert manifest["status"] == "degraded"
    assert manifest["required_slots"] == list(MARKET_SLOTS)
    assert [row["slot"] for row in manifest["slot_status"]] == list(MARKET_SLOTS)
    assert {row["status"] for row in manifest["slot_status"]} == {"unavailable"}
    assert {
        row["reason"] for row in manifest["slot_status"]
    } == {"source_has_no_quote_level_predeadline_timestamp"}
    assert manifest["admitted_live_snapshots"] == []
    assert manifest["comparator"]["content_sha256"] == comparator["content_sha256"]
    assert manifest["content_sha256"] == artifact_hash(manifest)

    changed = deepcopy(comparator)
    changed["match_count"] += 1
    with pytest.raises(FootballDataOddsError, match="content hash mismatch"):
        build_football_data_checkpoint_manifest(
            season="2026-27",
            decision_cutoff="2026-08-21T17:30:00Z",
            assessed_at="2026-08-18T08:05:00Z",
            comparator=changed,
        )


def test_comparator_cannot_be_relabelled_as_live() -> None:
    changed = deepcopy(_comparator())
    changed["timing_label"] = "registered_predeadline"
    changed["content_sha256"] = artifact_hash(changed)
    with pytest.raises(FootballDataOddsError, match="source_scheduled_preclosing"):
        build_football_data_checkpoint_manifest(
            season="2026-27",
            decision_cutoff="2026-08-21T17:30:00Z",
            assessed_at="2026-08-18T08:05:00Z",
            comparator=changed,
        )


def test_exact_local_observation_can_stage_a_live_predeadline_snapshot() -> None:
    comparator = normalise_football_data_csv(
        CSV,
        season="2026-27",
        origin="fixture://football-data/E0.csv",
        observed_at="2026-08-20T17:25:00Z",
        available_at="2026-08-20T17:30:00Z",
    )
    snapshot = build_observed_live_snapshot(
        comparator,
        slot="T-24h",
        decision_cutoff="2026-08-21T17:30:00Z",
    )
    assert snapshot["source_id"] == "football-data-co-uk"
    assert snapshot["slot"] == "T-24h"
    assert snapshot["payload"]["quote_type"] == "preclosing"
    assert snapshot["payload"]["source_timing"] == (
        "exact_local_observation_of_source_scheduled_quotes"
    )
    assert len(snapshot["payload"]["markets"]) == 2
    assert snapshot["lead_time_hours"] == 24.0

    capture = build_live_forecast_capture(
        bootstrap={
            "events": [{"id": 1, "deadline_time": "2026-08-21T17:30:00Z"}],
            "teams": [],
            "elements": [],
        },
        bootstrap_manifest={"content_hash_sha256": "a" * 64},
        observed_at="2026-08-20T17:25:00Z",
        decision_cutoff="2026-08-21T17:30:00Z",
        launch_context=None,
        market_snapshots=[snapshot],
        source_registry=load_registry(),
        freeze_launch=False,
    )
    assert capture["market_evidence"]["snapshots"][0]["source_id"] == (
        "football-data-co-uk"
    )

    with pytest.raises(FootballDataOddsError, match="outside the T-2h"):
        build_observed_live_snapshot(
            comparator,
            slot="T-2h",
            decision_cutoff="2026-08-21T17:30:00Z",
        )



def test_late_local_observation_cannot_stage_a_live_snapshot() -> None:
    late = normalise_football_data_csv(
        CSV,
        season="2026-27",
        origin="fixture://football-data/E0.csv",
        observed_at="2026-08-21T17:30:00Z",
    )
    with pytest.raises(FootballDataOddsError, match="strictly before"):
        build_observed_live_snapshot(
            late,
            slot="final",
            decision_cutoff="2026-08-21T17:30:00Z",
        )
