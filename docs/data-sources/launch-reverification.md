# FPL launch re-verification log

**Last pass:** 2026-07-27
**Official bootstrap:** `data/live-shadow/fpl/20260727T100527Z/api_bootstrap-static.json`
**Ruleset:** `2026-27-v1.0`
**Machine blockers:** 0
**Owner advisory sign-off:** pending

## Official state

The official FPL bootstrap capture succeeded with HTTP 200 and is bound by
SHA-256 `605dd760aa4a7697f99479c81911fe046c7b252704cfe7622c61fc5fd09399b5`.
It contains the live 2026/27 teams, 558 current players, GW1 deadline and launch
prices/positions. The earlier 403 residual is superseded operational evidence,
not silently deleted.

Decision-relevant element fields remain present:

- availability: `status`, `chance_of_playing_*`, `news`, `news_added`;
- projections: `ep_this`, `ep_next`;
- defensive contributions and component statistics;
- ownership/price: `selected_by_percent`, `now_cost*`, `cost_change_*`.

## Rules verification

All 39 catalogue rules are confirmed from official Premier League/FPL sources.
Every rule has `source_url`, `source_published_at` and `verified_at`. The
maintained detailed FPL Basics pages published in 2025 are explicitly linked
from the dated 24 July 2026 official Help page; their older publication dates
are preserved rather than relabelled.

The typed activation result is:

- zero blockers;
- £100m, 15-player, 2/5/5/3 squad and maximum three per club;
- one free transfer, maximum five banked, four-point excess-transfer cost;
- saved transfers retained across Wildcard/Free Hit;
- half-profit selling-price rule;
- two chip sets, GW19 first-half expiry, one chip per Gameweek;
- Wildcard/Free Hit unavailable in GW1 and no consecutive GW19/GW20 Free Hits;
- no 2026/27 AFCON transfer top-up;
- 38 Gameweeks and terminal state GW39.

The malformed chip-boundary string was replaced by a structured value. The
first-half expiry year was corrected to 2 January 2027.

## Remaining gate

The data/rules audit is complete. Advisory engine use remains blocked only on
explicit owner approval of the exact ruleset ID and SHA in
`docs/rules/2026-27-owner-signoff.md`. That approval does not grant browser
execution or FPL account writes.

Any later official rule amendment requires a new ruleset version/hash, a fresh
activation artifact, semantic diff and owner review.
