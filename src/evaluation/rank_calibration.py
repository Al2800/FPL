"""Point-in-time FPL score-to-overall-rank calibration.

Rank calibration is deliberately downstream of replay scoring.  It annotates a
revealed cumulative score and never feeds forecasts, optimisation, or policy
state.  Missing or unapproved standings remain ``unavailable`` rather than
being replaced with a guessed global rank.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


class RankCalibrationError(ValueError):
    """Raised when a rank calibration artifact is malformed or unsafe."""


MODES = frozenset({"exact", "bounded", "unavailable"})
SEASON_GAMEWEEKS = range(1, 39)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNAVAILABLE_SOURCE_HASH = hashlib.sha256(b"fpl-rank-calibration:unavailable").hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _utc_timestamp(value: Any, field: str) -> str:
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RankCalibrationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise RankCalibrationError(f"{field} must include a timezone")
    return text


def _integer(value: Any, field: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise RankCalibrationError(f"{field} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise RankCalibrationError(f"{field} must be an integer") from exc
    if str(value).strip() != str(number):
        raise RankCalibrationError(f"{field} must be an integer")
    if minimum is not None and number < minimum:
        raise RankCalibrationError(f"{field} must be >= {minimum}")
    return number


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise RankCalibrationError(f"{field} must be boolean")
    return value


def validate_row(row: Mapping[str, Any], *, season: str | None = None) -> dict[str, Any]:
    """Validate and return a normalised observation row.

    Rows use rank positions (lower is better).  ``rank_lower`` and
    ``rank_upper`` are intentionally optional only for ``unavailable`` rows.
    """

    required = {
        "season",
        "gameweek",
        "cumulative_points",
        "rank_lower",
        "rank_upper",
        "exact",
        "field_size",
        "snapshot_at",
        "finalised",
        "auto_sub_finalised",
        "tie_rule",
        "source_id",
        "source_artifact_hash",
        "derivation_method",
        "mode",
    }
    missing = sorted(required - set(row))
    if missing:
        raise RankCalibrationError("rank row missing fields: " + ", ".join(missing))

    result = dict(row)
    row_season = str(row["season"])
    if season is not None and row_season != season:
        raise RankCalibrationError(f"row season {row_season!r} does not match {season!r}")
    gameweek = _integer(row["gameweek"], "gameweek", minimum=1)
    if gameweek not in SEASON_GAMEWEEKS:
        raise RankCalibrationError("gameweek must be between 1 and 38")
    result["season"] = row_season
    result["gameweek"] = gameweek
    result["cumulative_points"] = _integer(row["cumulative_points"], "cumulative_points", minimum=0)
    if str(row["mode"]) == "unavailable" and row["field_size"] is None:
        result["field_size"] = None
    else:
        result["field_size"] = _integer(row["field_size"], "field_size", minimum=0 if str(row["mode"]) == "unavailable" else 1)
    result["exact"] = _bool(row["exact"], "exact")
    result["finalised"] = _bool(row["finalised"], "finalised")
    result["auto_sub_finalised"] = _bool(row["auto_sub_finalised"], "auto_sub_finalised")
    result["snapshot_at"] = _utc_timestamp(row["snapshot_at"], "snapshot_at")
    result["tie_rule"] = str(row["tie_rule"])
    result["source_id"] = str(row["source_id"])
    result["source_artifact_hash"] = str(row["source_artifact_hash"])
    result["derivation_method"] = str(row["derivation_method"])
    result["mode"] = str(row["mode"])
    if result["mode"] not in MODES:
        raise RankCalibrationError(f"unknown rank calibration mode: {result['mode']}")
    if not result["tie_rule"] or not result["source_id"] or not result["derivation_method"]:
        raise RankCalibrationError("tie_rule, source_id and derivation_method are required")
    if not SHA256_RE.fullmatch(result["source_artifact_hash"]):
        raise RankCalibrationError("source_artifact_hash must be a lowercase SHA-256")

    lower = row["rank_lower"]
    upper = row["rank_upper"]
    if result["mode"] == "unavailable":
        if lower is not None or upper is not None or result["exact"]:
            raise RankCalibrationError("unavailable rows cannot contain a rank or exact=true")
    else:
        if lower is None or upper is None:
            raise RankCalibrationError("rank bounds are required for exact/bounded rows")
        lower_i = _integer(lower, "rank_lower", minimum=1)
        upper_i = _integer(upper, "rank_upper", minimum=1)
        if lower_i > upper_i or upper_i > result["field_size"]:
            raise RankCalibrationError("rank bounds must be ordered and within field_size")
        result["rank_lower"] = lower_i
        result["rank_upper"] = upper_i
        if result["mode"] == "exact" and (not result["exact"] or lower_i != upper_i):
            raise RankCalibrationError("exact rows require exact=true and equal bounds")
        if result["mode"] == "bounded" and (result["exact"] or lower_i >= upper_i):
            raise RankCalibrationError("bounded rows require exact=false and a non-zero bound")
    return result


def build_unavailable_season(
    *,
    season: str = "2025-26",
    snapshot_at: str = "2026-07-31T00:00:00Z",
    reason: str = "no approved source provides defensible historical rank thresholds",
    source_registry_version: str = "unknown",
) -> dict[str, Any]:
    """Create an explicit 38-gameweek unavailable artifact without inventing ranks."""

    if not reason.strip():
        raise RankCalibrationError("reason must not be empty")
    rows = [
        validate_row(
            {
                "season": season,
                "gameweek": gameweek,
                "cumulative_points": 0,
                "rank_lower": None,
                "rank_upper": None,
                "exact": False,
                "field_size": None,
                "snapshot_at": snapshot_at,
                "finalised": False,
                "auto_sub_finalised": False,
                "tie_rule": "unavailable",
                "source_id": "unavailable",
                "source_artifact_hash": UNAVAILABLE_SOURCE_HASH,
                "derivation_method": "unavailable:no_approved_source",
                "mode": "unavailable",
                "reason": reason,
            },
            season=season,
        )
        for gameweek in SEASON_GAMEWEEKS
    ]
    return {
        "schema_version": "rank-thresholds-v1",
        "season": season,
        "status": "unavailable",
        "source_registry_version": source_registry_version,
        "reason": reason,
        "rows": rows,
        "mode_counts": {"unavailable": len(rows)},
        "gameweek_count": len(rows),
        "artifact_sha256": _sha256(rows),
    }


def validate_artifact(artifact: Mapping[str, Any], *, season: str | None = None) -> dict[str, Any]:
    """Validate an artifact, including its content hash and one row per GW."""

    if str(artifact.get("schema_version")) != "rank-thresholds-v1":
        raise RankCalibrationError("unsupported rank-thresholds schema")
    artifact_season = str(artifact.get("season", ""))
    if season is not None and artifact_season != season:
        raise RankCalibrationError("artifact season does not match requested season")
    rows_raw = artifact.get("rows")
    if not isinstance(rows_raw, list):
        raise RankCalibrationError("artifact rows must be a list")
    rows = [validate_row(row, season=artifact_season) for row in rows_raw]
    gameweeks = [row["gameweek"] for row in rows]
    if sorted(gameweeks) != list(SEASON_GAMEWEEKS):
        raise RankCalibrationError("artifact must contain exactly one row for GW1-GW38")
    if len(set(gameweeks)) != len(gameweeks):
        raise RankCalibrationError("artifact contains duplicate gameweeks")
    expected_hash = str(artifact.get("artifact_sha256", ""))
    if not SHA256_RE.fullmatch(expected_hash) or expected_hash != _sha256(rows):
        raise RankCalibrationError("artifact SHA-256 mismatch")
    result = dict(artifact)
    result["rows"] = rows
    result["artifact_sha256"] = expected_hash
    result["status"] = str(artifact.get("status", ""))
    if result["status"] not in MODES and result["status"] != "mixed":
        raise RankCalibrationError("artifact status must be exact, bounded, unavailable or mixed")
    return result


def load_artifact(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Load and verify a JSON artifact before it can be used for reporting."""

    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RankCalibrationError(f"unable to read rank artifact: {path}") from exc
    validated = validate_artifact(artifact)
    if expected_sha256 is not None and validated["artifact_sha256"] != expected_sha256:
        raise RankCalibrationError("artifact SHA-256 does not match expected value")
    return validated


