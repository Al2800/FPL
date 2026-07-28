"""Cutoff-safe event-sourced fixture schedules for blank/double detection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from src.data.temporal import parse_aware_datetime


class FixtureStateError(ValueError):
    """Raised when fixture history is ambiguous, corrupt, or not cutoff-safe."""


SCHEDULE_FIELDS = (
    "id",
    "event",
    "kickoff_time",
    "provisional_start_time",
    "team_h",
    "team_a",
    "team_h_difficulty",
    "team_a_difficulty",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def fixture_state_hash(value: Mapping[str, Any]) -> str:
    """Hash a fixture artifact without its circular content-hash field."""

    return _fingerprint(
        {
            key: deepcopy(item)
            for key, item in value.items()
            if key != "content_sha256"
        }
    )


def _canonical_timestamp(value: Any, *, field: str) -> str:
    parsed = parse_aware_datetime(str(value), field=field).astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise FixtureStateError(f"{field} must be a positive integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise FixtureStateError(f"{field} must be a positive integer") from exc
    if result < 1:
        raise FixtureStateError(f"{field} must be a positive integer")
    return result


def _normalise_fixture(source: Mapping[str, Any]) -> dict[str, Any]:
    try:
        fixture_id = _positive_int(source["id"], field="fixture.id")
        home = _positive_int(source["team_h"], field=f"fixture {fixture_id} team_h")
        away = _positive_int(source["team_a"], field=f"fixture {fixture_id} team_a")
    except KeyError as exc:
        raise FixtureStateError(f"fixture is missing schedule field {exc.args[0]}") from exc
    if home == away:
        raise FixtureStateError(f"fixture {fixture_id} has the same home and away team")
    event_value = source.get("event")
    event = (
        None
        if event_value is None
        else _positive_int(event_value, field=f"fixture {fixture_id} event")
    )
    kickoff_value = source.get("kickoff_time")
    kickoff = (
        None
        if kickoff_value is None
        else _canonical_timestamp(
            kickoff_value,
            field=f"fixture {fixture_id} kickoff_time",
        )
    )
    provisional = source.get("provisional_start_time", False)
    if not isinstance(provisional, bool):
        raise FixtureStateError(
            f"fixture {fixture_id} provisional_start_time must be boolean"
        )
    row = {
        "id": fixture_id,
        "event": event,
        "kickoff_time": kickoff,
        "provisional_start_time": provisional,
        "team_h": home,
        "team_a": away,
        "team_h_difficulty": _positive_int(
            source.get("team_h_difficulty"),
            field=f"fixture {fixture_id} team_h_difficulty",
        ),
        "team_a_difficulty": _positive_int(
            source.get("team_a_difficulty"),
            field=f"fixture {fixture_id} team_a_difficulty",
        ),
    }
    return row


def normalise_fixture_snapshot(
    snapshot: Mapping[str, Any],
    *,
    season: str,
) -> dict[str, Any]:
    """Normalize one full-season official schedule snapshot."""

    observed_at = _canonical_timestamp(
        snapshot.get("observed_at"),
        field="observed_at",
    )
    available_at = _canonical_timestamp(
        snapshot.get("available_at", observed_at),
        field="available_at",
    )
    if parse_aware_datetime(
        available_at, field="available_at"
    ) < parse_aware_datetime(observed_at, field="observed_at"):
        raise FixtureStateError("available_at cannot precede observed_at")
    raw_fixtures = snapshot.get("fixtures")
    if not isinstance(raw_fixtures, list):
        raise FixtureStateError("fixture snapshot body must be an array")
    fixtures = [_normalise_fixture(row) for row in raw_fixtures]
    fixture_ids = [row["id"] for row in fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise FixtureStateError("fixture snapshot contains duplicate fixture IDs")
    fixtures.sort(key=lambda row: row["id"])
    schedule_sha256 = _fingerprint(fixtures)
    source_content_sha256 = snapshot.get("source_content_sha256")
    if source_content_sha256 is not None and (
        not isinstance(source_content_sha256, str)
        or len(source_content_sha256) != 64
    ):
        raise FixtureStateError("source_content_sha256 must be a SHA-256")
    source_id = str(snapshot.get("source_id", "fpl-official-endpoints"))
    snapshot_id = str(
        snapshot.get("snapshot_id")
        or f"fixture-snapshot:{season}:{available_at}:{schedule_sha256[:16]}"
    )
    return {
        "snapshot_id": snapshot_id,
        "season": str(season),
        "source_id": source_id,
        "observed_at": observed_at,
        "available_at": available_at,
        "source_content_sha256": source_content_sha256,
        "schedule_sha256": schedule_sha256,
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }


def load_fixture_acquisition(
    body_path: Path,
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Load and verify one immutable official FPL fixtures acquisition."""

    meta_path = manifest_path or body_path.with_name(
        f"{body_path.stem}.meta.json"
    )
    manifest = json.loads(meta_path.read_text(encoding="utf-8"))
    if manifest.get("acquisition_status") != "success":
        raise FixtureStateError("fixture acquisition was not successful")
    if manifest.get("source_id") != "fpl-official-endpoints":
        raise FixtureStateError("fixture acquisition source is not official FPL")
    if manifest.get("body_file") != body_path.name:
        raise FixtureStateError("fixture acquisition body filename mismatch")
    body = body_path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if manifest.get("content_hash_sha256") != digest:
        raise FixtureStateError("fixture acquisition content hash mismatch")
    try:
        fixtures = json.loads(body)
    except json.JSONDecodeError as exc:
        raise FixtureStateError("fixture acquisition body is not valid JSON") from exc
    return {
        "snapshot_id": str(manifest["manifest_id"]),
        "source_id": str(manifest["source_id"]),
        "observed_at": str(manifest["observed_at"]),
        "available_at": str(
            manifest.get("available_at") or manifest["observed_at"]
        ),
        "source_content_sha256": digest,
        "fixtures": fixtures,
    }


