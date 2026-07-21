# WP-04 profiles: disabled / pending Tier 2 sources

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
