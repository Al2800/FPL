# Effective ownership

**Phase:** 5 · **§19:** Effective ownership

## Purpose

Estimate ownership conditional on active/template managers for differential strategy — not raw overall ownership alone.

## Anticipated interfaces

- `ownership_estimates`: player_uid, gameweek, overall_pct, effective_pct, cohort_definition, available_at
- Feature join into projections; never a hard constraint

## Prerequisites

- Reliable and permitted population / sample data
- Clear cohort definition recorded with each estimate

## Activation criteria

- Data licence and sampling method accepted
- Ablation shows value over overall ownership baseline

## Non-goals (Phase 1)

- No ownership collectors beyond official FPL fields already on snapshots
