# 16 — ICT feature ablation

Status: needs-triage
Type: task
Track: Model feature ablation

Activation gate: sufficient pre-deadline ICT snapshots and finalised outcomes
must exist for a time-based evaluation split.

## Context

Influence, creativity, threat and `ict_index` are preserved in historical lag
aggregates but are not inputs to the current projection formula. They are
official FPL-derived signals, but their marginal value over event-rate and
team-context baselines is unknown.

## Scope

- Preregister lag windows, missing-value handling and evaluation metrics.
- Evaluate the components separately and jointly against the existing
  player-event baseline using only cutoff-safe observations.
- Report calibration and error by position and horizon, including whether ICT
  merely duplicates existing inputs.

## Done when

- The ablation reproduces from versioned inputs and records either a measured
  improvement or a negative result.
- ICT enters a live forecast only through a versioned feature policy after
  meeting the preregistered threshold.
