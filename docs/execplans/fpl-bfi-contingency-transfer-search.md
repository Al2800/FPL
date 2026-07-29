# FPL-bfi — Profile and bound contingency-aware transfer search

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Remove the known runtime roadblock when `probabilistic_v1` squad-contingency
valuation is combined with transfer search, without changing the selected output
for the same declared candidate set. Profile the W10/kcc scale fixture first,
then apply equivalence-preserving levers, a deterministic candidate budget and an operational deadline fallback.

## Progress

- [x] Mapped the contingency × transfer hot path and sealed policy-off widths.
- [x] Added memoisation, shared missing-state reuse, hot-path caches, formation
  upper-bound pruning and `search_deadline_ms`.
- [x] Added profiler, focused tests, initial performance report and evaluation note.
- [x] Replaced timing-dependent partial pools with deterministic candidate budgets and
  a stable no-transfer watchdog fallback.
- [x] Regenerated reconstructible before/after profiles and ranked opportunity matrix.
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
- Observation: width-one p50 improved 1.64x and width-two p50 improved 1.51x
  with identical candidate hashes, counts and output fingerprints. Width two
  still exceeds the 60s p95 budget; three-transfer full search remains
  impractical without a separately labelled non-isomorphic bound.
- Observation: an attempted deep width-two tracemalloc/cProfile pass exceeded
  21 minutes because instrumentation dominated runtime. Deep profiles are now
  restricted to representative width one; five clean latency samples remain
  mandatory at widths one and two.

## Decision Log

- Decision: keep production contingency default and W10 zero-transfer result
  unchanged; reject enabling three-transfer contingency.
  Rationale: bead closure allows budget failure evidence for three-transfer.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: use `search_candidate_budget` for reproducible partial-pool
  benchmarks. Treat `search_deadline_ms` only as an operational watchdog; on
  expiry discard timing-dependent partial candidates and return the deterministic
  no-transfer baseline.
  Rationale: machine scheduling must never change a sealed solver result.
  Date/Author: 2026-07-29 / Codex takeover review.
- Decision: defer a full width-two deep-memory pass by owner direction after
  establishing that runtime, not observed memory growth, is the roadblock.
  Rationale: avoid delaying replay/process work for optional profiling.
  Date/Author: 2026-07-29 / Alastair and Codex.
- Decision: apply only equivalence-preserving levers in this bead; any shortlist
  challenger must be a separately named non-isomorphic arm.
  Rationale: prevents silent policy change under a performance label.
  Date/Author: 2026-07-29 / Cursor agent.

## Outcomes & Retrospective

Focused tests lock exact repeated output, one-transfer contingency fingerprints,
declared widths, deterministic candidate budgeting, stable watchdog fallback
and policy-off scale fingerprints. Exact-commit baseline and optimized reports
record five-sample latency distributions, host metadata, candidate hashes,
profiles and the three-transfer promotion rejection. Width one meets budget;
width two and the full width-three search do not.

## Validation

```bash
python -m pytest -q \
  tests/performance/test_contingency_transfer_search.py \
  tests/optimisation/test_squad_contingency.py \
  tests/test_optimiser.py
python scripts/profile_contingency_transfer_search.py --widths 1,2,3 --samples 5 --deep-profile-widths 1
```
