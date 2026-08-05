# ADR-0025: Rotowire manual-citation line-up trial (no scrape, no API)

**Status:** Accepted  
**Date:** 2026-08-05  
**Decides:** Operationalisation ticket 13  
**Related:** `docs/data-sources/2026-27-lineups-citation-decision.md`  
**Owners:** Alastair

## Context

Expected minutes is the weakest forecast input. Official team-sheet citation
capture is already enabled. The owner wants a consolidatable predicted/confirmed
line-up signal with good human access. Rotowire publishes predicted and
confirmed Premier League line-ups on the web without offering this project an
API.

Rotowire’s terms prohibit using manual or automated software, devices or other
processes to crawl or spider their pages, and the company has enforced against
scraping. Automated HTML collection and unofficial API use are therefore out of
bounds.

## Decision

1. Name **Rotowire** as the external line-up **trial** source for expected-minutes
   evidence, **alongside** (not replacing) the official citation path.
2. Permitted collection method: **manual citation only** — same discipline as
   `official-lineups-minutes` (immutable citation snapshot with publication /
   observation / effective / finalisation times, identity map, content hash).
3. **No** automated scrape, spider, unofficial API or redistribution.
4. Registry entry `rotowire-lineups` is added with `licence_status: restricted`,
   `enabled: true` for manual citation only, pending ticket-19 benchmark before
   any live forecast influence beyond governed evidence adjustments.
5. Understat/FBref and ClubElo remain **disabled** and are not approved by this
   decision. FFS, Sofascore and FotMob are not selected for this trial.

## Consequences

Ticket 19 implements citation capture + start/minutes benchmarks for Rotowire
only. A failed or rights-blocked trial leaves the source unable to influence
live forecasts and records the negative result. A consolidator layer may merge
official citations, FPL availability flags and Rotowire citations only through
the evidence-adjustment policy.
