# Browser dry-run

**Phase:** 7 · **§19:** Browser dry-run

## Purpose

Exercise FPL UI flows without committing writes — screenshots and precondition checks only.

## Anticipated interfaces

- `src/execution/` (future): `DryRunSession`, `SelectorMap`, `PreconditionCheck`
- Artefacts: gitignored screenshots under `data/raw/browser-dry-run/`; audit JSONL by run_id
- Inputs: approved Gameweek Decision Record + frozen snapshot ids

## Prerequisites

- Terms review for automated browsing
- Stable selectors documented and versioned
- Several consecutive live Gameweeks of stable advisory operation (ADR-0015)

## Activation criteria

- ADR-0015 threshold met
- Human present for the session; no auto-submit

## Non-goals (Phase 1)

- Empty `src/execution/` remains intentional; no browser automation code
