# Core capacity and genuine-replay readiness audit

**Date:** 23 July 2026  
**Audit bead:** `FPL-60q`  
**Genuine replay bead:** `FPL-bsw.13`  
**Scope:** evidence-backed capacity check plus end-to-end process, data and
algorithm readiness for the 2025/26 Benchmark v0 replay and 2026/27 live use.

## Executive verdict

The system is not blocked by general Python, JSON or sequential orchestration
performance. Reading all 38 observed episodes takes about 0.4 seconds, policy
state tests are sub-second, and one existing small-fixture solve takes about ten
seconds. That is acceptable for one live weekly decision.

The current system is, however, **not ready for a defensible 38-Gameweek policy
comparison**. Bead 13 currently sits across four missing or incomplete seams:

1. there is no deadline-safe episode-to-feature/market adapter;
2. there is no single canonical validated plan consumed by both scoring and
   policy-state transition;
3. there is no realised outcome scorer for XI, bench, captaincy, chips, blanks
   and doubles; and
4. the optimiser's toy fixture hides a combinatorial scale problem at realistic
   candidate-pool widths.

These are process and algorithm issues, not reasons to introduce distributed
systems or broad performance engineering. Three prerequisite beads now block
Bead 13:

- `FPL-3nw` — deadline-safe historical feature and market adapter;
- `FPL-5i9` — canonical validated plan and realised outcome scorer;
- `FPL-kcc` — season-aware, replay-scale deterministic optimiser.

Benchmark v0 remains valuable. Its correct immediate purpose is to prove
chronology, isolation, state transitions, reproducibility, failure modes and the
structured baseline process. Historical evidence-agent results and exact
financial optimality must not be overstated where point-in-time evidence or
prices are unavailable.

## Existing execution graph

```text
frozen source files
  -> historical_episode_builder
      -> episode-manifest.json
      -> observed.json
      -> hidden-outcome.json (sealed)
      -> ruleset.yaml / identity-map.json

observed episode + arm policy state
  -> MISSING deadline-safe feature/market state
  -> existing forecasting evaluation modules (not yet an inference adapter)
  -> SolverInput
  -> optimisation.solve
  -> MISSING canonical ValidatedGameweekPlan
  -> deterministic validation
  -> policy-result + GDR freeze
  -> hidden outcome reveal
  -> MISSING realised outcome scorer
  -> transition_policy_state
  -> arm-specific successor state
  -> replay artefacts
  -> Bead 14 paired/counterfactual evaluation
```

The existing `replay_harness.py` skips this graph. It loads one synthetic solver
fixture, solves it, wraps it in a GDR and optionally accepts a manually supplied
points total. `run_replay_pilot_set.py` repeats that fixture under different
Gameweek labels. This is correctly described by Bead 13 as a smoke test, not a
historical replay.

## Measurement method and environment

Machine and runtime:

- Windows 11;
- AMD Ryzen 7 8745HS, 8 cores / 16 logical processors;
- Python 3.13.7;
- pandas 3.0.3, NumPy 2.5.1, PyYAML 6.0.3 and jsonschema 4.26.0.

The committed profiling harness is
`scripts/profile_core_performance.py`. Ordinary latency and CPU samples are
captured without a profiler. CPU, Python allocation and application-I/O
profiles are separate instrumented passes. Timing thresholds are deliberately
not test assertions; deterministic output and domain invariants are.

Seven warm samples were captured for each workload. Seven observations are
enough to expose order-of-magnitude constraints but not to claim production SLO
precision. Percentiles use linear interpolation.

| Workload | p50 | p95 | p99 | Throughput |
|---|---:|---:|---:|---:|
| Golden solver: 20 players, max 2, 123 candidates | 9.775 s | 11.246 s | 11.427 s | 0.098 solves/s |
| In-memory synthetic replay | 10.217 s | 10.446 s | 10.507 s | 0.099 replays/s |
| Read/decode all 38 v2 observed episodes (27.9 MB) | 0.396 s | 0.444 s | 0.450 s | 96.3 episodes/s |

