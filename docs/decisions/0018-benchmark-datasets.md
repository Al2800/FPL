# ADR-0018: Stage benchmark datasets by evidence value and rights risk

**Status:** Accepted
**Date:** 2026-07-22
**Owners:** Project owner
**Related:** ADR-0001, ADR-0002, ADR-0005, ADR-0007, ADR-0017;
`docs/data-sources/dataset-roadmap.md`

## Context

The kernel needs genuine point-in-time episodes, but more data is not
automatically better. Closing odds can leak deadline-late information, current
ratings can contaminate replay, unstructured evidence is hard to reconstruct and
event feeds add cost and licensing risk before their decision value is known.

## Decision

Adopt the four-tier roadmap as an integration and trust sequence. All named streams
are intended platform inputs because each may contribute to decision quality. Tier
0 is the canonical FPL episode spine and manual manager state. Tier 1 integrates
results, timestamped market and team-strength baselines. Tier 2 integrates cited
expected-minutes evidence. Tier 3 establishes the event-data adapter and feature
contract with open data, while commercial EPL activation remains conditional on a
successful value-versus-cost ablation. Registry enablement remains a separate
owner-controlled decision.

Every stream must use the common acquisition, identity, temporal-normalisation,
quality and deadline-safe feature-view boundaries. Models must declare required
and optional features plus deterministic fallback behaviour; no source becomes an
implicit hard dependency merely because it is integrated.

Every observation used by an episode must have a source, observation or
publication time, cutoff comparison and retained hash. An unavailable timestamp is
not inferred. Unknown or restricted candidates remain disabled.

## Consequences

- historical replay remains honest about which streams are recoverable;
- live snapshots accumulate evidence that old seasons cannot reliably recover;
- market, rating, evidence and event streams gain stable integration contracts;
- weak sources can support reconciliation without controlling model output;
- event-data spend is delayed until measured value justifies it, but its interface
  and open-data prototype are not deferred;
- manual evidence work remains necessary while automated HTML/browser collection
  is unapproved.

## Ratification checklist

- [x] Approve Tier 0 cadence, retention and manual manager-state boundary.
- [x] Approve integration of all named streams through common reliability gates.
- [x] Approve manual, cited Tier 2 evidence before publisher-specific automation.
- [x] Approve StatsBomb as the open event-interface and method prototype.
- [x] Approve the ablation gate before commercial event-data procurement.

Accepted by the project owner in conversation on 2026-07-22. Dataset collectors
depending on a disabled source must not run until the corresponding registry entry
is enabled; fixture-backed contracts and tests may merge while collection is
disabled.
