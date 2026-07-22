# Benchmark kernel protocol

**Status:** Proposed for the 2026/27 benchmark programme
**Contract version:** 1.0
**Decision:** ADR-0017

## Purpose

The benchmark kernel compares decision policies, not isolated prose outputs.
Every policy receives the same point-in-time episode, operates under a declared
resource budget, submits a rules-valid proposal and is scored only after that
proposal has been frozen. The protocol is intended to answer whether agentic
orchestration adds measurable value over deterministic forecasting and
optimisation without contaminating the comparison with extra information.

## Experimental unit

An **episode** is one manager decision at one FPL deadline. Its immutable
manifest is defined by `control/schemas/benchmark/episode-manifest.json` and
contains:

- season, Gameweek, cutoff and deadline;
- code commit and versioned ruleset hash;
- immutable source, manager-state, feature and forecast-uncertainty references;
- the tools and resource budget available to the arms;
- the fixed policy-arm set; and
- an opaque hidden-outcome reference whose value is unavailable until freeze.

All source artefacts must have `available_at <= cutoff <= deadline`. A manifest
violating that ordering is quarantined rather than repaired. The observed
episode hash is the pairing key: arms with different observed hashes are not a
paired comparison.

## Policy arms

Every fixed evaluation set runs these five arms:

1. `naive_baseline` — simple, pre-declared statistical policy with no agent.
2. `forecast_optimizer` — point-in-time forecasts plus deterministic optimiser.
3. `evidence_agent` — one constrained tool-using agent that may propose cited adjustments.
4. `evidence_challenger` — evidence agent followed by separately recorded challenger review.
5. `human_decision` — the recorded human choice from the same observed episode.

Arms may differ in allowed tools and budgets only when that difference is an
explicit experimental treatment. They never differ silently in data cutoff,
ruleset, manager state or outcome visibility.

## Kernel sequence and isolation boundary

```text
build immutable observed episode
  -> seal outcome payload
  -> run each arm under its budget
  -> deterministically validate proposal
  -> freeze proposal and Gameweek Decision Record
  -> reveal outcome to evaluation process only
  -> score paired sub-decisions and transition that arm's state
```

The policy runner receives the manifest with `hidden_outcome_ref`, never the
referenced outcome payload. A policy result must validate against
`control/schemas/benchmark/policy-result.json`; that contract requires a passed
rule-validation reference, a `frozen_at` timestamp and
`outcome_access = sealed_until_proposal_frozen`. Outcome fields are forbidden by
`additionalProperties: false`. The evaluator rejects a reveal timestamp earlier
than `proposal.frozen_at`.

## Budgets and degraded operation

Each episode declares wall-clock, tool-call, token and currency limits. Results
record both the limit and actual usage. Deterministic arms record zero model
tokens and may record zero cost. When an evidence stage times out, exceeds its
budget or loses an approved source, it falls back to the recorded deterministic
proposal and marks the result `degraded` with a reason. It must not delay the
deadline or improvise an unregistered source.

## Historical and live evidence

Historical replay is primary evidence for structured-data arms because results,
prices and many player statistics survive across seasons. It is not assumed to
reconstruct missing press conferences, injury reports or predicted line-ups.
Historical evidence-agent runs are therefore plumbing and safety tests unless a
Gameweek has a demonstrably complete pre-deadline evidence snapshot.

Live shadow episodes are primary evidence for evidence-dependent arms. The
multi-manager cohort provides supporting evidence about execution and adherence,
but managers remain separate experimental clusters and credentials never enter
the repository. Results from historical replay, live shadow operation and the
cohort are reported separately before any synthesis.

## Outcomes and comparisons

Comparisons are paired on observed episode hash and decomposed into transfer,
captaincy, bench and chip decisions. Reports include realised gain against a
feasible do-nothing policy, regret, forecast calibration, validation failures,
degraded runs, cost and latency. Estimates are clustered by season/Gameweek and,
for the live cohort, by manager. Effect sizes and uncertainty intervals are
reported; one season total is not treated as sufficient evidence.

The detectable-effect-size analysis is fixed before comparative results are
examined. Null findings and negative agent value are publishable outcomes.

## Reproducibility record

An episode/result pair preserves:

- source and snapshot identifiers plus SHA-256 hashes;
- code commit, ruleset, policy, model, prompt and tool versions;
- manager-state, feature and uncertainty artefact hashes;
- allowed tools and resource limits/usage;
- ordered trace reference and degraded-operation reason;
- deterministic validation and frozen proposal hashes; and
- hidden outcome reference, reveal event and later evaluation artefacts.

Agent reruns use recorded tool results and cached model responses. They do not
claim bit-identical regeneration from a fresh model sample.

## Human gates

ADR-0017 must be ratified before episode-builder beads merge. Model-provider
selection remains Open Decision 8 and gates provider-specific evidence-agent
work. Browser execution is outside this kernel and remains deferred to Phase 7.
