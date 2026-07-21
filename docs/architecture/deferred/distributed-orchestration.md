# Distributed orchestration

**Phase:** 9 · **§19:** Distributed orchestration

## Purpose

Run pipeline stages across workers with retries when plain Python scripts become limiting.

## Anticipated interfaces

- Keep stage boundaries already implied by packages (`ingestion` → … → `reporting`)
- Trace format remains JSONL by run_id (ADR-0010); substrate may change via superseding ADR

## Prerequisites

- Clear scale or reliability requirement
- Agent vs non-agent comparison must stay uncontaminated (deterministic path distinguishable)

## Activation criteria

- Superseding ADR to ADR-0010 documenting the new substrate
- Replay harness still runnable locally for evaluation

## Non-goals (Phase 1)

- Plain Python only (ADR-0010)
