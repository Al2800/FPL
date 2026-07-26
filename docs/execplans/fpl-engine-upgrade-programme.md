# Upgrade the Replay Engine into a Live-Faithful Decision Policy

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

The completed 2025/26 replay is a frozen control showing that the current structured forecast and optimiser can maintain legal longitudinal state and finish a season reproducibly. It is not yet a sufficiently calibrated or forward-looking decision policy for 2026/27. This programme upgrades the engine in measured challenger stages: first make its errors and decision value observable, then improve event forecasts, team context, minutes and bench handling, robustness, multiweek transfers, chips, and captaincy.

After this work, a user can run the same timestamp-safe historical episodes through the frozen control and each challenger, inspect forecast calibration and decision decomposition, and promote only changes that improve declared metrics without using information unavailable at the deadline. The same interfaces will then accept immutable live snapshots in 2026/27.

## Progress

- [x] (2026-07-25 20:40Z) Completed and froze the canonical 2025/26 GW1-GW38 replay; the active structured arms finished on 2010 points and the naive arm on 1990 points.
- [x] (2026-07-25 20:40Z) Identified the principal gaps: selected-player forecast overstatement, inactive event features, coupled team attack/defence adjustment, no probabilistic bench value, noisy top-projection selection, one-week transfer valuation, no autonomous chip policy, and simplistic captain selection.
- [x] (2026-07-25 20:40Z) Claimed `FPL-bsw.14` as the measurement and equivalence-oracle foundation.
- [x] (2026-07-25 21:05Z) Implemented `FPL-bsw.14`: realised feasible-baseline contracts, paired cluster-aware metrics, calibration, uncertainty, resource use, detectable-effect-size analysis, and a read-only 38-Gameweek control report.
- [x] (2026-07-26 03:48Z) Completed the timestamp-sealed GW12 evidence fork under `FPL-98p`: the isolated +14 reduces to +4 through an independent GW38 continuation, with canonical artifacts unchanged and opportunity ceilings separated by feasibility.
- [x] (2026-07-26 04:28Z) Generalised timestamp-sealed evidence under `FPL-bsw.24`: reusable multi-bundle input, isolated no-state-advance attribution, one independent longitudinal chain, canonical tree protection, direct-versus-compounding decomposition, exact one-off hash equivalence and 421 passing repository tests.
- [x] (2026-07-25 21:20Z) Evaluated the sealed 0.25 player-event challenger and rejected promotion: selected cohorts improved slightly, but all-player calibration regressed.
- [x] (2026-07-26 00:05Z) Separated attack and defence context, calibrated it before 2025/26, and rejected promotion after it worsened all, owned, and selected-player calibration.
- [x] (2026-07-25 23:15Z) Added calibrated three-state appearances and opt-in legal goalkeeper, bench-order, automatic-substitution, and vice-captain planning value without changing realised scoring.
- [x] (2026-07-26 01:47Z) Added a sealed reliability-aware robust-selection challenger with raw/central/lower/upper audit values, unchanged legal solver integration, locked held-out gates, and explicit sensitivity reporting.
- [x] (2026-07-26 02:21Z) Added a bounded same-cutoff receding-horizon transfer challenger with legal state carry, first-action-only execution, deterministic fallback, and an exploratory GW12 result.
- [x] (2026-07-26 03:29Z) Implemented the autonomous chip policy and GW31 Free Hit counterfactual in `FPL-q8s`: same-cutoff trajectory projection, eight frozen alternatives, exact state restoration, a GW32-GW38 branch, canonical tree-hash protection, documentation, and 416 passing repository tests.
- [x] (2026-07-26 03:07Z) Added a captain/vice challenger with calibrated zero-minute fallback, ceiling and uncertainty; rejected it on locked 2024/25 despite a descriptive +7 on 2025/26.
- [x] (2026-07-26 10:15Z) Ran the complete governed matrix, preserved eight rejected/deferred/eligible rows, completed the GW2-GW38 isolated legal robust replay, proved the canonical tree unchanged, and nominated robust selection for observation-only 2026/27 live shadow with v1 still executable.

## Surprises & Discoveries

