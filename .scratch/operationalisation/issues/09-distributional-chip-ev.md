# 09 — Distributional chip EV and horizon ratification

Status: needs-triage
Type: task
Track: Phase 2 (distributional chip policy)
Blocked by: 05, 08, 18

## Context

Chips are season-scale assets with a GW19 first-half expiry; plan §12.3 warns against greedy chip use. Current chip selection (`chips.py`) compares deterministic EPs plus a heuristic reserve. With the simulation layer (05) and the solver implementation selected through tickets 08/18 available, chip EV can be computed against distributions over future fixtures (e.g. Bench Boost now versus the best remaining Double Gameweek).

## Scope

- Chip-timing evaluation using simulated plan distributions across the multi-week horizon, including blank/double scenarios from the fixture-revision ledger.
- Surface chip recommendations with a distributional justification in the GDR (probability chip-now beats best-later).
- Replay the 2025/26 benchmark set under the owner-authorised horizon policy
  versus the single-GW/ADR-0020 baseline and report the paired difference.

## Done when

- Chip candidates in the GDR carry distribution-based EV comparisons, and the
  horizon comparison required by the accepted ADR is reproducible.

## Boundaries

This Phase 2 ticket does not itself select or change the live planning horizon.
