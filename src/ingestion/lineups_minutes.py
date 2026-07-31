"""Cutoff-safe provider lineup snapshots reconciled to official FPL minutes."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


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
        "provider_not_enabled",
        "rights_unapproved",
        "empty_snapshot",
        "invalid_snapshot",
    }
)

RAW_SNAPSHOT_FIELDS = frozenset(
    {
        "schema_version",
        "provider_id",
        "source_id",
        "source_version",
        "provider_fixture_id",
        "observed_at",
        "available_at",
        "players",
        "acquisition_status",
        "http_status",
        "content_sha256",
        "source_sha256",
    }
)


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def source_snapshot_hash(value: Mapping[str, Any]) -> str:
    """Hash canonical captured source bytes independently of envelope hashes."""

    return hashlib.sha256(
        _bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key not in {"content_sha256", "source_sha256"}
            }
        )
    ).hexdigest()

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


def _provider_entry(config: Mapping[str, Any], provider_id: str) -> Mapping[str, Any]:
    providers = {
        str(item.get("provider_id")): item
        for item in config.get("providers", [])
        if isinstance(item, Mapping)
    }
    if provider_id not in providers:
        raise LineupsMinutesError("Unregistered provider")
    return providers[provider_id]


def provider_activation_gate(
    config: Mapping[str, Any], provider_id: str
) -> str | None:
    """Return a degraded reason if the provider must not be fetched or admitted.

    Exact selection, registry enablement, and completed rights approval are all
    required. A null selected_provider never activates a fetch.
    """

    selected = config.get("selected_provider")
    if selected is None or selected == "":
        return "no_provider_selected"
    if str(selected) != provider_id:
        return "no_provider_selected"
    entry = _provider_entry(config, provider_id)
    if entry.get("registry_enabled") is not True:
        return "provider_not_enabled"
    if entry.get("rights_approved") is not True:
        return "rights_unapproved"
    admission = config.get("admission", {})
    if isinstance(admission, Mapping) and admission.get(
        "owner_approval_required_before_enable", True
    ):
        if entry.get("owner_approved") is not True:
            return "rights_unapproved"
    return None


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
                "registry_enabled": item.get("registry_enabled") is True,
                "rights_approved": item.get("rights_approved") is True,
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


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise LineupsMinutesError(f"{field} must be a boolean")
    return value


def admit_raw_provider_snapshot(
    snapshot: Mapping[str, Any],
    *,
    expected_provider_id: str,
    observed_at: str,
) -> dict[str, Any]:
    """Validate a closed raw-snapshot envelope and seal it before admission."""

    if not isinstance(snapshot, Mapping):
        raise LineupsMinutesError("provider fetch must return a mapping")
    unknown = set(snapshot) - RAW_SNAPSHOT_FIELDS
    if unknown:
        raise LineupsMinutesError(
            f"Raw snapshot contains unexpected fields: {sorted(unknown)}"
        )
    if str(snapshot.get("schema_version")) != "1.0":
        raise LineupsMinutesError("Raw snapshot schema_version must be 1.0")
    if str(snapshot.get("provider_id")) != expected_provider_id:
        raise LineupsMinutesError("Raw snapshot provider_id mismatch")
    if str(snapshot.get("source_id", "")) == "":
        raise LineupsMinutesError("Raw snapshot source_id is required")
    if str(snapshot.get("source_version", "")) == "":
        raise LineupsMinutesError("Raw snapshot source_version is required")
    if str(snapshot.get("provider_fixture_id", "")) == "":
        raise LineupsMinutesError("Raw snapshot provider_fixture_id is required")
    observed_text, provider_observed_at = _time(
        snapshot.get("observed_at"), "provider.observed_at"
    )
    available_text, provider_available_at = _time(
        snapshot.get("available_at", observed_text), "provider.available_at"
    )
    capture_observed_text, _ = _time(observed_at, "observed_at")
    if observed_text != capture_observed_text:
        raise LineupsMinutesError(
            "provider.observed_at must equal capture observed_at"
        )
    if provider_available_at > provider_observed_at:
        raise LineupsMinutesError(
            "provider.available_at must not be after provider.observed_at"
        )
    players = snapshot.get("players")
    if not isinstance(players, list) or not players:
        raise LineupsMinutesError("Raw snapshot players must be a non-empty list")

    sealed_body = {
        "schema_version": "1.0",
        "provider_id": expected_provider_id,
        "source_id": str(snapshot["source_id"]),
        "source_version": str(snapshot["source_version"]),
        "provider_fixture_id": str(snapshot["provider_fixture_id"]),
        "observed_at": observed_text,
        "available_at": available_text,
        "acquisition_status": str(snapshot.get("acquisition_status", "success")),
        "players": deepcopy(list(players)),
    }
    if "http_status" in snapshot:
        sealed_body["http_status"] = snapshot["http_status"]

    source_digest = source_snapshot_hash(sealed_body)
    claimed_source_digest = snapshot.get("source_sha256")
    if (
        claimed_source_digest is not None
        and str(claimed_source_digest) != source_digest
    ):
        raise LineupsMinutesError("Raw snapshot source_sha256 mismatch")
    sealed_body["source_sha256"] = source_digest
    sealed = _seal(sealed_body)
    claimed_content_digest = snapshot.get("content_sha256")
    if (
        claimed_content_digest is not None
        and str(claimed_content_digest) != sealed["content_sha256"]
    ):
        raise LineupsMinutesError("Raw snapshot content hash mismatch")
    return sealed


def verify_snapshot_integrity(snapshot: Mapping[str, Any]) -> str:
    """Recompute and verify the snapshot content digest."""

    digest = artifact_hash(snapshot)
    claimed = snapshot.get("content_sha256")
    if not isinstance(claimed, str) or claimed != digest:
        raise LineupsMinutesError("Provider snapshot content hash mismatch")
    source = snapshot.get("source_sha256")
    if not isinstance(source, str) or source != source_snapshot_hash(snapshot):
        raise LineupsMinutesError("Provider snapshot source_sha256 mismatch")
    return digest

def capture_provider_snapshot_or_degrade(
    *,
    config: Mapping[str, Any],
    provider_id: str,
    observed_at: str,
    environ: Mapping[str, str] | None = None,
    fetch: Any | None = None,
) -> dict[str, Any]:
    """Attempt a live provider capture only when activation gates pass.

    Null selection, disabled registry entries, and incomplete rights approval
    always degrade without invoking fetch. Never retries. Never mutates the
    shared structured baseline.
    """

    gate = provider_activation_gate(config, provider_id)
    if gate is not None:
        return degraded_lineups_family(
            reason=gate,
            observed_at=observed_at,
            provider_id=provider_id,
            detail="provider activation gate refused fetch",
        )

    entry = _provider_entry(config, provider_id)
    env_name = str(entry.get("credential_environment", ""))
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
    try:
        return admit_raw_provider_snapshot(
            snapshot,
            expected_provider_id=provider_id,
            observed_at=observed_at,
        )
    except LineupsMinutesError as exc:
        return degraded_lineups_family(
            reason="invalid_snapshot",
            observed_at=observed_at,
            provider_id=provider_id,
            detail=str(exc),
        )


def _completeness_threshold(config: Mapping[str, Any]) -> dict[str, int]:
    admission = config.get("admission", {})
    if not isinstance(admission, Mapping):
        admission = {}
    return {
        "min_started_xi": int(admission.get("min_started_xi", 11)),
        "min_admitted_players": int(admission.get("min_admitted_players", 11)),
    }


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
    gate = provider_activation_gate(config, provider_id)
    if gate is not None:
        raise LineupsMinutesError(
            f"Reconciliation refused for unselected/unapproved provider: {gate}"
        )
    source_sha256 = verify_snapshot_integrity(provider_snapshot)
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
    seen_provider_ids: set[str] = set()
    seen_fpl_ids: set[str] = set()
    started_count = 0

    for row in rows:
        if not isinstance(row, Mapping):
            raise LineupsMinutesError("provider player must be an object")
        provider_player_id = str(row.get("provider_player_id", ""))
        if not provider_player_id:
            raise LineupsMinutesError("provider_player_id is required")
        if provider_player_id in seen_provider_ids:
            raise LineupsMinutesError(
                f"Duplicate provider_player_id: {provider_player_id}"
            )
        seen_provider_ids.add(provider_player_id)
        started = _require_bool(row.get("started"), "started")
        if started:
            started_count += 1
        fpl_id = player_aliases.get(provider_player_id)
        if fpl_id is None:
            gaps.append(f"unmapped_provider_player:{provider_player_id}")
            continue
        if fpl_id in seen_fpl_ids:
            raise LineupsMinutesError(f"Duplicate fpl_player_id: {fpl_id}")
        seen_fpl_ids.add(fpl_id)
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
                "started": started,
                "minutes": admitted_minutes,
                "status": status,
                "reasons": reasons,
            }
        )

    thresholds = _completeness_threshold(config)
    admitted_count = sum(1 for row in out if row["status"] == "admitted")
    complete = (
        bool(out)
        and not gaps
        and not quarantined
        and started_count >= thresholds["min_started_xi"]
        and admitted_count >= thresholds["min_admitted_players"]
    )
    status = "complete" if complete else "degraded"
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
                "admitted_player_count": admitted_count,
                "started_count": started_count,
                "min_started_xi": thresholds["min_started_xi"],
                "min_admitted_players": thresholds["min_admitted_players"],
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


OFFICIAL_TEAM_SHEETS_PROVIDER = "official-team-sheets"
OFFICIAL_LINEUPS_SOURCE_ID = "official-lineups-minutes"


def build_official_team_sheet_citation(
    *,
    citation_url: str,
    publisher: str,
    published_at: str,
    observed_at: str,
    provider_fixture_id: str,
    starting_xi: Sequence[Mapping[str, Any]],
    substitutions: Sequence[Mapping[str, Any]] | None = None,
    corrections: Sequence[Mapping[str, Any]] | None = None,
    available_at: str | None = None,
    source_version: str = "official-team-sheet-citation-v1",
) -> dict[str, Any]:
    """Seal an immutable official team-sheet citation without network access.

    This is the governed official-path rehearsal builder. It never enables the
    production ``selected_provider`` and never fetches remote pages.
    """

    if not str(citation_url).strip():
        raise LineupsMinutesError("citation_url is required")
    if not str(publisher).strip():
        raise LineupsMinutesError("publisher is required")
    if not str(provider_fixture_id).strip():
        raise LineupsMinutesError("provider_fixture_id is required")

    published_text, published_dt = _time(published_at, "published_at")
    observed_text, observed_dt = _time(observed_at, "observed_at")
    available_text, available_dt = _time(
        available_at if available_at is not None else published_at,
        "available_at",
    )
    if available_dt > observed_dt:
        raise LineupsMinutesError("available_at must not be after observed_at")
    if published_dt > observed_dt:
        raise LineupsMinutesError("published_at must not be after observed_at")

    if len(starting_xi) < 11:
        raise LineupsMinutesError("official citation requires an 11-player starting XI")

    players: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in starting_xi:
        if not isinstance(row, Mapping):
            raise LineupsMinutesError("starting XI rows must be objects")
        player_id = str(row.get("provider_player_id", ""))
        if not player_id or player_id in seen:
            raise LineupsMinutesError("starting XI provider_player_id must be unique")
        seen.add(player_id)
        minutes = row.get("minutes")
        if (
            isinstance(minutes, bool)
            or not isinstance(minutes, int)
            or not 0 <= minutes <= 130
        ):
            raise LineupsMinutesError(
                "citation player minutes must be an integer from 0 to 130"
            )
        players.append(
            {
                "provider_player_id": player_id,
                "started": True,
                "minutes": minutes,
                "role": "starting_xi",
            }
        )

    for row in substitutions or []:
        if not isinstance(row, Mapping):
            raise LineupsMinutesError("substitution rows must be objects")
        player_id = str(row.get("provider_player_id", ""))
        if not player_id or player_id in seen:
            raise LineupsMinutesError("substitution provider_player_id must be unique")
        seen.add(player_id)
        minutes = row.get("minutes")
        if (
            isinstance(minutes, bool)
            or not isinstance(minutes, int)
            or not 0 <= minutes <= 130
        ):
            raise LineupsMinutesError(
                "citation player minutes must be an integer from 0 to 130"
            )
        players.append(
            {
                "provider_player_id": player_id,
                "started": False,
                "minutes": minutes,
                "role": "substitution",
                "on_minute": row.get("on_minute"),
                "off_player_id": row.get("off_player_id"),
            }
        )

    correction_rows = []
    for row in corrections or []:
        if not isinstance(row, Mapping):
            raise LineupsMinutesError("correction rows must be objects")
        correction_rows.append(
            {
                "corrected_at": _time(row.get("corrected_at"), "corrected_at")[0],
                "field": str(row.get("field", "")),
                "from_value": deepcopy(row.get("from_value")),
                "to_value": deepcopy(row.get("to_value")),
                "reason": str(row.get("reason", "")),
            }
        )

    citation_body = {
        "schema_version": "1.0",
        "provider_id": OFFICIAL_TEAM_SHEETS_PROVIDER,
        "source_id": OFFICIAL_LINEUPS_SOURCE_ID,
        "source_version": source_version,
        "provider_fixture_id": str(provider_fixture_id),
        "observed_at": observed_text,
        "available_at": available_text,
        "acquisition_status": "success",
        "players": players,
        "citation": {
            "url": str(citation_url),
            "publisher": str(publisher),
            "published_at": published_text,
            "capture_method": "manual_citation",
            "redistribution": False,
        },
        "corrections": correction_rows,
    }
    # Citation metadata is retained beside the sealed provider envelope via a
    # separate rehearsal pack; the raw admit path only accepts known fields.
    raw_for_admit = {
        key: value
        for key, value in citation_body.items()
        if key in RAW_SNAPSHOT_FIELDS or key == "players"
    }
    # Drop citation-only player keys before admit while preserving minutes/started.
    raw_for_admit["players"] = [
        {
            "provider_player_id": player["provider_player_id"],
            "started": player["started"],
            "minutes": player["minutes"],
        }
        for player in players
    ]
    sealed = admit_raw_provider_snapshot(
        raw_for_admit,
        expected_provider_id=OFFICIAL_TEAM_SHEETS_PROVIDER,
        observed_at=observed_text,
    )
    return _seal(
        {
            "schema_version": "official-team-sheet-citation-v1",
            "provider_snapshot": sealed,
            "citation": citation_body["citation"],
            "corrections": correction_rows,
            "starting_xi_count": sum(1 for player in players if player["started"]),
            "substitution_count": sum(
                1 for player in players if not player["started"]
            ),
            "account_writes": False,
            "network_fetch": False,
        }
    )


def rehearsal_config_for_official_citation(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return a temporary config that admits official citation reconciliation.

    Production ``selected_provider`` remains null in the committed file; this
    helper is only for rehearsal/tests.
    """

    cfg = deepcopy(dict(config))
    cfg["selected_provider"] = OFFICIAL_TEAM_SHEETS_PROVIDER
    found = False
    for item in cfg.get("providers", []):
        if not isinstance(item, Mapping):
            continue
        if item.get("provider_id") != OFFICIAL_TEAM_SHEETS_PROVIDER:
            continue
        item["registry_enabled"] = True
        item["rights_approved"] = True
        item["owner_approved"] = True
        found = True
    if not found:
        raise LineupsMinutesError("official-team-sheets provider is not registered")
    return cfg


