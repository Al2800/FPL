"""Convert The Odds API captures into team-prior 1X2 snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.forecasting.live_faithful import artifact_hash


class LiveOddsTeamPriorError(ValueError):
    """Raised when an odds capture cannot be projected into team-prior slots."""


# Odds API event team names → FPL bootstrap ``teams[].name``.
ODDS_API_NAME_TO_FPL_NAME: dict[str, str] = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "AFC Bournemouth": "Bournemouth",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton and Hove Albion": "Brighton",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry City": "Coventry City",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull City": "Hull City",
    "Ipswich Town": "Ipswich Town",
    "Leeds United": "Leeds",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Man City": "Man City",
    "Manchester United": "Man Utd",
    "Man United": "Man Utd",
    "Newcastle United": "Newcastle",
    "Newcastle": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Spurs",
    "Tottenham": "Spurs",
    "Sunderland": "Sunderland",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
}


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveOddsTeamPriorError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveOddsTeamPriorError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _as_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def discover_latest_odds_capture(root: Path) -> Path | None:
    """Return the newest odds capture JSON under a local shadow root."""

    if not root.is_dir():
        return None
    candidates = sorted(root.rglob("*.json"))
    # Prefer explicit captures/ directory artifacts when present.
    preferred = [path for path in candidates if "captures" in path.parts]
    pool = preferred or candidates
    return pool[-1] if pool else None


def _fpl_name(raw: str) -> str | None:
    text = str(raw).strip()
    return ODDS_API_NAME_TO_FPL_NAME.get(text)


def _implied_from_outcomes(
    outcomes: Sequence[Mapping[str, Any]],
    *,
    home_team: str,
    away_team: str,
) -> dict[str, float] | None:
    prices: dict[str, float] = {}
    for item in outcomes:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", "")).strip()
        try:
            price = float(item["price"])
        except (KeyError, TypeError, ValueError):
            continue
        if price <= 1.0:
            continue
        prices[name] = price
    if home_team not in prices or away_team not in prices or "Draw" not in prices:
        return None
    inv = {
        "p_home": 1.0 / prices[home_team],
        "p_draw": 1.0 / prices["Draw"],
        "p_away": 1.0 / prices[away_team],
    }
    total = sum(inv.values())
    if total <= 0:
        return None
    return {key: value / total for key, value in inv.items()}


def average_h2h_probabilities(
    markets: Sequence[Mapping[str, Any]],
    *,
    event_id: str,
    home_team: str,
    away_team: str,
) -> dict[str, float] | None:
    """Average bookmaker-normalised 1X2 probabilities for one event."""

    rows: list[dict[str, float]] = []
    for market in markets:
        if not isinstance(market, Mapping):
            continue
        if str(market.get("event_id")) != event_id:
            continue
        if str(market.get("market_key")) != "h2h":
            continue
        probs = _implied_from_outcomes(
            list(market.get("outcomes") or []),
            home_team=home_team,
            away_team=away_team,
        )
        if probs is not None:
            rows.append(probs)
    if not rows:
        return None
    return {
        key: sum(row[key] for row in rows) / len(rows)
        for key in ("p_home", "p_draw", "p_away")
    }


def _slot_window_ok(
    *,
    slot: str,
    lead_hours: float,
    slots_config: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(slots_config, Mapping) or slot not in slots_config:
        return False
    window = slots_config[slot]
    if not isinstance(window, Mapping):
        return False
    minimum = float(window["exclusive_minimum_lead_hours"])
    maximum = float(window["inclusive_maximum_lead_hours"])
    return minimum < lead_hours <= maximum


def odds_snapshots_from_capture(
    capture: Mapping[str, Any],
    *,
    fixtures: Sequence[Mapping[str, Any]],
    bootstrap: Mapping[str, Any],
    decision_cutoff: str,
    slots_config: Mapping[str, Any] | None = None,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """Project a local Odds API capture into fixture-keyed team-prior snapshots.

    Snapshots are admitted only when the capture observation is before the
    packet decision cutoff and the capture slot is valid for that cutoff's
    lead time. Missing or unsafe captures degrade cleanly to an empty mapping.
    """

    summary: dict[str, Any] = {
        "status": "absent",
        "reason": "odds_absent",
        "fixture_count": 0,
        "matched_fixtures": 0,
        "source_sha256": None,
        "observed_at": None,
        "slot": None,
    }
    snapshot = capture.get("snapshot")
    if not isinstance(snapshot, Mapping):
        return {}, summary
    if str(snapshot.get("source_id")) != "the-odds-api":
        summary["reason"] = "odds_rejected_source"
        return {}, summary

    observed = _timestamp(snapshot.get("observed_at"), "odds.observed_at")
    cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if observed >= cutoff:
        summary["reason"] = "odds_rejected_at_or_after_cutoff"
        summary["observed_at"] = _as_z(observed)
        return {}, summary

    slot = str(snapshot.get("slot", "")).strip()
    lead_hours = (cutoff - observed).total_seconds() / 3600.0
    if not _slot_window_ok(
        slot=slot, lead_hours=lead_hours, slots_config=slots_config
    ):
        summary.update(
            {
                "reason": "odds_rejected_outside_slot_window_for_decision_cutoff",
                "observed_at": _as_z(observed),
                "slot": slot,
                "lead_hours_to_decision_cutoff": round(lead_hours, 6),
            }
        )
        return {}, summary

    payload = snapshot.get("payload")
    if not isinstance(payload, Mapping):
        summary["reason"] = "odds_rejected_payload"
        return {}, summary

    teams = {
        str(team["name"]): str(int(team["id"]))
        for team in bootstrap.get("teams", [])
        if isinstance(team, Mapping)
    }
    fixture_index: dict[tuple[str, str], int] = {}
    for raw in fixtures:
        if not isinstance(raw, Mapping) or raw.get("event") is None:
            continue
        try:
            fixture_id = int(raw["id"])
            home = str(int(raw["team_h"]))
            away = str(int(raw["team_a"]))
        except (KeyError, TypeError, ValueError):
            continue
        # Invert club_id → name
        home_name = next((name for name, club in teams.items() if club == home), None)
        away_name = next((name for name, club in teams.items() if club == away), None)
        if home_name and away_name:
            fixture_index[(home_name, away_name)] = fixture_id

    markets = list(payload.get("markets") or [])
    odds_events = list(payload.get("fixtures") or [])
    result: dict[int, dict[str, Any]] = {}
    unmatched_events = 0
    for event in odds_events:
        if not isinstance(event, Mapping):
            continue
        home_odds = str(event.get("home_team", "")).strip()
        away_odds = str(event.get("away_team", "")).strip()
        home_fpl = _fpl_name(home_odds)
        away_fpl = _fpl_name(away_odds)
        if home_fpl is None or away_fpl is None:
            unmatched_events += 1
            continue
        fixture_id = fixture_index.get((home_fpl, away_fpl))
        if fixture_id is None:
            unmatched_events += 1
            continue
        probs = average_h2h_probabilities(
            markets,
            event_id=str(event.get("event_id")),
            home_team=home_odds,
            away_team=away_odds,
        )
        if probs is None:
            unmatched_events += 1
            continue
        total = sum(probs.values())
        result[fixture_id] = {
            "timing_label": "registered_predeadline",
            "captured_at": _as_z(observed),
            "p_home": round(probs["p_home"] / total, 6),
            "p_draw": round(probs["p_draw"] / total, 6),
            "p_away": round(probs["p_away"] / total, 6),
            "source_id": "the-odds-api",
            "slot": slot,
            "provider_event_id": str(event.get("event_id")),
        }

    summary.update(
        {
            "status": "applied" if result else "absent",
            "reason": "odds_accepted" if result else "odds_fixtures_unmatched",
            "fixture_count": len(odds_events),
            "matched_fixtures": len(result),
            "unmatched_events": unmatched_events,
            "source_sha256": snapshot.get("source_sha256"),
            "observed_at": _as_z(observed),
            "slot": slot,
            "lead_hours_to_decision_cutoff": round(lead_hours, 6),
        }
    )
    summary["content_sha256"] = artifact_hash(summary)
    return result, summary
