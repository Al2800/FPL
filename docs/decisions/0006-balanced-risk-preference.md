# ADR-0006: Balanced risk preference with weekly aggressive override

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 9 (`docs/plan.md` Section 25)

## Context

Candidate plans span conservative to aggressive/differential (Sections 4.4 and 12.3); the recommended plan needs a default risk profile.

## Decision

The default risk preference is **balanced**. Every Gameweek Decision Record also presents the aggressive/differential alternative (and the conservative one), and the owner may select a different profile in any given week.

## Consequences

- Optimiser default objective weights reflect the balanced profile.
- The weekly approval interface offers the alternatives without requiring a pipeline re-run.
- Retrospectives record which profile was chosen each week and its outcome, so the default can be revisited with evidence.
