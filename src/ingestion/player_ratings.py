"""Capture immutable, cutoff-safe player-rating observations."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.ingestion.registry import assert_collectable


SELECTED_SOURCE_ID = "statsbomb-open"
APPROVED_SOURCE_IDS = frozenset({SELECTED_SOURCE_ID})
PREREGISTERED_SOURCE_IDS = frozenset(
    {"statsbomb-open", "commercial-epl-event-data", "fbref"}
)
RATING_MIN = 0.0
RATING_MAX = 10.0
DEFAULT_MAX_AGE_HOURS = 720


class PlayerRatingError(ValueError):
    """Raised when a rating artifact is ambiguous or temporally unsafe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash an artifact without its circular content hash."""

    return hashlib.sha256(
        _canonical_bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PlayerRatingError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise PlayerRatingError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _optional_timestamp(value: Any, field: str) -> tuple[str | None, datetime | None]:
    if value in (None, ""):
        return None, None
    return _timestamp(value, field)


def _sha256(value: Any, field: str) -> str:
    text = str(value)
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise PlayerRatingError(f"{field} must be a lowercase SHA-256")
    return text


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _rating(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result) or not RATING_MIN <= result <= RATING_MAX:
        return None
    return round(result, 6)


def _stable_id(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def normalise_player_rating_snapshot(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    source_sha256: str,
    origin: str,
    methodology_id: str,
    methodology_version: str,
    observed_at: str,
    available_at: str,
    decision_cutoff: str,
    identity_map: Mapping[str, Any],
    published_at: str | None = None,
    effective_at: str | None = None,
    finalised_at: str | None = None,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
) -> dict[str, Any]:
    """Normalise already-acquired ratings without guessing player identities."""

    if source_id not in PREREGISTERED_SOURCE_IDS:
        raise PlayerRatingError(
            f"source_id is not preregistered for player ratings: {source_id}"
        )
    if source_id not in APPROVED_SOURCE_IDS:
        raise PlayerRatingError(
            f"source_id is not approved for capture: {source_id}"
        )
    registry_source = assert_collectable(source_id)
    if "method_prototyping" not in str(registry_source["allowed_use"]):
        raise PlayerRatingError(
            "source registry does not allow player-rating method prototyping"
        )
    source_hash = _sha256(source_sha256, "source_sha256")
    origin_text = str(origin).strip()
    method_id = str(methodology_id).strip()
    method_version = str(methodology_version).strip()
    if not origin_text or not method_id or not method_version:
        raise PlayerRatingError(
            "origin, methodology_id and methodology_version are required"
        )
    observed_text, observed = _timestamp(observed_at, "observed_at")
    available_text, available = _timestamp(available_at, "available_at")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    published_text, published = _optional_timestamp(published_at, "published_at")
    effective_text, effective = _optional_timestamp(effective_at, "effective_at")
    finalised_text, finalised = _optional_timestamp(finalised_at, "finalised_at")
    if available < observed:
        raise PlayerRatingError("available_at cannot be before observed_at")
    if observed >= cutoff or available >= cutoff:
        raise PlayerRatingError(
            "observed_at and available_at must be strictly before decision_cutoff"
        )
    for field, timestamp in (
        ("published_at", published),
        ("effective_at", effective),
        ("finalised_at", finalised),
    ):
        if timestamp is not None and timestamp > available:
            raise PlayerRatingError(f"{field} cannot be after available_at")
    if (
        isinstance(max_age_hours, bool)
        or not isinstance(max_age_hours, int)
        or max_age_hours <= 0
    ):
        raise PlayerRatingError("max_age_hours must be a positive integer")
    expires_at = (available + timedelta(hours=max_age_hours)).isoformat().replace(
        "+00:00", "Z"
    )

    source_rows = [deepcopy(dict(row)) for row in rows]
    seen_source_ids: set[str] = set()
    present_source_ids = {
        str(row.get("source_player_id", "")).strip()
        for row in source_rows
        if str(row.get("source_player_id", "")).strip()
    }
    mapped_targets: dict[int, list[str]] = {}
    for source_player_id in present_source_ids:
        raw_official_id = identity_map.get(source_player_id)
        official_id = _positive_int(raw_official_id)
        if official_id is not None:
            mapped_targets.setdefault(official_id, []).append(
                str(source_player_id)
            )
    ambiguous_targets = {
        official_id
        for official_id, source_ids in mapped_targets.items()
        if len(source_ids) > 1
    }

    admitted: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for row_number, row in enumerate(source_rows, start=1):
        source_player_id = str(row.get("source_player_id", "")).strip()
        player_name = str(row.get("player_name", "")).strip()
        team_name = str(row.get("team_name", "")).strip()
        if not source_player_id:
            quarantined.append(
                {
                    "row_number": row_number,
                    "source_player_id": None,
                    "player_name": player_name or None,
                    "team_name": team_name or None,
                    "reason": "missing_source_player_id",
                }
            )
            continue
        if source_player_id in seen_source_ids:
            raise PlayerRatingError(
                f"duplicate source_player_id: {source_player_id}"
            )
        seen_source_ids.add(source_player_id)
        official_player_id = _positive_int(identity_map.get(source_player_id))
        if official_player_id is None:
            quarantined.append(
                {
                    "row_number": row_number,
                    "source_player_id": source_player_id,
                    "player_name": player_name or None,
                    "team_name": team_name or None,
                    "reason": "unresolved_player_identity",
                }
            )
            continue
        if official_player_id in ambiguous_targets:
            quarantined.append(
                {
                    "row_number": row_number,
                    "source_player_id": source_player_id,
                    "player_name": player_name or None,
                    "team_name": team_name or None,
                    "reason": "ambiguous_official_identity_mapping",
                }
            )
            continue
        normalised_rating = _rating(row.get("rating"))
        if normalised_rating is None:
            quarantined.append(
                {
                    "row_number": row_number,
                    "source_player_id": source_player_id,
                    "player_name": player_name or None,
                    "team_name": team_name or None,
                    "reason": "invalid_rating",
                }
            )
            continue
        if not player_name or not team_name:
            quarantined.append(
                {
                    "row_number": row_number,
                    "source_player_id": source_player_id,
                    "player_name": player_name or None,
                    "team_name": team_name or None,
                    "reason": "missing_source_identity_context",
                }
            )
            continue
        observation_key = {
            "source_id": source_id,
            "source_sha256": source_hash,
            "source_player_id": source_player_id,
            "official_player_id": official_player_id,
            "rating": normalised_rating,
            "available_at": available_text,
            "methodology_id": method_id,
            "methodology_version": method_version,
        }
        admitted.append(
            {
                "observation_id": _stable_id(observation_key),
                "official_player_id": official_player_id,
                "source_player_id": source_player_id,
                "player_name": player_name,
                "team_name": team_name,
                "rating": normalised_rating,
                "rating_scale": [RATING_MIN, RATING_MAX],
                "observed_at": observed_text,
                "available_at": available_text,
                "expires_at": expires_at,
            }
        )

    admitted.sort(key=lambda row: row["official_player_id"])
    quarantined.sort(
        key=lambda row: (
            row["row_number"],
            str(row.get("source_player_id") or ""),
            row["reason"],
        )
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "family": "player_ratings",
        "source_id": source_id,
        "source_sha256": source_hash,
        "origin": origin_text,
        "methodology": {
            "methodology_id": method_id,
            "version": method_version,
            "rating_scale": [RATING_MIN, RATING_MAX],
        },
        "published_at": published_text,
        "effective_at": effective_text,
        "finalised_at": finalised_text,
        "observed_at": observed_text,
        "available_at": available_text,
        "decision_cutoff": cutoff_text,
        "expires_at": expires_at,
        "status": "complete" if admitted and not quarantined else "degraded",
        "input_row_count": len(source_rows),
        "admitted_count": len(admitted),
        "quarantined_count": len(quarantined),
        "quarantine_rate": (
            round(len(quarantined) / len(source_rows), 6) if source_rows else 0.0
        ),
        "ratings": admitted,
        "quarantine": quarantined,
        "identity_policy": "explicit_mapping_only_never_name_guessing",
        "collection_mode": "pre_acquired_local_rows_no_network_fetch",
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_player_rating_ledger(
    snapshots: Iterable[Mapping[str, Any]],
    *,
    as_of: str,
) -> dict[str, Any]:
    """Resolve the latest admissible, non-expired rating per player."""

    as_of_text, as_of_time = _timestamp(as_of, "as_of")
    admissible: list[dict[str, Any]] = []
    excluded_future: list[str] = []
    for raw in snapshots:
        snapshot = deepcopy(dict(raw))
        snapshot_id = str(snapshot.get("content_sha256", ""))
        if snapshot_id != artifact_hash(snapshot):
            raise PlayerRatingError("player-rating snapshot content hash mismatch")
        if snapshot.get("source_id") not in APPROVED_SOURCE_IDS:
            raise PlayerRatingError("player-rating snapshot source is not approved")
        _, available = _timestamp(snapshot.get("available_at"), "available_at")
        if available > as_of_time:
            excluded_future.append(snapshot_id)
        else:
            admissible.append(snapshot)
    admissible.sort(
        key=lambda value: (
            str(value["available_at"]),
            str(value["observed_at"]),
            str(value["content_sha256"]),
        )
    )

    histories: dict[int, list[dict[str, Any]]] = {}
    for snapshot in admissible:
        for raw_rating in snapshot.get("ratings", []):
            rating = deepcopy(dict(raw_rating))
            rating["snapshot_content_sha256"] = snapshot["content_sha256"]
            rating["source_id"] = snapshot["source_id"]
            rating["methodology"] = deepcopy(snapshot["methodology"])
            histories.setdefault(int(rating["official_player_id"]), []).append(
                rating
            )

    ratings: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    for official_player_id in sorted(histories):
        history = histories[official_player_id]
        latest = deepcopy(history[-1])
        latest["superseded_snapshot_ids"] = [
            row["snapshot_content_sha256"] for row in history[:-1]
        ]
        _, expiry = _timestamp(latest["expires_at"], "expires_at")
        if as_of_time >= expiry:
            expired.append(
                {
                    "official_player_id": official_player_id,
                    "snapshot_content_sha256": latest[
                        "snapshot_content_sha256"
                    ],
                }
            )
        else:
            ratings.append(latest)

    quarantine = [
        {
            **deepcopy(row),
            "snapshot_content_sha256": snapshot["content_sha256"],
        }
        for snapshot in admissible
        for row in snapshot.get("quarantine", [])
    ]
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "family": "player_ratings",
        "as_of": as_of_text,
        "status": "ready" if ratings else "degraded",
        "admissible_snapshot_ids": [
            snapshot["content_sha256"] for snapshot in admissible
        ],
        "excluded_future_snapshot_ids": sorted(excluded_future),
        "ratings": ratings,
        "expired": expired,
        "quarantine": quarantine,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_player_rating_feature_payload(
    ledger: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose an isolated ratings family without assigning forecast weights."""

    value = deepcopy(dict(ledger))
    if value.get("content_sha256") != artifact_hash(value):
        raise PlayerRatingError("player-rating ledger content hash mismatch")
    ratings = [
        {
            "official_player_id": row["official_player_id"],
            "rating": row["rating"],
            "rating_scale": deepcopy(row["rating_scale"]),
            "observation_id": row["observation_id"],
            "snapshot_content_sha256": row["snapshot_content_sha256"],
            "source_id": row["source_id"],
            "methodology": deepcopy(row["methodology"]),
        }
        for row in value.get("ratings", [])
    ]
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "family": "player_ratings",
        "ledger_content_sha256": value["content_sha256"],
        "status": "shadow_ready" if ratings else "degraded",
        "ratings": ratings,
        "effect_weights": None,
        "promotion_status": "shadow_only_pending_point_in_time_ablation",
        "fallback": None if ratings else "byte_identical_baseline",
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def write_immutable_json(path: Path, value: Mapping[str, Any]) -> str:
    """Write canonical JSON once; allow byte-identical idempotent reruns."""

    body = json.dumps(
        value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != body:
            raise PlayerRatingError(
                f"refusing to overwrite immutable artifact: {path}"
            )
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return "written"