- Observation: The current event model computes xG, xA, clean-sheet, saves, bonus, card, and defensive-contribution features but the locked configuration assigns them a weight of zero.
  Evidence: `control/models/live-faithful-v1.feature-complete.json` contains `event_model_weight: 0.0`.

- Observation: Forecast accuracy is materially worse on the players selected by the optimiser than on the full available player pool, which is consistent with selection on noisy extreme estimates.
  Evidence: The post-season review found all-player correlation about 0.56 and MAE about 1.09, versus selected-XI correlation about 0.21 and MAE about 3.25.

- Observation: The one-week transfer search is tractable, but its fixed banked-transfer value is not a forecast of actual future fixtures or players.
  Evidence: The control uses an expected-hit-avoidance bridge worth 1.8 points per retained transfer and declares this limitation in every replay summary.

- Observation: The replay recorded meaningful automatic-substitution value that the optimiser did not price directly.
  Evidence: Across the season, 27 automatic substitutions produced 85 realised points while the ordinary lineup objective ignored probabilistic bench value.

- Observation: The GW1 cold start has no `shared-locked-forecast.json`, while GW2 onward do.
  Evidence: The real season review retains GW1 in paired policy scoring and begins forecast calibration at GW2.

- Observation: The pre-season 0.25 event blend helps players the optimiser owned or selected but harms the full forecast population.
  Evidence: On the sealed 2025/26 evaluation, selected-XI MAE changed by -0.052 and absolute bias by -0.122, while all-player MAE worsened by +0.118 and correlation changed by -0.0025. The predeclared promotion rule rejected it.

- Observation: Better team-level xG prediction does not automatically improve player-level FPL forecasts.
  Evidence: The selected model reached 0.617 team-xG MAE on locked 2024/25 but worsened 2025/26 player MAE versus v1 by +0.137 overall, +0.168 for owned players, and +0.210 for selected-XI players.

- Observation: The prior optimiser ignored material expected value in its ordered bench and vice-captain choices.
  Evidence: The new appearance bins improve locked 2024/25 multiclass Brier from 0.37164 to 0.36219; the exact 123-candidate contingency search now runs in 5.49 seconds after isomorphic structural caching, versus 65.09 seconds initially.

- Observation: Reliability-aware upper-tail shrinkage improves selected-player calibration consistently, but ranking regret does not move in the same direction in every season.
  Evidence: Locked 2024/25 selected-top-15 MAE improves by 0.045 and mean regret by 2.211 points per Gameweek; final 2025/26 selected MAE improves by 0.204 while the unconstrained regret proxy worsens by 2.395.

- Observation: A captain policy can raise expected value and finish ahead in one season while still failing the prior held-out gate.
  Evidence: `captain-v1` improved training captain points by 18 and final 2025/26 by 7, but lost 9 points to control on locked 2024/25.

- Observation: In the sealed GW31 input, Wildcard and Free Hit do not improve the immediate three-transfer XI; their apparent one-week planning gain comes entirely from retaining five banked transfers.
  Evidence: The prototype gives the same 50.02 immediate objective to the no-chip, Wildcard, and Free Hit three-transfer squads, while the chip variants retain 7.2 rather than 3.6 points of transfer-option value.

- Observation: The realised best chip and the forecast policy decision can disagree sharply without indicating a process defect.
  Evidence: Triple Captain realised 76 versus 63 for no chip, but its frozen expected gain was only 5.89 before an eight-point reserve. The declared policy therefore retained the chip. A separate Free Hit branch finished GW31-GW38 28 points ahead despite being forecast below the persistent squad at the GW31 cutoff.

- Observation: One successful evidence intervention does not preserve its isolated value after state compounding.
  Evidence: The reconstructed GW12 availability fork gains 14 points immediately but only four across GW12-GW38 after every later action is independently replanned.

- Observation: The difference between direct evidence attribution and state compounding is itself a decision metric.
  Evidence: The reusable weekly programme records +14 isolated direct value, +4 longitudinal value and therefore -10 from later compounding for the GW12 intervention.

