# Mini-league rival analysis

**Phase:** 5 · **§19:** Mini-league rival analysis

## Purpose

Surface ownership and differential context versus named rivals without letting rivalry override rules validation.

## Anticipated interfaces

- `rival_snapshots`: league_id, manager_id, gameweek, picks[], observed_at, available_at
- GDR optional block: `competitive_context` (ownership diffs, template risk) — advisory only
- Agent tool: `get_rival_picks(league_id, as_of)` gated by registry

## Prerequisites

- Stable, permitted manager/league data access (terms review)
- Manual or authenticated manager state (ADR-0005 evolution)

## Activation criteria

- Rights-cleared access path documented in source registry
- Phase 1 advisory pipeline stable for several live Gameweeks

## Non-goals (Phase 1)

- No league scraping; no differential objective in the optimiser
