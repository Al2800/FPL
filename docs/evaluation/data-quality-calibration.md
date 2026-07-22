# Data-quality calibration

Production quality thresholds must be earned from evidence rather than inferred
from synthetic fixtures. The calibration harness summarizes immutable historical
replay and live-shadow cases; it never edits the production quality policy.

## Evidence roles

Historical replay tests semantic correctness and downstream sensitivity where
genuinely timestamped snapshots exist. It measures identity joins, cutoff safety,
duplicate classification and the difference between unrestricted and quality-gated
feature views and decisions.

Live shadow capture tests operational reliability: schema drift, staleness, late
arrival, corrections and intermittent source failures. Its manifest fixes
`execution_mode: no_execution`, `browser_actions: false` and
`account_writes: false`. It cannot submit or stage FPL changes.

## Segmentation and metrics

Cases are grouped by gate, source, field and entity type while retaining their
Gameweeks and evidence modes. Each segment reports distributions for schema,
duplicate, coverage, identity, freshness and disagreement metrics, plus:

- false quarantine: the gate recommends exclusion but review says the data was
  safe;
- false admission: the gate admits data that review says should have been
  excluded;
- paired action-change rate and projected-score delta between unrestricted and
  gated decisions.

Adjudication is an explicit case input. Outcome data may be used only after the
corresponding decision and feature views have been frozen.

## Promotion review

`evals/data-quality/calibration-plan.yaml` contains evaluation maturity criteria,
not production data thresholds. The harness emits one of:

- `insufficient_evidence`;
- `retain_observe_only`;
- `eligible_for_owner_review`.

`automatic_policy_update` is always false. Any production enforcement change
requires owner review, a new `data-quality.yaml` policy version and regression of
the affected historical and live-shadow cases.
