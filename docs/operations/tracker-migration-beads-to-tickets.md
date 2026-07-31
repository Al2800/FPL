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
| 01 | Restore fresh-clone CI artifact boundary | ready-for-agent | — | `FPL-cfb` |
| 02 | Approve historical overall-rank threshold source | ready-for-human | — | `FPL-761` |
| 03 | Close historical score-to-overall-rank calibration | ready-for-agent | 02 | `FPL-2xu` |
| 04 | Capture 2026/27 official global standings snapshots | ready-for-agent | 02 | `FPL-762` |
| 05 | Rehearse official lineup capture or approve a low-cost challenger | ready-for-human | — | `FPL-eah` |
| 06 | Finish live initial-squad policy and human approval | ready-for-human | — | `FPL-bsw.38` |
| 07 | Close Benchmark Kernel residual | ready-for-agent | 06 | `FPL-bsw` |

Frontier (unblocked now): **01, 02, 05, 06**.

## How to work a ticket

1. Claim: set `Status: claimed` on the ticket file.
2. Implement with `/implement` / `/tdd` as appropriate; stay inside `AGENTS.md` ground rules.
3. Resolve: tick acceptance criteria, set `Status: resolved`, append `## Answer` if useful.