- Observation: Better selected-player calibration did not translate into better legal isolated decisions for the robust challenger.
  Evidence: Across identical GW2-GW38 canonical starting states, robust selection changed 17 transfer choices and 30 lineups, never changed captaincy, and scored 1,935 versus 1,954 for control, a 19-point loss.

## Decision Log

- Decision: Treat the completed `live-faithful-v1` replay and its artifacts as immutable control data.
  Rationale: Rewriting the control would destroy reproducibility and make improvements impossible to attribute.
  Date/Author: 2026-07-25 / Codex

- Decision: Implement evaluation and equivalence guardrails before changing forecasts or optimisation.
  Rationale: The upgrade order must be driven by measured calibration and decision value, not by retrospective season totals or intuition.
  Date/Author: 2026-07-25 / Codex

- Decision: Build each behavioural change as a versioned challenger with one main lever.
  Rationale: Additive challengers permit paired comparisons on identical deadline-safe inputs, straightforward rollback, and clear attribution.
  Date/Author: 2026-07-25 / Codex

- Decision: Use both isolated and longitudinal evidence tests.
  Rationale: Isolated forks identify the value of one week of evidence, while longitudinal arms reveal compounding effects on squad, bank, transfers, and chips.
  Date/Author: 2026-07-25 / Codex

- Decision: Optimise for the 2026/27 live process while using 2025/26 as a systems and evaluation test.
  Rationale: Historical outcomes are useful for validation but must not leak into deadline decisions or induce season-specific tuning.
  Date/Author: 2026-07-25 / Codex

- Decision: Keep probabilistic squad contingency as an opt-in planning policy and leave the official realised scorer unchanged.
  Rationale: Forecast uncertainty should influence lineup, bench, and captain choices before the deadline, while revealed outcomes must continue to follow the versioned deterministic FPL rules without expected-value substitutions.
  Date/Author: 2026-07-25 / Codex

- Decision: Promote robust selection only to challenger status, not directly to the 2026/27 live policy.
  Rationale: The predeclared locked validation gate passes, but final 2025/26 calibration and unconstrained ranking regret disagree; the legal full-season challenger matrix must resolve downstream decision value.
  Date/Author: 2026-07-26 / Codex

- Decision: Reject `captain-v1` and retain the highest-expected-points control rule.
  Rationale: The captain-only alternative failed the locked 2024/25 realised-points gate; its descriptive +7 in 2025/26 cannot be used for retrospective promotion.
  Date/Author: 2026-07-26 / Codex

- Decision: Treat chip use as a same-cutoff multiweek allocation decision with an explicit reserve value.
  Rationale: Immediate expected points alone systematically spends scarce chips too early, while realised points would leak hindsight. The policy therefore combines the frozen current-week forecast, a discounted future trajectory from the same cutoff, and a predeclared value for retaining each chip.
  Date/Author: 2026-07-26 / Codex

- Decision: Retain the no-chip three-transfer GW31 control under `chip-policy-v1`.
  Rationale: No chip cleared both its declared reserve and the two-point deployment margin on the same-cutoff forecast. The later Triple Captain and Free Hit gains remain descriptive evaluation evidence rather than inputs to selection.
  Date/Author: 2026-07-26 / Codex

- Decision: Model multiple evidence weeks as isolated attribution rows plus one combined independent trajectory.
  Rationale: Advancing state separately for each isolated test would contaminate attribution, while evaluating only one combined trajectory would hide which bundle caused a direct change. The two views are complementary and their difference quantifies compounding.
  Date/Author: 2026-07-26 / Codex

- Decision: Nominate `robust-selection-v2` only as an observation-only shadow while retaining `live-faithful-v1` as the executable policy.
  Rationale: Robust selection is the only current challenger to pass its locked gate and complete the identical full legal episode comparison, but its negative 2025/26 isolated result and conflicting regret metrics rule out execution. Prospective shadowing can test generalisation without risking the live team.
  Date/Author: 2026-07-26 / Codex


## Outcomes & Retrospective

