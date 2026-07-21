# Snapshot cadence

**Source:** `fpl-official-endpoints` (enabled)  
**Script:** `python3 -m scripts.run_snapshot`  
**Output:** `data/raw/fpl/<UTC-stamp>/` (gitignored)

## Recommended schedule (plan Section 15)

| When | Capture |
|---|---|
| Daily (morning UK) | `bootstrap-static`, `fixtures` |
| T-48h / T-8h / T-2h relative to deadline | same, plus note in run metadata |
| During matches (later phase) | `event/{gw}/live` |
| After 09:00 UK Gameweek lock | bootstrap + live for final reconciliation |

Until a scheduler is installed, run the snapshotter manually at least once per day in pre-season and more often near deadlines. A simple cron example:

```cron
0 7 * * * cd /path/to/FPL && python3 -m scripts.run_snapshot >> logs/snapshot.log 2>&1
```

## Launch verification note

As of 21 July 2026 the public endpoints returned HTTP 200 in this environment. Re-check top-level `bootstrap-static` keys and player fields (`chance_of_playing_*`, `ep_next`, `news`, defensive contribution fields) after each FPL schema reset; record findings under `docs/data-sources/`.
