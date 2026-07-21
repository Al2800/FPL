"""Normalise raw / fixture payloads into decision-plane tables."""

from __future__ import annotations

from typing import Any

import pandas as pd


def players_from_bootstrap(bootstrap: dict[str, Any], *, available_at: str) -> pd.DataFrame:
    rows = []
    teams = {t["id"]: t for t in bootstrap.get("teams", [])}
    for el in bootstrap.get("elements", []):
        team = teams.get(el.get("team"), {})
        rows.append(
            {
                "player_id": str(el["id"]),
                "web_name": el.get("web_name"),
                "position": _element_type_to_pos(el.get("element_type")),
                "club_id": str(el.get("team")),
                "club_name": team.get("short_name") or team.get("name"),
                "now_cost": el.get("now_cost", 0) / 10.0,
                "selected_by_percent": float(el.get("selected_by_percent") or 0),
                "form": float(el.get("form") or 0),
                "ep_next": float(el.get("ep_next") or 0),
                "ep_this": float(el.get("ep_this") or 0),
                "chance_of_playing_next_round": el.get("chance_of_playing_next_round"),
                "status": el.get("status"),
                "news": el.get("news") or "",
                "news_added": el.get("news_added"),
                "available_at": available_at,
            }
        )
    return pd.DataFrame(rows)


def players_from_skeleton_fixture(fixture: dict[str, Any]) -> pd.DataFrame:
    """Normalise the committed synthetic historical fixture used by the walking skeleton."""
    available_at = fixture["decision_cutoff"]
    rows = []
    for p in fixture["players"]:
        rows.append(
            {
                "player_id": str(p["player_id"]),
                "web_name": p["web_name"],
                "position": p["position"],
                "club_id": str(p["club_id"]),
                "club_name": p.get("club_name"),
                "now_cost": float(p["now_cost"]),
                "selected_by_percent": float(p.get("selected_by_percent", 0)),
                "form": float(p.get("form", 0)),
                "ep_next": float(p.get("ep_next", 0)),
                "ep_this": float(p.get("ep_this", 0)),
                "chance_of_playing_next_round": p.get("chance_of_playing_next_round"),
                "status": p.get("status", "a"),
                "news": p.get("news", ""),
                "news_added": p.get("news_added"),
                "minutes_last": int(p.get("minutes_last", 0)),
                "points_last": float(p.get("points_last", 0)),
                "available_at": available_at,
            }
        )
    return pd.DataFrame(rows)


def filter_available(df: pd.DataFrame, deadline: str) -> pd.DataFrame:
    """Point-in-time filter: keep rows with available_at <= deadline."""
    return df[df["available_at"] <= deadline].copy()


def _element_type_to_pos(element_type: int | None) -> str:
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type or 0, "UNK")
