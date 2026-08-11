# 16 — ICT feature ablation

Status: resolved
Type: task
Track: Model feature ablation

Activation gate: sufficient pre-deadline ICT snapshots and finalised outcomes
must exist for a time-based evaluation split.

Owner authorised historical ICT ablation on 6 August 2026 (live forecasts stay
ICT-free until a versioned promotion is recorded).

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

## Answer

Fail-closed **remain_shadow_only** — no cutoff-safe historical PIT ICT +
finalised-outcome corpus exists for promotion folds. ICT remains outside the
frozen four optional_family_arms preregistration
(`odds`, `team_strength`, `set_piece_role`, `player_ratings`); this ticket does
not thaw that matrix.

Shipped:

- Candidate weights (ablation-only, `live_active: false`):
  `control/policies/ict-feature-weights-v1.json`
  (lag window 3 GW; missing → shared baseline; components separate + joint;
  MAE / Spearman / optional start Brier; promotion thresholds preregistered)
- Applicator + corpus gate + sealed decision:
  `src/evaluation/ict_ablation.py`
- Script: `scripts/evaluate_ict_ablation.py`
- Report: `reports/forecasting/ict-ablation-decision.{json,md}`
- Live `player_events` / `live_faithful` stay ICT-free (`live_effect_weights: null`)

Re-run when ≥3 paired cutoff-safe ICT lag snapshots + finalised outcomes exist;
only then can `promotion_eligible` flip for owner review.
