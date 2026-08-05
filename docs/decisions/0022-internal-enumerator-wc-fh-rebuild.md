# ADR-0022: Keep transparent internal enumerator; add bounded WC/FH rebuild

**Status:** Accepted  
**Date:** 2026-08-05  
**Supersedes:** ADR-0011 (Proposed → Accepted as amended by this ADR)  
**Decides:** Operationalisation ticket 08 / Open Decision 7 revisit  
**Owners:** Alastair

## Context

ADR-0011 chose a smaller transparent internal optimiser over adapting
`open-fpl-solver` or introducing a MILP stack. Ticket 08 asked whether to keep
that enumerator, authorise PuLP/OR-Tools, or adapt `open-fpl-solver`, and
whether Wildcard/Free Hit full-squad rebuild should leave its hit-accounting
stub.

## Decision

1. **Keep the internal enumerator** in `src/optimisation/` — pure Python,
   deterministic, rules from `control/rules/`, every plan through
   `src.scoring.validator`. No PuLP, OR-Tools or `open-fpl-solver` dependency
   for the live path.
2. **Extend it** with a **bounded** full-squad rebuild search for Wildcard and
   Free Hit (declared sell/buy pools and expansion caps), still labelled as
   highest EV in the candidate domain — not a global MILP optimum.
3. Retain the current enumerator as the regression oracle and fallback if a
   rebuild search fails or exceeds resource bounds.

## Rejected alternatives

- **Internal MILP (PuLP/OR-Tools):** more complete search, but opaque
  dependency surface and a second constraint encoding risk.
- **`open-fpl-solver` adaptation:** couples the lab to external modelling
  assumptions and projection conventions.

## Consequences

Ticket 18 implements bounded WC/FH rebuild under this ADR. A future MILP or
external solver still requires another superseding ADR.
