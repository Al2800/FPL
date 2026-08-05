# ADR-0023: Four-Gameweek destination horizon; live single-GW until forecasts exist

**Status:** Accepted  
**Date:** 2026-08-05  
**Amends:** ADR-0012, ADR-0020  
**Decides:** Operationalisation ticket 08 (horizon)  
**Owners:** Alastair

## Context

Effective FPL decisions need multi-week foresight (banking, chips, fixtures).
ADR-0012 set Phase 1 live optimisation to a single Gameweek; ADR-0020 added an
expected-hit-avoidance bridge for banked transfers. Policy
`control/policies/transfer-horizon-v1.json` already experiments with a
**4-Gameweek** receding horizon and discount `0.9`. The initial-squad policy
separately uses a **6-Gameweek** preseason horizon (`horizon_gameweeks: 6`) —
that is not the live weekly optimiser.

## Decision

1. **Destination live planning horizon is 4 Gameweeks**, with discount factor
   **0.9** (aligned with `transfer-horizon-v1`), once cutoff-safe multi-GW
   forecasts exist.
2. **Until then**, the live weekly optimiser remains **single-Gameweek** with
   the ADR-0020 option-value bridge as the auditable interim.
3. Initial-squad **GW1–GW6** horizon stays a preseason-only policy; it does not
   authorise 6-GW live transfer search.
4. Chip-timing evaluation over longer windows remains behind ticket 09 once
   the 4-GW forecast path is live.

## Consequences

Ticket 18 must implement WC/FH rebuild under the current single-GW live
objective, and expose the `horizon_gameweeks` / `discount_factors` interface for
the 4-GW switch without inventing future player points. Ticket 09 consumes
distributions over the ratified horizon once forecasts and solver support it.
