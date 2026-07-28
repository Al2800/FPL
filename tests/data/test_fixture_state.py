"""Point-in-time fixture history and blank/double Gameweek contracts."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.data.fixture_state import (
    FixtureStateError,
    build_fixture_revision_log,
    fixture_state_hash,
    fixture_view_at,
    fixture_weeks_from_view,
    load_fixture_acquisition,
    team_fixture_counts,
    write_immutable_fixture_artifact,
)


SEASON = "2026-27"


def _fixture(
    fixture_id: int,
    event: int | None,
    home: int,
    away: int,
    *,
    kickoff: str,
) -> dict[str, object]:
    return {
        "id": fixture_id,
        "event": event,
        "kickoff_time": kickoff,
        "provisional_start_time": False,
        "team_h": home,
        "team_a": away,
        "team_h_difficulty": 3,
        "team_a_difficulty": 3,
        # Outcome-capable fields exist in the endpoint but must never enter state.
        "team_h_score": 4,
        "team_a_score": 2,
        "stats": [{"identifier": "goals_scored"}],
    }


def _snapshots() -> list[dict[str, object]]:
    unchanged = [
        _fixture(
            10,
            1,
            1,
            4,
            kickoff="2026-08-15T14:00:00Z",
        ),
        _fixture(
            11,
            2,
            1,
            2,
            kickoff="2026-08-22T14:00:00Z",
        ),
        _fixture(
            12,
            3,
            1,
            3,
            kickoff="2026-08-29T14:00:00Z",
        ),
    ]
    postponed = deepcopy(unchanged)
    postponed[1]["event"] = None
    postponed[1]["kickoff_time"] = None
    rescheduled = deepcopy(postponed)
    rescheduled[1]["event"] = 3
    rescheduled[1]["kickoff_time"] = "2026-08-30T14:00:00Z"
    return [
        {
            "snapshot_id": "s1",
            "observed_at": "2026-07-01T09:00:00Z",
            "available_at": "2026-07-01T09:00:00Z",
            "fixtures": unchanged,
        },
        {
            "snapshot_id": "s2",
            "observed_at": "2026-07-08T09:00:00Z",
            "available_at": "2026-07-08T09:00:00Z",
            "fixtures": postponed,
        },
        {
            "snapshot_id": "s3",
            "observed_at": "2026-07-15T09:00:00Z",
            "available_at": "2026-07-15T09:00:00Z",
            "fixtures": rescheduled,
        },
    ]


def _count(
    table: dict,
    *,
    gameweek: int,
    team_id: int,
) -> dict:
    return next(
        row
        for row in table["rows"]
        if row["gameweek"] == gameweek and row["team_id"] == team_id
    )


def test_cutoffs_reconstruct_original_blank_and_double_schedules() -> None:
    revision_log = build_fixture_revision_log(_snapshots(), season=SEASON)

    original = fixture_view_at(
        revision_log,
        cutoff="2026-07-01T09:00:00Z",
    )
    postponed = fixture_view_at(
        revision_log,
        cutoff="2026-07-08T09:00:00Z",
    )
    rescheduled = fixture_view_at(
        revision_log,
        cutoff="2026-07-15T09:00:00Z",
    )
    original_counts = team_fixture_counts(
        original,
        gameweeks=[2, 3],
    )
    postponed_counts = team_fixture_counts(
        postponed,
        gameweeks=[2, 3],
    )
    rescheduled_counts = team_fixture_counts(
        rescheduled,
        gameweeks=[2, 3],
    )

    assert _count(original_counts, gameweek=2, team_id=1)["classification"] == "single"
    assert _count(postponed_counts, gameweek=2, team_id=1) == {
        "gameweek": 2,
        "team_id": 1,
        "fixture_count": 0,
        "classification": "blank",
        "fixture_ids": [],
    }
    assert _count(rescheduled_counts, gameweek=3, team_id=1) == {
        "gameweek": 3,
        "team_id": 1,
        "fixture_count": 2,
        "classification": "double",
        "fixture_ids": [11, 12],
    }
    fixture_11_changes = [
        row["change_type"]
        for row in revision_log["revisions"]
        if row["fixture_uid"] == f"fixture:{SEASON}:11"
    ]
    assert fixture_11_changes == ["created", "postponed", "rescheduled"]
    assert all(
        "team_h_score" not in row["payload"]["state"]
        for row in revision_log["revisions"]
        if row["payload"]["state"] is not None
    )


def test_fixture_weeks_bind_counts_and_revision_lineage() -> None:
    revision_log = build_fixture_revision_log(_snapshots(), season=SEASON)
    view = fixture_view_at(
        revision_log,
        cutoff="2026-07-15T09:00:00Z",
    )
    weeks = fixture_weeks_from_view(
        view,
        gameweeks=[2, 3],
        team_ids=[1, 2, 3, 4],
    )

    assert weeks[0]["team_fixture_counts"][f"team:{SEASON}:1"] == 0
    assert weeks[1]["team_fixture_counts"][f"team:{SEASON}:1"] == 2
    assert len(weeks[1]["fixtures"]) == 2
    assert weeks[1]["fixture_state_sha256"] == view["content_sha256"]
    assert weeks[1]["schedule_provenance"]["revision_log_sha256"] == (
        revision_log["content_sha256"]
    )


def test_ambiguous_same_available_at_snapshots_are_refused() -> None:
    snapshots = _snapshots()[:2]
    snapshots[1]["available_at"] = snapshots[0]["available_at"]
    snapshots[1]["observed_at"] = snapshots[0]["observed_at"]
    with pytest.raises(FixtureStateError, match="order is ambiguous"):
        build_fixture_revision_log(snapshots, season=SEASON)


def test_acquisition_hash_and_immutable_derived_artifact(tmp_path: Path) -> None:
    body = json.dumps(_snapshots()[0]["fixtures"]).encode("utf-8")
    body_path = tmp_path / "api_fixtures.json"
    body_path.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    manifest = {
        "manifest_id": "manifest-1",
        "source_id": "fpl-official-endpoints",
        "observed_at": "2026-07-01T09:00:00Z",
        "acquisition_status": "success",
        "content_hash_sha256": digest,
        "body_file": body_path.name,
    }
    manifest_path = tmp_path / "api_fixtures.meta.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = load_fixture_acquisition(body_path)
    revision_log = build_fixture_revision_log([loaded], season=SEASON)
    output = tmp_path / "derived" / "fixture-revisions.json"
    write_immutable_fixture_artifact(output, revision_log)
    write_immutable_fixture_artifact(output, revision_log)

    later = build_fixture_revision_log(_snapshots(), season=SEASON)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_immutable_fixture_artifact(output, later)

    body_path.write_bytes(body + b"\n")
    with pytest.raises(FixtureStateError, match="content hash mismatch"):
        load_fixture_acquisition(body_path, manifest_path=manifest_path)


def test_cutoff_and_hash_guards_fail_closed() -> None:
    revision_log = build_fixture_revision_log(_snapshots(), season=SEASON)
    with pytest.raises(FixtureStateError, match="no fixture snapshot"):
        fixture_view_at(
            revision_log,
            cutoff="2026-06-30T23:59:59Z",
        )

    tampered = deepcopy(revision_log)
    tampered["revisions"][0]["change_type"] = "invented"
    assert fixture_state_hash(tampered) != tampered["content_sha256"]
    with pytest.raises(FixtureStateError, match="content hash mismatch"):
        fixture_view_at(
            tampered,
            cutoff="2026-07-15T09:00:00Z",
        )
