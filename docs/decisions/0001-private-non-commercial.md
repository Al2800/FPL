# ADR-0001: The project is private and non-commercial

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 1 (`docs/plan.md` Section 25)

## Context

Every data-governance judgement in the plan — what may be collected, retained and reused (Sections 6.2–6.3) — depends on whether the project is private research or something public or commercial. Phase 0 makes this a hard gate on all raw-data collection.

## Decision

The project is entirely private and non-commercial: a personal research project. No data, derived dataset, model output or report is published commercially, and no third-party data is redistributed.

## Consequences

- Source-registry `allowed_use` entries are evaluated against private, non-commercial analysis only.
- The governance side of the raw-data collection gate is cleared; each source still needs its own registry entry before collection.
- If the project's status ever changes (publication, dataset sharing, any commercial use), every registry entry and this decision must be re-reviewed first.