def rehearse_official_team_sheet_capture(
    *,
    config: Mapping[str, Any],
    citation_url: str,
    publisher: str,
    published_at: str,
    observed_at: str,
    provider_fixture_id: str,
    starting_xi: Sequence[Mapping[str, Any]],
    fpl_minutes: Mapping[str, Any],
    aliases: Mapping[str, Any],
    cutoff: str,
    substitutions: Sequence[Mapping[str, Any]] | None = None,
    corrections: Sequence[Mapping[str, Any]] | None = None,
    available_at: str | None = None,
) -> dict[str, Any]:
    """Run one complete official citation → reconcile rehearsal pack."""

    if config.get("selected_provider") not in {None, ""}:
        raise LineupsMinutesError(
            "production selected_provider must remain null during citation rehearsal"
        )

    citation = build_official_team_sheet_citation(
        citation_url=citation_url,
        publisher=publisher,
        published_at=published_at,
        observed_at=observed_at,
        available_at=available_at,
        provider_fixture_id=provider_fixture_id,
        starting_xi=starting_xi,
        substitutions=substitutions,
        corrections=corrections,
    )
    reconcile_config = rehearsal_config_for_official_citation(config)
    reconciled = reconcile_lineups_minutes(
        citation["provider_snapshot"],
        fpl_minutes=fpl_minutes,
        aliases=aliases,
        config=reconcile_config,
        cutoff=cutoff,
    )
    return _seal(
        {
            "schema_version": "official-team-sheet-rehearsal-v1",
            "chosen_branch": "official_citation",
            "production_selected_provider": config.get("selected_provider"),
            "citation": citation,
            "reconciliation": reconciled,
            "disagreement_policy": config.get("disagreement_policy"),
            "account_writes": False,
            "network_fetch": False,
        }
    )