Five separate cold-process solver runs produced p50 8.538 s, p95 8.909 s and
p99 8.956 s. They are not directly comparable with the warm series because
they ran later under different machine conditions; they confirm the same
order of magnitude.

External process-tree sampling measured approximately:

- 98.2 MB peak working set for one solver process;
- 102.8 MB peak working set for a full 38-episode observed scan;
- 1.36 MB peak traced Python heap for the solver's retained Python
  allocations; and
- 5.88 MB peak traced Python heap while scanning all observed episodes.

The full repository suite passed twice:

- 250 tests in 154.75 seconds;
- 250 tests in 171.23 seconds with slow-test reporting.

Almost all suite time is repeated optimiser work. The slowest tests were 10–30
seconds each and repeatedly exercised the same golden solve/replay.

## Measured CPU, allocation and I/O profile

One cProfile solver pass took 22.88 instrumented seconds:

| Frame | Calls | Cumulative time |
|---|---:|---:|
| `solve` | 1 | 22.88 s |
| `_evaluate_squad` | 122 | 22.77 s |
| `choose_starting_xi` | 122 | 22.57 s |
| `load_rules` | 123 | 10.27 s |
| `legal_formations` | 122 | 10.20 s |

Application-level I/O instrumentation found:

- the 20.5 KB 2026/27 YAML rules file was read **123 times** in one solve;
- those reads totalled 2.52 MB;
- the solver input JSON was read once.

The dominant retained allocations are in the PyYAML composer and pandas
DataFrame/index/Arrow-string machinery. This supports two precise findings:

1. rules are being reparsed inside candidate-lineup evaluation; and
2. each 15-player candidate is repeatedly converted to and filtered as a
   DataFrame.

No database N+1 issue exists. The measured analogue is the repeated YAML load.
Network, queues, locks and concurrency are not on this path.

## Realistic optimiser scale

The golden fixture has only five unowned players and produces 123 legal
candidates. It is not representative of the declared pool limits.

With a normal 15-player squad, five possible sells per position (where the
squad permits) and eight buys per position, the current candidate contract
produces:

| Transfers | Candidate sets | Enumeration time | Enumeration peak Python heap |
|---:|---:|---:|---:|
| 1 | 120 | 0.134 s | 0.69 MB |
| 2 | 5,856 | 0.247 s | 1.92 MB |
| 3 | 151,672 | 2.795 s | 40.0 MB |

Enumeration itself is not the main problem. The current implementation then
rebuilds and validates a pandas lineup for every candidate. Extrapolating the
measured candidate-evaluation cost makes a realistic two-transfer solve take
minutes and a three-transfer solve potentially take hours. That would block a
38 × 5 replay and make hit/chip scenarios impractical.

This is the one optimisation area that moves the needle enough to be a replay
prerequisite. The intended change is not approximation:

- accept the exact episode rules mapping once;
- generate candidates lazily in the same deterministic order;
- precompute player, finance and club indexes;
- evaluate legal formations with exact pure-data top-by-position selection;
- retain the same objective, candidate pool, tie order and emitted plans;
- differential-test the new evaluator against the current implementation on
  the golden case and generated legal squads.

Full Wildcard and Free Hit rebuild optimisation is not implemented today.
The current solver's maximum of three transfers cannot be presented as a full
chip optimiser. That capability must remain explicitly gated.

## Point-in-time data findings

### What the v2 episode corpus does correctly

- 38 distinct 2025/26 episodes exist.
- Observed and hidden-outcome partitions are physically separate.
- Every episode embeds the validated 2025/26 ruleset bytes and hash.
- Current fixtures and completed prior results are separated from player
  outcomes.
- Same-Gameweek points, minutes, bonus, BPS and unsafe xP are hidden.
- Identity-map, dataset and source hashes are retained.
- The hidden-outcome reference is excluded from the pairing hash.

### Player history is only one Gameweek deep per episode

GW2 contains GW1 player rows, GW3 contains GW2 rows, and so on. The existing
forecast code requires rolling-three and cumulative-prior features.

