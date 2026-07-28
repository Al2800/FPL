from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.ingestion.fpl_performance_features import (
    FplPerformanceError,
    apply_fpl_performance_ablation,
    artifact_hash,
    build_fpl_performance_snapshot,
    payload_hash,
    write_immutable_json,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-fpl-performance.json").read_text()
)


def envelope(
    payload: object,
    *,
    label: str,
    observed_at: str = "2026-08-24T22:00:00Z",
) -> dict:
    return {
        "manifest_id": f"manifest:{label}",
        "source_sha256": hashlib.sha256(label.encode()).hexdigest(),
        "payload_sha256": payload_hash(payload),
        "observed_at": observed_at,
        "available_at": observed_at,
        "payload": payload,
    }


def cumulative(player_id: int, code: int, **overrides: object) -> dict:
    row = {
        "id": player_id,
        "code": code,
        "total_points": 0,
        "minutes": 0,
        "starts": 0,
        "bps": 0,
        "influence": "0.0",
        "creativity": "0.0",
        "threat": "0.0",
        "ict_index": "0.0",
        "expected_goals": "0.00",
        "expected_assists": "0.00",
        "expected_goal_involvements": "0.00",
        "defensive_contribution": 0,
        "recoveries": 0,
    }
    row.update(overrides)
    return row


def weekly(**overrides: object) -> dict:
    row = {
        "total_points": 10,
        "minutes": 170,
        "starts": 2,
        "bps": 40,
        "influence": "30.0",
        "creativity": "20.0",
        "threat": "50.0",
        "ict_index": "10.0",
        "expected_goals": "0.50",
        "expected_assists": "0.20",
        "expected_goal_involvements": "0.70",
        "defensive_contribution": 12,
        "recoveries": 8,
    }
    row.update(overrides)
    return row


def bundle() -> dict:
    before = {
        "elements": [
            cumulative(1, 101, total_points=20, minutes=270, starts=3, bps=60),
            cumulative(2, 202, total_points=15, minutes=180, starts=2, bps=45),
        ]
    }
    after = {
        "elements": [
            cumulative(
                1,
                101,
                total_points=30,
                minutes=440,
                starts=5,
                bps=100,
                influence="30.0",
                creativity="20.0",
                threat="50.0",
                ict_index="10.0",
                expected_goals="0.50",
                expected_assists="0.20",
                expected_goal_involvements="0.70",
                defensive_contribution=12,
                recoveries=8,
            ),
            cumulative(2, 202, total_points=15, minutes=180, starts=2, bps=45),
        ]
    }
    live = {
        "elements": [
            {
                "id": 1,
                "stats": weekly(),
                "explain": [{"fixture": 11, "stats": []}, {"fixture": 12, "stats": []}],
            },
            {
                "id": 2,
                "stats": weekly(
                    total_points=0,
                    minutes=0,
                    starts=0,
                    bps=0,
                    influence="0.0",
                    creativity="0.0",
                    threat="0.0",
                    ict_index="0.0",
                    expected_goals="0.00",
                    expected_assists="0.00",
                    expected_goal_involvements="0.00",
                    defensive_contribution=0,
                    recoveries=0,
                ),
                "explain": [],
            },
        ]
    }
    history = [
        {
            "round": 1,
            "fixture": 11,
            **weekly(
                total_points=4,
                minutes=90,
                starts=1,
                bps=18,
                influence="12.0",
                creativity="9.0",
                threat="20.0",
                ict_index="4.1",
                expected_goals="0.20",
                expected_assists="0.10",
                expected_goal_involvements="0.30",
                defensive_contribution=5,
                recoveries=3,
            ),
        },
        {
            "round": 1,
            "fixture": 12,
            **weekly(
                total_points=6,
                minutes=80,
                starts=1,
                bps=22,
                influence="18.0",
                creativity="11.0",
                threat="30.0",
                ict_index="5.9",
                expected_goals="0.30",
                expected_assists="0.10",
                expected_goal_involvements="0.40",
                defensive_contribution=7,
                recoveries=5,
            ),
        },
    ]
    return {
        "schema_version": "1.0",
        "season": "2026-27",
        "gameweek": 1,
        "cutoff": "2026-08-24T23:00:00Z",
        "bootstrap_before": envelope(before, label="before"),
        "bootstrap_after": envelope(after, label="after"),
        "event_live": envelope(live, label="live"),
        "element_summaries": [
            {
                "fpl_player_id": 1,
                **envelope(
                    {"history": history, "fixtures": [], "history_past": []},
                    label="summary-1",
                ),
            },
            {
                "fpl_player_id": 2,
                **envelope(
                    {"history": [], "fixtures": [], "history_past": []},
                    label="summary-2",
                ),
            },
        ],
    }


