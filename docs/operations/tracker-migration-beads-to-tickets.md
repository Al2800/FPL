# Tracker migration: Beads → `/to-tickets`

**Date:** 31 July 2026  
**Skills:** [mattpocock/skills engineering](https://github.com/mattpocock/skills/tree/main/skills/engineering)  
**Setup:** `docs/agents/issue-tracker.md` (local markdown)

## Decision

Active work tracking moves from Beads to **local markdown tickets** managed by
the engineering skills (`/to-tickets`, `/triage`, `/implement`, …). Beads remain
archive-only under `.beads/`.

## Published tickets

Feature directory: `.scratch/outstanding-beads/`

| # | Ticket | Status | Blocked by | Former bead |
|---|---|---|---|---|
| 01 | Restore fresh-clone CI artifact boundary | resolved | — | `FPL-cfb` |
| 02 | Approve or decline a historical overall-rank threshold source | resolved | — | `FPL-761` |
| 03 | Close historical score-to-overall-rank calibration | resolved | 02 | `FPL-2xu` |
| 04 | Capture 2026/27 official global standings snapshots | ready-for-human | — (implementation gated by prospective source approval) | `FPL-762` |
| 05 | Rehearse official lineup capture or approve a low-cost challenger | ready-for-human | — | `FPL-eah` |
| 06 | Approve the live initial-squad policy | ready-for-human | — | `FPL-bsw.38` |
| 07 | Close Benchmark Kernel residual | ready-for-agent | 06 | `FPL-bsw` |

Frontier (unblocked now): **04, 05, 06**. These begin with owner decisions;
ticket 04 changes to `ready-for-agent` only after its prospective source gate
is approved. Tickets 01–03 are resolved.

## How to work a ticket

1. Claim: set `Status: claimed` on the ticket file.
2. Implement with `/implement` / `/tdd` as appropriate; stay inside `AGENTS.md` ground rules.
3. Resolve: tick acceptance criteria, set `Status: resolved`, append `## Answer` if useful.
