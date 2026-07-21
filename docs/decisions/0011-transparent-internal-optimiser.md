# ADR-0011: Smaller transparent internal optimiser

**Status:** Proposed
**Date:** 2026-07-21
**Decides:** Open Decision 7 (`docs/plan.md` Section 25)

## Context

WP-07 requires choosing whether to adapt [`open-fpl-solver`](https://github.com/solioanalytics/open-fpl-solver) or build a smaller internal model. The laboratory needs plans that:

- load every hard constraint from versioned rules YAML (not hard-coded constants);
- validate through the deterministic rules validator (WP-06);
- reproduce identical outputs from a saved solver input;
- remain inspectable for agent-versus-optimiser comparisons.

`open-fpl-solver` is a mature tutorial/recipe collection for FPL MIP optimisation, but it brings its own modelling assumptions, projection conventions and dependency surface. Adapting it would either fork rules into a second encoding or couple this repo to an external project's evolution.

## Decision

Build a **smaller transparent internal optimiser** in `src/optimisation/`:

- pure Python, deterministic enumeration / ranking (no external MIP solver in Phase 1);
- constraints and hit costs read from `control/rules/`;
- every candidate plan passed through `src.scoring.validator` before acceptance;
- solver inputs and outputs serialised as versioned JSON for exact replay.

Revisit adapting or wrapping `open-fpl-solver` (or introducing PuLP/OR-Tools) only if Phase 1 transfer/horizon search becomes intractable under the effort budget — via a superseding ADR.

## Consequences

- Phase 1 transfer search is intentionally bounded (same-position swaps, capped market pools, capped hit depth).
- Chip handling starts as legality + objective modifiers (Triple Captain / Bench Boost); full Free Hit / Wildcard squad rebuild remains an extension behind the same interface.
- Optimiser quality is judged against baselines and human cohort performance, not against open-fpl-solver parity.
