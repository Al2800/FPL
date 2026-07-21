#!/usr/bin/env python3
"""Profile historical datasets for WP-04. Writes reports under docs/data-sources/wp04/."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League"
FD = REPO / "data" / "raw" / "football-data"
OUT = REPO / "docs" / "data-sources" / "wp04"
OUT.mkdir(parents=True, exist_ok=True)


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def profile_vaastav() -> dict:
    data_root = VAASTAV / "data"
    seasons = sorted(
        [p.name for p in data_root.iterdir() if p.is_dir() and re.match(r"^\d{4}-\d{2}$", p.name)]
    ) if data_root.exists() else []

    season_profiles = []
    all_columns = {}
    identity_stats = []

    for season in seasons:
        sdir = data_root / season
        merged = sdir / "gws" / "merged_gw.csv"
        players = sdir / "players_raw.csv"
        teams = sdir / "teams.csv"
        fixtures = sdir / "fixtures.csv"
        info: dict = {"season": season, "files": {}}
        for label, path in {
            "merged_gw": merged,
            "players_raw": players,
            "teams": teams,
            "fixtures": fixtures,
        }.items():
            info["files"][label] = path.exists()

        if merged.exists():
            df = pd.read_csv(merged, low_memory=False, encoding="latin-1")
            cols = list(df.columns)
            all_columns[season] = cols
            info["n_rows"] = int(len(df))
            info["n_players"] = int(df["element"].nunique()) if "element" in df.columns else None
            info["gameweeks"] = sorted(df["GW"].dropna().unique().tolist()) if "GW" in df.columns else []
            info["has_xP"] = "xP" in cols
            info["has_minutes"] = "minutes" in cols
            info["has_total_points"] = "total_points" in cols
            info["has_value"] = "value" in cols
            info["has_selected"] = "selected" in cols
            info["has_news"] = "news" in cols
            info["defensive_cols"] = [
                c
                for c in cols
                if any(
                    k in c.lower()
                    for k in ("clearance", "block", "intercept", "tackle", "recover", "defensive")
                )
            ]
            # Leakage heuristic: correlation of xP with same-GW points if both present
            if info["has_xP"] and info["has_total_points"]:
                sub = df[["xP", "total_points"]].dropna()
                if len(sub) > 100:
                    info["xP_same_gw_points_corr"] = float(sub["xP"].corr(sub["total_points"]))
            # Position coverage
            if "position" in cols:
                info["positions"] = {str(k): int(v) for k, v in df["position"].value_counts().to_dict().items()}
            elif "element_type" in cols:
                info["element_types"] = {
                    str(k): int(v) for k, v in df["element_type"].value_counts().to_dict().items()
                }

        if players.exists() and season != seasons[0]:
            # Cross-season identity: compare name keys to prior season where possible
            pass

        season_profiles.append(info)

    # Identity match across consecutive seasons via player name in cleaned_players or players_raw
    for a, b in zip(seasons, seasons[1:]):
        pa = data_root / a / "players_raw.csv"
        pb = data_root / b / "players_raw.csv"
        if not (pa.exists() and pb.exists()):
            continue
        da = pd.read_csv(pa, low_memory=False, encoding="latin-1")
        db = pd.read_csv(pb, low_memory=False, encoding="latin-1")
        # Prefer code if present (stable across seasons), else first+second name
        if "code" in da.columns and "code" in db.columns:
            set_a = set(da["code"].dropna().astype(int))
            set_b = set(db["code"].dropna().astype(int))
            inter = set_a & set_b
            identity_stats.append(
                {
                    "from": a,
                    "to": b,
                    "method": "fpl_code",
                    "n_a": len(set_a),
                    "n_b": len(set_b),
                    "matched": len(inter),
                    "match_rate_of_earlier": round(len(inter) / max(len(set_a), 1), 3),
                    "match_rate_of_later": round(len(inter) / max(len(set_b), 1), 3),
                }
            )
        else:
            def names(df):
                if {"first_name", "second_name"}.issubset(df.columns):
                    return set((df["first_name"].fillna("") + "|" + df["second_name"].fillna("")).str.lower())
                if "web_name" in df.columns:
                    return set(df["web_name"].fillna("").str.lower())
                return set()

            set_a, set_b = names(da), names(db)
            inter = set_a & set_b
            identity_stats.append(
                {
                    "from": a,
                    "to": b,
                    "method": "name",
                    "n_a": len(set_a),
                    "n_b": len(set_b),
                    "matched": len(inter),
                    "match_rate_of_earlier": round(len(inter) / max(len(set_a), 1), 3),
                    "match_rate_of_later": round(len(inter) / max(len(set_b), 1), 3),
                }
            )

    # Column evolution
    col_presence = defaultdict(list)
    for season, cols in all_columns.items():
        for c in cols:
            col_presence[c].append(season)

    return {
        "source_id": "vaastav-fpl",
        "profiled_at": _utc(),
        "repo_path": str(VAASTAV.relative_to(REPO)) if VAASTAV.exists() else None,
        "seasons": seasons,
        "season_profiles": season_profiles,
        "identity_match_consecutive_seasons": identity_stats,
        "columns_by_season_count": {c: len(v) for c, v in sorted(col_presence.items())},
    }


def profile_football_data() -> dict:
    files = sorted(FD.glob("E0_*.csv")) if FD.exists() else []
    seasons = []
    for path in files:
        df = pd.read_csv(path, low_memory=False, encoding="latin-1")
        odds_cols = [c for c in df.columns if any(x in c for x in ("B365", "PS", "Avg", "Max", "BbAv"))]
        seasons.append(
            {
                "file": path.name,
                "n_rows": int(len(df)),
                "columns": list(df.columns),
                "has_fthg_ftag": {"FTHG", "FTAG"}.issubset(df.columns),
                "odds_columns": odds_cols,
                "n_odds_columns": len(odds_cols),
            }
        )
    return {
        "source_id": "football-data-co-uk",
        "profiled_at": _utc(),
        "files": seasons,
    }


def assess_news_recoverability(vaastav_profile: dict) -> dict:
    """Which seasons/GWs have news fields in historical dumps (evidence-dependent replay)."""
    findings = []
    for sp in vaastav_profile.get("season_profiles", []):
        findings.append(
            {
                "season": sp["season"],
                "has_news_column_in_merged_gw": bool(sp.get("has_news")),
                "note": (
                    "merged_gw lacks a news column — pre-deadline news environment not preserved here"
                    if not sp.get("has_news")
                    else "news column present — inspect timestamps before trusting for replay"
                ),
            }
        )
    return {
        "assessed_at": _utc(),
        "summary": (
            "Evidence-dependent historical replay is generally NOT feasible from vaastav alone: "
            "structured stats are preserved, but the pre-deadline news / predicted-line-up environment is not. "
            "Recoverable islands: (1) any archived bootstrap-static snapshots that include news/news_added "
            "with observed_at <= deadline; (2) selective Wayback captures of club/injury pages for named GWs. "
            "Default stance per Section 17.6: use multi-season replay for structured-data strategies only; "
            "lean on live 2026/27 day-one archives for evidence-dependent questions."
        ),
        "seasons": findings,
        "recommended_pilot_gameweeks_structured_only": [
            {"season": "2023-24", "gameweeks": [1, 10, 20, 30, 38]},
            {"season": "2024-25", "gameweeks": [1, 10, 20, 30]},
        ],
        "evidence_dependent_feasibility": "low_without_external_archives",
    }


def write_markdown_reports(vaastav: dict, football: dict, news: dict) -> None:
    # vaastav profile
    lines = [
        "# WP-04 profile: vaastav/Fantasy-Premier-League",
        "",
        f"Profiled at: `{vaastav['profiled_at']}`",
        f"Local path: `{vaastav.get('repo_path')}` (gitignored)",
        "",
        "## Licence and use",
        "",
        "- Registry: `vaastav-fpl` (enabled for private local use only).",
        "- Upstream code MIT; underlying data property of FPL / Understat — **no redistribution**.",
        "- ADR-0001 / ADR-0007 apply.",
        "",
        "## Coverage",
        "",
        f"Seasons present: {', '.join(vaastav['seasons']) or 'none'}",
        "",
        "| Season | rows | players | GWs | xP | minutes | value | selected | defensive cols | xP↔pts corr |",
        "|---|---:|---:|---:|:---:|:---:|:---:|:---:|---|---:|",
    ]
    for sp in vaastav["season_profiles"]:
        gws = sp.get("gameweeks") or []
        lines.append(
            "| {season} | {rows} | {players} | {ngw} | {xp} | {mins} | {val} | {sel} | {defs} | {corr} |".format(
                season=sp["season"],
                rows=sp.get("n_rows", ""),
                players=sp.get("n_players", ""),
                ngw=len(gws),
                xp="Y" if sp.get("has_xP") else "N",
                mins="Y" if sp.get("has_minutes") else "N",
                val="Y" if sp.get("has_value") else "N",
                sel="Y" if sp.get("has_selected") else "N",
                defs=", ".join(sp.get("defensive_cols") or []) or "—",
                corr=f"{sp['xP_same_gw_points_corr']:.2f}" if "xP_same_gw_points_corr" in sp else "—",
            )
        )
    lines += [
        "",
        "## Gaps",
        "",
        "- No reliable pre-deadline `news` / predicted line-ups in `merged_gw` (see news assessment).",
        "- Defensive-contribution action detail sparse before 2025/26; official endpoints now expose DC fields for live work.",
        "- Season completeness varies; confirm final GW count before training.",
        "",
        "## Leakage risk",
        "",
        "- Treat `xP` as **unsafe for same-GW labels** unless independently verified as pre-deadline; prefer shift(1) or drop.",
        "- `total_points`, bonus, and BPS in the same row as features for that GW are outcomes — use only as labels or lagged features.",
        "- Prices/`selected` mid-GW may reflect post-deadline movement depending on scrape time; prefer features known at deadline.",
        "",
        "## Identity match rates (consecutive seasons via FPL `code`)",
        "",
        "| From | To | method | n_from | n_to | matched | rate_from | rate_to |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in vaastav["identity_match_consecutive_seasons"]:
        lines.append(
            f"| {row['from']} | {row['to']} | {row['method']} | {row['n_a']} | {row['n_b']} | "
            f"{row['matched']} | {row['match_rate_of_earlier']} | {row['match_rate_of_later']} |"
        )
    (OUT / "vaastav-profile.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # football-data
    flines = [
        "# WP-04 profile: football-data.co.uk",
        "",
        f"Profiled at: `{football['profiled_at']}`",
        "",
        "## Licence and use",
        "",
        "- Registry: `football-data-co-uk` (enabled for private analysis with attribution).",
        "- Do not republish their CSV files.",
        "",
        "## Coverage",
        "",
        "| File | rows | FTHG/FTAG | odds columns |",
        "|---|---:|:---:|---:|",
    ]
    for f in football["files"]:
        flines.append(
            f"| {f['file']} | {f['n_rows']} | {'Y' if f['has_fthg_ftag'] else 'N'} | {f['n_odds_columns']} |"
        )
    flines += [
        "",
        "## Gaps",
        "",
        "- Player-level props (anytime goalscorer) are thin historically; derive clean-sheet / match probs from 1X2 and totals where needed (plan §11.2).",
        "- No FPL player IDs — join to FPL via team/date fixtures only.",
        "",
        "## Leakage risk",
        "",
        "- Closing odds may include late information; for decision replay prefer odds captured before the FPL deadline (live capture going forward).",
        "- Historical CSVs are typically closing or settlement-oriented — label as such; do not claim pre-deadline without timestamps.",
        "",
    ]
    (OUT / "football-data-profile.md").write_text("\n".join(flines) + "\n", encoding="utf-8")

    # disabled sources short profiles
    disabled = """# WP-04 profiles: disabled / pending Tier 2 sources