Sequential replay can accumulate the prior episodes, but that accumulated
feature state is decision-relevant and therefore needs its own canonical hash
and lineage. It cannot exist as unrecorded mutable memory, nor may a standalone
GW20 replay silently query an unsealed full-season table.

### Double Gameweek leakage in the existing lag helper

`add_lagged_features` groups by player and shifts rows, not player-Gameweeks.
For a player with two rows in one Double Gameweek, the second fixture row can
observe the first fixture's result through `shift(1)`. Both fixtures were locked
at the same FPL deadline, so this is within-Gameweek look-ahead.

Observed examples:

- the GW27 episode carries 896 rows for 817 players from GW26;
- the GW34 episode carries 1,077 rows for 829 players from GW33;
- the GW37 episode carries 920 rows for 838 players from GW36.

The correct sequence is: aggregate completed fixture rows to one
player-Gameweek observation, then create lags/rolling windows. Upcoming Double
Gameweek projections may be made per fixture and summed only after prediction.

### Blank Gameweeks make the market incomplete

The GW35 episode carries only 582 prior-player rows because GW34 had seven
fixtures. A player with no fixture has no `merged_gw` row, but remains selectable
and may be owned. A market constructed from only the immediately preceding
Gameweek will therefore omit legal players and can make state transition fail.

The historical feature state must maintain a full player catalogue and carry
the latest safe quote/identity forward with explicit age and staleness.

### Deadline-accurate prices are not recoverable from this corpus

The upstream vaastav scraper runs after each Gameweek ends. Its documentation
defines `value` as the price “at this gameweek”, but does not establish it as a
deadline snapshot. The repository's own WP-04 assessment already warns that
prices and ownership can reflect post-deadline movement.

Comparing consecutive recorded Gameweeks:

- an average of 56.4 common players changed recorded price;
- the maximum was 165 changed players before the GW3 row;
- 560 new-player appearances and 409 temporary missing-player appearances
  occur across consecutive partitions.

Current-GW `value` must therefore not be moved into the observed partition and
labelled deadline-safe. The strict historical lane should use the last safely
observed value with `source_gameweek`, age and a limitation flag. A separate,
explicitly contaminated sensitivity lane may compare final/current-GW values
to quantify how often financial legality or choice changes, but it cannot
support benchmark-performance claims.

For 2026/27 this limitation is avoidable: immutable official bootstrap snapshots
at T-48h, T-8h, T-2h and the cutoff provide actual decision-time prices.

### GW1 is a controlled seed, not a forecastable episode today

The GW1 observed partition has no prior player rows or prior results. No current
production seed artifact exists. Benchmark v0 should encode the source-backed
pre-deadline Scout squad, lineup/captain evidence, launch prices, player IDs and
hash. All arms begin from it. GW1 then tests seed scoring and state
initialisation; policy divergence begins at GW2.

This does not define the 2026/27 starting-team process. Live 2026/27 selection
will use launch snapshots, pre-season priors and the evidence/agent process.

## Forecast-algorithm findings

The corrected forecasting functions run on the frozen 2025/26 full source when
adapted in memory. Provisional measurements were:

- naive prior-start Brier: 0.1125;
- rolling start/minutes Brier: 0.0912;
- rolling start log loss: 0.3126;
- expected-minutes MAE: 14.51;
- rolling points MAE: 1.04028;
- home/away adjusted rolling points MAE: 1.04028.

The rolling start model improves on the naive start model. The existing simple
home/away adjustment adds effectively no measured value. These figures are
provisional because the current row-level lag implementation mishandles Double
Gameweeks; they must be regenerated after player-Gameweek aggregation.

More importantly, these modules are evaluation builders, not an inference
adapter:

- they load a complete season CSV directly;
- they return forecasts on historical rows rather than construct rows for an
  upcoming fixture set;
- team Elo and odds modules are not joined into player expected points;
- `naive_expected_points` expects live bootstrap-style columns absent from the
  historical episode;
- there is no function that takes `observed episode + feature state` and emits
  a versioned player-projection artifact.

