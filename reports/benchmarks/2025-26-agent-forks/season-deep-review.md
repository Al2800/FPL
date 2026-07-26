# 2025/26 evidence-fork season review

## Executive finding

The audited trajectory is complete through GW38 and finishes strongly, but it does **not** show that weekly unstructured evidence was the main source of the gain.

From GW12-GW38, the accepted fork scored 1,530 gross points and incurred one eight-point hit, for 1,522 net. The canonical forecast-optimizer control scored 1,465 gross and also incurred eight hit points, for 1,457 net. The accepted fork therefore leads by 65 net points over the comparable period. Adding the shared canonical GW1-GW11 score of 553 gives a hybrid full-season total of 2,075 net versus 2,010 canonical.

The correct interpretation is:

- The deterministic policy plus its accumulated squad state performed better than canonical over this one path.
- Paired same-state tests from GW13-GW38 attribute only +16 realised points directly to current-week evidence, concentrated in four weeks.
- GW30-GW38 contributed +49 versus canonical, but all nine same-state evidence deltas were zero. That late gain came from the carried state and deterministic choices, not direct weekly evidence intervention.
- Because earlier evidence can alter later squad state, the residual 49 points over GW12-GW38 is not a pure deterministic estimate. A full long-horizon no-evidence counterfactual is required to separate deterministic policy from downstream evidence inheritance.
- These are exploratory historical results. The evidence cases were recovered after outcomes were known, were not preregistered, and are not valid headline claims about model skill.

## Scorecard

| Window | Fork gross | Fork hits | Fork net | Canonical gross | Canonical hits | Canonical net | Net delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| GW12-GW17 | 343 | 0 | 343 | 330 | 0 | 330 | +13 |
| GW18-GW22 | 219 | 0 | 219 | 236 | 0 | 236 | -17 |
| GW23-GW29 | 410 | 0 | 410 | 390 | 0 | 390 | +20 |
| GW30-GW38 | 558 | 8 | 550 | 509 | 8 | 501 | +49 |
| GW12-GW38 | 1,530 | 8 | 1,522 | 1,465 | 8 | 1,457 | +65 |
| Shared GW1-GW11 + GW12-GW38 | - | - | 2,075 | - | - | 2,010 | +65 |

The fork beat canonical in 13 gameweeks, lost in 13, and tied once. Its mean weekly score was 56.7, median 57, population standard deviation 16.9, range 28-92. There was no 100-point week. That is not itself a defect: the policy optimises pre-deadline expected value rather than hindsight weekly ceiling, and this path did not activate chips.

## Weekly accepted trajectory

| GW | Version | Fork | Canonical | Delta | Hits | Transfers | Captain | Evidence decision | Same-state evidence delta |
|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| 12 | sol-v1 | 43 | 29 | +14 | 0 | 1 | Salah | adapter applied | n/a |
| 13 | sol-v1 | 37 | 36 | +1 | 0 | 0 | Salah | degraded fallback | 0 |
| 14 | sol-v1 | 60 | 63 | -3 | 0 | 3 | Haaland | applied | -1 |
| 15 | sol-v1 | 53 | 55 | -2 | 0 | 0 | Haaland | abstained | 0 |
| 16 | sol-v1 | 58 | 59 | -1 | 0 | 1 | Haaland | applied | -1 |
| 17 | sol-v1 | 92 | 88 | +4 | 0 | 2 | Haaland | applied | +13 |
| 18 | sol-v1 | 31 | 33 | -2 | 0 | 1 | Haaland | applied | 0 |
| 19 | sol-v1 | 33 | 36 | -3 | 0 | 1 | Haaland | abstained | 0 |
| 20 | sol-v3 | 49 | 65 | -16 | 0 | 0 | Haaland | applied | 0 |
| 21 | sol-v3 | 57 | 55 | +2 | 0 | 1 | Haaland | applied | 0 |
| 22 | sol-v3 | 49 | 47 | +2 | 0 | 2 | Haaland | applied | +5 |
| 23 | sol-v2 | 36 | 41 | -5 | 0 | 0 | Haaland | abstained | 0 |
| 24 | sol-v1 | 45 | 60 | -15 | 0 | 1 | Haaland | abstained | 0 |
| 25 | sol-v3 | 73 | 58 | +15 | 0 | 1 | Bruno | abstained | 0 |
| 26 | sol-v3 | 64 | 68 | -4 | 0 | 1 | Gabriel | applied | 0 |
| 27 | sol-v1 | 43 | 43 | 0 | 0 | 0 | Haaland | abstained | 0 |
| 28 | sol-v1 | 82 | 67 | +15 | 0 | 1 | Haaland | applied | 0 |
| 29 | sol-v1 | 67 | 53 | +14 | 0 | 1 | Semenyo | abstained | 0 |
| 30 | sol-v5 | 55 | 45 | +10 | 0 | 1 | Haaland | abstained | 0 |
| 31 | sol-v3 | 60 | 63 | -3 | 0 | 3 | Bruno | applied | 0 |
| 32 | sol-v1 | 60 | 53 | +7 | 0 | 1 | Bruno | abstained | 0 |
| 33 | sol-v3 | 86 | 79 | +7 | 0 | 3 | Haaland | applied | 0 |
| 34 | sol-v1 | 28 | 36 | -8 | 8 | 3 | Bruno | applied | 0 |
| 35 | sol-v1 | 61 | 44 | +17 | 0 | 0 | Haaland | applied | 0 |
| 36 | sol-v1 | 87 | 89 | -2 | 0 | 2 | Haaland | applied | 0 |
| 37 | sol-v1 | 64 | 70 | -6 | 0 | 0 | Bruno | abstained | 0 |
| 38 | sol-v1 | 57 | 30 | +27 | 0 | 0 | Haaland | abstained | 0 |

