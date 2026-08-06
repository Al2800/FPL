# Decision: Rotowire FPL editorial rankings citation (2026/27)

**Date:** 2026-08-05  
**Source:** `rotowire-fpl-editorial` (registry 0.6.5+)  
**Collection:** manual citation only (owner paste)

## Decision

Owner-pasted RotoWire FPL editorial rankings and short-horizon fixture
commentary may be sealed as immutable private citation snapshots for analysis
priors (initial-squad / short-horizon planning context).

This is **not**:

- expected-minutes evidence (`rotowire-lineups` / official team sheets);
- the StatsBomb `player_ratings` family;
- an authorised live optimiser input.

## First sealed pack

- Article: *FPL Gameweeks 1-5 Rankings: Best Players to Start the 2026/27 Season*
  (Adam Zdroik, 5 August 2026)
- Local artifact (gitignored):  
  `data/live-shadow/rotowire/rankings/2026-08-05-gw1-5-rankings-citation.json`
- Influence policy on the pack: `editorial_prior_only_no_live_optimiser_selection`
- Canonical article URL was absent from the paste (`pending_owner_url`)

## Rights

Same Rotowire terms discipline as ADR-0025: no crawl, spider, scrape,
unofficial API or redistribution.
