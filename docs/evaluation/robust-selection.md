# Robust selection challenger

`live-faithful-v2-robust` is an additive decision challenger. It does not
rewrite the locked `live-faithful-v1` forecasts, the official FPL rules, the
realised scorer, or any 2025/26 replay artifact.

## Why it exists

The control review found a selection effect: forecast error was much larger
for the players chosen by the optimiser than for the full player pool. A
solver that maximises point estimates can repeatedly select positive noise at
the top of a ranking. This challenger tests whether reliability-aware
shrinkage makes those decisions less fragile.

## Locked transformation

For each Gameweek and position, let `a` be the 90th percentile of raw expected
points, `r` be the pre-deadline prior reliability in `[0, 1]`, and `x` be raw
expected points. The central forecast used for calibration is:

```text
central = x - 0.75 * (1 - r) * max(x - a, 0)
```

Only the upper tail is shrunk. Players at or below the positional anchor are
not inflated. A forecast without an individual prior reliability uses the
explicit conservative fallback `r = 0`; this is recorded in the model config.

The training residuals are split into reliability buckets
`[0,.25], (.25,.5], (.5,.75], (.75,1]`. Their locked 80th-percentile absolute
errors are respectively `0.848051`, `1.165605`, `2.150262`, and `3.326782`
points. These widths create bounded lower, central, and upper scenarios. The
solver's robust point value is:

```text
robust = max(0, central - 0.2 * error_q80)
```

Every optimiser player row retains `raw_expected_points` and adds the anchor,
reliability, central forecast, uncertainty, lower/upper bounds, and robust
value. The adapter then calls the unchanged legal solver. It reports both raw
and robust objectives and whether transfers, XI, or captain change under each
scenario.

## Split and selection policy

- Fit and control selection: target seasons 2022/23 and 2023/24.
- Locked validation: 2024/25.
- Final out-of-sample diagnostic: 2025/26.
- Neither 2024/25 nor 2025/26 is used to retune the controls.

The position anchor and shrinkage strength were selected on training data
using selected-top-15 MAE, regret, and absolute bias. Risk aversion was then
selected on training data using selected-top-15 MAE plus `0.05 ×` mean
top-15 regret. The top-15 measure is a ranking proxy; it does not claim to
model FPL budget, position-count, or club constraints.

## Results

The reproducible report is
`reports/forecasting/live-faithful-v2-robust-evaluation.json`.

| Evaluation | Selected MAE delta | Mean top-15 regret delta | All-player MAE delta |
| --- | ---: | ---: | ---: |
| Training | -0.049 | -1.632 | -0.005 |
| Locked 2024/25 | -0.045 | -2.211 | -0.006 |
| Final 2025/26 | -0.204 | +2.395 | -0.005 |

Negative is better for all three columns. The locked gate passes, so the model
is eligible to remain a challenger. It is not promoted to the 2026/27 live
policy: final 2025/26 calibration improves while the unconstrained ranking
regret worsens, which is exactly the kind of disagreement the separate metrics
are intended to expose.

A legal GW12 smoke test used the frozen solver input and unchanged rules. Raw
and robust selected the same transfers (none), XI, and captain. The lower
scenario changed the XI; the upper scenario changed both transfers and XI.
That demonstrates observable sensitivity even when the central robust action
matches control. Runtime for raw, robust, lower, central, and upper solves was
about 43 seconds on the development machine, which is acceptable for a weekly
decision and is not treated as an optimisation target.

## Reproduction

```powershell
python -m src.forecasting.calibrate_robust_selection
python -m pytest tests/optimisation/test_robust_objective.py -q
```

The calibration command regenerates only the challenger report. It never
modifies sealed benchmark episodes or control replay outputs.

## Interpretation and next gate

This slice establishes a deterministic, auditable robust objective and a
positive held-out gate. A full isolated legal comparison across the sealed
2025/26 episodes belongs in the final challenger matrix, where robust plans
can be frozen and scored through the existing hidden-outcome boundary. Any
live-shadow nomination must consider legal realised decision value alongside
calibration, not select this challenger solely from the top-15 proxy.
