# ADR-0005: Manager state is entered manually at first

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 5 (`docs/plan.md` Section 25)

## Context

The optimiser requires exact personal financial state before each deadline (Section 7.4). Authenticated automated capture carries terms and automation risk (Section 6.1, Tier 1).

## Decision

Manager state (squad, bank, selling prices, free transfers, chip state) is entered manually before each live deadline, starting at Gameweek 1. Automated or authenticated capture is deferred and reviewed under the later-phase prerequisites (Sections 15.2 and 18, Phases 2 and 7); the owner intends to push this to automation over time.

## Consequences

- The pre-deadline workflow (Section 15.3) includes a manual state-entry step, which must fit inside the effort budget (ADR-0003).
- Publicly readable entry endpoints may cross-check manual entry where their registry entry permits.
- Manager-state capture begins at Gameweek 1 so selling prices are never reconstructed from incomplete data (Section 6.1 obligation).
