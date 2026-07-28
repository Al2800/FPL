# Deterministic Claim-Value Ledger

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Turn frozen evidence-replay artifacts into deterministic ex-post accounting
without changing any policy, prompt, forecast, optimiser decision or replay
state. The report must keep claim lifecycle facts, application facts and
gameweek-level paired attribution separate so a weekly score delta is never
misrepresented as the causal value of one claim.

## Progress

- [x] (2026-07-28 16:19Z) Claimed `FPL-f55` after checking active Beads and
  confirming no declared file overlap.
- [x] (2026-07-28 16:35Z) Audited the early longitudinal, enhanced factorial
  and accepted agent-fork artifact schemas.
- [x] (2026-07-28 16:45Z) Established the artifact-derived oracles:
  enhanced Scout is GW2-GW11 early longitudinal plus GW12-GW38 enhanced,
  both enhanced arms have 17 applied weeks, union non-zero weeks are
  GW7/12/17/18/22, and paired sums are 0 Scout / +11 optimized. The accepted
  agent fork is a separate mode with +16 across GW13-GW38.
- [x] (2026-07-28 17:10Z) Implemented the pure ledger builder, accepted
  namespace resolution, manifest-bound all-player minutes and immutable CLI
  output.
- [x] (2026-07-28 17:18Z) Added six focused tests covering signal joins,
  causal scope, zero-claim weeks, source-metadata gaps, sealed outcome binding,
  idempotence, tamper rejection and both repository oracles.
- [x] (2026-07-28 17:38Z) Generated versioned canonical reports, proved
  byte-identical reruns, passed 6 focused tests, 115 evaluation/agent-replay
  regressions and the full 692-test suite.

## Discoveries

- Observation: the PR handoff's enhanced oracle cannot be recovered from
  `reports/benchmarks/2025-26-enhanced/arms/scout_evidence` alone.
  Evidence: that directory begins at GW12 and contains 15 applied weeks with
  a +8 paired sum; composing
  `reports/benchmarks/2025-26-early-evidence/longitudinal` for GW2-GW11 adds
  the two early applications and GW7's -8, yielding the published 17 and 0.

- Observation: historical hosted artifacts do not record registry authority or
  a stable source-family field for every claim.
  Evidence: validated historical claims carry `source_ids` and document IDs,
  while the live ledger schema carries `claim_type` and `source_rights`.
  Missing historical metadata must therefore render as unavailable, not be
  inferred from prose or the current registry.


- Observation: replay `realised-outcome.json` files contain only players
  relevant to the scored squad, but sealed episode `hidden-outcome.json` files
  contain all-player minutes and are hash-bound by both the episode manifest
  and replay outcome.
  Evidence: the canonical reports now bind those two hashes per Gameweek and
  expose `minutes_source=sealed_all_player_hidden_outcome` for every claim.

- Observation: adapter audits often name a signal ID in `claim_ids`.
  Evidence: validated evidence output contains the authoritative
  signal-to-claim mapping. Application joins must resolve signal IDs before
  marking a claim applied.

- Observation: paired same-state deltas are gameweek-arm effects, not
  claim-level effects.
  Evidence: one week may contain multiple cited claims and multiple applied
  adjustments but only one paired control. Claim rows may reference the
  application group; score deltas are aggregated exactly once at group level.

## Decision Log

- Decision: Model the output as `claims`, `application_groups`, `gameweeks` and
  mode/arm summaries rather than putting the weekly delta directly into a
  claim-value number.
  Rationale: this preserves the causal scope of the existing paired replay and
  prevents double counting when multiple claims share one decision.
  Date/Author: 2026-07-28 / Codex

- Decision: Select the accepted agent-fork namespace as the highest numbered
  `sol-vN` with completed evidence and challenger runs plus a comparison.
  Rationale: failed and degraded namespaces are intentionally preserved; this
  rule reproduces the accepted season trajectory without parsing prose.
  Date/Author: 2026-07-28 / Codex

- Decision: Render GW1 explicitly as `not_applicable_seed` with zero claims in
  the enhanced mode.
  Rationale: zero-claim weeks are part of the experiment population and must
  not disappear from rates or reviews.
  Date/Author: 2026-07-28 / Codex

- Decision: Verify only structurally testable zero-minutes assertions as
  `verified` or `contradicted`; expose realised minutes but label all weaker
  assertions `indeterminate`.
  Rationale: actual minutes alone cannot adjudicate nuanced uncertainty,
  training, role or selection claims without a preregistered assertion type.
  Date/Author: 2026-07-28 / Codex

## Implementation

Add `src/evaluation/claim_value_ledger.py` with pure JSON readers, artifact-hash
validation, run-directory extraction, signal-to-claim joins, exact timestamp
age calculation, limited post-match verification, application-group
attribution and deterministic report sealing. Expose builders for an arbitrary
list of run specifications as well as repository-layout helpers for the
enhanced factorial and accepted agent-fork modes.

Add `scripts/build_claim_value_ledger.py` with explicit input roots and output
paths. It writes canonical, newline-terminated JSON and refuses to overwrite
different bytes. Re-running identical inputs is a no-op.

Add `tests/evaluation/test_claim_value_ledger.py`. Synthetic tests cover
signal-to-claim application, zero-claim rendering, missing historical metadata,
zero-minute verification, no claim-level delta duplication, hash rejection and
byte stability. Repository tests enforce the enhanced and agent-fork oracles.

Generate:

    reports/evaluation/claim-value/2025-26-enhanced-v1.json
    reports/evaluation/claim-value/2025-26-agent-fork-v1.json

## Validation

Focused command:

    .\.venv\Scripts\python.exe -m pytest tests/evaluation/test_claim_value_ledger.py -q

Related evaluation regression:

    .\.venv\Scripts\python.exe -m pytest tests/evaluation tests/agent-evals -q

Full command:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

The deterministic join reproduces the published enhanced factorial result only
when the Scout arm is correctly composed from the early longitudinal and later
enhanced artifacts: 17 applied weeks per arm, non-zero paired results in the
union GW7/12/17/18/22, and same-state sums of 0 Scout / +11 optimized. The
separate accepted agent-fork resolver chooses the highest completed namespace,
including GW20-GW22 `sol-v3` and GW30 `sol-v5`, and reproduces +16 over the 26
paired weeks.

The enhanced report contains 88 claim rows and 74 application groups; the
agent-fork report contains 32 claim rows and 27 groups. Every claim uses the
sealed all-player hidden outcome for realised minutes. Binary zero-minutes
assertions are adjudicated; weaker statements retain `indeterminate` status.
Historical source family and registry authority remain unavailable where the
frozen artifacts never recorded them. The report exposes those gaps rather
than deriving labels from prose or applying today's registry retrospectively.

Validation completed:

    6 passed in 1.04s
    115 passed in 141.45s
    692 passed in 486.43s

An identical CLI rerun returned `written: false` for both canonical reports,
proving byte stability and write-once behavior.
