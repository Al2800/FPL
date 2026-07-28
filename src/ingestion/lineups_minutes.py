"""Cutoff-safe provider lineup snapshots reconciled to official FPL minutes."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class LineupsMinutesError(ValueError):
    pass


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def artifact_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_bytes({key: deepcopy(item) for key, item in value.items() if key != "content_sha256"})).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value)); result["content_sha256"] = artifact_hash(result); return result


def _time(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LineupsMinutesError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None: raise LineupsMinutesError(f"{field} must include timezone")
    utc = parsed.astimezone(timezone.utc); return utc.isoformat().replace("+00:00", "Z"), utc


def _alias_index(aliases: Mapping[str, Any], provider_id: str) -> tuple[dict[str, str], dict[str, str]]:
    players: dict[str, str] = {}; fixtures: dict[str, str] = {}
    for row in aliases.get("aliases", []):
        if not isinstance(row, Mapping) or str(row.get("provider_id")) != provider_id: continue
        kind, external, canonical = str(row.get("entity_type")), str(row.get("provider_entity_id")), str(row.get("fpl_entity_id"))
        if kind not in {"player", "fixture"} or not external or not canonical: raise LineupsMinutesError("Invalid lineup provider alias")
        target = players if kind == "player" else fixtures
        if external in target and target[external] != canonical: raise LineupsMinutesError("Conflicting lineup provider alias")
        target[external] = canonical
    return players, fixtures


def reconcile_lineups_minutes(provider_snapshot: Mapping[str, Any], *, fpl_minutes: Mapping[str, Any], aliases: Mapping[str, Any], config: Mapping[str, Any], cutoff: str) -> dict[str, Any]:
    """Map a captured provider fixture to FPL IDs and quarantine disagreements."""
    if config.get("schema_version") != "1.0": raise LineupsMinutesError("Unsupported config schema")
    cutoff_text, cutoff_at = _time(cutoff, "cutoff")
    provider_id = str(provider_snapshot.get("provider_id", ""))
    if provider_id not in {str(item.get("provider_id")) for item in config.get("providers", [])}: raise LineupsMinutesError("Unregistered provider")
    observed_text, observed_at = _time(provider_snapshot.get("observed_at"), "provider.observed_at")
    if observed_at > cutoff_at: raise LineupsMinutesError("Provider snapshot is after cutoff")
    player_aliases, fixture_aliases = _alias_index(aliases, provider_id)
    fixture_id = fixture_aliases.get(str(provider_snapshot.get("provider_fixture_id")))
    if fixture_id is None: raise LineupsMinutesError("Missing explicit fixture alias")
    oracle = fpl_minutes.get(fixture_id)
    if not isinstance(oracle, Mapping): raise LineupsMinutesError("Missing FPL reconciliation fixture")
    rows = provider_snapshot.get("players")
    if not isinstance(rows, list): raise LineupsMinutesError("provider.players must be a list")
    out=[]; gaps=[]; quarantined=0
    for row in rows:
        if not isinstance(row, Mapping): raise LineupsMinutesError("provider player must be an object")
        provider_player_id=str(row.get("provider_player_id", "")); fpl_id=player_aliases.get(provider_player_id)
        if fpl_id is None:
            gaps.append(f"unmapped_provider_player:{provider_player_id}"); continue
        minutes=row.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, int) or not 0 <= minutes <= 130: raise LineupsMinutesError("provider minutes must be an integer from 0 to 130")
        expected=oracle.get(fpl_id)
        if not isinstance(expected, int):
            status="quarantined"; reasons=["missing_fpl_oracle_minutes"]; quarantined += 1
        elif abs(minutes-expected) > int(config["minutes_tolerance"]):
            status="quarantined"; reasons=["minutes_disagreement"]; quarantined += 1
        else: status="admitted"; reasons=[]
        out.append({"fpl_player_id": fpl_id, "provider_player_id": provider_player_id, "started": bool(row.get("started")), "minutes": minutes if status == "admitted" else None, "status": status, "reasons": reasons})
    status="complete" if out and not gaps and not quarantined else "degraded"
    return _seal({"schema_version":"1.0", "fixture_id":fixture_id, "provider_id":provider_id, "observed_at":observed_text, "cutoff":cutoff_text, "status":status, "players":sorted(out,key=lambda item:item["fpl_player_id"]), "quality":{"gaps":sorted(gaps), "quarantined_player_count":quarantined}, "oracle":"fpl-official-endpoints", "account_writes":False})


def write_immutable_json(path: str | Path, value: Mapping[str, Any]) -> str:
    target=Path(path); encoded=json.dumps(value,sort_keys=True,indent=2)+"\n"
    if target.exists():
        if target.read_text() != encoded: raise FileExistsError(f"Refusing to overwrite immutable artifact: {target}")
        return "identical"
    target.parent.mkdir(parents=True,exist_ok=True); target.write_text(encoded); return "created"
