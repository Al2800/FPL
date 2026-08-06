# 09 — Distributional chip EV and horizon ratification

Status: resolved
Type: task
Track: Phase 2 (distributional chip policy)
Blocked by: 05, 08, 18

Triage (6 August 2026): blockers 05/08/18 resolved; ready for implementation
against ADR-0023 destination horizon (replay comparison) while live remains
single-GW + ADR-0020. Monte Carlo from ticket 05 annotates distributions only —
chip EV must consume those distributions without changing optimiser selection
until this ticket’s GDR surface is wired.

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

## Answer

Implemented distributional chip-now vs later EV as a GDR annotation layer that
consumes Monte Carlo plan-point samples without changing live optimiser
selection or the live planning horizon (still single-GW + ADR-0020).

- `src/optimisation/chip_distributional_ev.py` — pathwise P(chip-now beats
  later control), candidate point distributions, sealed ADR-0023 horizon
  comparison builder, and extraction from sealed GW34 hit-gate evaluation
- `run_gameweek(..., chip_decision=, horizon_comparison=)` attaches
  `chip_distributional_ev` (+ optional `chip_horizon_policy_comparison`) when
  Monte Carlo path points cover chip-candidate XIs
- GDR HTML surfaces the distributional chip EV and horizon comparison sections
- Sealed replay comparison:
  `reports/optimisation/chip-horizon-policy-comparison-2025-26-gw34.json`
  (from `reports/benchmarks/2025-26-counterfactuals/gw-34/transfer-hit-evaluation.json`)
- Script: `scripts/build_chip_horizon_policy_comparison.py`

Tests: `tests/optimisation/test_chip_distributional_ev.py`, GDR HTML contract,
and `tests/integration/test_run_gameweek.py` chip-EV attach case.
