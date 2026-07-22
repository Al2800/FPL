# Data-quality gates and quarantine

Quality evaluation sits between temporal normalisation and feature
materialisation. It emits the strict report defined by
`control/schemas/data/data-quality-report.json`; it never rewrites or deletes raw
evidence.

## Staged operation

The versioned policy supports three modes:

- `observe_only` measures checks and recommended dispositions while admitting the
  data. This is the initial default.
- `shadow` records the exact quarantine that would apply, but does not enforce it.
- `enforce` activates only checks whose policy entry has `enforce: true`.

Reports therefore retain both `recommended_disposition` and
`enforced_disposition`. Freshness, coverage and disagreement thresholds begin as
measured but unenforced. Acquisition integrity, malformed temporal records,
conflicting duplicates and incomplete decision-critical FPL identity joins are
the initial hard gates.

## Scope and dispositions

Checks operate at record, partition, snapshot or episode scope. The evaluator
quarantines at the smallest scope it can identify safely. A bad record or a
conflicting natural key does not discard unrelated observations from the same
snapshot. If an identity failure cannot be linked safely to individual
observations, the source partition is the smallest defensible scope.

`pass`, `degrade`, `quarantine` and `stop` are ordered recommendations. Optional
source failures normally degrade the run. A required source may stop it when the
snapshot itself is unavailable or corrupt.

Quarantine is logical and immutable. The raw artefact remains available for
diagnosis, while `admitted_observation_ids` is the only allow-list that downstream
feature code may consume. `require_admissible()` fails closed when a view asks for
an excluded observation or a wholly blocked snapshot.

## Duplicate and disagreement semantics

- Repeated observation hashes are exact duplicates: count and collapse them.
- Equal natural keys and values with different provenance hashes are equivalent
  duplicates: keep the lowest stable observation ID and count the collapsed rows.
- Equal natural keys with different values are conflicts: retain the evidence and
  quarantine those records when enforcement is enabled.
- Later corrections with different `available_at` values are revisions, not
  duplicates.
- Cross-source disagreements retain every claim, source ID and observation ID.
  They initially degrade rather than silently selecting a winner.

## Calibration

Every report contains rates for schema errors, exact and conflicting duplicates,
coverage, identity matching, freshness and reconciliation disagreement. Thresholds
must be calibrated using two complementary evidence streams:

1. Historical replay measures semantic correctness, cutoff safety and downstream
   decision sensitivity where authentic snapshots exist.
2. Immutable live-shadow snapshots measure operational schema drift, staleness,
   late arrival and correction behaviour. They make no account changes.

Broader enforcement requires a reviewed policy-version change backed by those
distributions. Avoid global thresholds: calibrate by source, field/entity type,
cadence and Gameweek context.
