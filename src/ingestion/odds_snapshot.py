"""Normalise Football-Data odds without inventing pre-deadline timestamps."""

from __future__ import annotations

import csv
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from typing import Any, Mapping


SOURCE_ID = "football-data-co-uk"
ODDS_PREFIXES = ("B365", "PS", "Avg")
MARKET_SLOTS = ("T-24h", "T-8h", "T-2h", "final")
TIMING_LABEL = "source_scheduled_preclosing"
MISSING_TIMESTAMP_REASON = "source_has_no_quote_level_predeadline_timestamp"
SLOT_WINDOWS_HOURS = {
    "T-24h": (18.0, 30.0),
    "T-8h": (5.0, 12.0),
    "T-2h": (0.5, 4.0),
    "final": (0.0, 0.5),
}


class FootballDataOddsError(ValueError):
    """Raised when Football-Data odds are malformed or provenance is ambiguous."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash a derived artifact without its circular content hash field."""

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
        raise FootballDataOddsError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise FootballDataOddsError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _text(row: Mapping[str, Any], field: str) -> str:
    value = str(row.get(field, "")).strip()
    if not value:
        raise FootballDataOddsError(f"Football-Data row is missing {field}")
    return value


def _decimal_odds(row: Mapping[str, Any]) -> tuple[str, dict[str, float]] | None:
    for prefix in ODDS_PREFIXES:
        fields = {side: f"{prefix}{suffix}" for side, suffix in (("home", "H"), ("draw", "D"), ("away", "A"))}
        try:
            values = {
                side: float(str(row.get(column, "")).strip())
                for side, column in fields.items()
            }
        except ValueError:
            continue
        if not all(math.isfinite(value) and value > 1.0 for value in values.values()):
            continue
        return prefix, values
    return None


def _probabilities(odds: Mapping[str, float]) -> dict[str, float]:
    inverse = {side: 1.0 / value for side, value in odds.items()}
    total = sum(inverse.values())
    return {
        f"p_{side}": round(inverse[side] / total, 12)
        for side in ("home", "draw", "away")
    }


