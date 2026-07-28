# FPL-6ai official FPL endpoint automation

This living plan expands the existing availability-only collector into a
bounded, checkpoint-aware, read-only capture of the approved public FPL
endpoints.

## Purpose

Capture the official state needed by the live 2026/27 engine without
authentication, account mutation, endpoint over-collection, or silent schema
drift. Raw responses remain immutable and local. Availability claims continue
to come only from exact timestamped bootstrap fields.

## Endpoint policy

- `bootstrap-static`: daily preseason and every pre-deadline checkpoint.
- `fixtures`: daily preseason and every pre-deadline checkpoint.
- `element-summary/{player_id}`: only for explicit owned/watchlist/candidate
  player IDs, at daily preseason and T-24h, with a per-run cap.
- `event/{gw}/live`: only after the deadline, for an explicit Gameweek.
- `availability_only`: backwards-compatible bootstrap-only mode used by the
  existing evidence claim contract.

`event-live` is outcome-side evidence and must never be admitted to a
pre-deadline episode. `element-summary` must never fan out over the entire
player universe implicitly.

## Guardrails

- Registry and config record Alastair's approval for private automated
  collection.
- GET only, no authentication, cookies, account endpoints, or account writes.
- Build and validate the complete request plan before the first network call.
- Bound total requests and explicit player IDs per run.
- Stop after HTTP 429, record `Retry-After`, and expose unattempted endpoints.
- Persist every response and failure through the immutable acquisition
  boundary.
- Compare response shape with endpoint-specific expected fields; retain raw
  bytes but degrade visibly on drift.
- Preserve the frozen no-evidence control when collection is incomplete.

## Progress

- [x] Claim the Bead and confirm no active file overlap.
- [x] Inspect the existing collector, source registry, checkpoint vocabulary,
  acquisition manifests, and prior tests.
- [x] Add red endpoint-plan, schema-drift, rate-limit, idempotency, and
  read-only tests.
- [x] Implement the multi-endpoint request planner and collector.
- [x] Extend the CLI and operating runbook.
- [x] Run focused and repository regression tests.
- [x] Record implementation details and close the Bead.

## Validation

    .venv\Scripts\python.exe -m pytest tests/integration/test_live_evidence_collection.py tests/integration/test_source_acquisition.py -q
    .venv\Scripts\python.exe -m pytest

## Outcomes

The configured collector is implemented and registry-approved. It preserves the
legacy availability-only call while adding bounded checkpoint plans for all four
public endpoint families. Schema drift, HTTP failures and rate limiting remain
explicit without fabricating data or disturbing the frozen control.

A real `daily_preseason` capture on 2026-07-28 completed two of two planned
requests (bootstrap and fixtures), added 48 exact-timestamp availability claims,
reported zero gaps and sealed output hash
`8608f08fa9c6f10e0bd3b24dd29a924a5e84d2447c399e14496bbd876bde65ff`.

All 666 collected repository tests pass in bounded batches: 327 core and agent
evaluations, 111 integrations, 148 historical/evaluation/optimisation tests,
and 80 performance plus root-level tests. `git diff --check` is clean.
