"""Odds-implied match baselines from football-data.co.uk 1X2 columns."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.forecasting.team_strength import SEASON_FILES, load_results

REPO = Path(__file__).resolve().parents[2]


def _implied_probs(row: pd.Series) -> tuple[float, float, float] | None:
    # Prefer B365, then PS, then Avg
    for prefix in ("B365", "PS", "Avg"):
        cols = (f"{prefix}H", f"{prefix}D", f"{prefix}A")
        if all(c in row.index and pd.notna(row[c]) for c in cols):
            odds = np.array([float(row[cols[0]]), float(row[cols[1]]), float(row[cols[2]])])
            if np.any(odds <= 1.0):
                return None
            inv = 1.0 / odds
            s = inv.sum()
            probs = inv / s
            return float(probs[0]), float(probs[1]), float(probs[2])
    return None


def build_odds_implied(season: str) -> pd.DataFrame:
    """Return match-level implied 1X2 probs. Timing: typically closing — label as such."""
    df = load_results(season)
    records = []
    for _, row in df.iterrows():
        probs = _implied_probs(row)
        if not probs:
            continue
        ph, pd_, pa = probs
        # Outcome one-hot
        if row["FTHG"] > row["FTAG"]:
            y = "H"
        elif row["FTHG"] < row["FTAG"]:
            y = "A"
        else:
            y = "D"
        records.append(
            {
                "Date": row["Date"],
                "HomeTeam": row["HomeTeam"],
                "AwayTeam": row["AwayTeam"],
                "p_home": ph,
                "p_draw": pd_,
                "p_away": pa,
                "result": y,
                "odds_timing_label": "closing_or_unspecified",
            }
        )
    return pd.DataFrame(records)


def odds_multiclass_log_loss(frame: pd.DataFrame) -> float:
    if frame.empty:
        return float("nan")
    mapping = {"H": "p_home", "D": "p_draw", "A": "p_away"}
    ll = []
    for _, r in frame.iterrows():
        p = float(r[mapping[r["result"]]])
        ll.append(-np.log(max(p, 1e-6)))
    return float(np.mean(ll))


def clean_sheet_proxy_from_odds(p_home: float, p_draw: float, p_away: float, side: str) -> float:
    """Crude CS proxy: home CS ≈ p_home + 0.5*p_draw (not calibrated — baseline only)."""
    if side == "home":
        return float(np.clip(p_home + 0.45 * p_draw, 0.02, 0.85))
    return float(np.clip(p_away + 0.45 * p_draw, 0.02, 0.85))