Data streams are therefore registered and preserved, but not yet
algorithmically combined in the replay path.

For Benchmark v0, the pre-declared deterministic structured forecast should
remain simple:

1. aggregate completed player data by player-Gameweek;
2. calculate rolling starts, minutes and points from prior Gameweeks only;
3. create one upcoming player-fixture row per current fixture;
4. emit zero for blanks and sum per-fixture projections for doubles;
5. record expected minutes separately;
6. use a declared fallback for new/no-history players;
7. do not arbitrarily weight Elo, closing odds or final FDR into player points
   until an ablation/calibration defines that mapping.

Prior match results and Elo can be retained as a parallel feature/baseline.
Their presence in an episode does not require a fabricated weight. A later
pre-declared model can prove whether they improve calibration and decisions.

Live evidence remains an agent treatment: every agent receives the same
deterministic projections, then may propose cited expected-minutes adjustments
under the existing evidence policy. Historical agent arms without a complete
news archive are plumbing/fallback tests, not fair agent-value estimates.

## Plan, scoring and state findings

The longitudinal policy-state implementation is the strongest completed
portion. It has tests for:

- independent arm histories;
- predecessor hashes;
- purchase/current/selling prices;
- normal transfers and hits;
- banked transfers and the GW16 AFCON top-up;
- Wildcard and Free Hit persistence;
- chip expiry and adjacent-half restrictions;
- terminal state.

It cannot yet be driven by the replay because:

- the GDR accepts an arbitrary `lineup` object;
- candidate-plan/final-proposal schemas do not specify the complete ordered
  bench, vice-captain, chip and financial result;
- `policy-result.json` references a GDR and validation artifact rather than
  defining a scoreable plan;
- no outcome module aggregates hidden player fixture rows, applies autosubs,
  captain fallback and chip multipliers, and supplies `gross_points`.

The needed deep module is a canonical `ValidatedGameweekPlan`. Its interface is
the test surface for optimiser output, agent proposals, GDR serialization,
outcome scoring and state transition. This concentrates the invariants instead
of translating several shallow dictionary shapes.

## Capacity implications

If every arm used the current small golden solve once, 38 × 5 solves would take
roughly 32 minutes at the measured replay p50. That is acceptable for an offline
research run and trivial compared with bounded agent calls.

That estimate is misleading for a real market. Realistic two/three-transfer
candidate counts make the current evaluator a genuine blocker. `FPL-kcc` must
establish the realistic scale baseline and exact evaluator before Bead 13.

For live 2026/27, one weekly decision does not need high throughput. The
operational priorities are:

- finish before the declared T-90m degrade threshold;
- retain deterministic fallback;
- avoid stale snapshots and ambiguous state;
- record cost and latency;
- never trade correctness for lower milliseconds.

## Opportunity matrix

Scores are qualitative and rank `(Impact × Confidence) / Effort`.

| Rank | Opportunity | Evidence | Impact | Confidence | Effort | Decision |
|---:|---|---|---|---|---|---|
| 1 | Deadline-safe feature/market state | One-GW history, DGW leakage, blank omissions, unsafe price timing | Critical correctness | High | Medium | Required: `FPL-3nw` |
| 2 | Canonical validated plan + outcome scorer | Several incompatible shallow shapes; no gross-points path | Critical correctness | High | Medium | Required: `FPL-5i9` |
| 3 | Streamed pure-data exact optimiser evaluator | 5,856/151,672 realistic candidates; pandas/YAML inner loop | Critical capacity | High | Medium | Required: `FPL-kcc` |
| 4 | Pass one explicit rules mapping through solver/lineup | 123 YAML loads and wrong default-season seam | High correctness, large speed gain | High | Low | Part of `FPL-kcc` |
| 5 | Load/verify one observed episode once and share immutable derived features across arms | Full corpus scan is only 0.4 s, but five repeated reads are needless | Low latency, useful parity | High | Low | Implement naturally in `.13` |
| 6 | Compile/cache JSON schemas | Repeated schema construction exists, but state/live builders are already sub-second | Low | Medium | Low | Defer |
| 7 | Parquet/DuckDB for replay artifacts | JSON scan is already 96 episodes/s and JSON is the audit interface | Low | High | Medium | Reject for now |
| 8 | Async I/O, bounded queues, backpressure, sharding, locks, work stealing | No concurrent or network-bound core workload | None now | High | High | Reject |
| 9 | Bloom filters, tries, spatial/interval structures, union-find, Dijkstra/A* | No matching problem shape or measured hotspot | None | High | Medium | Reject |
| 10 | General object pooling/string interning/zero-copy | No memory pressure; allocations are caused by avoidable pandas/YAML work | Low | Medium | Medium | Reject |