def normalise_football_data_csv(
    body: bytes,
    *,
    season: str,
    origin: str,
    observed_at: str,
    available_at: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic comparator containing no realised outcomes."""

    observed_text, observed = _timestamp(observed_at, "observed_at")
    available_text, available = _timestamp(
        available_at or observed_text, "available_at"
    )
    if available < observed:
        raise FootballDataOddsError("available_at cannot be before observed_at")
    if not body:
        raise FootballDataOddsError("Football-Data CSV is empty")
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FootballDataOddsError("Football-Data CSV must be UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text))
    required = {"Date", "HomeTeam", "AwayTeam"}
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise FootballDataOddsError(
            "Football-Data CSV must contain Date, HomeTeam and AwayTeam"
        )

    matches: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        date = _text(row, "Date")
        home = _text(row, "HomeTeam")
        away = _text(row, "AwayTeam")
        fixture_key = f"{date}|{home}|{away}"
        if fixture_key in seen:
            raise FootballDataOddsError(
                f"Duplicate Football-Data fixture: {fixture_key}"
            )
        seen.add(fixture_key)
        selected = _decimal_odds(row)
        if selected is None:
            rejected.append(
                {
                    "row_number": row_number,
                    "fixture_key": fixture_key,
                    "reason": "no_complete_valid_1x2_odds_family",
                }
            )
            continue
        prefix, odds = selected
        matches.append(
            {
                "fixture_key": fixture_key,
                "date": date,
                "home_team": home,
                "away_team": away,
                "odds_family": prefix,
                "decimal_odds": {
                    side: round(odds[side], 8)
                    for side in ("home", "draw", "away")
                },
                "probabilities": _probabilities(odds),
                "timing_label": TIMING_LABEL,
                "live_forecast_admissible": False,
            }
        )

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "source_id": SOURCE_ID,
        "season": str(season),
        "origin": str(origin),
        "observed_at": observed_text,
        "available_at": available_text,
        "source_sha256": hashlib.sha256(body).hexdigest(),
        "timing_label": TIMING_LABEL,
        "quote_type": "preclosing",
        "source_collection_schedule": {
            "weekend_games": "Friday afternoon",
            "midweek_games": "Tuesday afternoon",
            "precision": "source_described_day_part_without_quote_timestamp",
        },
        "timing_guarantee": "schedule_only_without_quote_level_timestamp",
        "use": "historical_preclosing_market_comparator",
        "live_forecast_admission": False,
        "match_count": len(matches),
        "rejected_count": len(rejected),
        "matches": sorted(matches, key=lambda value: value["fixture_key"]),
        "rejected": sorted(rejected, key=lambda value: value["fixture_key"]),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_football_data_checkpoint_manifest(
    *,
    season: str,
    decision_cutoff: str,
    assessed_at: str,
    comparator: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Report the four unsupported live slots and bind an optional comparator."""

    cutoff_text, _ = _timestamp(decision_cutoff, "decision_cutoff")
    assessed_text, _ = _timestamp(assessed_at, "assessed_at")
    comparator_ref: dict[str, Any] | None = None
    if comparator is not None:
        value = deepcopy(dict(comparator))
        if value.get("source_id") != SOURCE_ID:
            raise FootballDataOddsError("Comparator source_id is not Football-Data")
        if value.get("timing_label") != TIMING_LABEL:
            raise FootballDataOddsError(
                "Football-Data comparator timing label must remain "
                "source_scheduled_preclosing"
            )
        if value.get("live_forecast_admission") is not False:
            raise FootballDataOddsError(
                "Football-Data comparator cannot be live-forecast admissible"
            )
        if value.get("content_sha256") != artifact_hash(value):
            raise FootballDataOddsError("Football-Data comparator content hash mismatch")
        comparator_ref = {
            "source_id": SOURCE_ID,
            "content_sha256": value["content_sha256"],
            "source_sha256": value["source_sha256"],
            "match_count": int(value["match_count"]),
            "timing_label": TIMING_LABEL,
            "use": "comparator_only",
        }

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "season": str(season),
        "decision_cutoff": cutoff_text,
        "assessed_at": assessed_text,
        "selected_source_id": SOURCE_ID,
        "status": "degraded",
        "required_slots": list(MARKET_SLOTS),
        "slot_status": [
            {
                "slot": slot,
                "status": "unavailable",
                "reason": MISSING_TIMESTAMP_REASON,
            }
            for slot in MARKET_SLOTS
        ],
        "admitted_live_snapshots": [],
        "comparator": comparator_ref,
        "fallback": "shared_structured_forecast_without_odds",
        "future_upgrade": "separately_approved_timestamped_live_provider",
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_observed_live_snapshot(
    comparator: Mapping[str, Any],
    *,
    slot: str,
    decision_cutoff: str,
) -> dict[str, Any]:
    """Stage an exact local pre-deadline observation for the live capture gate."""

    if slot not in MARKET_SLOTS:
        raise FootballDataOddsError(f"Unknown market capture slot: {slot}")
    value = deepcopy(dict(comparator))
    if value.get("source_id") != SOURCE_ID:
        raise FootballDataOddsError("Comparator source_id is not Football-Data")
    if value.get("content_sha256") != artifact_hash(value):
        raise FootballDataOddsError("Football-Data comparator content hash mismatch")
    if (
        value.get("quote_type") != "preclosing"
        or value.get("timing_label") != TIMING_LABEL
    ):
        raise FootballDataOddsError(
            "Live snapshot requires Football-Data preclosing odds"
        )
    observed_text, observed = _timestamp(value.get("observed_at"), "observed_at")
    available_text, available = _timestamp(value.get("available_at"), "available_at")
    _, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if observed >= cutoff or available >= cutoff:
        raise FootballDataOddsError(
            "Observed and available times must be strictly before the decision cutoff"
        )
    evidence_time = max(observed, available)
    lead_hours = (cutoff - evidence_time).total_seconds() / 3600.0
    minimum, maximum = SLOT_WINDOWS_HOURS[slot]
    if not (minimum < lead_hours <= maximum):
        raise FootballDataOddsError(
            f"Observation is outside the {slot} capture window: "
            f"lead_hours={lead_hours:.3f}, expected=({minimum}, {maximum}]"
        )

    payload = {
        "schema_version": "1.0",
        "quote_type": "preclosing",
        "source_timing": "exact_local_observation_of_source_scheduled_quotes",
        "comparator_content_sha256": value["content_sha256"],
        "markets": deepcopy(list(value.get("matches", []))),
    }
    return {
        "source_id": SOURCE_ID,
        "slot": slot,
        "observed_at": observed_text,
        "available_at": available_text,
        "payload": payload,
        "lead_time_hours": round(lead_hours, 6),
        "slot_window_hours": {"exclusive_min": minimum, "inclusive_max": maximum},
        "source_sha256": hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
    }
