"""Rotowire FPL editorial rankings manual-citation packs.

No network access. Operators paste structured ranking rows; this module seals
an immutable citation envelope for short-horizon editorial priors.
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


ROTOWIRE_EDITORIAL_SOURCE_ID = "rotowire-fpl-editorial"
ROTOWIRE_EDITORIAL_PROVIDER_ID = "rotowire-fpl-editorial"
ROTOWIRE_RANKINGS_SCHEMA = "rotowire-fpl-short-horizon-rankings-citation-v1"

POSITION_ALIASES = {
    "G": "GKP",
    "GK": "GKP",
    "GKP": "GKP",
    "D": "DEF",
    "DEF": "DEF",
    "M": "MID",
    "MID": "MID",
    "F": "FWD",
    "FW": "FWD",
    "FWD": "FWD",
}


class RotowireRankingsError(LineupsMinutesError):
    """Raised when a rankings citation pack is incomplete or unsafe."""


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
        raise RotowireRankingsError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RotowireRankingsError(f"{field} must include timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _position(value: Any) -> str:
    token = str(value or "").strip().upper()
    if token not in POSITION_ALIASES:
        raise RotowireRankingsError(
            f"unsupported position {value!r}; use GKP/DEF/MID/FWD (or G/D/M/F)"
        )
    return POSITION_ALIASES[token]


def _price(value: Any) -> float:
    try:
        price = float(value)
    except (TypeError, ValueError) as exc:
        raise RotowireRankingsError(f"price must be numeric, got {value!r}") from exc
    if price <= 0:
        raise RotowireRankingsError(f"price must be positive, got {price}")
    return round(price, 1)


def _score(value: Any, field: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise RotowireRankingsError(f"{field} must be numeric") from exc
    return round(score, 3)


def _normalise_player(row: Mapping[str, Any], *, expected_rank: int) -> dict[str, Any]:
    rank = int(row.get("rank") or expected_rank)
    if rank != expected_rank:
        raise RotowireRankingsError(
            f"player ranks must be contiguous; expected {expected_rank}, got {rank}"
        )
    name = str(row.get("name") or "").strip()
    if not name:
        raise RotowireRankingsError(f"rank {rank}: player name is required")
    team = str(row.get("team") or row.get("team_name") or "").strip()
    team_code = str(row.get("team_code") or "").strip().upper()
    if not team and not team_code:
        raise RotowireRankingsError(f"rank {rank}: team or team_code is required")
    slug = "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")
    provider_player_id = str(row.get("provider_player_id") or "").strip() or (
        f"rw:rank:{rank}:{slug}"
    )
    return {
        "rank": rank,
        "provider_player_id": provider_player_id,
        "name": name,
        "team": team or team_code,
        "team_code": team_code or None,
        "position": _position(row.get("position")),
        "price": _price(row.get("price")),
        "adjusted_total": _score(row.get("adjusted_total"), "adjusted_total"),
    }


def _normalise_team_fixture_ranks(
    rows: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        rank = int(row.get("rank") or index)
        team = str(row.get("team") or "").strip()
        if not team:
            raise RotowireRankingsError(f"team_fixture_ranks[{index}]: team required")
        out.append(
            {
                "rank": rank,
                "team": team,
                "team_code": str(row.get("team_code") or "").strip().upper() or None,
                "opening_5_read": str(row.get("opening_5_read") or "").strip() or None,
            }
        )
    return out


def build_rotowire_short_horizon_rankings_pack(
    *,
    players: Sequence[Mapping[str, Any]],
    observed_at: str,
    published_at: str | None = None,
    available_at: str | None = None,
    citation_url: str | None = None,
    citation_title: str,
    author: str = "Adam Zdroik",
    publisher: str = "RotoWire",
    season: str = "2026-27",
    horizon_gameweeks: Sequence[int] | None = None,
    team_fixture_ranks: Sequence[Mapping[str, Any]] | None = None,
    narrative: Mapping[str, Any] | None = None,
    notes: str | None = None,
    require_registry: bool = True,
) -> dict[str, Any]:
    """Seal a short-horizon FPL rankings citation pack (no network)."""

    if require_registry:
        source = assert_collectable(ROTOWIRE_EDITORIAL_SOURCE_ID)
        if source.get("collection_method") != "manual_citation":
            raise RotowireRankingsError(
                "rotowire-fpl-editorial must remain manual_citation in the registry"
            )

    if not players:
        raise RotowireRankingsError("at least one ranked player is required")
    if not str(citation_title).strip():
        raise RotowireRankingsError("citation_title is required")

    observed_text, observed_dt = _time(observed_at, "observed_at")
    published_text, published_dt = _time(
        published_at if published_at is not None else observed_at, "published_at"
    )
    available_text, available_dt = _time(
        available_at if available_at is not None else published_at or observed_at,
        "available_at",
    )
    if published_dt > observed_dt or available_dt > observed_dt:
        raise RotowireRankingsError(
            "published_at/available_at must not be after observed_at"
        )

    normalised_players = [
        _normalise_player(row, expected_rank=index)
        for index, row in enumerate(players, start=1)
    ]
    horizon = [int(gw) for gw in (horizon_gameweeks or [1, 2, 3, 4, 5])]
    if horizon != sorted(horizon) or min(horizon) < 1:
        raise RotowireRankingsError("horizon_gameweeks must be ascending positive ints")

    url = str(citation_url).strip() if citation_url else ""
    pack = {
        "schema_version": ROTOWIRE_RANKINGS_SCHEMA,
        "provider_id": ROTOWIRE_EDITORIAL_PROVIDER_ID,
        "source_id": ROTOWIRE_EDITORIAL_SOURCE_ID,
        "season": season,
        "horizon_gameweeks": horizon,
        "window_label": "FPL short-horizon rankings (manual citation)",
        "observed_at": observed_text,
        "available_at": available_text,
        "citation": {
            "url": url or None,
            "canonical_url_status": "resolved" if url else "pending_owner_url",
            "title": str(citation_title).strip(),
            "author": str(author).strip(),
            "publisher": str(publisher),
            "published_at": published_text,
            "capture_method": "manual_citation",
            "redistribution": False,
            "network_fetch": False,
        },
        "player_count": len(normalised_players),
        "players": normalised_players,
        "team_fixture_ranks": _normalise_team_fixture_ranks(team_fixture_ranks),
        "narrative": deepcopy(dict(narrative or {})),
        "identity_mapping_status": "names_only_pending_fpl_aliases",
        "influence_policy": "editorial_prior_only_no_live_optimiser_selection",
        "notes": notes
        or (
            "Short-horizon editorial rankings transcribed by the owner from "
            "RotoWire. Not expected-minutes evidence; not an official projection."
        ),
        "account_writes": False,
        "browser_actions": False,
    }
    return _seal(pack)


def write_rotowire_short_horizon_rankings_pack(
    pack: Mapping[str, Any],
    path: Path,
) -> str:
    """Create-only write for a sealed Rotowire rankings citation pack."""

    return write_immutable_json(path, pack)
