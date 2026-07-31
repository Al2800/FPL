# Decision: 2026/27 line-ups evidence path

**Ticket:** `.scratch/outstanding-beads/issues/05-lineup-capture-or-challenger.md`  
**Date:** 2026-07-31  
**Outcome:** **official citation path selected and enabled**

## Decision

Pre-match lineup evidence for 2026/27 uses the official Premier League / club
team-sheet **citation** path. Sportradar and other paid challengers remain off.

Because `official-lineups-minutes` is registered with confirmed restricted
citation rights, the path is enabled:

- `selected_provider`: `official-team-sheets`
- registry `official-lineups-minutes`: `enabled: true`
- capture method: **manual citation only** (no automated HTML scrape, no API key)

## Rights / cost

- Source: `official-lineups-minutes` (registry 0.6.2+)
- Licence: restricted; allowed use private analysis citation snapshots
- Cost: zero (manual citation; no paid provider)
- Owner: Alastair, 2026-07-31
- Scope: manual citation capture; no redistribution; no HTML scrape; Sportradar off

## Rehearsal evidence

One complete synthetic rehearsal artifact is committed at
`evals/golden-cases/evidence/official-team-sheet-citation-rehearsal.json`.
It demonstrates XI/substitution citation, publication/observation times,
correction history, identity mapping and reconciliation to the official FPL
minutes oracle without averaging disagreeing feeds.
