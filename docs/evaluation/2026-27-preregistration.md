# 2026/27 forecast and evidence preregistration

This protocol was frozen on 27 July 2026, before the 2026/27 Premier League season. It defines what the live shadow may measure and what evidence would be required before an optional data family can join the candidate engine. It does not activate account writes or browser execution.

The canonical machine-readable contract is `reports/forecasting/2026-27-preregistration/preregistration.json`, hash `e2d514efd774ca22f30a9cf701a453563d51d82f65188032ed66a8176388e19f`. The observation-only policy binds that hash in `control/policies/live-shadow-candidate.json`.

## What remains fixed

The shared structured baseline is `live-faithful-v1.feature-complete`, config hash `579865597123d0f6a86156dc4a70c6bab696207b296e8fb2b540d644366e62b2`. That artifact was selected before 2025/26 outcomes and is not rewritten here.

Every agent receives the same baseline projections and legal decision state. Unstructured evidence remains a separate, cited and bounded treatment. The continuously frozen no-evidence plan remains the counterfactual for the evidence arm.

No result from the already-studied 2025/26 season can promote a feature. Historical cases may expose a defect, test the mechanics, or justify a new prospective hypothesis; they are always production-ineligible.

## Appearance calibration first

The first live question is whether the engine predicts who starts and how many minutes they play. These quantities drive nearly every downstream player-points estimate.

The appearance report includes:

- start probability Brier score, log loss, expected calibration error, and reliability bins;
- expected-minutes bias, MAE, RMSE, mean squared error, calibration gap, and reliability bins;
- the same metrics within five declared Gameweek spans;
- model and source hashes, with no refit on the evaluated target rows.

The fixed baseline’s 2025/26 exploratory diagnostic covers 29,338 player-Gameweeks:

| Measure | Result |
|---|---:|
| Start Brier | 0.11164 |
| Start expected calibration error | 0.03937 |
| Expected-minutes MAE | 17.31 |

The early GW1–6 span is materially weaker: start Brier `0.13060`, calibration error `0.10180`, and minutes MAE `21.24`. This supports the decision to prioritise early-season minutes/start calibration, but these observed results do not authorise a retrospective parameter change.

## Isolated optional-family arms

Each candidate differs from the shared baseline by exactly one family:

| Family | Shadow arm | Current status |
|---|---|---|
| Pre-deadline odds | `forecast_optimizer_plus_odds` | Awaiting complete live capture |
| Team strength | `forecast_optimizer_plus_team_strength` | Awaiting isolated live rows |
| Set-piece role | `forecast_optimizer_plus_set_piece_role` | Awaiting immutable role observations |
| Player ratings | `forecast_optimizer_plus_player_ratings` | Awaiting immutable rating snapshots |

Missing optional input always degrades to the byte-identical shared baseline. It is not imputed from a later quote or current rating.

The previous 2025/26 team-context challenger is not promotion evidence. It failed every declared promotion check and had no odds in 37 Gameweeks. It also combined components, so it is not the isolated team-strength test defined here.

## Point-in-time and causal contract

Every ablation row binds:

- an immutable source snapshot hash available strictly before the deadline;
- baseline and candidate frozen-plan hashes;
- one shared realised-outcome hash;
- legal baseline, candidate, and hindsight-feasible decision scores;
- candidate latency, degradation state, fold, season, and Gameweek.

Rows with more than one candidate family, late availability, illegal plans, missing hashes, duplicate episodes, or undeclared folds fail closed.

The report always places these results together:

- forecast proper score and calibration;
- legal decision regret and net decision points;
- paired uncertainty;
- mean and p95 latency;
- degradation and validation-failure rates;
- current evidence, inherited state, and total evidence-trajectory effects.

This is deliberately closer to a quant research protocol than a leaderboard. A family must improve what the engine predicts and the legal decisions it makes, without buying the result through leakage, frequent fallback, or unacceptable operational cost.

## Rolling-origin folds

The live season is evaluated in five immutable spans:

1. GW1–6, trained only through 2025/26;
2. GW7–12, trained only through live GW6;
3. GW13–19, trained only through live GW12;
4. GW20–28, trained only through live GW19;
5. GW29–38, trained only through live GW28.

The 2025/26 exploratory fold is separate and can never count towards the minimum live-fold gate.

At least three live folds with four episodes each are required before review eligibility. The candidate must improve mean squared forecast error by at least `0.0001`, improve legal regret by at least `0.01`, worsen calibration error by no more than `0.01`, degrade in no more than 5% of rows, and keep p95 candidate latency at or below 30 seconds.

Passing every gate produces `eligible_for_owner_review`, not automatic activation. Promotion still requires explicit owner review. Final season points cannot override a failed gate.

## What happens next

At each 2026/27 deadline, capture the baseline and four candidate shadows from identical structured state. Capture odds at T-24h, T-8h, T-2h, and final when an approved provider exists. Freeze source and plan hashes before the cutoff. After finalisation, append the shared outcome and legal hindsight comparison, then update only the now-complete rolling fold.

The preseason readiness artifact is `reports/forecasting/2026-27-preregistration/family-readiness.json`, hash `c35772b67c7a2cb3765692798f9344b9193a4e8274b71583ee7a896b64fa660c`. Every optional family currently remains shadow-only.
