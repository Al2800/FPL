# 06 — Benchmark underused official FPL forecast fields

Status: resolved
Type: task
Track: Phase 2 (official-data baselines)
Blocked by: 02

Activation gate: Phase 2 authorised by owner on 4 August 2026 (tickets 06, 14).

## Context

Official Tier 1 data is already captured but incompletely benchmarked:
`ep_next`, FDR and bootstrap team-strength ratings are available before a
deadline; `element-summary` contains current and past-season histories. WP-05
requires official `ep_next` and FDR to be measured against the established
baselines once enough cutoff-safe snapshots exist.

## Scope

- Benchmark official `ep_next` and FDR against the odds-implied and naive
  baselines on pre-deadline snapshots.
- Separately benchmark the bootstrap home/away attack and defence strength
  ratings against the existing team-strength model.
- Assess whether `element-summary` histories add cutoff-safe prior information
  beyond the governed vaastav warehouse; document duplication, leakage and
  retention implications before adoption.
- Record each field's marginal value under time-based evaluation. A null result
  is retained (plan §11.2), not converted into a feature.

## Done when

- `ep_next`, FDR, official team-strength ratings and `element-summary` histories
  each have a reproducible benchmark or a documented reason the available
  sample is not yet sufficient.
- Only fields that improve the preregistered baseline are promoted, with source
  references and transformation versions retained.

## Boundaries

This ticket does not cover ICT (ticket 16), set pieces (ticket 15), ownership
(ticket 20) or price changes (ticket 07).

## Answer

Implemented:

- `src/forecasting/official_field_benchmarks.py` — time-based MAE / association
  harness for `ep_next`, FDR and bootstrap strength; element-summary adoption
  assessment (duplication, leakage, retention); **no auto-promotion**
- `scripts/benchmark_official_fpl_fields.py` — offline CLI
- Live corpus report: `reports/forecasting/official-fpl-field-benchmarks.{json,md}`
  — **insufficient_sample** (pre-deadline snapshots present; zero paired
  finished-GW outcomes; no element-summary corpus) so nothing is promoted
- `docs/data-sources/wp05-status.md` updated

Tests: `tests/forecasting/test_official_field_benchmarks.py`.
