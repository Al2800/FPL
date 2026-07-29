# ADR-0015: Stability threshold before browser dry-run

**Status:** Proposed  
**Date:** 2026-07-21  
**Decides:** Open Decision 11 (`docs/plan.md` Section 25)  
**Related:** [browser-dry-run.md](../architecture/deferred/browser-dry-run.md) ·
[browser-feasibility.md](../architecture/deferred/browser-feasibility.md)

## Context

Open Decision 11 asks how many live Gameweeks of stable advisory operation are
required before browser dry-run work begins. Dry-run introduces terms, selector
fragility and operational risk.

A separate documentary bead (`FPL-bsw.6`) records that an authenticated
squad-selection dry run already exercised reversible staging only:
**Enter Squad was not selected**, there was **no submission**, and **no account
mutation was committed**. That record does not enable browser execution.

## Decision

Require **at least four consecutive live Gameweeks** of advisory operation in which:

1. a Gameweek Decision Record is produced before the deadline;
2. rules validation passes for the approved plan;
3. no unrecoverable pipeline failure occurs; and
4. human approval is recorded in the journal.

Only then may Phase 7 browser dry-run design proceed toward an execution test
(see `docs/architecture/deferred/browser-dry-run.md` and the feasibility
prerequisites in `browser-feasibility.md`).

Any future write path must additionally require: explicit owner approval,
selector and screenshot evidence, pre-action read, staged diff, single write
with **no-retry**, submission acknowledgement, post-action **read-back**, and
an **ambiguous**-write halt with rollback or escalation. Browser execution
remains disabled until a separately approved bead satisfies those gates.

## Consequences

- Early-season chaos does not unlock automation.
- The count resets after a severe pipeline incident (owner judgement).
- Documentary dry-run evidence cannot be mistaken for authorisation to write.
