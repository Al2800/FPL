# FPL-bfi — Profile and bound contingency-aware transfer search

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Remove the known runtime roadblock when `probabilistic_v1` squad-contingency
valuation is combined with transfer search, without changing the selected output
for the same declared candidate set. Profile the W10/kcc scale fixture first,
then apply equivalence-preserving levers and an explicit search deadline.

## Progress

- [x] Mapped the contingency × transfer hot path and sealed policy-off widths.
- [x] Added memoisation, shared missing-state reuse, hot-path caches, formation
  upper-bound pruning and `search_deadline_ms`.
- [x] Added profiler, focused tests, performance report and evaluation note.
- [x] Confirmed one-transfer isomorphic fingerprint and rejected promoting
  three-transfer contingency as the production default.

## Surprises & Discoveries

- Observation: policy-off widths (120 / 5,856 / 151,672) remain exact under
  contingency; the explosion is valuation cost, not enumeration.
- Observation: squad-level memoisation rarely hits on the scale fixture because
  almost every transfer changes the 15-player set.
- Observation: `expected_auto_sub_points` dominates CPU time; local appearance
  caches and shared missing-state reuse preserve fingerprints while cutting
  wall time roughly in half versus the unoptimised path.
- Observation: two-transfer isomorphic search still exceeds the 60s p95 budget
  on this host after equivalence-preserving levers; three-transfer remains
  impractical without a non-isomorphic shortlist.

## Decision Log

- Decision: keep production contingency default and W10 zero-transfer result
  unchanged; reject enabling three-transfer contingency.
  Rationale: bead closure allows budget failure evidence for three-transfer.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: expose `search_deadline_ms` and label partial results as
  `highest_ev_in_partial_deadline_bounded_pool`, never as full declared-pool
  equivalence.
  Rationale: a hang is worse than an explicit degraded advisory result.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: apply only equivalence-preserving levers in this bead; any shortlist
  challenger must be a separately named non-isomorphic arm.
  Rationale: prevents silent policy change under a performance label.
  Date/Author: 2026-07-29 / Cursor agent.

## Outcomes & Retrospective

Focused tests lock one-transfer contingency fingerprints, declared widths,
deadline degradation and policy-off scale fingerprints. The performance report
records host/commit, candidate hashes, latency percentiles, hotspots and the
promotion rejection for three-transfer contingency.

## Validation

```bash
python -m pytest -q \
  tests/performance/test_contingency_transfer_search.py \
  tests/optimisation/test_squad_contingency.py \
  tests/test_optimiser.py
python scripts/profile_contingency_transfer_search.py --widths 1,2 --samples 5
```