def test_doubles_blanks_and_cumulative_deltas_are_reconciled() -> None:
    result = build_fpl_performance_snapshot(bundle(), config=CONFIG)
    by_code = {row["fpl_code"]: row for row in result["players"]}

    double = by_code[101]
    assert double["fixture_count"] == 2
    assert double["fixture_ids"] == [11, 12]
    assert double["metrics"]["fpl_points"]["value"] == 10
    assert double["metrics"]["minutes"]["value"] == 170
    assert double["metrics"]["xgi"]["value"] == 0.7
    assert double["metrics"]["recoveries"]["value"] == 8
    assert all(
        row["status"] == "admitted" for row in double["metrics"].values()
    )

    blank = by_code[202]
    assert blank["fixture_count"] == 0
    assert blank["blank"] is True
    assert blank["metrics"]["fpl_points"]["value"] == 0
    assert result["content_sha256"] == artifact_hash(result)


def test_output_joins_by_stable_code_when_element_id_changes() -> None:
    source = bundle()
    source["bootstrap_before"]["payload"]["elements"][0]["id"] = 99
    source["bootstrap_before"]["payload_sha256"] = payload_hash(
        source["bootstrap_before"]["payload"]
    )
    result = build_fpl_performance_snapshot(source, config=CONFIG)
    player = next(row for row in result["players"] if row["fpl_code"] == 101)
    assert player["fpl_player_id"] == 1
    assert player["prior_fpl_player_id"] == 99


def test_schema_drift_and_disagreement_quarantine_only_affected_metric() -> None:
    source = bundle()
    source["event_live"]["payload"]["elements"][0]["stats"]["recoveries"] = "bad"
    source["event_live"]["payload"]["elements"][0]["stats"]["total_points"] = 11
    source["event_live"]["payload_sha256"] = payload_hash(
        source["event_live"]["payload"]
    )
    result = build_fpl_performance_snapshot(source, config=CONFIG)
    player = next(row for row in result["players"] if row["fpl_code"] == 101)

    assert player["status"] == "degraded"
    assert player["metrics"]["recoveries"]["status"] == "quarantined"
    assert player["metrics"]["fpl_points"]["status"] == "quarantined"
    assert player["metrics"]["minutes"]["status"] == "admitted"


def test_future_or_tampered_envelope_fails_closed() -> None:
    future = bundle()
    future["event_live"]["observed_at"] = "2026-08-25T00:00:00Z"
    future["event_live"]["available_at"] = "2026-08-25T00:00:00Z"
    with pytest.raises(FplPerformanceError, match="after cutoff"):
        build_fpl_performance_snapshot(future, config=CONFIG)

    tampered = bundle()
    tampered["event_live"]["payload"]["elements"][0]["stats"]["minutes"] = 1
    with pytest.raises(FplPerformanceError, match="payload hash"):
        build_fpl_performance_snapshot(tampered, config=CONFIG)


def test_absent_ablation_is_byte_identical_and_writer_is_immutable(
    tmp_path: Path,
) -> None:
    baseline = {"solver_input": {"players": [1, 2]}, "content_sha256": "x"}
    original = deepcopy(baseline)
    assert apply_fpl_performance_ablation(baseline, snapshot=None) == baseline
    assert baseline == original

    snapshot = build_fpl_performance_snapshot(bundle(), config=CONFIG)
    overlaid = apply_fpl_performance_ablation(baseline, snapshot=snapshot)
    assert overlaid != baseline
    assert overlaid["feature_families"]["fpl_native_performance"][
        "snapshot_sha256"
    ] == snapshot["content_sha256"]

    target = tmp_path / "snapshot.json"
    assert write_immutable_json(target, snapshot) == "created"
    assert write_immutable_json(target, snapshot) == "identical"
    changed = deepcopy(snapshot)
    changed["status"] = "changed"
    with pytest.raises(FileExistsError):
        write_immutable_json(target, changed)

