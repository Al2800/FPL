# Decision: 2026/27 line-ups evidence path

**Ticket:** `.scratch/outstanding-beads/issues/05-lineup-capture-or-challenger.md`  
**Date:** 2026-07-31  
**Outcome:** **official citation path selected**

## Decision

Pre-match lineup evidence for 2026/27 uses the official Premier League / club
team-sheet **citation** path. Sportradar and other paid challengers remain off.
`selected_provider` stays `null` and registry collection for
`official-lineups-minutes` stays disabled until an explicit live matchday enable
decision after this rehearsal.

## Rights / cost

- Source: `official-lineups-minutes` (registry 0.6.1+)
- Licence: restricted; allowed use private analysis citation snapshots
- Cost: zero (manual citation; no paid provider)
- Owner: Alastair, 2026-07-31
- Scope: citation rehearsal only; no redistribution; no network collector

## Rehearsal evidence

One complete synthetic rehearsal artifact is committed at
`evals/golden-cases/evidence/official-team-sheet-citation-rehearsal.json`.
It demonstrates XI/substitution citation, publication/observation times,
correction history, identity mapping and reconciliation to the official FPL
minutes oracle without averaging disagreeing feeds.
