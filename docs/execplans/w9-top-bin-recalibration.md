# Per-Position Top-Bin Forecast Recalibration Challenger

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Build an auditable post-composition recalibration layer for
`live-faithful-v1` that targets its documented high-EP overprediction without
flattening genuine premium ordering. Fit only on 2022/23 and 2023/24, evaluate
once on locked 2024/25, and treat 2025/26 as descriptive only. The production
v1 path remains unchanged unless the owner later promotes this challenger.

## Progress

- [x] (2026-07-28 19:49Z) Created and claimed `FPL-y0e` after confirming W8
  is complete and no active Bead owns the W9 files.
- [x] (2026-07-28 19:57Z) Read the July review/handoff, mandated plan sections,
  live-faithful policy, W8 contract, existing calibrators and rejected robust
  challenger.
- [x] (2026-07-28 20:26Z) Established immutable 2022/23-2023/24 fit,
  locked 2024/25 validation and descriptive-only 2025/26 frames with source
  lineage hashes.
- [x] (2026-07-28 20:43Z) Implemented deterministic per-position quantile-bin
  recalibration with weighted isotonic pooling and real `price_band` support.
- [x] (2026-07-28 20:50Z) Published hash-bound configuration and evaluation
  artifacts; a repeat run reproduced them byte-for-byte.
- [x] (2026-07-28 20:01Z) Registered the failed challenger in the sealed matrix
  using matrix-only generation; v1 and the live-shadow policy remained unchanged.
- [x] (2026-07-28 20:22Z) Passed 7 focused, 57 affected and 724 full-suite tests.

## Discoveries

- The local vaastav estate contains complete weekly player outcomes through
  2025/26, so W9's split can run without downloading data.
- The existing robust challenger already improves locked top-15 MAE and its
  ranking-regret proxy, but it uses reliability shrinkage rather than directly
  calibrating position-specific prediction levels.
- W8's true XI-regret metric requires an owned squad or optimiser-supplied
  legal market candidates. Historical calibration rows alone cannot establish
  club and budget legality. W9 must not relabel an unconstrained top-15 proxy
  as legal XI regret.
- The locked promotion gate must therefore report both calibration/ranking
  proxies now and explicitly reserve legal replay as a separate requirement
  before production promotion.
- Real historical calibration frames expose launch-price cohorts as `price_band`,
  not exact `price`. The premium-rank proxy now uses a declared 7.5 lower-bound
  band threshold and the contract test exercises that real schema.
- Locked validation rejected the recalibrator despite better selected top-15 MAE:
  precision fell 0.0667, ranking regret rose 15.2632 points per Gameweek,
  premium rank correlation fell 0.2047, and overall RMSE rose 0.0360.
- Matrix-only generation must bind to the existing sealed live-shadow candidate;
  generating a hypothetical replacement would make the matrix point at policy
  bytes that were never admitted.

## Decisions

- Use fixed-count prediction quantile bins per position learned only on the fit
  seasons, then pool adjacent violating bins with deterministic weighted
  isotonic regression. This preserves monotonic ordering while correcting
  level bias and avoids a new dependency.
- Store edges, fitted values, sample sizes and source hashes as versioned model
  data. Values below/above the fitted range use the first/last calibrated bin.
- Gate on locked 2024/25: absolute top-bin bias must improve; top-15 precision,
  selected top-15 MAE, premium rank correlation and the existing ranking-regret
  proxy may not worsen beyond explicitly zero tolerance.
- Do not claim legal XI-regret improvement from calibration rows. If locked
  proxy gates pass, register the model as eligible for a future legal replay;
  promotion remains owner-gated.
- Publish the failed result and stop before legal replay. A selected-player MAE
  gain cannot override worse ranking decisions or a failed locked gate.

## Validation

Focused:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting/test_recalibration.py tests/evaluation/test_challenger_matrix.py -q

Affected:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting tests/evaluation/test_challenger_matrix.py -q

Full:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

The per-position recalibrator was fitted without 2024/25 or 2025/26 leakage and
published as `live-faithful-v2.recalibrated` (`a6ebc282...ec7`). It reduced
selected top-15 MAE by 0.3688 points on locked 2024/25, but failed four of five
proxy gates: absolute top-bin bias, top-15 precision, top-15 ranking regret and
premium ordering all worsened. The sealed report therefore records
`reject_locked_validation`; no legal replay or owner promotion was attempted.

The challenger matrix retains this negative result, continues to nominate
`robust-selection-v2`, and now binds its nomination to the unchanged sealed
live-shadow candidate (`23bc92f...1a71c`). Production `live-faithful-v1` is
unchanged. Focused tests passed 7/7, the affected suite passed 57/57, and the
final repository suite passed 724/724 in 452.59 seconds.