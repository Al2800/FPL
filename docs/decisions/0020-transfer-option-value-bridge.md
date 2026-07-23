# ADR-0020: Expected-hit-avoidance value for banked transfers

**Status:** Accepted for replay review
**Date:** 2026-07-24
**Amends:** ADR-0012

## Context

The locked structured forecast makes GW2 player projections plausible, but a
one-Gameweek objective spends free transfers whenever the immediate expected
points are positive. That ignores the ability to respond to injuries,
availability changes and better information at the next deadline.

A genuine multi-Gameweek forecast is preferable, but is not yet available.
Inventing future player projections would be less auditable than declaring a
small bridge policy.

## Decision

The replay optimiser may opt into `expected_hit_avoidance_v1`. For ordinary
transfers it calculates next-Gameweek free transfers from the loaded season
rules and values each transfer banked above the ordinary weekly award as:

`hit cost × probability an extra transfer is needed × future discount`.

The reviewed initial assumptions are probability `0.50` and discount `0.90`.
With a four-point hit this is `1.80` expected points per banked option unit.
These values are policy assumptions, not fitted coefficients. Every review
artifact must preserve the unadjusted immediate objective, show the zero-,
one- and two-transfer alternatives, and publish action breakpoints and a
sensitivity sweep.

The inactive policy remains byte-compatible in meaning with the existing
single-Gameweek solver. Wildcard and Free Hit preserve the existing bank, so
their option term is action-invariant.

## Consequences

- Transfer flexibility is no longer silently valued at zero.
- The bridge does not claim to predict future player points or chip timing.
- Replay results can evaluate whether the assumptions reduce churn; the
  untouched 2025/26 season cannot be used to tune them after outcomes are seen.
- A cutoff-safe multi-Gameweek forecast should eventually replace this bridge,
  at which point both methods should remain as benchmark ablations.
