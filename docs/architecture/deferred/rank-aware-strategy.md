# Rank-aware strategy

**Phase:** 5 · **§19:** Rank-aware strategy

## Purpose

Adjust risk (differentials, hits, chips) based on rank gap to a target — without replacing the balanced default (ADR-0006).

## Anticipated interfaces

- `rank_context`: overall_rank, target_rank, mini_league_rank, observed_at
- Strategy selector enum on solver input: `balanced | aggressive | rank_chase`
- GDR alternatives already reserve aggressive/conservative slots

## Prerequisites

- Decision objective and risk policy defined (ADR-0006; any superseding ADR)
- Reliable rank observation source

## Activation criteria

- Explicit owner policy for when rank-chase may override balanced default
- Paired evaluation design ready (plan §17.6)

## Non-goals (Phase 1)

- Optimiser remains expected-points − hits; no rank utility in the objective yet
