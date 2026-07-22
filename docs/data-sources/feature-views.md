# Deadline-safe feature views

The deadline feature view is the immutable hand-off between governed source data
and live or historical benchmark episodes. It consumes temporal observations,
snapshot-scoped quality reports and explicit observation-to-snapshot lineage.

## Admission rules

An observation can enter a feature only when all of the following hold:

1. `available_at <= episode cutoff`.
2. The latest quality report for its source evaluated at or before the cutoff is
   selected.
3. The observation belongs to that report's immutable source snapshot.
4. Its ID appears in the report's `admitted_observation_ids` allow-list.
5. Its source and field appear in the versioned feature-source policy.

Reports evaluated after the cutoff are ignored. This prevents a later correction,
quarantine decision or replacement snapshot from changing an already frozen view.

## Precedence and missing data

`control/policies/feature-source-precedence.yaml` declares candidates in preference
order. No implicit fallback or value imputation is allowed. A fallback is retained
as a degraded-feature record containing the preferred and selected sources.

Required feature scopes must be supplied by the episode builder and fail closed
when no admissible candidate exists. Optional scopes may be requested; if missing,
the manifest records `missing_optional_feature` and emits no invented value.

## Lineage and reproducibility

Every feature retains its observation ID, source ID, source field, snapshot ID,
quality-report ID, observation time and availability time. The manifest also
retains each selected quality mode, quality-policy version and disposition, plus
the feature transformation and source-precedence policy versions. Equally timed
competing reports for one source fail as ambiguous rather than winning by hash.
Canonical sorting plus a content hash makes the feature view independent of input
ordering and suitable for both live and historical episode builders.
