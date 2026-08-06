"""Rotowire predicted/confirmed lineup manual-citation packs (ADR-0025).

No network access. Operators paste or type structured XI rows; this module
seals an immutable citation envelope for expected-minutes evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from src.ingestion.lineups_minutes import LineupsMinutesError, write_immutable_json
from src.ingestion.registry import assert_collectable


ROTOWIRE_PROVIDER_ID = "rotowire-lineups"
ROTOWIRE_SOURCE_ID = "rotowire-lineups"
ROTOWIRE_CITATION_SCHEMA = "rotowire-predicted-lineups-citation-v1"
DEFAULT_CITATION_URL = "https://www.rotowire.com/soccer/lineups.php"


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


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


def _normalise_player(row: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    name = str(row.get("name") or "").strip()
    if not name:
        raise LineupsMinutesError(f"{role} player name is required")
    slot = str(row.get("slot") or row.get("position") or "").strip()
    status = str(row.get("status") or "expected").strip().lower()
    if status not in {"expected", "ques", "out", "sus", "confirmed"}:
        raise LineupsMinutesError(
            f"unsupported player status {status!r}; use expected/ques/out/sus/confirmed"
        )
    provider_player_id = str(row.get("provider_player_id") or "").strip()
    if not provider_player_id:
        club = str(row.get("club_code") or "unk").strip().lower()
        slug = "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")
        provider_player_id = f"rw:{club}:{slug}"
    return {
        "provider_player_id": provider_player_id,
        "name": name,
        "slot": slot or None,
        "status": status,
        "role": role,
        "started": role == "starting_xi",
    }


def _normalise_xi(
    rows: Sequence[Mapping[str, Any]], *, club_code: str
) -> list[dict[str, Any]]:
    if len(rows) != 11:
        raise LineupsMinutesError(
            f"predicted starting XI for {club_code} must contain exactly 11 players"
        )
    players: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        payload = dict(row)
        payload.setdefault("club_code", club_code)
        player = _normalise_player(payload, role="starting_xi")
        if player["provider_player_id"] in seen:
            raise LineupsMinutesError(
                f"duplicate provider_player_id in {club_code} XI: "
                f"{player['provider_player_id']}"
            )
        seen.add(player["provider_player_id"])
        players.append(player)
    return players


def _normalise_notes(
    rows: Sequence[Mapping[str, Any]] | None, *, club_code: str
) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for row in rows or []:
        payload = dict(row)
        payload.setdefault("club_code", club_code)
        status = str(payload.get("status") or "ques").strip().lower()
        payload["status"] = status
        notes.append(_normalise_player(payload, role="injury_note"))
    return notes


def build_rotowire_predicted_lineup_pack(
    *,
    fixtures: Sequence[Mapping[str, Any]],
    observed_at: str,
    published_at: str | None = None,
    available_at: str | None = None,
    citation_url: str = DEFAULT_CITATION_URL,
    publisher: str = "RotoWire",
    season: str = "2026-27",
    gameweek: int | None = 1,
    window_label: str | None = None,
    notes: str | None = None,
    require_registry: bool = True,
) -> dict[str, Any]:
    """Seal a multi-fixture predicted-lineup citation pack (no network)."""

    if require_registry:
        source = assert_collectable(ROTOWIRE_SOURCE_ID)
        if source.get("collection_method") != "manual_citation":
            raise LineupsMinutesError(
                "rotowire-lineups must remain manual_citation in the registry"
            )

    if not fixtures:
        raise LineupsMinutesError("at least one fixture is required")

    observed_text, observed_dt = _time(observed_at, "observed_at")
    published_text, published_dt = _time(
        published_at if published_at is not None else observed_at, "published_at"
    )
    available_text, available_dt = _time(
        available_at if available_at is not None else published_at or observed_at,
        "available_at",
    )
    if published_dt > observed_dt or available_dt > observed_dt:
        raise LineupsMinutesError(
            "published_at/available_at must not be after observed_at"
        )

    normalised: list[dict[str, Any]] = []
    for index, row in enumerate(fixtures):
        if not isinstance(row, Mapping):
            raise LineupsMinutesError(f"fixtures[{index}] must be an object")
        home_code = str(row.get("home_code") or "").strip().upper()
        away_code = str(row.get("away_code") or "").strip().upper()
        if not home_code or not away_code:
            raise LineupsMinutesError("home_code and away_code are required")
        kickoff = _time(row.get("kickoff_at"), "kickoff_at")[0]
        provider_fixture_id = str(
            row.get("provider_fixture_id")
            or f"rw:{season}:gw{int(gameweek or 0):02d}:{home_code}-{away_code}:{kickoff}"
        )
        home_xi = _normalise_xi(list(row.get("home_xi") or []), club_code=home_code)
        away_xi = _normalise_xi(list(row.get("away_xi") or []), club_code=away_code)
        normalised.append(
            {
                "provider_fixture_id": provider_fixture_id,
                "kickoff_at": kickoff,
                "home_code": home_code,
                "away_code": away_code,
                "home_club": str(row.get("home_club") or home_code),
                "away_club": str(row.get("away_club") or away_code),
                "prediction_kind": str(row.get("prediction_kind") or "predicted"),
                "home_xi": home_xi,
                "away_xi": away_xi,
                "home_injury_notes": _normalise_notes(
                    list(row.get("home_injuries") or []), club_code=home_code
                ),
                "away_injury_notes": _normalise_notes(
                    list(row.get("away_injuries") or []), club_code=away_code
                ),
            }
        )

    pack = {
        "schema_version": ROTOWIRE_CITATION_SCHEMA,
        "provider_id": ROTOWIRE_PROVIDER_ID,
        "source_id": ROTOWIRE_SOURCE_ID,
        "season": season,
        "gameweek": gameweek,
        "window_label": window_label
        or "Premier League predicted lineups (manual citation)",
        "observed_at": observed_text,
        "available_at": available_text,
        "citation": {
            "url": str(citation_url),
            "publisher": str(publisher),
            "published_at": published_text,
            "capture_method": "manual_citation",
            "redistribution": False,
            "network_fetch": False,
        },
        "fixture_count": len(normalised),
        "fixtures": normalised,
        "identity_mapping_status": "names_only_pending_fpl_aliases",
        "notes": notes
        or (
            "Predicted XIs transcribed by the owner from RotoWire. "
            "Not confirmed team sheets. Official sheets remain adjudication truth."
        ),
        "account_writes": False,
        "browser_actions": False,
    }
    return _seal(pack)


def write_rotowire_predicted_lineup_pack(
    pack: Mapping[str, Any],
    path: Path,
) -> str:
    """Create-only write for a sealed Rotowire citation pack."""

    return write_immutable_json(path, pack)
