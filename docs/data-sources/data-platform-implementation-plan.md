# Data-platform implementation plan

This living plan implements ADR-0018. It is self-contained because the repository
does not currently contain the referenced `.agent/PLANS.md` template.

## Objective

Make every approved FPL, results, market, strength, expected-minutes and event
stream usable through one reproducible point-in-time path without turning an
optional or failed source into a silent model dependency.

## Invariants

- Registry enablement gates real acquisition; fixtures may exercise disabled
  adapters.
- Raw inputs are immutable and content-addressed.
- Source identifiers resolve to canonical identities with confidence and review
  state.
- `available_at <= episode_cutoff` is enforced before feature materialisation.
- Quality failures are explicit, quarantined and represented in run artefacts.
- Every feature retains source snapshot and transformation lineage.

## Milestones

1. Publish a source-neutral acquisition manifest and land one FPL snapshot through
   it without changing the existing collector's external behaviour.
2. Resolve source team/player/fixture identifiers into canonical identities and
   fail closed on ambiguous decision-critical joins.
3. Normalise source times into the point-in-time contract and prove that later
   corrections cannot enter an earlier episode.
4. Emit source health and quarantine decisions for schema, freshness, coverage,
   duplicate and reconciliation failures.
5. Materialise a deadline-safe feature view with deterministic source preference,
   fallback and lineage, then run it in the historical episode builder.

## Progress

- 2026-07-22: Immutable acquisition, canonical identity resolution and temporal
  normalisation are implemented with offline contracts.
- 2026-07-22: Data-quality gate design approved. Implementation uses staged
  observe-only, shadow and enforcement modes so threshold error rates can be
  measured before broad quarantine is activated.

## Quality-gate rollout decisions

- Detect conservatively, enforce gradually. The default policy is observe-only.
- Retain recommended and enforced dispositions separately in every report.
- Quarantine logically at record, partition, snapshot or episode scope; never
  move, overwrite or delete immutable source evidence.
- Count and collapse exact duplicates. Quarantine conflicting natural keys at the
  smallest safe scope. Treat timestamped corrections as revisions.
- Initially hard-enforce only acquisition integrity, observation-schema validity,
  conflicting duplicates and incomplete decision-critical FPL identities.
- Calibrate freshness, coverage, match-rate and disagreement thresholds through
  historical replay plus immutable live-shadow capture before enabling them.

## Stream sequence

Use FPL as the first end-to-end tracer. Add basic results reconciliation, then
Betfair and team-strength features, cited expected-minutes evidence, and finally
the StatsBomb-backed event adapter. Each stream must reuse the same five boundaries
and ship its own contract, leakage and degraded-mode tests.

## Verification

Each milestone has focused contract/integration tests and must leave the complete
offline test suite green. No test may require live collection, credentials or a
browser session. Historical replay must demonstrate distinct cutoff-safe inputs,
not relabelled fixtures.