The evaluation foundation is complete. `reports/evaluation/2025-26-control-review.json` reproduces the +20 season difference as only +0.53 points per paired Gameweek, with a 95% normal interval of about -5.64 to +6.69 and an estimated minimum detectable effect of 8.81 points per Gameweek. It also reproduces the selected-XI correlation of 0.21, MAE of 3.25, and actual-minus-predicted bias of -0.93. The focused tests pass 23/23 and the complete project suite passes 373/373 in `.venv`. Same-starting-state do-nothing, captain, transfer, bench, and chip artifacts remain work for their dedicated challenger slices; the evaluator now forbids presenting expected proxies as realised comparisons and accepts only frozen alternatives with identical scoring provenance.

The chip milestone is complete. `reports/benchmarks/2025-26-counterfactuals/gw-31/evaluation.json` freezes eight legal alternatives before reveal, retains the no-chip three-transfer plan under the declared expected-value and reserve rule, proves exact Free Hit restoration, and carries the restored branch through GW38. The realised Triple Captain gain and the Free Hit branch's descriptive +28 remain visible but do not alter the pre-outcome selection. The report marks the reconstructed future schedule and bounded search as high uncertainty and promotion-ineligible. Focused chip/state/optimiser tests pass 52/52 and the full repository passes 416/416.

The final matrix is complete. `reports/benchmarks/2025-26-challenger-matrix/matrix.json` binds all eight challenger rows to identical episode/configuration evidence, retains every rejection and historical-provenance limitation, and records latency, memory, cost and fallback evidence. The full robust legal report is a negative but useful result: -19 isolated points over GW2-GW38. The generated `live-shadow-candidate.json` therefore keeps v1 executable and runs robust selection only as a non-blocking, non-executing shadow. The canonical 2,740-file replay tree has the same hash before and after matrix construction. An explicit 37-week recomputation reproduced the sealed report in 354.9 seconds, focused matrix/robust tests pass 9/9, and the full repository passes 425/425 in 202.57 seconds.

## Context and Orientation

The repository root is `C:/Users/Alastair/FPL`. A Gameweek episode is the immutable set of information available before an FPL deadline. A policy arm is one independently evolving decision process, such as `forecast_optimizer` or `naive_baseline`. A validated plan is the legal squad, transfers, lineup, captain, vice-captain, and chip choice frozen before outcomes are revealed. A counterfactual is another legal decision scored against the same revealed matches. An isolated fork changes one episode and then stops; a longitudinal fork carries its changed squad and transfer state into later weeks.

The chronological replay is implemented in `src/orchestration/genuine_replay.py`. Player forecasting is implemented under `src/forecasting/`, especially `live_faithful.py`, `player_events.py`, `team_strength.py`, and `minutes.py`. Lineup and transfer optimisation lives under `src/optimisation/`. Frozen reports are under `reports/benchmarks/2025-26/gw-NN/`. The official 2025/26 control model is `control/models/live-faithful-v1.feature-complete.json`; it must not be edited by this programme.

The first milestone is tracked as `FPL-bsw.14`. The exploratory GW12 evidence work is tracked as `FPL-98p` and is owned separately; its files must not be changed by unrelated slices. Chip work already exists as `FPL-q8s`.

## Plan of Work

Milestone one establishes the measurement layer. Extend `src/reporting/baseline_comparison.py` so realised alternatives are never confused with expected-point proxies. Add `src/evaluation/paired_metrics.py` for paired per-episode differences and season/Gameweek-aware uncertainty, `src/evaluation/calibration.py` for forecast error and reliability summaries, and `src/evaluation/power.py` for the minimum effect the current sample can reasonably detect. Extend the decision outcome and retrospective schemas so every result retains the frozen proposal hash, baseline provenance, resource use, and whether a comparison is expected, realised, isolated, or longitudinal. Prove the layer with synthetic fixtures and the frozen replay artifacts without modifying those artifacts.

Milestone two completes evidence attribution. Allow `FPL-98p` to finish its GW12 contract, then extract a reusable isolated-fork runner for other Gameweeks. Every evidence item must be timestamped before the deadline and every adjustment must cite its source, confidence, expiry, and affected feature. Run isolated forks first; run a longitudinal evidence arm separately so state compounding is visible rather than mixed into single-week attribution.

