#!/usr/bin/env python3
"""Build a local DuckDB + Parquet analytical warehouse from enabled raw dumps.

Only reads registry-enabled sources already on disk (vaastav, football-data).
Output under data/warehouse/ (gitignored via data/**).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
WAREHOUSE = REPO / "data" / "warehouse"
VAASTAV = RAW / "vaastav" / "Fantasy-Premier-League" / "data"
FD = RAW / "football-data"


def build_player_gw_parquet(out_dir: Path) -> Path:
    frames = []
    for season_dir in sorted(p for p in VAASTAV.iterdir() if p.is_dir()):
        merged = season_dir / "gws" / "merged_gw.csv"
        if not merged.exists():
            continue
        df = pd.read_csv(merged, encoding="latin-1", low_memory=False)
        df["season"] = season_dir.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No vaastav merged_gw files found — run download_historical.py")
    all_df = pd.concat(frames, ignore_index=True, sort=False)
    out = out_dir / "player_gw.parquet"
    all_df.to_parquet(out, index=False)
    return out


def build_matches_parquet(out_dir: Path) -> Path | None:
    files = sorted(FD.glob("E0_*.csv"))
    if not files:
        return None
    frames = []
    for p in files:
        df = pd.read_csv(p, encoding="latin-1").copy()
        code = p.stem.replace("E0_", "")
        df["fd_file"] = p.name
        df["fd_season_code"] = code
        frames.append(df)
    all_df = pd.concat(frames, ignore_index=True, sort=False)
    out = out_dir / "matches_e0.parquet"
    all_df.to_parquet(out, index=False)
    return out


def build_duckdb(out_dir: Path, player_gw: Path, matches: Path | None) -> Path:
    db = out_dir / "lab.duckdb"
    con = duckdb.connect(str(db))
    con.execute(f"CREATE OR REPLACE VIEW player_gw AS SELECT * FROM read_parquet('{player_gw}')")
    if matches is not None:
        con.execute(f"CREATE OR REPLACE VIEW matches_e0 AS SELECT * FROM read_parquet('{matches}')")
    # Handy summary tables
    con.execute(
        """
        CREATE OR REPLACE TABLE season_row_counts AS
        SELECT season, COUNT(*) AS n_rows,
               COUNT(DISTINCT element) AS n_players,
               COUNT(DISTINCT GW) AS n_gws
        FROM player_gw
        GROUP BY 1
        ORDER BY 1
        """
    )
    con.close()
    return db


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=WAREHOUSE)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    player_gw = build_player_gw_parquet(args.out)
    matches = build_matches_parquet(args.out)
    db = build_duckdb(args.out, player_gw, matches)
    print(f"player_gw={player_gw} bytes={player_gw.stat().st_size}")
    if matches:
        print(f"matches_e0={matches} bytes={matches.stat().st_size}")
    print(f"duckdb={db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
