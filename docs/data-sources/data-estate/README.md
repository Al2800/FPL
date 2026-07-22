# Local data estate

**Purpose:** Make the large historical dumps we already hold usable, and grow only within registry-enabled sources.

## What’s on disk (gitignored)

| Area | Approx size | Registry | Role |
|---|---:|---|---|
| `data/raw/vaastav/` | ~355 MB | `vaastav-fpl` enabled | Full community FPL history (merged_gw, players, understat mirrors, …) |
| `data/raw/football-data/` | ~1.5 MB | `football-data-co-uk` enabled | E0 results + odds, 2015/16–2024/25 |
| `data/raw/fpl/` | ~9.5 MB | `fpl-official-endpoints` enabled | Live bootstrap/fixtures snapshots |
| `data/raw/world-cup/` | small | manual priors | Working files; committed CSV under `control/identities/` |
| `data/warehouse/` | ~8.6 MB | derived | Parquet + DuckDB views for analysis |

Committed inventory snapshot: [`inventory.json`](inventory.json) (regenerate anytime).

## What we use today vs leave idle

**In models / evals now**

- vaastav `merged_gw` for **2022-23…2024-25** (WP-05)
- football-data E0 for Elo/odds (WP-05; mapping now covers 2015/16+)

**Already downloaded but not yet in the modelling path**

- vaastav seasons **2016-17…2021-22** and **2025-26**
- per-player history files and **understat/** xG mirrors inside vaastav (private local analysis only; do **not** scrape understat.com — registry `understat` stays disabled)
- `cleaned_merged_seasons*.csv`
- Full FPL snapshot history as a feature store (need pre-deadline discipline)

## Commands

```bash
# Refresh enabled raw dumps
PYTHONPATH=. python3 -m scripts.download_historical

# Scan disk → docs/data-sources/data-estate/inventory.json
PYTHONPATH=. python3 -m scripts.inventory_data_estate

# Materialise analytical layer (Parquet + DuckDB)
PYTHONPATH=. python3 -m scripts.build_warehouse

# Example query
python3 -c "import duckdb; c=duckdb.connect('data/warehouse/lab.duckdb'); print(c.execute('select * from season_row_counts').df())"
```

## Growth options (ordered)

1. **Deepen what we have** — train/eval on more vaastav seasons; join understat-in-vaastav xG carefully with leakage controls; warehouse joins to Elo/odds. *(This PR)*
2. **Expand enabled downloads** — more football-data seasons/divisions if useful; keep attribution; no redistribution.
3. **Live corpus** — schedule FPL snapshots; that becomes the large *decision-time* dataset for 2026/27.
4. **New sources** — ClubElo / FBref / Core-Insights only after `licence_status` + `allowed_use` resolved and `enabled: true` (still false today).

## Explicit non-goals right now

- Enabling Understat/FBref HTML scrapers
- Committing raw dumps to Git
- Cloud warehouse (deferred — `docs/architecture/deferred/cloud-warehouse.md`)
