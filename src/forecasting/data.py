"""Load vaastav merged_gw tables with leakage-safe column handling."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"

# Never use same-GW xP as a feature for that GW's points (WP-04).
LEAKY_SAME_GW_FEATURES = {"xP", "total_points", "bonus", "bps"}
START_COLUMNS = ("started", "starts", "is_starting")


def recorded_start_indicator(df: pd.DataFrame) -> pd.Series:
    """Return an explicit start indicator, or nullable unknown when unavailable.

    Minutes are deliberately not used: a start is a line-up event, not a
    threshold on playing time.
    """
    for column in START_COLUMNS:
        if column in df.columns:
            values = pd.to_numeric(df[column], errors="coerce")
            return values.map(lambda value: float(value > 0) if pd.notna(value) else pd.NA).astype(
                "Float64"
            )
    return pd.Series(pd.NA, index=df.index, dtype="Float64")


def list_seasons(root: Path | None = None) -> list[str]:
    root = root or DEFAULT_VAASTAV
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "gws" / "merged_gw.csv").exists())


def load_merged_gw(season: str, root: Path | None = None) -> pd.DataFrame:
    root = root or DEFAULT_VAASTAV
    path = root / season / "gws" / "merged_gw.csv"
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    # Normalise gameweek column
    if "GW" in df.columns and "round" not in df.columns:
        df = df.rename(columns={"GW": "round"})
    if "round" not in df.columns and "GW" in df.columns:
        df["round"] = df["GW"]
    df["season"] = season
    df["element"] = df["element"].astype(int)
    df["round"] = df["round"].astype(int)
    return df


def add_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
    """Within each player-season, lag outcome-like fields so GW t uses only ≤ t-1 info."""
    out = df.sort_values(["season", "element", "round"]).copy()
    out["started"] = recorded_start_indicator(out)
    g = out.groupby(["season", "element"], sort=False)
    out["minutes_lag1"] = g["minutes"].shift(1)
    out["started_lag1"] = g["started"].shift(1)
    out["points_lag1"] = g["total_points"].shift(1)
    out["minutes_roll3"] = g["minutes"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["points_roll3"] = g["total_points"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    # Cumulative prior minutes for per-90
    out["minutes_prior_sum"] = g["minutes"].transform(lambda s: s.shift(1).cumsum())
    for col in ("goals_scored", "assists", "clean_sheets"):
        if col in out.columns:
            out[f"{col}_prior_sum"] = g[col].transform(lambda s: s.shift(1).cumsum())
    return out