Milestone three creates a player-event challenger. Keep the v1 model unchanged, introduce a new versioned configuration, and calibrate the event components only on seasons or earlier Gameweeks available before the evaluated deadline. Compare event-level probability metrics, player-point calibration, selected-player calibration, and downstream decision value. Promotion requires improvement outside the calibration sample and no leakage-gate failure.

Milestone four fixes team context. Model attacking and defensive strength separately so a strong attack changes scoring expectations while a strong defence changes opponent scoring and clean-sheet expectations. Combine timestamp-safe xG/xGA, Elo, and registered pre-deadline odds with explicit missing-feed degradation. Test promoted teams and transfers as cold-start cases.

Milestone five models availability and the whole 15-player squad. Replace a single expected-minutes scalar in the decision objective with a bounded appearance distribution sufficient to value a starter playing zero, under 60, or at least 60 minutes. Compute legal automatic-substitution expectation in bench order, goalkeeper contingency, formation constraints, and vice-captain fallback. Keep the official realised scorer unchanged; this milestone changes planning value, not FPL scoring rules.

Milestone six makes selection robust. Shrink extreme forecasts according to measured reliability, evaluate multiple calibrated scenarios, and penalise decisions that depend on a fragile ordering of near-equal players. Report the unshrunk objective, robust objective, and decision sensitivity so conservatism remains observable rather than hidden.

Milestone seven implements a three-to-six-week receding-horizon transfer planner. “Receding horizon” means planning several future weeks but executing only the first move before forecasting again at the next deadline. The state must include squad, purchase and selling prices, bank, free transfers, hits, fixtures, availability, and chip effects. Compare it with the v1 one-week bridge on identical starting states and record both immediate and trajectory value.

Milestone eight implements chips through `FPL-q8s`, using the multiweek planner to price the opportunity cost of Wildcard, Free Hit, Bench Boost, and Triple Captain. The existing GW31 Free Hit case is a focused legality and state-restoration test, not a hindsight rule.

Milestone nine adds a captain-specific decision model using expected points, start probability, ceiling distribution, vice-captain contingency, and uncertainty. Captain-only counterfactuals must keep transfers and lineup fixed so their value is attributable.

The final milestone runs the challenger matrix on sealed 2025/26 episodes and live-like shadow inputs. It reports forecast calibration, realised paired effects, uncertainty, latency, peak memory, cost, degradation, and safety failures. Promotion to the 2026/27 shadow policy requires a predeclared rule; no model is selected only because it achieved the highest retrospective total.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Before starting each Bead, run:

    powershell.exe -Command "cd 'C:\Users\Alastair\FPL'; & 'C:\Users\Alastair\AppData\Local\beads\bin\bd.exe' list --status in_progress --json"

Claim only an open Bead whose declared files do not overlap another in-progress Bead. Record progress as implementation proceeds.

For the measurement milestone, run the focused tests:

    python -m pytest tests/test_benchmark_evaluation.py -q

Then run the complete suite:

    python -m pytest -q

For later challengers, first run the relevant focused test directory, then the complete suite, then a paired replay command documented by that milestone. All generated challenger reports must use a new output directory and must not overwrite `reports/benchmarks/2025-26/`.

## Validation and Acceptance

The measurement milestone is accepted when a synthetic set of episode pairs produces the exact known mean difference, sample standard deviation, confidence interval, effect size, and minimum detectable effect; schemas reject a result whose proposal or baseline provenance is missing; expected-point proxies are labelled and cannot be presented as realised gains; and the full repository test suite passes.

Each forecast milestone is accepted only when its configuration is versioned, its training and evaluation windows are explicit, its inputs obey the deadline gate, and paired reports show calibration for all players, owned players, selected XI players, and the resulting decisions. Each optimisation milestone must demonstrate legal decisions, exact state transitions, deterministic reruns, and decomposition against feasible hold, lineup, captain, bench, transfer, or chip alternatives.

The final programme is accepted when the frozen v1 control and all eligible challengers can be replayed from the same episode hashes, the report explains statistical and practical uncertainty, and one configuration can be nominated for 2026/27 live shadow use without changing the historical control.

## Idempotence and Recovery