These sources are registered but **not enabled**. Profiles are from documentation and plan constraints, not bulk local dumps.

## FPL-Core-Insights
- Potential: 2025/26 detailed actions, cups, Europe, Elo.
- Licence/provenance of Opta-like fields unresolved → disabled.
- Alternative: official FPL + football-data + (later) FBref.

## ClubElo
- Potential: team-strength baseline, promoted-club priors.
- Terms not fully reviewed → disabled.
- Alternative: Elo fitted on football-data.co.uk results.

## Understat
- Potential: xG / xA.
- No supported public API; terms unresolved → disabled.
- Alternative: score from shots unavailable; use goals/assists rates and odds.

## FBref
- Potential: per-match defensive actions for DC modelling enrichment.
- Sports Reference terms restrict bulk reuse → disabled pending review.
- **Not a launch blocker:** official FPL exposes `defensive_contribution`, `clearances_blocks_interceptions`, `tackles`, `recoveries` (see schema notes).

## World Cup 2026
- Required for GW1–5 expected-minutes priors (plan §7.7).
- Collection method: **manual one-off** (enabled:false automated).
- Status: assemble per-player minutes, elimination dates, return-to-training once the tournament concludes; until then increase uncertainty for known tournament squads.
- Alternative interim: binary `world_cup_participant` flag from published squads + elimination round when known.
"""
    (OUT / "disabled-sources-profile.md").write_text(disabled, encoding="utf-8")

    nlines = [
        "# WP-04: Point-in-time news recoverability",
        "",
        f"Assessed at: `{news['assessed_at']}`",
        "",
        news["summary"],
        "",
        f"**Evidence-dependent feasibility:** `{news['evidence_dependent_feasibility']}`",
        "",
        "## Per-season merged_gw news field",
        "",
        "| Season | news column | Note |",
        "|---|:---:|---|",
    ]
    for s in news["seasons"]:
        nlines.append(
            f"| {s['season']} | {'Y' if s['has_news_column_in_merged_gw'] else 'N'} | {s['note']} |"
        )
    nlines += [
        "",
        "## Recommended structured-only pilot Gameweeks",
        "",
    ]
    for block in news["recommended_pilot_gameweeks_structured_only"]:
        nlines.append(f"- {block['season']}: GW {block['gameweeks']}")
    nlines += [
        "",
        "## Implication for WP-09",
        "",
        "Size the replay harness for hundreds of structured decisions (ADR-0004). Do not block harness work on historical news reconstruction — limit that to a feasibility sample if Wayback/bootstrap archives appear later.",
        "",
    ]
    (OUT / "news-recoverability.md").write_text("\n".join(nlines) + "\n", encoding="utf-8")

    targets = """# WP-04: Recommended training targets by model component

