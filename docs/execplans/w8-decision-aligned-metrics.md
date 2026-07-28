# Decision-Aligned Forecast Metrics

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Add deterministic evaluation-only metrics for the decisions that score FPL
points while preserving every existing MAE/RMSE value and every promotion
criterion. A reviewer should be able to compare forecast models on legal XI
selection, captaincy and premium-player ranking without allowing hindsight
fields to enter proposal or replay inputs.

## Progress

- [x] (2026-07-28 17:55Z) Claimed `FPL-ejl` after rechecking active Beads and
  confirming no declared file overlap.
- [x] (2026-07-28 18:05Z) Audited `forecasting.evaluate`,
  `evaluation.calibration`, event/team-context/robust challengers and the replay
  review.
- [x] (2026-07-28 18:24Z) Implemented the pure decision-aligned metric and legal-lineup engine.
- [x] (2026-07-28 18:24Z) Added a pandas-facing comparison-table adapter without changing existing
  evaluation outputs.
- [x] (2026-07-28 18:42Z) Added focused contracts, reproduced existing
  MAE/RMSE exactly, and passed all 698 repository tests.

## Discoveries

- Observation: existing event and team-context challengers evaluate all-player,
  owned and selected-XI calibration against the canonical plan, but do not
  rescore a legal lineup chosen by each challenger.
  Evidence: both construct `calibration_by_cohort` rows with only predicted,
  actual and cohort labels.

- Observation: the robust challenger reports top-15 ranking regret but
  explicitly states that squad price/club/legal constraints are evaluated
  elsewhere.
  Evidence: `calibrate_robust_selection.py` selects the top 15 rows directly.

- Observation: a market-wide hindsight XI cannot be called legal from player
  rows alone.
  Evidence: budget, three-per-club and squad-construction constraints are not
  encoded in the calibration rows. Market evaluation must therefore receive
  optimizer-generated legal candidate lineups; owned-squad evaluation needs
  only formation legality.

- Observation: an initial insertion placed the new top-level block before the
  existing `calibration_by_cohort` return.
  Evidence: the broad calibration suite failed while focused W8 tests passed.
  The return was restored before the new block and the complete 698-test suite
  then passed.

## Decision Log

- Decision: Compute XI regret as best legal realised XI points minus the
  evaluated model's legal selected-XI realised points on the identical
  candidate boundary.
  Rationale: this measures the actual selection decision while keeping the
  oracle strictly post-outcome and evaluation-only.
  Date/Author: 2026-07-28 / Codex

- Decision: Compute captain regret within the model's selected XI.
  Rationale: this isolates captain choice from lineup selection; comparing
  against an oracle player outside the chosen XI would conflate two decisions.
  Date/Author: 2026-07-28 / Codex

- Decision: Infer the model XI/captain from predicted points when explicit
  frozen decisions are absent, but validate any supplied decisions against the
  same legal candidate set.
  Rationale: the metric works for both pure forecast comparisons and replay
  plans while refusing illegal hindsight shortcuts.
  Date/Author: 2026-07-28 / Codex

- Decision: Use average ranks for ties and return explicit `empty`,
  `insufficient` or `degenerate_tie` status rather than inventing a
  correlation.
  Rationale: premium cohorts can be small or tied; null with a reason is more
  reproducible than coercing missing evidence to zero.
  Date/Author: 2026-07-28 / Codex

## Implementation

Extend `src/evaluation/calibration.py` with:

- strict decision-row normalization;
- legal formation validation and deterministic owned-squad lineup generation;
- optimizer-supplied legal-lineup validation for market boundaries;
- XI regret, captain regret and top-price-band Spearman correlation;
- a deterministic multi-model comparison table with point-error metrics
  retained alongside the new metrics.

Extend `src/forecasting/evaluate.py` with a pandas-facing adapter that maps
named prediction columns into the pure comparison API. It must not alter
`evaluate_minutes`, `evaluate_player_events`, `evaluate_season` or their
existing fields.

Add `tests/forecasting/test_decision_aligned_metrics.py` covering legality,
market candidate requirements, explicit/inferred decisions, ties, empty
cohorts, deterministic ordering, hindsight labels and exact legacy
MAE/RMSE preservation.

## Validation

Focused command:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting/test_decision_aligned_metrics.py -q

Related regression:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting tests/evaluation -q

Full command:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

W8 is implemented as an additive evaluation surface. Existing point-error
calculations and promotion criteria are unchanged. The new report labels all
hindsight fields as evaluation-only, compares models only on an identical
player/outcome/price boundary, validates owned-squad formations, and requires
optimizer-supplied legal candidates for a market boundary where budget and
club constraints cannot be reconstructed from calibration rows alone.

Validation completed on 2026-07-28:

- focused W8 contracts: 6 passed;
- forecasting and benchmark calibration regressions: 63 passed;
- complete repository suite: 698 passed in 468.99 seconds.