All measurement commands are read-only with respect to sealed control artifacts. Generated reports use new versioned directories and can be regenerated from hashes. New challengers are additive. If a challenger fails, leave v1 unchanged, record the failed result, and resume from the last passing milestone. Never repair a failing comparison by editing a historical episode or revealed outcome.

## Artifacts and Notes

The initial control result is:

    season: 2025-26
    Gameweeks: 38
    active structured arms: 2010 points
    naive baseline: 1990 points
    paired season difference: +20 points

This season-level number is descriptive, not proof of superiority. The evaluation layer must preserve Gameweek-level pairs and uncertainty.

## Interfaces and Dependencies

`src.evaluation.paired_metrics` must expose a deterministic function that accepts episode-level paired observations and returns count, mean and median difference, sample standard deviation, standard error, confidence interval, standardised effect, wins, ties, and losses. It must support cluster identifiers without treating repeated observations as independent.

`src.evaluation.calibration` must accept prediction/actual records and return bias, mean absolute error, root mean square error, correlation when defined, and calibration bins. It must preserve named cohorts such as all available players, owned squad, and selected XI.

`src.evaluation.power` must expose a normal-approximation minimum-detectable paired effect using sample size, observed standard deviation, significance level, and target power. It must describe the approximation and return `null` rather than invent precision when the sample is insufficient.

`src.reporting.baseline_comparison` must distinguish expected proxies from realised feasible counterfactuals in both data and text. A realised comparison must include the baseline plan identifier and hash, the evaluated plan identifier and hash, identical episode identity, and the scoring provenance.

The implementation uses the repository’s existing Python standard library, NumPy, pandas, JSON Schema, and pytest dependencies. No new package is required.

Plan revision note (2026-07-25): Created the initial self-contained programme after the completed 2025/26 replay review. The order deliberately begins with evaluation and preserves the v1 replay as immutable control.

Plan revision note (2026-07-25): Completed the evaluation foundation, recorded the GW1 cold-start artifact difference, and added measured control-review and test evidence.

Plan revision note (2026-07-25): Completed the event challenger experiment. Recorded its mixed cohort result and rejection so later team-context and robustness work can address the mechanism without silently promoting it.

Plan revision note (2026-07-26): Completed the separate team-context experiment. Recorded its governed source policy, pre-2025/26 calibration, and rejection so the live policy does not inherit a team-level model that degrades player decisions.


Plan revision note (2026-07-25): Completed the probabilistic squad-contingency slice with a pre-2024/25 calibrated appearance model, exact ruleset-driven bench legality, opt-in solver decomposition, adapter plumbing, and unchanged control/scoring behaviour.

Plan revision note (2026-07-26): Completed the robust-selection slice with reliability-aware upper-tail shrinkage, residual scenarios, raw-versus-robust solver reporting, locked 2024/25 promotion gates, and a deliberately qualified 2025/26 diagnostic.

Plan revision note (2026-07-26): Completed the isolated captain/vice slice, preserved exact squad/transfer/XI/bench attribution, and rejected the position-residual challenger under its locked validation rule.

Plan revision note (2026-07-26): Began the chip-policy milestone after tracing the existing rules, scorer, and longitudinal transition contracts. Added the declared candidate and reserve-value design before opening GW31 outcomes.

Plan revision note (2026-07-26): Completed the GW31 chip implementation and sealed evaluation. Recorded the no-chip policy decision, tempting but inadmissible realised chip gains, exact Free Hit restoration, high historical schedule uncertainty, and the remaining full-suite publication gate.

Plan revision note (2026-07-26): Completed the taken-over GW12 evidence experiment, adding feasibility-labelled score ceilings and a full independent continuation. The result now distinguishes direct evidence attribution (+14) from longitudinal compounded value (+4).

Plan revision note (2026-07-26): Generalised the evidence experiment into a reusable multi-bundle programme. Added deadline rejection, isolated no-state-advance attribution, one independent longitudinal chain, canonical tree protection and an explicit direct-versus-compounding decomposition.

Plan revision note (2026-07-26): Completed the final challenger matrix and full legal robust replay. Preserved every rejected and exploratory result, recorded robust selection's -19 isolated result, bound operational profiles, and nominated it only for observation-only live shadow with the frozen control unchanged.
