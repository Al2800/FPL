# ADR-0012: Single-Gameweek optimiser horizon for Phase 1

**Status:** Amended by ADR-0020 and ADR-0023
**Date:** 2026-07-21
**Decides:** Open Decision 14 (`docs/plan.md` Section 25)

## Context

Section 12.3 notes that single-Gameweek optimisation undervalues banked transfers and chip timing, while long horizons multiply forecast error. Open Decision 14 asks for the initial planning horizon and discounting approach.

## Decision

Phase 1 uses a **single-Gameweek expected-points objective** (starting XI with captaincy, minus transfer-hit costs, plus optional Bench Boost bench points).

The solver interface reserves:

- `horizon_gameweeks` (default `1`);
- `discount_factors` (optional list; unused while horizon is 1);
- candidate plan labels for `bank_transfer` and chip alternatives so multi-Gameweek and chip-timing policies can be added without changing call sites.

Chip *timing* (e.g. Bench Boost now versus a future Double Gameweek) is out of scope until multi-Gameweek forecasts exist; the initial build may still emit chip versus no-chip alternatives for the **current** Gameweek only.

## Consequences

- Transfer banking is represented as an explicit candidate plan, not as a multi-period value-of-information calculation.
- A later ADR must define discounting before horizon > 1 becomes the live default.
