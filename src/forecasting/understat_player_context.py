"""Identity-safe Understat player rates for the live-faithful event path."""

from __future__ import annotations

from copy import deepcopy
import re
import unicodedata
from typing import Any, Mapping

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.understat_team_context import UNDERSTAT_TITLE_TO_FPL_NAME


class UnderstatPlayerContextError(ValueError):
    """Raised when Understat player context is malformed."""


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _finite(value: Any, field: str, *, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise UnderstatPlayerContextError(f"{field} must be numeric") from exc
    if number < minimum:
        raise UnderstatPlayerContextError(f"{field} must be at least {minimum}")
    return number


def _player_name_keys(full_name: str, *, web_name: str | None = None) -> set[str]:
    keys = {_norm(full_name)}
    if web_name:
        keys.add(_norm(web_name))
    parts = _norm(full_name).split()
    if parts:
        keys.add(parts[-1])
        if len(parts) >= 2:
            keys.add(f"{parts[0][0]} {parts[-1]}")
            keys.add(f"{parts[0][0]}.{parts[-1]}")
            keys.add(" ".join(parts[-2:]))
    return {key for key in keys if key}


def _bootstrap_players(bootstrap: Mapping[str, Any]) -> list[dict[str, Any]]:
    teams = bootstrap.get("teams")
    elements = bootstrap.get("elements")
    if not isinstance(teams, list) or not isinstance(elements, list):
        raise UnderstatPlayerContextError(
            "bootstrap must include teams and elements lists"
        )
    team_name = {}
    for raw in teams:
        if not isinstance(raw, Mapping):
            continue
        try:
            team_name[int(raw["id"])] = str(raw["name"])
        except (KeyError, TypeError, ValueError):
            continue
    rows: list[dict[str, Any]] = []
    for raw in elements:
        if not isinstance(raw, Mapping):
            continue
        try:
            player_id = str(int(raw["id"]))
            fpl_code = int(raw["code"])
            team_id = int(raw["team"])
            first = str(raw.get("first_name", "")).strip()
            second = str(raw.get("second_name", "")).strip()
            web_name = str(raw.get("web_name", "")).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise UnderstatPlayerContextError(
                "bootstrap element requires id, code and team"
            ) from exc
        full = f"{first} {second}".strip()
        rows.append(
            {
                "player_id": player_id,
                "fpl_code": fpl_code,
                "web_name": web_name,
                "full_name": full,
                "club_id": str(team_id),
                "team_name": team_name.get(team_id, ""),
                "name_keys": _player_name_keys(full, web_name=web_name),
            }
        )
    return rows


def _understat_team_titles(raw_title: str) -> list[str]:
    return [part.strip() for part in str(raw_title).split(",") if part.strip()]


def build_understat_player_join(
    *,
    bootstrap: Mapping[str, Any],
    understat_capture: Mapping[str, Any],
) -> dict[str, Any]:
    """Join Understat player rows to FPL identities with explicit quarantine."""

    fpl_players = _bootstrap_players(bootstrap)
    by_club: dict[str, list[dict[str, Any]]] = {}
    by_code: dict[int, dict[str, Any]] = {}
    for row in fpl_players:
        by_club.setdefault(row["club_id"], []).append(row)
        by_code[int(row["fpl_code"])] = row

    fpl_name_to_club = {
        str(team["name"]): str(int(team["id"]))
        for team in bootstrap.get("teams", [])
        if isinstance(team, Mapping)
    }

    players = understat_capture.get("players")
    if players is None:
        players = []
    if not isinstance(players, list):
        raise UnderstatPlayerContextError("understat capture players must be a list")

    matched: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    rates_by_fpl_code: dict[int, dict[str, Any]] = {}

    for index, raw in enumerate(players):
        if not isinstance(raw, Mapping):
            raise UnderstatPlayerContextError(
                f"understat players[{index}] must be an object"
            )
        name = str(raw.get("player_name", "")).strip()
        if not name:
            unmatched.append(
                {
                    "understat_player_id": str(raw.get("id", "")),
                    "reason": "missing_player_name",
                }
            )
            continue
        try:
            minutes = _finite(raw.get("time", 0), "time")
            xg = _finite(raw.get("xG", 0), "xG")
            xa = _finite(raw.get("xA", 0), "xA")
        except UnderstatPlayerContextError as exc:
            unmatched.append(
                {
                    "understat_player_id": str(raw.get("id", "")),
                    "player_name": name,
                    "reason": f"invalid_rates:{exc}",
                }
            )
            continue

        titles = _understat_team_titles(str(raw.get("team_title", "")))
        club_ids: list[str] = []
        for title in titles:
            fpl_name = UNDERSTAT_TITLE_TO_FPL_NAME.get(title)
            if fpl_name is None:
                continue
            club_id = fpl_name_to_club.get(fpl_name)
            if club_id is not None:
                club_ids.append(club_id)

        name_keys = _player_name_keys(name)
        candidates: dict[int, dict[str, Any]] = {}
        match_basis = "team_scoped_name"

        search_pools: list[list[dict[str, Any]]]
        if club_ids:
            search_pools = [by_club.get(club_id, []) for club_id in club_ids]
        else:
            search_pools = [fpl_players]
            match_basis = "global_unique_name"

        for pool in search_pools:
            for row in pool:
                if name_keys & set(row["name_keys"]):
                    candidates[int(row["fpl_code"])] = row

        # Dual-club / transferred: if team-scoped missed, try unique global full-name.
        if not candidates and club_ids:
            full_key = _norm(name)
            global_hits = [
                row
                for row in fpl_players
                if _norm(row["full_name"]) == full_key and full_key
            ]
            if len(global_hits) == 1:
                candidates[int(global_hits[0]["fpl_code"])] = global_hits[0]
                match_basis = "cross_club_unique_full_name"
            elif len(global_hits) > 1:
                quarantined.append(
                    {
                        "understat_player_id": str(raw.get("id", "")),
                        "player_name": name,
                        "team_title": str(raw.get("team_title", "")),
                        "reason": "ambiguous_cross_club_full_name",
                        "candidate_fpl_codes": sorted(
                            int(row["fpl_code"]) for row in global_hits
                        ),
                    }
                )
                continue

        if len(candidates) > 1:
            quarantined.append(
                {
                    "understat_player_id": str(raw.get("id", "")),
                    "player_name": name,
                    "team_title": str(raw.get("team_title", "")),
                    "reason": "ambiguous_name_match",
                    "candidate_fpl_codes": sorted(candidates),
                    "match_basis": match_basis,
                }
            )
            continue
        if not candidates:
            unmatched.append(
                {
                    "understat_player_id": str(raw.get("id", "")),
                    "player_name": name,
                    "team_title": str(raw.get("team_title", "")),
                    "reason": (
                        "not_in_current_bootstrap_universe"
                        if not club_ids
                        else "name_not_matched"
                    ),
                    "resolved_club_ids": club_ids,
                }
            )
            continue

        fpl_code = next(iter(candidates))
        per90_minutes = minutes / 90.0 if minutes > 0 else 0.0
        rates = {
            "fpl_code": fpl_code,
            "player_id": candidates[fpl_code]["player_id"],
            "understat_player_id": str(raw.get("id", "")),
            "player_name": name,
            "match_basis": match_basis,
            "sample_minutes": int(round(minutes)),
            "expected_goals_per_90": (
                round(xg / per90_minutes, 6) if per90_minutes > 0 else 0.0
            ),
            "expected_assists_per_90": (
                round(xa / per90_minutes, 6) if per90_minutes > 0 else 0.0
            ),
        }
        # Prefer the higher-minutes Understat row when an FPL code appears twice.
        existing = rates_by_fpl_code.get(fpl_code)
        if existing is None or int(rates["sample_minutes"]) > int(
            existing["sample_minutes"]
        ):
            rates_by_fpl_code[fpl_code] = rates
        matched.append(rates)

    report = {
        "schema_version": "understat-player-join-v1",
        "source_id": str(understat_capture.get("source_id", "understat")),
        "capture_season": str(understat_capture.get("season", "")),
        "bootstrap_player_count": len(fpl_players),
        "understat_player_count": len(players),
        "counts": {
            "matched_rows": len(matched),
            "matched_unique_fpl_codes": len(rates_by_fpl_code),
            "quarantined_ambiguous": len(quarantined),
            "unmatched": len(unmatched),
            "promoted_or_absent_understat_club": sum(
                1
                for row in unmatched
                if row.get("reason") == "not_in_current_bootstrap_universe"
            ),
        },
        "matched": sorted(matched, key=lambda row: int(row["fpl_code"])),
        "quarantined": quarantined,
        "unmatched": unmatched,
        "rates_by_fpl_code": {
            str(code): rates_by_fpl_code[code]
            for code in sorted(rates_by_fpl_code)
        },
    }
    report["content_sha256"] = artifact_hash(report)
    return report


def enrich_player_prior_with_understat_event_rates(
    player_prior: Mapping[str, Any],
    *,
    join_report: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Overlay Understat xG/xA rates onto player-prior event fields only.

    ``points_per_90`` and ``start_probability`` are untouched so
    ``event_model_weight=0`` forecasts remain byte-stable.
    """

    enriched = deepcopy(dict(player_prior))
    rates = join_report.get("rates_by_fpl_code")
    if not isinstance(rates, Mapping) or not rates:
        summary = {
            "status": "absent",
            "players_enriched": 0,
            "join_content_sha256": join_report.get("content_sha256"),
        }
        return enriched, summary

    by_code = {
        int(code): dict(row)
        for code, row in rates.items()
        if isinstance(row, Mapping)
    }
    updated = 0
    for row in enriched.get("players", []):
        if not isinstance(row, dict):
            continue
        try:
            code = int(row["fpl_code"])
        except (KeyError, TypeError, ValueError):
            continue
        rate = by_code.get(code)
        if rate is None:
            continue
        row["expected_goals_per_90"] = float(rate["expected_goals_per_90"])
        row["expected_assists_per_90"] = float(rate["expected_assists_per_90"])
        row["understat_event_rate_source"] = {
            "understat_player_id": rate["understat_player_id"],
            "sample_minutes": int(rate["sample_minutes"]),
            "match_basis": rate["match_basis"],
        }
        updated += 1

    enriched.pop("content_sha256", None)
    enriched["content_sha256"] = artifact_hash(enriched)
    counts = join_report.get("counts", {})
    unique = int(counts.get("matched_unique_fpl_codes", 0) or 0)
    quarantined = int(counts.get("quarantined_ambiguous", 0) or 0)
    if updated == 0:
        status = "absent"
    elif quarantined > 0 or unique > updated:
        status = "partial"
    else:
        status = "applied"
    summary = {
        "status": status,
        "players_enriched": updated,
        "matched_unique_fpl_codes": unique,
        "quarantined_ambiguous": quarantined,
        "unmatched": int(counts.get("unmatched", 0) or 0),
        "join_content_sha256": join_report.get("content_sha256"),
    }
    return enriched, summary
