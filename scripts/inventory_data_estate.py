#!/usr/bin/env python3
"""Inventory local raw datasets and write a machine-readable estate report.

Does not download anything — read-only scan of gitignored data/raw/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
DEFAULT_OUT = REPO / "docs" / "data-sources" / "data-estate" / "inventory.json"


def _dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def inventory_vaastav() -> dict:
    root = RAW / "vaastav" / "Fantasy-Premier-League" / "data"
    if not root.exists():
        return {"present": False}
    seasons = []
    for season_dir in sorted(p for p in root.iterdir() if p.is_dir() and (p / "gws").exists()):
        merged = season_dir / "gws" / "merged_gw.csv"
        understat = season_dir / "understat"
        players = season_dir / "players"
        entry = {
            "season": season_dir.name,
            "bytes": _dir_size(season_dir),
            "merged_gw_rows": None,
            "has_understat": understat.exists(),
            "understat_files": len(list(understat.glob("*.csv"))) if understat.exists() else 0,
            "player_dirs": len([p for p in players.iterdir()]) if players.exists() else 0,
            "used_by_wp05": season_dir.name in {"2022-23", "2023-24", "2024-25"},
        }
        if merged.exists():
            # Fast line count
            with merged.open("r", encoding="latin-1", errors="replace") as fh:
                entry["merged_gw_rows"] = sum(1 for _ in fh) - 1
        seasons.append(entry)
    return {
        "present": True,
        "source_id": "vaastav-fpl",
        "bytes": _dir_size(root),
        "seasons": seasons,
        "cross_season_files": [
            p.name for p in root.glob("*.csv")
        ],
        "usage_today": {
            "wp05": "merged_gw for 2022-23..2024-25 only",
            "unused_locally": [
                "per-player history CSVs",
                "understat/ xG mirrors (already on disk via vaastav; not in models yet)",
                "seasons before 2022-23 for WP-05 eval",
                "cleaned_merged_seasons*.csv",
            ],
        },
    }


def inventory_football_data() -> dict:
    root = RAW / "football-data"
    if not root.exists():
        return {"present": False}
    files = []
    for p in sorted(root.glob("E0_*.csv")):
        try:
            df = pd.read_csv(p, encoding="latin-1", nrows=0)
            cols = list(df.columns)
        except Exception:
            cols = []
        with p.open("r", encoding="latin-1", errors="replace") as fh:
            rows = sum(1 for _ in fh) - 1
        files.append({"file": p.name, "bytes": p.stat().st_size, "rows": rows, "n_cols": len(cols)})
    return {
        "present": True,
        "source_id": "football-data-co-uk",
        "bytes": _dir_size(root),
        "files": files,
        "usage_today": {
            "wp05": "Elo + 1X2 odds for seasons mapped in team_strength.SEASON_FILES",
            "gap": "Only a handful of E0 season files; older seasons not yet downloaded",
        },
    }


def inventory_fpl_snapshots() -> dict:
    root = RAW / "fpl"
    if not root.exists():
        return {"present": False}
    snaps = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        snaps.append({"id": d.name, "bytes": _dir_size(d), "files": [p.name for p in d.iterdir()]})
    return {
        "present": True,
        "source_id": "fpl-official-endpoints",
        "bytes": _dir_size(root),
        "snapshots": snaps,
        "usage_today": "Snapshotter / schema notes; not yet a full pre-deadline feature store",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = {
        "raw_root": str(RAW),
        "total_bytes": _dir_size(RAW),
        "vaastav": inventory_vaastav(),
        "football_data": inventory_football_data(),
        "fpl_snapshots": inventory_fpl_snapshots(),
        "world_cup": {
            "present": (RAW / "world-cup").exists(),
            "bytes": _dir_size(RAW / "world-cup"),
            "committed_priors": "control/identities/world-cup-2026-priors.csv",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"total_raw_gb={report['total_bytes']/1e9:.3f}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