## Equivalence and regression guardrails

No optimiser change is accepted on timing alone.

### Rules loading

Isomorphism argument: parsing the same immutable YAML bytes once and passing the
result to every call produces the same rule mapping that repeated parsing
produces. Guardrails:

- compare ruleset byte hash and semantic activation profile;
- golden solver output fingerprint unchanged;
- explicit 2025/26 and 2026/27 rule tests;
- fail closed on mismatched ruleset identity.

### Lazy candidate generation

Isomorphism argument: replace the materialised list with an iterator yielding
the exact same transfer tuples in the exact same order. Guardrails:

- sequence equality against the reference enumerator for bounded fixtures;
- candidate count equality at 1/2/3 transfers;
- identical deterministic tie ordering and selected output.

### Pure-data lineup evaluation

Isomorphism argument: for each legal squad and rule mapping, enumerate the same
legal formations, choose the same EP-ranked players with the same ID
tie-breakers, captain and bench ordering, and calculate the same objective.
Guardrails:

- golden output fingerprint;
- property/differential cases across generated legal squads, equal-EP ties,
  unavailable players, chips and blanks/doubles;
- every result revalidated by the existing deterministic validator.

### Shared episode/feature materialisation

Isomorphism argument: every arm receives a read-only value derived once from the
same canonical observed bytes and feature-state hash. Arm state remains copied
and isolated. Guardrails:

- same observed and feature hash recorded for all arms;
- mutation attempts rejected or operate on copies;
- hidden outcome unavailable to the feature module;
- arm histories retain distinct predecessor hashes.

## Recommended implementation sequence

1. Complete this audit gate and ratify the capability/claim limits.
2. Implement `FPL-3nw`:
   controlled seed, player-Gameweek aggregation, cumulative feature state,
   full market carry-forward, price-staleness policy, fixture-aware projections.
3. Implement `FPL-5i9`:
   one strict plan shape, freeze/reveal interface and official-outcome scorer.
4. Implement `FPL-kcc`:
   explicit rules, exact streamed candidate search and realistic scale tests.
5. Resume `FPL-bsw.13`:
   episode reader, five arm runners/fallbacks, independent ledgers, deterministic
   artifact persistence and 38-Gameweek process run.
6. Review the first full run for state drift, missing data, degraded modes and
   reproducibility before interpreting points.
7. Complete `FPL-bsw.14` for realised counterfactuals, calibration, effect sizes
   and clustered uncertainty.
8. Shift the primary programme to 2026/27 live capture and agent evaluation.

## Claims allowed after the first 2025/26 run

Allowed:

- the chronological pipeline completes;
- all arms receive identical structured inputs;
- no outcome is exposed before freeze;
- state transitions and artifacts reproduce;
- structured baseline forecasts and plans are produced under declared
  limitations;
- price/data uncertainty and degraded modes are quantified.

Not yet allowed:

- exact reconstruction of what a manager could afford at every 2025/26
  deadline;
- fair historical evidence-agent value without complete pre-deadline evidence;
- globally optimal season strategy from a single-Gameweek bounded optimiser;
- full Wildcard/Free Hit optimality;
- causal value attributed to Elo, odds, news or other streams without a
  pre-declared ablation.

That claim discipline lets Benchmark v0 improve the engine and process without
optimising the project around hindsight or overstating historical data quality.
