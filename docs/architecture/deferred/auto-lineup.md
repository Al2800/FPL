# Automatic line-up submission

**Phase:** 7/8 · **§19:** Automatic line-up submission

## Purpose

Submit an already-approved starting XI / captain / bench after dry-run success.

## Anticipated interfaces

- `executions` schema (already in catalog): mode=automated, proposal_id, read_back hash
- Preconditions: approval.status=approved; validation ok; deadline not passed; dry-run green
- Read-back: re-fetch picks and compare to intended GDR recommendation

## Prerequisites

- Browser dry-run proven (above)
- Verified approval journal entry
- Strong audit logging

## Activation criteria

- Explicit owner enablement per season
- Failed read-back → halt and escalate (no retry storm)

## Non-goals (Phase 1)

- Manual entry only (plan advisory mode)
