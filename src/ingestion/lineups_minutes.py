"""Cutoff-safe provider lineup snapshots reconciled to official FPL minutes."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


class LineupsMinutesError(ValueError):
    pass


DEGRADED_REASONS = frozenset(
    {
        "missing_credential",
        "timeout",
        "rate_limited",
        "provider_outage",
        "trial_access_gated",
        "no_provider_selected",
        "empty_snapshot",
    }
)


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def artifact_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _time(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LineupsMinutesError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise LineupsMinutesError(f"{field} must include timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _alias_index(
    aliases: Mapping[str, Any], provider_id: str
) -> tuple[dict[str, str], dict[str, str]]:
    players: dict[str, str] = {}
    fixtures: dict[str, str] = {}
    for row in aliases.get("aliases", []):
        if not isinstance(row, Mapping) or str(row.get("provider_id")) != provider_id:
            continue
        kind = str(row.get("entity_type"))
        external = str(row.get("provider_entity_id"))
        canonical = str(row.get("fpl_entity_id"))
        if kind not in {"player", "fixture"} or not external or not canonical:
            raise LineupsMinutesError("Invalid lineup provider alias")
        target = players if kind == "player" else fixtures
        if external in target and target[external] != canonical:
            raise LineupsMinutesError("Conflicting lineup provider alias")
        target[external] = canonical
    return players, fixtures


def provider_credential_status(
    config: Mapping[str, Any], *, environ: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Report credential presence for registered candidates without printing secrets."""

    env = environ if environ is not None else os.environ
    rows: list[dict[str, Any]] = []
    for item in config.get("providers", []):
        if not isinstance(item, Mapping):
            raise LineupsMinutesError("providers entries must be objects")
        provider_id = str(item.get("provider_id", ""))
        env_name = str(item.get("credential_environment", ""))
        present = bool(env_name and env.get(env_name))
        rows.append(
            {
                "provider_id": provider_id,
                "credential_environment": env_name,
                "credential_present": present,
                "status": str(item.get("status", "candidate")),
                # Never echo credential values.
                "value_redacted": True,
            }
        )
    any_present = any(row["credential_present"] for row in rows)
    return _seal(
        {
            "schema_version": "1.0",
            "season": config.get("season"),
            "selected_provider": config.get("selected_provider"),
            "any_candidate_credential_present": any_present,
            "providers": rows,
            "account_writes": False,
        }
    )


def degraded_lineups_family(
    *,
    reason: str,
    observed_at: str,
    provider_id: str | None = None,
    detail: str | None = None,
    retry_scheduled: bool = False,
) -> dict[str, Any]:
    """Return a safe degraded feature-family artifact that never invents minutes."""

    if reason not in DEGRADED_REASONS:
        raise LineupsMinutesError(f"Unsupported degraded reason: {reason}")
    observed_text, _ = _time(observed_at, "observed_at")
    if retry_scheduled:
        raise LineupsMinutesError(
            "Network retry storms are forbidden; retry_scheduled must be false"
        )
    return _seal(
        {
            "schema_version": "1.0",
            "family": "lineups_minutes",
            "status": "degraded",
            "reason": reason,
            "detail": detail,
            "provider_id": provider_id,
            "observed_at": observed_text,
            "available_at": observed_text,
            "players": [],
            "quality": {
                "gaps": [reason],
                "quarantined_player_count": 0,
                "retry_scheduled": False,
            },
            "oracle": "fpl-official-endpoints",
            "baseline_unchanged": True,
            "account_writes": False,
        }
    )


def capture_provider_snapshot_or_degrade(
    *,
    config: Mapping[str, Any],
    provider_id: str,
    observed_at: str,
    environ: Mapping[str, str] | None = None,
    fetch: Any | None = None,
) -> dict[str, Any]:
    """Attempt a live provider capture only when a credential is present.

    Without a credential, or when the fetch reports timeout / rate-limit /
    outage, return a degraded family. Never retries. Never mutates the shared
    structured baseline.
    """

    providers = {
        str(item.get("provider_id")): item
        for item in config.get("providers", [])
        if isinstance(item, Mapping)
    }
    if provider_id not in providers:
        raise LineupsMinutesError("Unregistered provider")
    if config.get("selected_provider") not in {None, provider_id}:
        return degraded_lineups_family(
            reason="no_provider_selected",
            observed_at=observed_at,
            provider_id=provider_id,
            detail="selected_provider is null or different; capture refused",
        )

    env_name = str(providers[provider_id].get("credential_environment", ""))
    env = environ if environ is not None else os.environ
    if not env_name or not env.get(env_name):
        return degraded_lineups_family(
            reason="missing_credential",
            observed_at=observed_at,
            provider_id=provider_id,
            detail=f"environment variable {env_name or '<unset>'} is absent",
        )

    if fetch is None:
        # Live HTTP collectors stay behind FPL-cm6 / credential operationalisation.
        return degraded_lineups_family(
            reason="trial_access_gated",
            observed_at=observed_at,
            provider_id=provider_id,
            detail="credential present but live collector not activated",
        )

    try:
        snapshot = fetch(provider_id=provider_id)
    except TimeoutError:
        return degraded_lineups_family(
            reason="timeout",
            observed_at=observed_at,
            provider_id=provider_id,
            detail="provider request timed out",
        )
    except ConnectionError:
        return degraded_lineups_family(
            reason="provider_outage",
            observed_at=observed_at,
            provider_id=provider_id,
            detail="provider connection failed",
        )

    if not isinstance(snapshot, Mapping):
        raise LineupsMinutesError("provider fetch must return a mapping")
    if snapshot.get("http_status") == 429:
        return degraded_lineups_family(
            reason="rate_limited",
            observed_at=observed_at,
            provider_id=provider_id,
            detail="provider returned HTTP 429; no retry scheduled",
        )
    if snapshot.get("acquisition_status") != "success":
        return degraded_lineups_family(
            reason="provider_outage",
            observed_at=observed_at,
            provider_id=provider_id,
            detail=str(snapshot.get("acquisition_status", "failed")),
        )
    if not snapshot.get("players"):
        return degraded_lineups_family(
            reason="empty_snapshot",
            observed_at=observed_at,
            provider_id=provider_id,
        )
    return _seal(dict(snapshot))