def _change_type(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any] | None,
    *,
    seen_before: bool,
) -> str:
    if previous is None and current is not None:
        return "restored" if seen_before else "created"
    if previous is not None and current is None:
        return "removed"
    assert previous is not None and current is not None
    previous_event = previous.get("event")
    current_event = current.get("event")
    if previous_event is not None and current_event is None:
        return "postponed"
    if previous_event is None and current_event is not None:
        return "rescheduled"
    if previous_event != current_event:
        return "gameweek_change"
    changed = [
        field
        for field in SCHEDULE_FIELDS
        if previous.get(field) != current.get(field)
    ]
    if changed == ["kickoff_time"]:
        return "kickoff_change"
    return "schedule_change"


def build_fixture_revision_log(
    snapshots: Iterable[Mapping[str, Any]],
    *,
    season: str,
) -> dict[str, Any]:
    """Build a deterministic revision stream from full official snapshots."""

    normalized = [
        normalise_fixture_snapshot(snapshot, season=season)
        for snapshot in snapshots
    ]
    if not normalized:
        raise FixtureStateError("at least one fixture snapshot is required")
    normalized.sort(
        key=lambda row: (
            row["available_at"],
            row["observed_at"],
            row["schedule_sha256"],
            row["snapshot_id"],
        )
    )
    unique: list[dict[str, Any]] = []
    by_available: dict[str, str] = {}
    seen_schedules: set[tuple[str, str]] = set()
    for snapshot in normalized:
        available_at = str(snapshot["available_at"])
        schedule_hash = str(snapshot["schedule_sha256"])
        existing = by_available.get(available_at)
        if existing is not None and existing != schedule_hash:
            raise FixtureStateError(
                "different fixture snapshots share one available_at; order is ambiguous"
            )
        by_available[available_at] = schedule_hash
        identity = (available_at, schedule_hash)
        if identity in seen_schedules:
            continue
        seen_schedules.add(identity)
        unique.append(snapshot)

    current: dict[int, dict[str, Any]] = {}
    ever_seen: set[int] = set()
    sequences: dict[int, int] = {}
    revisions: list[dict[str, Any]] = []
    snapshot_metadata: list[dict[str, Any]] = []
    for snapshot in unique:
        incoming = {int(row["id"]): row for row in snapshot["fixtures"]}
        for fixture_id in sorted(set(current) | set(incoming)):
            previous = current.get(fixture_id)
            candidate = incoming.get(fixture_id)
            if previous == candidate:
                continue
            sequences[fixture_id] = sequences.get(fixture_id, 0) + 1
            fixture_uid = f"fixture:{season}:{fixture_id}"
            event_core = {
                "fixture_uid": fixture_uid,
                "revision_seq": sequences[fixture_id],
                "change_type": _change_type(
                    previous,
                    candidate,
                    seen_before=fixture_id in ever_seen,
                ),
                "payload": {"state": deepcopy(candidate)},
                "observed_at": snapshot["observed_at"],
                "available_at": snapshot["available_at"],
                "provenance": {
                    "source_ids": [snapshot["source_id"]],
                    "content_hash_sha256": (
                        snapshot["source_content_sha256"]
                        or snapshot["schedule_sha256"]
                    ),
                    "transformation_version": "fixture-state-v1",
                },
            }
            revisions.append(
                {
                    "revision_id": f"fxr:{_fingerprint(event_core)[:24]}",
                    **event_core,
                }
            )
            ever_seen.add(fixture_id)
        current = deepcopy(incoming)
        snapshot_metadata.append(
            {
                key: deepcopy(snapshot[key])
                for key in (
                    "snapshot_id",
                    "source_id",
                    "observed_at",
                    "available_at",
                    "source_content_sha256",
                    "schedule_sha256",
                    "fixture_count",
                )
            }
        )

    result = {
        "schema_version": "1.0",
        "artifact_type": "fixture_revision_log",
        "season": str(season),
        "snapshots": snapshot_metadata,
        "revisions": revisions,
    }
    result["content_sha256"] = fixture_state_hash(result)
    return result


