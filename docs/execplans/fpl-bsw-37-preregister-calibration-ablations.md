# Preregister live calibration and data-family ablations

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, the 2026/27 live shadow will have a frozen evaluation contract before relevant outcomes exist. It will report whether start probabilities and expected minutes are calibrated, and it will test odds, team strength, set-piece role, and player-rating inputs one family at a time against the same structured baseline. A good-looking result on the already-known 2025/26 season will remain exploratory and can never promote a feature.

## Progress

- [x] (2026-07-27 10:10Z) Claimed `FPL-bsw.37`, confirmed no competing Bead, and searched prior agent history.
- [x] (2026-07-27 10:14Z) Inspected existing forecast calibration, team-context and robust-selection challengers, source policies, model hashes, live shadow policy, and 2025/26 reports.
- [x] (2026-07-27 10:25Z) Added binary start and expected-minutes calibration with reliability and locked time-split summaries.
- [x] (2026-07-27 10:31Z) Added point-in-time rolling-origin feature-family ablation and fail-closed promotion guards.
- [x] (2026-07-27 10:37Z) Froze the 2026/27 policy, candidate-arm matrix, thresholds, and exploratory historical status in hashed artifacts and documentation.
- [x] (2026-07-27 10:42Z) Added focused tests, ran the full suite, recorded results, closed the Bead, and prepared the verified tree for commit and push.

## Surprises & Discoveries

- Observation: The repository already has a strong pre-2025/26 calibration chain and an executable `live-faithful-v1.feature-complete` baseline.
  Evidence: All model artifacts validate their content hashes; the live policy points to hash `579865...`, not the older structured-only file named in the Bead.

- Observation: The 2025/26 team-context challenger is already rejected and degraded without odds in 37 weeks.
  Evidence: `reports/forecasting/live-faithful-v2-team-context/evaluation.json` records `promotion_eligible: false`, all four promotion checks false, and `odds_absent: 37`.

- Observation: The fixed baseline's 2025/26 appearance diagnostic is weakest in GW1–6.
  Evidence: GW1–6 start Brier is 0.13060, start ECE is 0.10180, and expected-minutes MAE is 21.24, versus full-season 0.11164, 0.03937, and 17.31.

- Observation: A focused integration test caught an incorrect nested hash replacement before publication.
  Evidence: The live policy rejected the mismatch; the nested preregistration hash and top-level policy hash were corrected and all live-shadow tests pass.
- Observation: Existing generic calibration reports continuous point errors but not binary Brier/log-loss/ECE, while the forecast calibrator computes only aggregate start Brier and minutes MAE.
  Evidence: Neither path currently produces start-probability reliability bins or locked time-split appearance reports.

## Decision Log

- Decision: Preserve all existing content-addressed model artifacts unchanged.
  Rationale: The executable baseline is already frozen and referenced by hash. Preregistration belongs in a new immutable report and the live policy, not by rewriting historical calibrated models.
  Date/Author: 2026-07-27 / Codex

- Decision: Treat 2025/26 evaluations as exploratory diagnostics even when they are out of sample relative to an older fit.
  Rationale: The season has now been repeatedly inspected and used to shape the engine. It can expose defects but cannot support a new 2026/27 promotion claim.
  Date/Author: 2026-07-27 / Codex

- Decision: Require point-in-time legality, declared rolling-origin folds, forecast improvement, calibration non-inferiority, legal decision-regret improvement, and operational completeness for feature promotion.
  Rationale: A family that improves average prediction but worsens actual feasible decisions, leaks timestamps, or frequently degrades should not enter the live candidate.
  Date/Author: 2026-07-27 / Codex

- Decision: Keep all optional families shadow-only at preregistration.
  Rationale: Odds lack a mature live corpus, the historical team-context candidate failed, and set-piece/ratings families do not yet have sufficient point-in-time ablation evidence.
  Date/Author: 2026-07-27 / Codex

## Outcomes & Retrospective

The 2026/27 live process now has a sealed five-fold evaluation contract, four isolated optional-family shadow arms, proper appearance calibration, immutable ablation row bindings, operational metrics, paired uncertainty, and owner-reviewed fail-closed promotion. The existing executable baseline remains unchanged at hash `579865...`. The generated 2025/26 appearance diagnostic is explicitly exploratory and shows the largest weakness in GW1–6. No optional data family is promoted preseason. Focused tests passed and the complete repository suite passed 533/533, including isolated contract cases for all four optional families.

## Context and Orientation

`src/forecasting/calibrate_live_faithful.py` builds leakage-safe player/Gameweek cases using prior seasons and only earlier target Gameweeks. It emits start probabilities, expected minutes, expected points, and realised outcomes. It needs an additive report builder that uses the already-frozen parameters rather than refitting on 2025/26.

`src/evaluation/calibration.py` computes continuous error and reliability summaries. It will gain a binary probability summary for starts and a bounded expected-minutes summary. A “reliability bin” groups similar forecasts and compares mean forecast with mean outcome.