| Component | Primary target | Features (pre-deadline only) | Notes |
|---|---|---|---|
| Expected minutes / start probability | Started (minutes≥60), minutes | Lagged minutes, status flags, chance_of_playing when snapshotted, fixture congestion | News/line-ups only from live archive going forward |
| Team strength | Goals for/against per match | Home/away, Elo/rolling rates, odds-implied probs | football-data for results/odds; label odds timing |
| Player events (G/A) | Goals, assists | Per-90 rates, team strength, minutes projection | Position-aware; cold-start priors for new players |
| Clean sheets | Team CS / player CS (60+ mins) | Team defence rates, odds | Midfielder CS worth 1 pt — keep separate |
| Defensive contributions | Threshold hit (binary) + actions | Official DC fields from 2025/26+; role/minutes | Pre-2025/26 history not directly comparable |
| Bonus | Bonus points / BPS rank | BPS components where known; do not claim exact BPS without Opta | Probabilistic; official points are outcome truth |
| FPL points | Derived via scoring engine from event forecasts | — | Do not train directly on `total_points` across rule regimes (plan §11.1) |

## Explicitly excluded / shifted features
- Same-GW `xP` / post-match `ep_this` as predictors of that GW's points
- Same-GW outcomes as features
- Un-timestamped closing odds presented as pre-deadline

## Open Decision 6 (usable seasons)
Provisionally usable for structured baselines: seasons with complete `merged_gw` + fixtures + stable `code` identity (see vaastav profile). Final call recorded when WP-05 evaluation splits are fixed.
"""
    (OUT / "training-targets.md").write_text(targets, encoding="utf-8")

    summary = {
        "wp": "WP-04",
        "profiled_at": _utc(),
        "vaastav_seasons": vaastav.get("seasons"),
        "identity_matches": vaastav.get("identity_match_consecutive_seasons"),
        "football_data_files": [f["file"] for f in football.get("files", [])],
        "news_feasibility": news.get("evidence_dependent_feasibility"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if not VAASTAV.exists():
        print("vaastav missing — run scripts/download_historical.py first", file=sys.stderr)
        return 1
    vaastav = profile_vaastav()
    football = profile_football_data()
    news = assess_news_recoverability(vaastav)
    write_markdown_reports(vaastav, football, news)
    print(f"Wrote reports under {OUT}")
    print(f"vaastav seasons: {vaastav['seasons']}")
    print(f"identity pairs: {len(vaastav['identity_match_consecutive_seasons'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
