"""Simple Elo team-strength baseline from football-data.co.uk results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_FD = REPO / "data" / "raw" / "football-data"

# football-data season code → approx end year label
SEASON_FILES = {
    "2015-16": "E0_1516.csv",
    "2016-17": "E0_1617.csv",
    "2017-18": "E0_1718.csv",
    "2018-19": "E0_1819.csv",
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


def fit_elo(
    results: pd.DataFrame,
    k: float = 20.0,
    home_adv: float = 60.0,
    draw_factor: float = 0.8,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Walk-forward three-way Elo with coherent home/draw/away probabilities."""
    ratings: dict[str, float] = {}
    rows = []

    def get(team: str) -> float:
        return ratings.setdefault(team, 1500.0)

    for _, m in results.iterrows():
        home, away = m["HomeTeam"], m["AwayTeam"]
        rh, ra = get(home), get(away)
        home_strength = 10 ** ((rh + home_adv) / 400.0)
        away_strength = 10 ** (ra / 400.0)
        draw_strength = draw_factor * (home_strength * away_strength) ** 0.5
        normalizer = home_strength + draw_strength + away_strength
        exp_home = home_strength / normalizer
        exp_draw = draw_strength / normalizer
        exp_away = away_strength / normalizer
        exp_score_home = exp_home + 0.5 * exp_draw
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
                "exp_draw": exp_draw,
                "exp_away_win": exp_away,
                "goals_home": m["FTHG"],
                "goals_away": m["FTAG"],
                "rating_home_pre": rh,
                "rating_away_pre": ra,
            }
        )
        ratings[home] = rh + k * (score_h - exp_score_home)
        ratings[away] = ra + k * ((1.0 - score_h) - (1.0 - exp_score_home))

    return ratings, pd.DataFrame(rows)


def elo_multiclass_log_loss(match_frame: pd.DataFrame) -> float:
    """Three-way log loss over home wins, draws and away wins."""
    import numpy as np

    if match_frame.empty:
        return float("nan")
    probabilities = []
    for _, row in match_frame.iterrows():
        if row["goals_home"] > row["goals_away"]:
            probabilities.append(row["exp_home_win"])
        elif row["goals_home"] < row["goals_away"]:
            probabilities.append(row["exp_away_win"])
        else:
            probabilities.append(row["exp_draw"])
    return float(-np.log(np.clip(probabilities, 1e-6, 1.0)).mean())


def elo_multiclass_brier(match_frame: pd.DataFrame) -> float:
    """Mean multiclass Brier score for the coherent three-way probabilities."""
    import numpy as np

    if match_frame.empty:
        return float("nan")
    losses = []
    for _, row in match_frame.iterrows():
        actual = np.array(
            [
                float(row["goals_home"] > row["goals_away"]),
                float(row["goals_home"] == row["goals_away"]),
                float(row["goals_home"] < row["goals_away"]),
            ]
        )
        predicted = np.array([row["exp_home_win"], row["exp_draw"], row["exp_away_win"]])
        losses.append(float(((predicted - actual) ** 2).sum()))
    return float(np.mean(losses))


def elo_log_loss(match_frame: pd.DataFrame) -> float:
    """Compatibility alias for the corrected multiclass Elo score."""
    return elo_multiclass_log_loss(match_frame)
