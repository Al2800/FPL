"""Point-in-time-safe temporal envelopes for acquired source observations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "control" / "policies" / "source-availability.yaml"
TIMESTAMP_FIELDS = (
    "event_at",
    "published_at",
    "observed_at",
    "ingested_at",
    "effective_at",
    "finalised_at",
)


class TemporalPolicyError(ValueError):
    """Raised when no valid, explicit availability policy applies."""


class TemporalValidationError(ValueError):
    """Raised when an observation violates the temporal contract."""


def load_availability_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or DEFAULT_POLICY
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or not policy.get("policy_version"):
        raise TemporalPolicyError(f"Invalid availability policy: {policy_path}")
    return policy


def parse_aware_datetime(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise TemporalValidationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TemporalValidationError(f"{field} must include a timezone offset")
    return parsed


def _canonical_timestamp(value: str, *, field: str) -> str:
    parsed = parse_aware_datetime(value, field=field).astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _field_policy(policy: dict[str, Any], source_id: str, field_name: str) -> dict[str, Any]:
    try:
        result = policy["sources"][source_id]["fields"][field_name]
    except (KeyError, TypeError) as exc:
        raise TemporalPolicyError(
            f"No availability policy for source={source_id!r}, field={field_name!r}"
        ) from exc
    if not isinstance(result, dict) or result.get("strategy") != "latest_of":
        raise TemporalPolicyError(
            f"Unsupported availability policy for source={source_id!r}, field={field_name!r}"
        )
    return result


def _derive_available_at(
    timestamps: dict[str, str | None], field_policy: dict[str, Any]
) -> str:
    candidates: list[datetime] = []
    missing_policy = field_policy.get("when_missing", {})
    for field in field_policy.get("timestamps", []):
        value = timestamps.get(field)
        if value is not None:
            candidates.append(parse_aware_datetime(value, field=field))
            continue
        action = missing_policy.get(field, "error")
        if action == "retain_missing":
            continue
        if action == "use_ingested_at":
            ingested_at = timestamps.get("ingested_at")
            if ingested_at is None:
                raise TemporalValidationError("ingested_at is required for conservative fallback")
            candidates.append(parse_aware_datetime(ingested_at, field="ingested_at"))
            continue
        raise TemporalValidationError(
            f"{field} is missing and policy action {action!r} does not permit it"
        )
    if not candidates:
        raise TemporalPolicyError("Availability policy produced no timestamp candidates")
    return max(candidates).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _observation_id(envelope: dict[str, Any]) -> str:
    payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalise_observation(
    observation: dict[str, Any], *, policy_path: Path | None = None
) -> dict[str, Any]:
    """Validate and wrap one observation under an explicit source/field policy."""

    policy = load_availability_policy(policy_path)
    source_id = str(observation.get("source_id", ""))
    field_name = str(observation.get("field_name", ""))
    entity_id = str(observation.get("entity_id", ""))
    if not source_id or not field_name or not entity_id:
        raise TemporalValidationError("source_id, field_name and entity_id are required")

    field_policy = _field_policy(policy, source_id, field_name)
    timestamps: dict[str, str | None] = {}
    for field in TIMESTAMP_FIELDS:
        value = observation.get(field)
        timestamps[field] = None if value is None else _canonical_timestamp(value, field=field)

    for required in ("observed_at", "ingested_at"):
        if timestamps[required] is None:
            raise TemporalValidationError(f"{required} is required")
    observed = parse_aware_datetime(timestamps["observed_at"], field="observed_at")
    ingested = parse_aware_datetime(timestamps["ingested_at"], field="ingested_at")
    if ingested < observed:
        raise TemporalValidationError("ingested_at cannot precede observed_at")

    envelope: dict[str, Any] = {
        "observation_version": "1.0",
        "policy_version": str(policy["policy_version"]),
        "source_id": source_id,
        "field_name": field_name,
        "entity_id": entity_id,
        "source_record_id": observation.get("source_record_id"),
        **timestamps,
        "available_at": _derive_available_at(timestamps, field_policy),
        "value": observation.get("value"),
        "correction_of": observation.get("correction_of"),
    }
    envelope["observation_id"] = _observation_id(envelope)
    return envelope


def observations_as_of(
    observations: Iterable[dict[str, Any]], cutoff: str
) -> list[dict[str, Any]]:
    """Return the latest eligible value per source/field/entity at an inclusive cutoff."""

    cutoff_at = parse_aware_datetime(cutoff, field="cutoff").astimezone(timezone.utc)
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    eligible = [
        observation
        for observation in observations
        if parse_aware_datetime(observation["available_at"], field="available_at") <= cutoff_at
    ]
    eligible.sort(key=lambda row: (row["available_at"], row["observation_id"]))
    for observation in eligible:
        key = (
            str(observation["source_id"]),
            str(observation["field_name"]),
            str(observation["entity_id"]),
        )
        latest[key] = observation
    return [latest[key] for key in sorted(latest)]