def reconcile_lineups_minutes(
    provider_snapshot: Mapping[str, Any],
    *,
    fpl_minutes: Mapping[str, Any],
    aliases: Mapping[str, Any],
    config: Mapping[str, Any],
    cutoff: str,
) -> dict[str, Any]:
    """Map a captured provider fixture to FPL IDs and quarantine disagreements."""

    if config.get("schema_version") != "1.0":
        raise LineupsMinutesError("Unsupported config schema")
    cutoff_text, cutoff_at = _time(cutoff, "cutoff")
    provider_id = str(provider_snapshot.get("provider_id", ""))
    if provider_id not in {
        str(item.get("provider_id")) for item in config.get("providers", [])
    }:
        raise LineupsMinutesError("Unregistered provider")
    observed_text, observed_at = _time(
        provider_snapshot.get("observed_at"), "provider.observed_at"
    )
    if observed_at > cutoff_at:
        raise LineupsMinutesError("Provider snapshot is after cutoff")
    available_raw = provider_snapshot.get("available_at", observed_text)
    available_text, available_at = _time(available_raw, "provider.available_at")
    if available_at > cutoff_at:
        raise LineupsMinutesError("Provider available_at is after cutoff")

    player_aliases, fixture_aliases = _alias_index(aliases, provider_id)
    fixture_id = fixture_aliases.get(str(provider_snapshot.get("provider_fixture_id")))
    if fixture_id is None:
        raise LineupsMinutesError("Missing explicit fixture alias")
    oracle = fpl_minutes.get(fixture_id)
    if not isinstance(oracle, Mapping):
        raise LineupsMinutesError("Missing FPL reconciliation fixture")
    rows = provider_snapshot.get("players")
    if not isinstance(rows, list):
        raise LineupsMinutesError("provider.players must be a list")

    out: list[dict[str, Any]] = []
    gaps: list[str] = []
    quarantined = 0
    source_id = str(provider_snapshot.get("source_id", provider_id))
    source_version = str(provider_snapshot.get("source_version", "unknown"))
    source_sha256 = provider_snapshot.get("content_sha256") or provider_snapshot.get(
        "source_sha256"
    )

    for row in rows:
        if not isinstance(row, Mapping):
            raise LineupsMinutesError("provider player must be an object")
        provider_player_id = str(row.get("provider_player_id", ""))
        fpl_id = player_aliases.get(provider_player_id)
        if fpl_id is None:
            gaps.append(f"unmapped_provider_player:{provider_player_id}")
            continue
        minutes = row.get("minutes")
        if (
            isinstance(minutes, bool)
            or not isinstance(minutes, int)
            or not 0 <= minutes <= 130
        ):
            raise LineupsMinutesError(
                "provider minutes must be an integer from 0 to 130"
            )
        expected = oracle.get(fpl_id)
        if not isinstance(expected, int):
            status = "quarantined"
            reasons = ["missing_fpl_oracle_minutes"]
            quarantined += 1
            admitted_minutes = None
        elif abs(minutes - expected) > int(config["minutes_tolerance"]):
            status = "quarantined"
            reasons = ["minutes_disagreement"]
            quarantined += 1
            admitted_minutes = None
        else:
            status = "admitted"
            reasons = []
            admitted_minutes = minutes
        out.append(
            {
                "fpl_player_id": fpl_id,
                "provider_player_id": provider_player_id,
                "started": bool(row.get("started")),
                "minutes": admitted_minutes,
                "status": status,
                "reasons": reasons,
            }
        )

    status = "complete" if out and not gaps and not quarantined else "degraded"
    return _seal(
        {
            "schema_version": "1.0",
            "fixture_id": fixture_id,
            "provider_id": provider_id,
            "source_id": source_id,
            "source_version": source_version,
            "source_sha256": source_sha256,
            "observed_at": observed_text,
            "available_at": available_text,
            "cutoff": cutoff_text,
            "status": status,
            "players": sorted(out, key=lambda item: item["fpl_player_id"]),
            "quality": {
                "gaps": sorted(gaps),
                "quarantined_player_count": quarantined,
                "admitted_player_count": sum(
                    1 for row in out if row["status"] == "admitted"
                ),
                "identity_coverage": (
                    1.0
                    if not gaps and out
                    else (
                        round(len(out) / (len(out) + len(gaps)), 6)
                        if (out or gaps)
                        else 0.0
                    )
                ),
            },
            "oracle": "fpl-official-endpoints",
            "account_writes": False,
        }
    )


def write_immutable_json(path: str | Path, value: Mapping[str, Any]) -> str:
    target = Path(path)
    encoded = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise FileExistsError(f"Refusing to overwrite immutable artifact: {target}")
        return "identical"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")
    return "created"