def _validate_artifact(value: Mapping[str, Any], *, name: str) -> None:
    expected = value.get("content_sha256")
    if not isinstance(expected, str) or expected != fixture_state_hash(value):
        raise FixtureStateError(f"{name} content hash mismatch")


def fixture_view_at(
    revision_log: Mapping[str, Any],
    *,
    cutoff: str,
) -> dict[str, Any]:
    """Reconstruct the inclusive point-in-time schedule at one cutoff."""

    _validate_artifact(revision_log, name="fixture revision log")
    cutoff_at = parse_aware_datetime(cutoff, field="cutoff").astimezone(
        timezone.utc
    )
    eligible_snapshots = [
        row
        for row in revision_log.get("snapshots", [])
        if parse_aware_datetime(
            str(row["available_at"]),
            field="available_at",
        ).astimezone(timezone.utc)
        <= cutoff_at
    ]
    if not eligible_snapshots:
        raise FixtureStateError("no fixture snapshot was available by cutoff")
    state: dict[str, dict[str, Any]] = {}
    eligible_revisions = [
        row
        for row in revision_log.get("revisions", [])
        if parse_aware_datetime(
            str(row["available_at"]),
            field="available_at",
        ).astimezone(timezone.utc)
        <= cutoff_at
    ]
    eligible_revisions.sort(
        key=lambda row: (
            row["available_at"],
            row["observed_at"],
            row["fixture_uid"],
            int(row["revision_seq"]),
            row["revision_id"],
        )
    )
    for revision in eligible_revisions:
        fixture_uid = str(revision["fixture_uid"])
        candidate = revision.get("payload", {}).get("state")
        if candidate is None:
            state.pop(fixture_uid, None)
        else:
            state[fixture_uid] = deepcopy(dict(candidate))
    fixtures = [
        {"fixture_uid": fixture_uid, **state[fixture_uid]}
        for fixture_uid in sorted(
            state,
            key=lambda value: int(value.rsplit(":", 1)[-1]),
        )
    ]
    result = {
        "schema_version": "1.0",
        "artifact_type": "fixture_state_view",
        "season": str(revision_log["season"]),
        "cutoff": _canonical_timestamp(cutoff, field="cutoff"),
        "revision_log_sha256": str(revision_log["content_sha256"]),
        "eligible_snapshot_ids": [
            str(row["snapshot_id"])
            for row in sorted(
                eligible_snapshots,
                key=lambda row: (row["available_at"], row["snapshot_id"]),
            )
        ],
        "fixtures": fixtures,
    }
    result["content_sha256"] = fixture_state_hash(result)
    return result


