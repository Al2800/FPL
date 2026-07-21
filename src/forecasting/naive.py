"""Crude baseline projections for the walking skeleton."""

from __future__ import annotations

import pandas as pd


def naive_expected_points(players: pd.DataFrame) -> pd.DataFrame:
    """Prefer official ep_next when present; else blend form and last-GW points.

    This is intentionally crude — WP-05 replaces it with proper baselines.
    """
    out = players.copy()
    ep_next = out.get("ep_next")
    form = out.get("form", 0).astype(float)
    points_last = out.get("points_last", 0).astype(float)
    minutes_last = out.get("minutes_last", 0).astype(float)

    # Start-probability heuristic: played 60+ last week → 0.85 else 0.35; injuries override.
    start_p = (minutes_last >= 60).astype(float) * 0.85 + (minutes_last < 60).astype(float) * 0.35
    chance = out.get("chance_of_playing_next_round")
    if chance is not None:
        override = chance.notna()
        start_p = start_p.where(~override, chance.fillna(100).astype(float) / 100.0)

    blended = 0.6 * form + 0.4 * points_last
    projected = ep_next.where(ep_next.fillna(0) > 0, blended) if ep_next is not None else blended
    out["expected_minutes"] = (start_p * 75).round(1)
    out["expected_points"] = (projected.astype(float) * start_p.clip(0.05, 1.0)).round(2)
    out["start_probability"] = start_p.round(3)
    return out
