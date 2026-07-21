# Source reputation scoring

**Phase:** 4 · **§19:** Source reputation scoring

## Purpose

Weight claims by historical accuracy of the source (e.g. predicted line-ups vs realised starts).

## Anticipated interfaces

- `source_reputation` record: source_id, metric_window, precision/recall or Brier by claim_type, computed_at
- Join key: `provenance.source_ids` on claims/signals
- Policy hook: evidence-adjustments.yaml may later multiply confidence by reputation

## Prerequisites

- Sufficient labelled claim → outcome pairs (live season capture)
- WP-05 start-prob baselines as the comparison target

## Activation criteria

- Enough historical claims/outcomes to estimate reputation without overfitting (plan §19)
- Scores versioned; never silently overwrite claim confidence

## Non-goals (Phase 1)

- No reputation model; treat all registered sources equally aside from quarantine rules