Haaland was captain in 18 of 27 fork weeks, Bruno in five, Salah in two, Gabriel and Semenyo once each. The fork made 30 transfers from GW12-GW38 versus canonical's 32. Both incurred their only eight-point hit in GW34.

## Evidence contribution

Twenty-six paired same-state comparisons exist from GW13-GW38:

- Four produced a non-zero realised score effect: GW14 -1, GW16 -1, GW17 +13, and GW22 +5.
- Twenty-two produced zero score effect.
- Eight changed the selected plan hash.
- Five changed transfer selections.
- The direct realised total was +16.

This is a healthy warning against equating "adjustment accepted" with "decision improved." Fourteen accepted weeks are labelled `applied`, but only four produced a non-zero same-state score effect. The artifacts should expose three separate concepts:

1. evidence accepted by governance;
2. solver plan changed;
3. realised score changed.

In GW30-GW38, five evidence adjustments were accepted and four weeks abstained. Two accepted adjustments changed plan hashes, none changed transfers, and none changed realised points. The late-season +49 versus canonical is therefore state/policy performance, not direct prose value.

The cases also reveal a targeting problem. Evidence was often relevant to an owned player but not close to the active transfer, lineup, or captaincy boundary. For live operation, case selection should be dynamic: first compute the deterministic decision and its near-ties, then retrieve evidence for players capable of changing that boundary. A broad news digest can remain available to the agent, but evaluation should record which passages could actually alter a decision.

## State, transfers, and scoring

The longitudinal state chain is valid from the reconstructed GW30 successor through GW38. Bank, free transfers, prices, squad, and hashes move legally week to week. GW38 is represented as a sealed terminal decision/outcome with no invented GW39 state.

The most important transfer-policy finding is GW34. With one free transfer, both fork and canonical selected three transfers and paid eight points during a blank gameweek. The fork scored 28 gross and 20 net. This may still be rational over a multiweek horizon, but the current artifact does not expose enough counterfactual value to justify the hit:

- points with zero, one, two, and three transfers;
- immediate gain before hit;
- expected gain over the chosen horizon;
- uncertainty interval;
- payback gameweek;
- alternative use of a Free Hit or Wildcard.

That counterfactual ladder should be mandatory whenever `hit_cost > 0`. A configurable risk premium should sit above the arithmetic four-point threshold because forecast error is large.

The repeated Timber sequence is another state issue. He was confirmed out in GW34, still out in GW35, and still out in GW36, yet the weekly deterministic baselines remained 43.0, 36.0, and 35.1 expected minutes until evidence was reapplied. Live evidence should update a stateful availability ledger with expiry and explicit recovery conditions. Repeatedly rediscovering the same injury is wasteful and risks inconsistent forecasts.

No chip was used. The GW38 starting state still listed all four second-half chips as available, and the earlier state also retained all first-half chips. This means the replay did not evaluate a complete FPL policy. It evaluated transfers, lineups, and captaincy while leaving Wildcard, Free Hit, Triple Captain, and Bench Boost value unrealised. Chip planning is the largest functional gap before treating 2,075 as a credible full-season policy score.

## Forecast and player evaluation

