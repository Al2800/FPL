# Contingency-aware transfer search

## Scope

This note records the FPL-bfi investigation into combining `probabilistic_v1`
squad-contingency valuation with the declared one-, two- and three-transfer
pools on the W10/kcc scale fixture.

## Declared widths

| Transfers | Layer candidates | Cumulative with no-transfer/bank |
|---|---:|---:|
| 1 | 120 | 122 |
| 2 | 5,856 | 5,978 |
| 3 | 151,672 | 157,650 |

Exact layer candidate SHA-256 digests are recorded in
`reports/performance/contingency-transfer-search.json`.

## Budgets

| Width | p95 target | Peak memory |
|---|---|---|
| 1 | ≤ 5 s | ≤ 1 GiB |
| 2 | ≤ 60 s | ≤ 1 GiB |
| 3 | ≤ 300 s (experimental) | ≤ 1 GiB |

## Equivalence-preserving levers

1. Reuse `_missing_count_distribution` across bench permutations of one XI.
2. Memoize full contingency lineups and per-lineup evaluations inside one solve.
3. Localise appearance probabilities inside `expected_auto_sub_points`.
4. Prune formations whose optimistic upper bound cannot beat the current best.
5. Bound benchmark work with `search_candidate_budget`; retain `search_deadline_ms` only as an operational watchdog that discards timing-dependent partial work and returns the no-transfer baseline.

A shortlist or truncated width is **not** isomorphic to the full declared set.
Candidate-budget searches use `highest_ev_in_deterministic_candidate_budget`.
Watchdog expiry uses `deterministic_no_transfer_deadline_fallback`; elapsed wall time
is recorded only by the profiler and never changes semantic solver output.

## Measured result

Both phases used Python 3.14 on the same 16-logical-CPU Windows host with
29.8 GB RAM, one warmup and five clean warm-process samples. Deep CPU and
allocation profiling was limited to width one so instrumentation did not
multiply the full width-two runtime.

| Width | Baseline p50 / p95 / p99 | Optimized p50 / p95 / p99 | p50 speedup | Equivalence |
|---|---:|---:|---:|---|
| 1 | 5.921 / 6.021 / 6.025 s | 3.599 / 3.778 / 3.794 s | 1.64x | candidate hash, candidate count and output fingerprint identical |
| 2 | 287.325 / 289.657 / 290.042 s | 190.615 / 287.988 / 290.626 s | 1.51x | candidate hash, candidate count and output fingerprint identical |
| 3 deterministic budget | n/a | 18.352 / 19.045 / 19.050 s for 300 total valid candidates | n/a | deliberately bounded; not isomorphic to 157,650 cumulative candidates |

Width one now meets its five-second p95 budget. Width two remains far above
60 seconds and has a loaded-host tail outlier, so full contingency search is an
offline diagnostic, not a deadline-path default. Width three remains disabled.

## Profiled opportunity matrix

Rank is `(impact × confidence) / effort`, each input scored 1–10.

| Rank | Opportunity | Impact | Confidence | Effort | Score | Decision |
|---:|---|---:|---:|---:|---:|---|
| 1 | Memoise or tabulate repeated auto-sub probability subproblems | 9 | 9 | 5 | 16.2 | next isomorphic investigation; dominant CPU hotspot |
| 2 | Precompute rounded appearance/state terms outside candidate loops | 7 | 8 | 4 | 14.0 | investigate with golden objective equality |
| 3 | Deterministic parallel candidate evaluation and ordered reduction | 8 | 6 | 8 | 6.0 | defer; higher implementation and memory risk |
| 4 | Expand full-squad memoisation | 2 | 9 | 3 | 6.0 | deprioritise; measured hit rate is low |

`expected_auto_sub_points` remains the dominant optimized CPU hotspot. Peak
traced Python heap for the representative width-one diagnostic was 49,429,750
bytes, below 1 GiB. Profiles ran on an active shared workstation, so absolute
wall times are host-load observations; candidate hashes and fingerprints are
the equivalence oracle.

A full width-two deep-memory pass is deferred by owner decision: the solver
completes, memory did not present as the roadblock, and further profiling would
delay higher-value replay/process work. The next optimization bead may add
low-overhead per-width process memory telemetry.
## Promotion decision

Three-transfer contingency remains disabled as a production default. The report
rejects promotion unless an isomorphic full-set run meets the experimental
budget and equivalence oracle. Existing W10 zero-transfer results and policy-off
optimiser-scale fingerprints remain unchanged.
