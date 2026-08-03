# 07 — Price-change model from transfer and ownership snapshots

Status: needs-triage
Type: task
Track: Phase 5 (price intelligence)

Activation gate: plan Phase 5 must be explicitly authorised and enough
cutoff-safe 2026/27 daily snapshots and observed price changes must exist to
support a time-based train/evaluation split. Until then, continue snapshotting
the inputs only.

## Context

`transfers_in_event`/`transfers_out_event` and `selected_by_percent` are captured daily but have no consumer in `src/`. Price changes affect team value and transfer *timing* — currently invisible to the optimiser. Plan §6.1 explicitly says these fields are "free groundwork for price-change modelling (Phase 5)"; this ticket builds the model, not the full Phase-5 strategy layer.

## Scope

- A daily-snapshot-based rise/fall probability model per player (transparent, threshold/logistic style — no black box), trained and evaluated on accumulated 2026/27 snapshots.
- Evaluation: precision/recall of predicted rises and falls against observed `cost_change_event`, time-based splits only.
- Expose predictions as an advisory annotation on candidate plans ("Player B likely rises tonight; early transfer saves 0.1"), not as an optimiser objective term yet.

## Done when

- A preregistered minimum sample and evaluation split are recorded before model
  fitting.
- Nightly predictions are produced from existing snapshots with documented
  precision, recall and calibration, and the GDR shows price-risk annotations
  on transfer plans.

## Boundaries

Rank-aware/EO strategy remains Phase 5. Do not enable the official price predictor source without registry resolution.
