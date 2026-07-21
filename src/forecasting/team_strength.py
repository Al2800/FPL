"""Simple Elo team-strength baseline from football-data.co.uk results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_FD = REPO / "data" / "raw" / "football-data"

# football-data season code → approx end year label
SEASON_FILES = {
    "2019-20": "E0_1920.csv",
    "2020-21": "E0_2021.csv",
    "2021-22": "E0_2122.csv",
    "2022-23": "E0_2223.csv",
    "2023-24": "E0_2324.csv",
    "2024-25": "E0_2425.csv",
}


def load_results(season: str, root: Path | None = None) -> pd.DataFrame:
    root = root or DEFAULT_FD
    fname = SEASON_FILES.get(season)
    if not fname:
        raise FileNotFoundError(f"No football-data mapping for season {season}")
    path = root / fname
    df = pd.read_csv(path, encoding="latin-1")
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.sort_values("Date")


def fit_elo(results: pd.DataFrame, k: float = 20.0, home_adv: float = 60.0) -> tuple[dict[str, float], pd.DataFrame]:
    """Walk forward Elo; return final ratings and per-match pre-match expectations."""
    ratings: dict[str, float] = {}
    rows = []

    def get(team: str) -> float:
        return ratings.setdefault(team, 1500.0)

    for _, m in results.iterrows():
        home, away = m["HomeTeam"], m["AwayTeam"]
        rh, ra = get(home), get(away)
        exp_home = 1.0 / (1.0 + 10 ** (-((rh + home_adv) - ra) / 400.0))
        exp_away = 1.0 - exp_home
        # Outcome: 1 home win, 0.5 draw, 0 away win
        if m["FTHG"] > m["FTAG"]:
            score_h = 1.0
        elif m["FTHG"] < m["FTAG"]:
            score_h = 0.0
        else:
            score_h = 0.5
        rows.append(
            {
                "Date": m["Date"],
                "HomeTeam": home,
                "AwayTeam": away,
                "exp_home_win": exp_home,
                "exp_draw_proxy": 0.0,  # Elo win-prob only; draw via odds elsewhere
                "exp_away_win": exp_away,
                "goals_home": m["FTHG"],
                "goals_away": m["FTAG"],
                "rating_home_pre": rh,
                "rating_away_pre": ra,
            }
        )
        ratings[home] = rh + k * (score_h - exp_home)
        ratings[away] = ra + k * ((1.0 - score_h) - exp_away)

    return ratings, pd.DataFrame(rows)


def elo_log_loss(match_frame: pd.DataFrame) -> float:
    """Binary home-win vs not using exp_home_win vs (FTHG>FTAG). Draws excluded."""
    import numpy as np

    m = match_frame[match_frame["goals_home"] != match_frame["goals_away"]].copy()
    if m.empty:
        return float("nan")
    y = (m["goals_home"] > m["goals_away"]).astype(float)
    p = m["exp_home_win"].clip(1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
