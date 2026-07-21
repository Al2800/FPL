# Live-match agents

**Phase:** 6 · **§19:** Live-match agents

## Purpose

During matches, propose bench/captain contingency notes from provisional events — never force mid-match rule violations.

## Anticipated interfaces

- `live_event_ticks`: fixture_uid, minute, event_type, player_uid, provisional=true, observed_at
- Agent stage: `live_monitor` with hard timeout; output → optional GDR appendix, not automatic execution
- Must filter `available_at <= now` and mark provisional until finalised_at

## Prerequisites

- Stable live data source in registry
- WP-08/09 GDR append path for degraded/live notes
- Agent budgets (ADR-0016)

## Activation criteria

- Stable live feed + provisional label discipline proven on dry runs
- Human still owns any line-up change (Phase 6 ≠ execution)

## Non-goals (Phase 1)

- No live collectors; no in-play agents
