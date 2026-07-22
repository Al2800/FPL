# ADR-0017: Fixed episode contract for the benchmark kernel

**Status:** Proposed
**Date:** 2026-07-22
**Owners:** Project owner
**Related:** ADR-0004, ADR-0009, ADR-0010, ADR-0016; `docs/evaluation/benchmark-protocol.md`

## Context

The existing replay scaffold can exercise components, but it does not yet
define the immutable unit supplied to every policy arm, the boundary that hides
outcomes, or the artefacts required for a paired comparison. Without a fixed
contract, an apparent agent advantage could instead come from later evidence,
different manager state, a different ruleset or an unrecorded resource budget.

## Decision

Adopt contract version 1.0 with two schemas:

- `episode-manifest.json` defines the immutable observed episode and opaque
  hidden-outcome reference;
- `policy-result.json` defines a validated, frozen, pre-outcome policy result.

The fixed arms are naive baseline, forecast plus optimiser, evidence agent,
evidence agent plus challenger, and human decision. The observed episode hash is
the pairing key. Outcome data is held outside the policy process until a valid
proposal has passed deterministic rules validation and been frozen.

Historical replay is the primary comparison surface for structured-data arms.
Live paired shadow evaluation is the primary comparison surface for
evidence-dependent arms, with the multi-manager cohort as supporting evidence.

## Consequences

Positive:

- information parity and look-ahead controls become explicit and testable;
- every policy result can be traced to exact inputs, versions and budgets;
- agent cost, latency and degraded operation are comparable with decision value;
- downstream live and historical episode builders share one interface.

Costs and limitations:

- builders must hash and preserve more artefacts;
- policy runs cannot begin from convenient mutable working tables;
- missing historical evidence remains an explicit limitation rather than being
  filled by hindsight;
- later contract changes require a schema-version migration.

## Alternatives considered

1. **Use the Gameweek Decision Record alone.** Rejected because it is an output
   record and does not define information parity or hidden-outcome isolation.
2. **Give each arm a bespoke input contract.** Rejected because it prevents a
   defensible paired comparison unless every difference is separately modelled.
3. **Evaluate only season totals.** Rejected because the sample is too small and
   noisy; paired sub-decisions and clustered uncertainty are required.
4. **Reconstruct all historical news.** Rejected as disproportionate and still
   unable to guarantee complete point-in-time evidence.

## Ratification checklist

- [ ] Approve the five fixed policy arms.
- [ ] Approve observed episode hash as the pairing key.
- [ ] Approve outcome reveal only after deterministic validation and freeze.
- [ ] Approve the historical/live evidence asymmetry.
- [ ] Approve version 1.0 schemas as the dependency contract for episode builders.

Dependent episode-builder beads may be implemented against the proposal, but
must not merge until this ADR is marked `Accepted` or amended by the owner.