`src/evaluation/feature_ablation.py` will be new. An “ablation” compares the baseline against a candidate differing by one named data family. “Rolling origin” means each test fold occurs strictly after its declared training end. “Legal decision regret” is the realised gap between the chosen feasible plan and the best feasible hindsight plan supplied by the optimiser evaluation, not an unconstrained top-player proxy.

`control/policies/live-shadow-candidate.json` is a content-hashed observation-only policy. It will name the frozen preregistration artifact, all candidate families, thresholds, degradation metrics, causal arm comparisons, and the prohibition on retrospective promotion. The baseline model artifacts remain byte-identical.

## Plan of Work

Extend calibration helpers with deterministic proper scores and reliability tables. Add a report builder to the live-faithful calibrator that evaluates fixed parameters by declared Gameweek spans and labels the 2025/26 result exploratory.

Implement a generic feature-family ablation evaluator. It will reject post-cutoff observations, undeclared families, duplicate episodes, missing feasible hindsight values, and malformed folds. It will report baseline and candidate proper scores, calibration, legal regret, uncertainty, latency, and degradation. Promotion is fail-closed and specifically barred for historical-only 2025/26 evidence.

Create a sealed preregistration artifact under `reports/forecasting/2026-27-preregistration/` and document the frozen protocol. Update the live-shadow policy with the artifact hash and candidate matrix, then recompute its content hash. Do not activate or fetch any source.

Add tests using small synthetic folds. Generate the exploratory appearance report from the existing local historical dataset if present; otherwise leave a deterministic command and explicit missing-data state. Run focused and full tests.

## Concrete Steps

From `C:\Users\Alastair\FPL`, run:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting/test_live_faithful_calibration.py tests/evaluation/test_feature_ablation.py -q

Then run:

    .\.venv\Scripts\python.exe -m pytest -q

The focused tests must prove Brier/reliability calculations, strict fold ordering, cutoff rejection, deterministic results, one-family isolation, historical promotion refusal, and fail-closed promotion when legal regret or degradation fails.

## Validation and Acceptance

The appearance report must include start Brier score, start log loss, expected calibration error, reliability bins, expected-minutes MAE/RMSE/bias, and the same metrics for declared locked Gameweek spans.

Each of odds, team strength, set-piece role, and player ratings must appear in the preregistered candidate matrix with an isolated arm, baseline, required source timing, degradation rule, and promotion status. No 2025/26-only report may return `promotion_eligible: true`.

An ablation can promote only when all declared locked folds pass temporal checks and aggregate thresholds for forecast proper score, calibration, legal decision regret, degradation, and latency. The live shadow policy must report causal differences and operational metrics alongside points.

## Idempotence and Recovery

All reports are content-hashed and deterministic from their inputs. Existing model files are not rewritten. Report generation may be rerun and must produce the same hash. If local private historical data is absent, no download is attempted; tests use synthetic fixtures and the report records the unavailable input.

## Artifacts and Notes

The unchanged baseline model hash is `579865597123d0f6a86156dc4a70c6bab696207b296e8fb2b540d644366e62b2`.

The sealed preregistration hash is `e2d514efd774ca22f30a9cf701a453563d51d82f65188032ed66a8176388e19f`; the readiness hash is `c35772b67c7a2cb3765692798f9344b9193a4e8274b71583ee7a896b64fa660c`; and the exploratory appearance diagnostic hash is `f93b84b4c3f38e4533baed2dc9c204c804645bea40d21449e5f2efaabc0a12be`.

    .\.venv\Scripts\python.exe -m pytest tests/forecasting/test_live_faithful_calibration.py tests/evaluation/test_feature_ablation.py tests/integration/test_live_shadow_pairing.py -q
    18 passed in 1.83s (before the final all-family parameter expansion; the complete run below is authoritative)

    .\.venv\Scripts\python.exe -m pytest -q
    533 passed in 320.41s

## Interfaces and Dependencies

No new dependency is required.

`src.evaluation.calibration` will expose:

    binary_calibration_summary(probabilities, outcomes, *, bins=10) -> dict
    minutes_calibration_summary(predictions, actuals, *, bins=10) -> dict

`src.forecasting.calibrate_live_faithful` will expose:

    appearance_calibration_report(cases, params, *, spans, evaluation_season, status) -> dict

`src.evaluation.feature_ablation` will expose:

    evaluate_feature_ablation(*, rows, preregistration, family) -> dict
    validate_preregistration(preregistration) -> None

Plan revision note (2026-07-27): Initial plan created after confirming the existing locked model chain and the rejected/degraded historical team-context challenger. It deliberately preserves old model artifacts and moves promotion evidence into preregistered live folds.


Plan revision note (2026-07-27): Recorded completed implementation, the exploratory appearance findings, the caught hash-binding failure, immutable artifact hashes, and final 530-test result; Git publication remains.

Plan revision note (2026-07-27): Expanded the evaluation contract across all four optional families and recorded the authoritative 533-test full-suite result.

Plan revision note (2026-07-27): Marked the verified implementation and Bead lifecycle complete; the tree is ready for Git publication.
