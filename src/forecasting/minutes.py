"""Expected-minutes and start-probability baselines."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.forecasting.data import add_lagged_features, load_merged_gw

REPO = Path(__file__).resolve().parents[2]
DEFAULT_WC = REPO / "control" / "identities" / "world-cup-2026-priors.csv"

FATIGUE_START_MULT = {
    "none": 1.0,
    "moderate": 0.92,
    "high": 0.8,
    "extreme": 0.65,
}


def naive_started_last(df: pd.DataFrame) -> pd.Series:
    """P(start) = 1 if minutes_lag1 >= 60 else 0 (undefined → 0.5)."""
    lag = df.get("minutes_lag1")
    if lag is None:
        raise ValueError("minutes_lag1 required — call add_lagged_features first")
    p = pd.Series(np.where(lag.isna(), 0.5, (lag >= 60).astype(float)), index=df.index)
    return p


def rolling_minutes_start_prob(df: pd.DataFrame) -> pd.Series:
    """Blend last-start with roll3 minutes/90 as soft probability."""
    base = naive_started_last(df)
    roll = df.get("minutes_roll3")
    if roll is None:
        return base
    soft = (roll.fillna(45) / 90.0).clip(0.05, 0.95)
    return (0.6 * base + 0.4 * soft).clip(0.05, 0.95)


def apply_world_cup_prior(
    start_prob: pd.Series,
    df: pd.DataFrame,
    *,
    gameweek: int | None = None,
    priors_path: Path | None = None,
    code_col: str = "element_code",
) -> pd.Series:
    """Fade WC fatigue multipliers over GW1–5 when priors + fpl codes are available."""
    path = priors_path or DEFAULT_WC
    if not path.exists() or code_col not in df.columns:
        return start_prob
    priors = pd.read_csv(path)
    if "fpl_code" not in priors.columns or "fatigue_prior" not in priors.columns:
        return start_prob
    # Only apply early season
    gw = gameweek
    if gw is None and "round" in df.columns:
        # row-wise fade
        fade = df["round"].map(lambda r: 1.0 if r <= 2 else 0.5 if r <= 4 else 0.0 if r <= 5 else 0.0)
    else:
        r = gw or 1
        fade_scalar = 1.0 if r <= 2 else 0.5 if r <= 4 else 0.0
        fade = pd.Series(fade_scalar, index=df.index)

    m = priors.set_index("fpl_code")["fatigue_prior"].to_dict()
    mult = df[code_col].map(lambda c: FATIGUE_START_MULT.get(m.get(c), 1.0))
    # Interpolate toward 1.0 as fade → 0
    effective = 1.0 - fade * (1.0 - mult.fillna(1.0))
    return (start_prob * effective).clip(0.05, 0.95)


def expected_minutes_from_start_prob(start_prob: pd.Series, typical_minutes: float = 75.0) -> pd.Series:
    return (start_prob * typical_minutes).round(1)


def build_minutes_frame(season: str) -> pd.DataFrame:
    df = add_lagged_features(load_merged_gw(season))
    df["start_prob_naive"] = naive_started_last(df)
    df["start_prob_rolling"] = rolling_minutes_start_prob(df)
    df["y_started"] = (df["minutes"] >= 60).astype(int)
    df["y_minutes"] = df["minutes"]
    return df
