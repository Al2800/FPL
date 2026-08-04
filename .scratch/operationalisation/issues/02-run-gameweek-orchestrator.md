# 02 — Single `run_gameweek` live orchestrator

Status: resolved
Type: task
Track: A (close the live loop)
Blocked by: 01

## Context

There is no end-to-end live command. The advisory path is a human-orchestrated chain of capture dispatch, `scripts/build_live_episode.py`, optimiser scripts and shadow freezing. Phase 1/2 exit criteria (plan §18) require a complete GDR produced end-to-end for a live deadline.

## Scope

One deterministic orchestrator (plain Python per ADR-0010), e.g. `scripts/run_gameweek.py --gw N`, chaining:

1. select latest pre-deadline snapshots (enforcing `available_at <= deadline` via existing point-in-time utilities);
2. build the live episode;
3. run forecasts (`live_faithful` composition);
4. adapter from ticket 01 → optimiser candidate plans (no-transfer, free-transfer, hit, chip candidates);
5. deterministic rules validation;
6. baseline comparison (`src/reporting/baseline_comparison.py`);
7. render the GDR to `reports/gameweeks/2026-27-gwNN/` with data-freshness and degraded-mode flags (§22.1).

Evidence/challenger stages are optional inputs: if absent or late, fall back to the deterministic plan and mark the record degraded (§15.3 T-90m rule).

## Done when

- One command produces a validated, rendered GDR from existing snapshots with no undocumented manual steps.
- Rerun with identical inputs reproduces the record (success criterion 6, plan §3.2).
- An integration test covers the chain on fixture data.

## Answer

Implemented:

- `src/orchestration/run_gameweek.py` — deterministic chain:
  - `select_latest_predeadline_snapshot` (point-in-time filter; late candidates ignored)
  - optional `build_live_faithful_forecast` composition → adapter market
  - ticket-01 `adapt_solve_and_record` (optimiser + baseline + GDR)
  - degraded flags when evidence absent/late or live-faithful degraded
  - writes `decision-record.json/.txt`, solver I/O and forecast market under the out dir
- `scripts/run_gameweek.py --gw N` — CLI wrapper (forecast JSON **or** live-faithful inputs)

Integration: `tests/integration/test_run_gameweek.py` — **3 passed**, including
reproducible fingerprints on identical inputs and schema-valid GDR with
`degraded=true` when evidence is absent.
