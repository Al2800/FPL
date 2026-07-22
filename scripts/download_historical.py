#!/usr/bin/env python3
"""Download registered historical datasets into gitignored data/raw/ (ADR-0007)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import httpx

from src.ingestion.registry import assert_collectable

RAW = REPO / "data" / "raw"


def download_vaastav(dest: Path) -> None:
    assert_collectable("vaastav-fpl")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest / ".git").exists():
        subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"], check=False)
        return
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/vaastav/Fantasy-Premier-League.git",
            str(dest),
        ],
        check=True,
    )


def download_football_data(dest: Path, seasons: list[str]) -> None:
    assert_collectable("football-data-co-uk")
    dest.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        for code in seasons:
            url = f"https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
            path = dest / f"E0_{code}.csv"
            resp = client.get(url)
            path.write_bytes(resp.content)
            print(f"{url} -> HTTP {resp.status_code} bytes={len(resp.content)} path={path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vaastav", action="store_true")
    parser.add_argument("--football-data", action="store_true")
    parser.add_argument(
        "--fd-seasons",
        default="1516,1617,1718,1819,1920,2021,2122,2223,2324,2425",
        help="Comma-separated football-data season codes (mmz4281 path)",
    )
    args = parser.parse_args(argv)
    if not args.vaastav and not args.football_data:
        args.vaastav = True
        args.football_data = True
    if args.vaastav:
        download_vaastav(RAW / "vaastav" / "Fantasy-Premier-League")
        print(f"vaastav ready at {RAW / 'vaastav' / 'Fantasy-Premier-League'}")
    if args.football_data:
        seasons = [s.strip() for s in args.fd_seasons.split(",") if s.strip()]
        download_football_data(RAW / "football-data", seasons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
