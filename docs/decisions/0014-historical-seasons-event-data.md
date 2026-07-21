# ADR-0014: Historical seasons with reliable event-level data

**Status:** Proposed
**Date:** 2026-07-21
**Decides:** Open Decision 6 (`docs/plan.md` Section 25)

## Context

Open Decision 6 asks which historical seasons have sufficiently reliable event-level data for replay and forecasting evaluation. WP-04 profiles (`docs/data-sources/wp04/`) measured coverage on vaastav / football-data.co.uk downloads.

## Decision

For Phase 1 structured-data work:

- **Primary evaluation seasons:** 2022-23, 2023-24, 2024-25 (merged_gw coverage used in WP-05).
- **Usable for team-strength / odds:** football-data.co.uk E0 files from 2019-20 onward where columns are present.
- **Pre-2019-20:** treat as secondary; do not rely on for event-level start-probability or DC-era scoring without an explicit gap note.
- **Evidence-dependent replay:** not claimed for any historical season (WP-04 news recoverability remains low) — structured-data strategies only.

## Consequences

- Replay harness volumes target these seasons' Gameweeks once fixtures are wired from historical manager states.
- Expanding earlier seasons requires a superseding ADR after a fresh coverage audit.
