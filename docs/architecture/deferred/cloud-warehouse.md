# Cloud warehouse

**Phase:** 9 · **§19:** Cloud warehouse

## Purpose

Move analytical storage off the local DuckDB + Parquet layout when collaboration or scale requires it.

## Anticipated interfaces

- Same logical tables as `control/schemas/`; physical engine swappable behind query helpers
- No change to GDR or rules YAML contracts

## Prerequisites

- Local DuckDB + Parquet proven limiting (ADR-0008 revisit)
- Privacy/non-commercial posture preserved (ADR-0001)

## Activation criteria

- Reliability, collaboration, or experimental need — not “cloud for its own sake” (plan §18)

## Non-goals (Phase 1)

- No cloud project scaffolding
