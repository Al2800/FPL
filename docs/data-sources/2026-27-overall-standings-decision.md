# Decision: 2026/27 official Overall standings capture

**Ticket:** `.scratch/outstanding-beads/issues/04-live-standings-capture.md`  
**Date:** 2026-07-31  
**Outcome:** **approved for disabled-by-default prospective capture**

## Decision

The official FPL Overall classic league (league id 314) standings endpoint is
approved for private local, post-finalisation snapshots during 2026/27 only.
Collection remains **disabled by default**. Snapshots may feed rank-calibration
threshold rows after reveal; they must never enter the pre-deadline decision
path and must never reconstruct 2025/26 history from live pages.

## Rights / retention

- Source: `fpl-official-endpoints` (registry 0.6.1+)
- Licence: restricted; allowed use private local retention, no redistribution
- Cost: zero (public read-only endpoint)
- Owner: Alastair, 2026-07-31

## Operational rule

Capture only after Gameweek scores are final and auto-subs applied. Missing
pages or missed checkpoints remain explicit gaps.
