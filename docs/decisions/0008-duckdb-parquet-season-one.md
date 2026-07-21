# ADR-0008: DuckDB plus Parquet for season one

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 4 (`docs/plan.md` Section 25)

## Context

Section 8.2 recommends Parquet, DuckDB and SQLite as the initial technologies; Open Decision 4 asked whether they suffice for the first season.

## Decision

Season one runs on Parquet (immutable analytical snapshots), DuckDB (local analytical queries) and SQLite for operational state. PostgreSQL and cloud storage are deferred to the conditions in Phase 9.

## Consequences

- No cloud infrastructure is a prerequisite for any Phase 0–3 work.
- Revisited only if local operation becomes limiting through reliability, collaboration or scale needs.