def summarise_season(rows: Iterable[Mapping[str, Any]], *, season: str = "2025-26") -> dict[str, Any]:
    """Reconcile all 38 gameweeks and report mode counts without imputing gaps."""

    validated = [validate_row(row, season=season) for row in rows]
    artifact = {
        "schema_version": "rank-thresholds-v1",
        "season": season,
        "status": "mixed" if len({row["mode"] for row in validated}) > 1 else validated[0]["mode"] if validated else "unavailable",
        "rows": sorted(validated, key=lambda row: row["gameweek"]),
    }
    return validate_artifact({**artifact, "artifact_sha256": _sha256(artifact["rows"])}, season=season)


def resolve_rank(
    cumulative_points: int,
    rows: Iterable[Mapping[str, Any]],
    *,
    season: str = "2025-26",
    gameweek: int,
) -> dict[str, Any]:
    """Resolve a score using exact support or a conservative bounded bracket.

    Scores outside the observed support are rejected rather than extrapolated.
    """

    score = _integer(cumulative_points, "cumulative_points", minimum=0)
    gw = _integer(gameweek, "gameweek", minimum=1)
    if gw not in SEASON_GAMEWEEKS:
        raise RankCalibrationError("gameweek must be between 1 and 38")
    candidates = sorted(
        (validate_row(row, season=season) for row in rows if int(row.get("gameweek", -1)) == gw),
        key=lambda row: row["cumulative_points"],
    )
    usable = [row for row in candidates if row["mode"] != "unavailable"]
    if not usable:
        return {
            "season": season,
            "gameweek": gw,
            "cumulative_points": score,
            "mode": "unavailable",
            "exact": False,
            "rank_lower": None,
            "rank_upper": None,
            "reason": "no approved rank observations available",
        }
    for row in usable:
        if row["cumulative_points"] == score:
            return {
                "season": season,
                "gameweek": gw,
                "cumulative_points": score,
                "mode": row["mode"],
                "exact": row["exact"],
                "rank_lower": row["rank_lower"],
                "rank_upper": row["rank_upper"],
                "source_id": row["source_id"],
                "source_artifact_hash": row["source_artifact_hash"],
                "derivation_method": "observed",
            }
    lower = max((row for row in usable if row["cumulative_points"] < score), key=lambda row: row["cumulative_points"], default=None)
    upper = min((row for row in usable if row["cumulative_points"] > score), key=lambda row: row["cumulative_points"], default=None)
    if lower is None or upper is None:
        raise RankCalibrationError("rank extrapolation outside observed score support is forbidden")
    return {
        "season": season,
        "gameweek": gw,
        "cumulative_points": score,
        "mode": "bounded",
        "exact": False,
        "rank_lower": min(lower["rank_lower"], upper["rank_lower"]),
        "rank_upper": max(lower["rank_upper"], upper["rank_upper"]),
        "support": [lower["cumulative_points"], upper["cumulative_points"]],
        "source_id": lower["source_id"],
        "source_artifact_hash": lower["source_artifact_hash"],
        "derivation_method": "bounded_bracket_no_extrapolation",
    }


def rank_label(result: Mapping[str, Any]) -> str:
    """Return a UI-safe label that distinguishes exact, estimated and missing."""

    mode = str(result.get("mode"))
    if mode == "exact":
        return f"exact rank {result['rank_lower']}"
    if mode == "bounded":
        return f"estimated rank band {result['rank_lower']}-{result['rank_upper']} (non-exact)"
    return "rank unavailable (no approved source)"

