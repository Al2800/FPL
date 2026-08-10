# 15 — Set-piece role effect ablation

Status: resolved
Type: task
Track: Model feature ablation

Activation gate: a cutoff-safe set-piece ledger and enough finalised outcomes
must exist for time-based evaluation. This is not authorised merely because the
ledger schema exists.

Owner authorised historical ablation on 6 August 2026 (live weights stay
shadow-only until promotion is recorded).

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

## Answer

Fail-closed **remain_shadow_only** — no cutoff-safe historical PIT ledger corpus
exists (vaastav role columns are end-of-season, not deadline-safe), and 2026/27
does not yet have enough finalised outcome folds for promotion under the frozen
preregistration.

Shipped:

- Candidate weights (ablation-only, `live_active: false`):
  `control/policies/set-piece-effect-weights-v1.json`
- Applicator + corpus gate + sealed decision:
  `src/evaluation/set_piece_ablation.py`
- Script: `scripts/evaluate_set_piece_ablation.py`
- Report: `reports/forecasting/set-piece-ablation-decision.{json,md}`
- Live `build_set_piece_feature_payload` still emits `effect_weights: null`

Re-run when ≥3 paired cutoff-safe ledgers + finalised outcomes exist; only then
can `promotion_eligible` flip for owner review.
