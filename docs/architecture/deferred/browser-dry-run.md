# Browser dry-run

**Phase:** 7 · **§19:** Browser dry-run  
**Feasibility summary:** [browser-feasibility.md](browser-feasibility.md) · **ADR:** [ADR-0015](../../decisions/0015-browser-dry-run-stability.md)

## Purpose

Exercise FPL UI flows without committing writes — screenshots, precondition
checks and reversible staging only. **Enter Squad was not selected** in the
recorded dry-run session and **no account mutation was committed**.

## Recorded dry-run (documentary)

A prior authenticated squad-selection dry run exercised:

| Step | Result |
|---|---|
| Read authenticated squad state | Observed |
| Player search | Observed |
| Reversible add / remove | Observed |
| Pitch / list toggle | Observed |
| Auto Pick staging | Observed |
| Submission control visibility | Observed (Enter Squad not selected) |
| Reset to clean staging state | Observed |
| Enter Squad / submission | **Not selected — no submission** |
| Account write | **None — no account mutation** |

Observed actions, inferences and untested actions are separated in
[browser-feasibility.md](browser-feasibility.md). This file does not authorise
repeating the browser session.

## Anticipated interfaces

- `src/execution/` (future): `DryRunSession`, `SelectorMap`, `PreconditionCheck`
- Artefacts: gitignored screenshots under `data/raw/browser-dry-run/`; audit JSONL by run_id
- Inputs: approved Gameweek Decision Record + frozen snapshot ids

## Risks that remain open

- Authentication lifetime for multi-step flows
- Selector volatility across FPL UI changes
- Screenshot and staging evidence retention
- Ambiguous writes (timeout / partial UI update)
- **No-retry** policy when acknowledgement is unclear
- Submission acknowledgement capture
- Post-action **read-back** verification

## Prerequisites

- Terms review for automated browsing
- Stable selectors documented and versioned
- Several consecutive live Gameweeks of stable advisory operation (ADR-0015)
- The execution-bead checklist in [browser-feasibility.md](browser-feasibility.md),
  including owner write approval, staged diff, single write with no-retry,
  acknowledgement, read-back, and ambiguous-write halt

## Activation criteria

- ADR-0015 threshold met
- Separate owner-approved execution bead (not this documentary note)
- Human present for the session; no auto-submit

## Non-goals (Phase 1 and this bead)

- Empty `src/execution/` remains intentional; no browser automation code
- No repeat browser session, no Enter Squad selection, no account write
- No claim of selector stability beyond the recorded session
