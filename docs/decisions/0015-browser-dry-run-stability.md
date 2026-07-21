# ADR-0015: Stability threshold before browser dry-run

**Status:** Proposed
**Date:** 2026-07-21
**Decides:** Open Decision 11 (`docs/plan.md` Section 25)

## Context

Open Decision 11 asks how many live Gameweeks of stable advisory operation are required before browser dry-run work begins. Dry-run introduces terms, selector fragility and operational risk.

## Decision

Require **at least four consecutive live Gameweeks** of advisory operation in which:

1. a Gameweek Decision Record is produced before the deadline;
2. rules validation passes for the approved plan;
3. no unrecoverable pipeline failure occurs; and
4. human approval is recorded in the journal.

Only then may Phase 7 browser dry-run design proceed to implementation (see `docs/architecture/deferred/browser-dry-run.md`).

## Consequences

- Early-season chaos does not unlock automation.
- The count resets after a severe pipeline incident (owner judgement).
