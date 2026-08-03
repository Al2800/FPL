# 15 — Set-piece role effect ablation

Status: needs-triage
Type: task
Track: Model feature ablation

Activation gate: a cutoff-safe set-piece ledger and enough finalised outcomes
must exist for time-based evaluation. This is not authorised merely because the
ledger schema exists.

## Context

`src/ingestion/set_piece_roles.py` emits `effect_weights: None` and
`promotion_status: shadow_only_pending_point_in_time_ablation`. Penalty,
direct-free-kick and corner duties can materially affect player event rates,
but applying unmeasured weights would weaken the deterministic baseline.

## Scope

- Define candidate, versioned effect-weight policies for penalty, direct-free-
  kick and corner duties without embedding FPL scoring rules in the feature.
- Run a point-in-time ablation against the unchanged player-event baseline.
- Measure event calibration and points-forecast improvement by position and
  sample size; retain the unchanged baseline if thresholds are not met.
- Keep the ledger shadow-only until the promotion decision is recorded.

## Done when

- The ablation, thresholds and result reproduce from recorded cutoff-safe
  inputs.
- A promoted policy carries source references, transformation version and
  effective dates; a negative result leaves `effect_weights` inactive.