def team_fixture_counts(
    fixture_view: Mapping[str, Any],
    *,
    gameweeks: Sequence[int],
    team_ids: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Return a complete team x Gameweek count table with blank/double labels."""

    _validate_artifact(fixture_view, name="fixture state view")
    weeks = sorted({_positive_int(value, field="gameweek") for value in gameweeks})
    if len(weeks) != len(gameweeks):
        raise FixtureStateError("gameweeks must be unique")
    fixtures = list(fixture_view.get("fixtures", []))
    derived_teams = sorted(
        {
            int(row[field])
            for row in fixtures
            for field in ("team_h", "team_a")
        }
    )
    teams = (
        sorted({_positive_int(value, field="team_id") for value in team_ids})
        if team_ids is not None
        else derived_teams
    )
    if not teams:
        raise FixtureStateError("fixture view contains no teams")
    rows: list[dict[str, Any]] = []
    for gameweek in weeks:
        for team_id in teams:
            fixture_ids = sorted(
                int(row["id"])
                for row in fixtures
                if row.get("event") == gameweek
                and team_id in (int(row["team_h"]), int(row["team_a"]))
            )
            count = len(fixture_ids)
            classification = (
                "blank"
                if count == 0
                else "single"
                if count == 1
                else "double"
                if count == 2
                else "multiple"
            )
            rows.append(
                {
                    "gameweek": gameweek,
                    "team_id": team_id,
                    "fixture_count": count,
                    "classification": classification,
                    "fixture_ids": fixture_ids,
                }
            )
    result = {
        "schema_version": "1.0",
        "artifact_type": "team_fixture_counts",
        "season": str(fixture_view["season"]),
        "cutoff": str(fixture_view["cutoff"]),
        "fixture_state_sha256": str(fixture_view["content_sha256"]),
        "gameweeks": weeks,
        "rows": rows,
    }
    result["content_sha256"] = fixture_state_hash(result)
    return result


def fixture_weeks_from_view(
    fixture_view: Mapping[str, Any],
    *,
    gameweeks: Sequence[int],
    team_ids: Sequence[int] | None = None,
) -> list[dict[str, Any]]:
    """Convert a point-in-time view to the shared multiweek schedule contract."""

    counts = team_fixture_counts(
        fixture_view,
        gameweeks=gameweeks,
        team_ids=team_ids,
    )
    by_week: dict[int, dict[str, int]] = {int(week): {} for week in counts["gameweeks"]}
    for row in counts["rows"]:
        by_week[int(row["gameweek"])][
            f"team:{fixture_view['season']}:{int(row['team_id'])}"
        ] = int(row["fixture_count"])
    result: list[dict[str, Any]] = []
    for gameweek in counts["gameweeks"]:
        fixtures = [
            {
                field: deepcopy(row.get(field))
                for field in SCHEDULE_FIELDS
            }
            for row in fixture_view["fixtures"]
            if row.get("event") == gameweek
        ]
        result.append(
            {
                "gameweek": int(gameweek),
                "fixtures": sorted(fixtures, key=lambda row: int(row["id"])),
                "team_fixture_counts": by_week[int(gameweek)],
                "fixture_state_sha256": str(fixture_view["content_sha256"]),
                "fixture_count_table_sha256": str(counts["content_sha256"]),
                "schedule_provenance": {
                    "source": "event_sourced_official_fpl_fixture_state",
                    "cutoff": str(fixture_view["cutoff"]),
                    "revision_log_sha256": str(
                        fixture_view["revision_log_sha256"]
                    ),
                    "fixture_state_sha256": str(fixture_view["content_sha256"]),
                    "fixture_count_table_sha256": str(counts["content_sha256"]),
                    "eligible_snapshot_ids": deepcopy(
                        list(fixture_view["eligible_snapshot_ids"])
                    ),
                },
            }
        )
    return result


def write_immutable_fixture_artifact(
    path: Path,
    artifact: Mapping[str, Any],
) -> None:
    """Write one content-addressed derived artifact without overwriting changes."""

    _validate_artifact(artifact, name="fixture artifact")
    encoded = (
        json.dumps(
            artifact,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(
                f"refusing to overwrite immutable fixture artifact: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
