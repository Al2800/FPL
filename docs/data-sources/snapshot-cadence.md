# Snapshot cadence

**Source:** `fpl-official-endpoints` (enabled)  
**Script:** `python3 -m scripts.run_snapshot`  
**Output:** `data/raw/fpl/<UTC-stamp>/` (gitignored)

## Recommended schedule (plan Section 15)

| When | Capture |
|---|---|
| Daily (morning UK) | `bootstrap-static`, `fixtures` |
| T-24h / T-8h / T-2h relative to deadline | same; optional approved market evidence uses the matching named slot |
| Final pre-deadline | same, as late as operationally safe while remaining strictly before cutoff |
| During matches (later phase) | `event/{gw}/live` |
| After 09:00 UK Gameweek lock | bootstrap + live for final reconciliation |

Until a scheduler is installed, run the snapshotter manually at least once per day in pre-season and more often near deadlines. A simple cron example:

```cron
0 7 * * * cd /path/to/FPL && python3 -m scripts.run_snapshot >> logs/snapshot.log 2>&1
```

## Launch verification note

As of 21 July 2026 the public endpoints returned HTTP 200 in this environment. Re-check top-level `bootstrap-static` keys and player fields (`chance_of_playing_*`, `ep_next`, `news`, defensive contribution fields) after each FPL schema reset; record findings under `docs/data-sources/`.

Freeze the launch catalogue exactly once before the GW1 deadline using
`scripts.capture_fpl_live_shadow --freeze-launch`. A conflicting rerun at the
same timestamp is refused. The four market slots remain explicit degraded
features until a live provider has separate terms and cost approval.

## Current odds status

**Status update — 28 July 2026:** Source registry `0.6.0` records
`the-odds-api` as the approved live provider for private local analysis, and
`scripts/capture_live_odds.py` implements the T-24h, T-8h, T-2h and final
pre-deadline captures. `THE_ODDS_API_KEY` must be supplied through the
environment and is never written to artifacts or logs. A missing key or slot
remains an explicit degraded feature, and odds remain shadow-only until their
registered ablation supports promotion. This update supersedes the historical
sentence immediately above; the source registry remains authoritative.
