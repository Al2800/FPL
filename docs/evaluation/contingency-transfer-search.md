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

## Promotion decision

Three-transfer contingency remains disabled as a production default. The report
rejects promotion unless an isomorphic full-set run meets the experimental
budget and equivalence oracle. Existing W10 zero-transfer results and policy-off
optimiser-scale fingerprints remain unchanged.