The solver consumes expected points, expected minutes, start probability, price, position, club constraints, bank, transfers, and option value. It does not separately optimise a realised post-match "player rating." Underlying player/team performance features may contribute upstream to expected points, but ratings are not an independent substitution criterion.

That is correct for pre-deadline decision-making: realised ratings must not leak backward. For future forecasts, ratings-like inputs should be point-in-time predictive features only when they add out-of-sample calibration beyond minutes, role, team strength, fixtures, and expected-goal involvement. Their incremental value should be tested by ablation, not assumed.

Recommended forecast evaluation:

- minutes: Brier score and calibration curves for starts and 60+ minutes;
- points: MAE, RMSE, rank correlation, and calibration by forecast decile;
- decisions: regret against a legal hindsight oracle, separated into transfer, lineup, captain, and chip regret;
- uncertainty: coverage of prediction intervals and sensitivity of the chosen plan;
- ablations: remove each data family in turn, including news, odds, team strength, player form, and ratings.

## Hosted-agent reliability

Sixteen degraded evidence/challenger artifacts are preserved across GW20-GW38. The final block alone required:

- GW30: nested claim schema, invalid expiry, refusal to infer omitted fields, and incorrect role literal;
- GW31: wrong adjustment key and fractional `completed_at`;
- GW33: response-hash mismatch and challenger reviewing the wrong adjustment ID.

The semantic judgements were usually sensible; serialization and protocol compliance were the weak point. The architecture currently asks the model to do work that belongs to the host.

Required protocol changes:

1. The model returns only the semantic structured payload. The host creates timestamps, attestation, usage, request binding, and hashes.
2. Use constrained structured output or tool calls, not prose JSON conformance.
3. Include allowed `claim_id`, `expires_at`, and adjustment IDs in the request. GW30 showed that the evidence document omitted fields later required in the response.
4. Replace ambiguous challenger `escalation_outcome="dismissed"` with an explicit proposal decision such as `accepted`, `downgraded`, `rerun`, or `escalated`.
5. Enforce the completion gate in shared orchestration, not only in a script. GW33 `sol-v2` exposed that a degraded challenger could previously be passed to fallback scoring. The diagnostic is preserved, `sol-v3` is the accepted week, and the final-block runner now refuses non-completed gates.
6. Report invalid-output rate, retry count, time to accepted decision, and semantic-versus-protocol failure separately.

## What the season does and does not establish

It establishes:

- legal state can be carried across a full remaining season;
- canonical controls remain immutable;
- evidence can be governed, challenged, attributed, and replayed;
- the fork can outperform the canonical policy on one historical path;
- evidence abstention works for missing or vague news;
- direct evidence value is sparse and measurable.

It does not establish:

- a globally competitive FPL rank;
- unbiased model performance;
- a robust chip policy;
- that the +65 points came from the language model;
- that the chosen evidence weighting generalises;
- complete live-source reliability or exact timestamp capture.

## Recommended implementation order for 2026/27

### P0: complete the policy

1. Implement and test chip action generation and multiweek chip valuation.
2. Add a mandatory hit counterfactual ladder and risk premium.
3. Move the non-completed-gate refusal into shared orchestration.
4. Make the host own wrapper metadata, hashes, and schema validation.

### P1: make evidence decision-relevant

5. Add a stateful availability ledger with source, confidence, expiry, and supersession.
6. Retrieve broadly, then rank evidence against transfer/lineup/captain/chip decision boundaries.
7. Add exact publication, observation, and availability timestamps with immutable source snapshots.
8. Freeze a no-evidence shadow trajectory beside the live evidence trajectory for long-horizon attribution.

### P2: improve forecasts without overfitting 2025/26

9. Calibrate minutes and start probabilities first; repeated Timber baselines show the current weakness.
10. Add point-in-time odds, team xG/xGA, Elo/team strength, set-piece role, promoted/transferred-player priors, and ratings only behind ablation tests.
11. Evaluate transfer horizon and terminal value using multiple seasons or rolling-origin folds, not this season alone.
12. Preregister live evidence policies and model arms for 2026/27.

## Bottom line

The replay infrastructure is now credible enough to support live shadow operation, but the decision policy is not complete until chips and hit justification are first-class. The evidence layer has demonstrated occasional value (+16 direct points) and strong abstention behaviour, yet most late-season gains came from deterministic state and policy. The next phase should improve protocol reliability and decision-boundary targeting, then run a continuously frozen no-evidence shadow alongside the live evidence arm so agentic value can be measured without hindsight or inherited-state ambiguity.
