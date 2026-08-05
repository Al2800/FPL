# Decision: Rotowire line-ups citation trial (2026/27)

**Ticket:** `.scratch/operationalisation/issues/13-expected-minutes-sources.md`  
**ADR:** `docs/decisions/0025-rotowire-manual-lineup-trial.md`  
**Date:** 2026-08-05  
**Outcome:** **Rotowire selected for manual-citation trial**

## Decision

Expected-minutes challenger evidence may cite RotoWire predicted and confirmed
Premier League line-ups. Collection is **manual citation only**. Automated
crawl, spider, scrape and unofficial API use are prohibited by RotoWire terms
and by this decision.

Official team-sheet citations (`official-lineups-minutes`) remain adjudication
truth. Sofascore, FotMob and Fantasy Football Scout are not authorised here.
Understat/FBref and ClubElo remain disabled.

## Rights / cost

- Source: `rotowire-lineups` (registry 0.6.4+)
- Terms: https://www.rotowire.com/termsandconditions.php
- Licence: restricted; private analysis citation snapshots
- Cost: zero (manual citation; no API product)
- Owner: Alastair, 2026-08-05
- Scope: manual citation; no redistribution; no HTML scrape

## Next

Ticket 19 implements citation capture, consolidator wiring through the
evidence-adjustment policy, and start/minutes benchmarks before live influence.
