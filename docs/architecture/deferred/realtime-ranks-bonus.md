# Real-time ranks / bonus

**Phase:** 6 · **§19:** Real-time ranks/bonus

## Purpose

Track provisional bonus and live rank movement for information only during Gameweeks.

## Anticipated interfaces

- `live_bonus_estimates`, `live_rank_ticks` with provisional flags
- Reporting view consumed by live-match agents; not an optimiser input until finalised

## Prerequisites

- Supported official or permitted source
- Clear finalisation rules when FPL confirms BPS

## Activation criteria

- Source operational value demonstrated (not vanity dashboards)
- Stale/provisional distinction enforced in schemas

## Non-goals (Phase 1)

- No live BPS ingestion beyond what bootstrap already exposes post-match
