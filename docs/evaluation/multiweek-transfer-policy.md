# Multiweek transfer policy

`transfer-horizon-v1` is an additive receding-horizon challenger. It plans four
Gameweeks, executes only the first action, and replans from the newly observed
state at the next deadline. It does not alter the locked one-week solver or the
canonical 2025/26 replay.

## Decision model

The horizon contains three to six consecutive Gameweeks and every projection
must bind the same cutoff and feature-state hash. Reading GW13's locked
forecast while making a GW12 decision is rejected because it would include
GW12 outcomes.

For the executable week, the planner uses the exact reviewed solver market.
Future weeks reuse the current cutoff's player posterior points-per-90 and
expected minutes, changing only the known fixtures and their official
difficulty rating:

```text
future EP = posterior points/90 × expected minutes/90 × FDR multiplier
```

The locked FDR multipliers for difficulties 1 through 5 are `1.2`, `1.1`,
`1.0`, `0.9`, and `0.8`. Prices are frozen at the decision cutoff. This is a
declared scenario, not a price forecast.

The objective is the discounted sum of weekly legal one-week objectives:

```text
total = immediate + 0.9 × GW+1 + 0.9² × GW+2 + 0.9³ × GW+3
```

Each weekly objective already subtracts transfer hits. The fixed
expected-hit-avoidance option proxy is disabled.

## State and search

Every simulated state carries:

- the 15-player squad;
- purchase, current and FPL selling prices;
- bank;
- free transfers, including the five-transfer cap;
- the 2025/26 GW16 exceptional transfer top-up.

The search is a deterministic beam search with:

- beam width 6;
- branch width 5;
- at most two transfers per week;
- sell pool 4 and buy pool 6 per position;
- maximum 20 expanded states.

Equivalent states are deduplicated. Tie-breaking uses canonical hashes. If the
node budget is exhausted before a complete path, the planner returns the
deterministic one-week solver action with the option proxy disabled. Wall-clock
latency is recorded but never decides which nodes are explored. Decision and
report hashes intentionally exclude that observational latency.

Chips are not considered here. They remain the responsibility of `FPL-q8s`,
which can consume this trajectory value later.

## GW12 exploratory result

The sealed artifact is
`reports/benchmarks/2025-26-multiweek/gw-12/comparison.json`.

The four-week search:

- expanded 18 states;
- generated 90 paths;
- deduplicated 24 paths;
- completed in about 3.1 seconds;
- reported 68.10 immediate projected points and 156.02 discounted future
  points, for 224.12 total.

Its executable GW12 action made two free transfers:

- Cody Gakpo to Declan Rice;
- Pedro Porro to Daniel Muñoz.

The advisory tail proposed later transfers, but none of them was executed or
bound into state. The first action was frozen and scored through the unchanged
validator and official outcome scorer. It earned 47 net points versus the
canonical control's 29, an isolated same-starting-state delta of +18.

This is interesting evidence, not a promotion result. The repository does not
contain complete point-in-time full fixture-schedule snapshots for old
deadlines. Future fixture fields were reconstructed from later stripped
episodes and outcome-capable fields were rejected, but rescheduling knowledge
may still be retrospective. The artifact is therefore marked
`exploratory_only: true` and `promotion_eligible: false`.

## Live use and next evaluation

For 2026/27, the same adapter should consume the immutable official fixture
snapshot captured at the current deadline. That removes the historical
schedule caveat. At each deadline it should:

1. build all horizon projections from that one cutoff;
2. plan three to six weeks;
3. freeze and execute only the first action;
4. observe outcomes, prices, availability and transfer state;
5. discard the old tail and replan.

A longitudinal 2025/26 comparison is deferred to the final challenger matrix.
It must not splice this isolated +18 result into the canonical trajectory.
