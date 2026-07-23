# Build and lock the live-faithful early-season forecast

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

The historical replay currently reaches the opening of Gameweek 2 with correct squad, finance, rules, fixture and outcome-sealing behavior, but its expected-points baseline simply carries one realised Gameweek forward. After this change, the structured engine will produce a transparent early-season forecast from a point-in-time player prior, expected minutes, current-season evidence and team/fixture strength. It will retain the raw rolling forecast as an ablation, which means a deliberately simpler comparison model used to measure whether the richer components add value.

The model specification and its weights will be selected using seasons before 2025/26. The sealed 2025/26 replay remains the test season and must not be used to tune the model after individual outcomes are inspected. A user can observe the result by preparing Gameweek 2: the setup report will show raw-rolling and live-faithful forecasts side by side, their component lineage and calibration version, and the transfer/captain decision produced by each. No Gameweek 2 outcome is read or frozen during this work.

## Progress

- [x] (2026-07-23 23:20Z) Paused `FPL-bsw.13` with GW2 sealed, claimed `FPL-5iu`, and created `FPL-dnr` for 2026/27 launch-prior and timestamped-odds capture.
- [x] (2026-07-23 23:24Z) Mapped the existing rolling feature state, expected-minutes, player-event, walk-forward Elo, odds and evaluation modules.
- [x] (2026-07-23 23:24Z) Recorded the current GW2 baseline: 102,391 candidates; 68 no-transfer objective; 110 selected objective; three transfers and a four-point hit; Ballard captain at 17 EP.
- [x] (2026-07-23 23:46Z) Defined the versioned point-in-time prior and forecast-component contracts, including fail-closed content and cutoff lineage.
- [x] (2026-07-23 23:50Z) Added tests for shrinkage, expected-minutes integration, position/price fallbacks, bounded team adjustments, blanks/doubles, optional-feed degradation and explicit replay-view selection.
- [x] (2026-07-23 23:50Z) Implemented the completed-season player-prior builder and pure live-faithful forecast composer without changing the raw rolling ablation.
- [x] (2026-07-24 00:03Z) Built the pinned pre-2025/26 calibration set, trained on 2022/23–2023/24 and opened 2024/25 once as locked validation.
- [x] (2026-07-24 00:08Z) Rebuilt sealed GW2 with raw and reliability-calibrated outputs; rejected the sparse-prior candidate, retained the corrected comparison, and kept the decision unfrozen.
- [x] (2026-07-24 00:09Z) Documented 2026/27 parity; immutable launch inputs and fixed-interval odds capture remain tracked by `FPL-dnr`.
- [x] (2026-07-24 00:11Z) Passed 329 tests and prepared the reviewed artifact set for commit/push; GW2 remains unfrozen pending `FPL-k21`.

## Surprises & Discoveries

- Observation: richer forecast modules already exist but are not joined to replay features.
  Evidence: `src/forecasting/minutes.py`, `player_events.py`, `team_strength.py` and `odds_implied.py` implement and evaluate separate baselines. `src/orchestration/historical_feature_state.py` still defines expected points solely as the mean of the last three completed Gameweek totals.

- Observation: expected minutes is carried to the solver input but does not affect the solver objective.
  Evidence: `src/forecasting/replay_adapter.py` emits `expected_minutes` and `start_probability`; `src/optimisation/solver.py::_objective` sums only `expected_points`, captain points, hits and active Bench Boost points.

- Observation: the repository inventory says raw 2016/17–2025/26 vaastav and 2015/16–2024/25 football-data files existed under `/workspace/data/raw`, but those raw files are not present in the current Windows workspace or WSL filesystem.
  Evidence: `docs/data-sources/data-estate/inventory.json` records 305,809,764 bytes, while `C:/Users/Alastair/FPL/data` currently contains only frozen benchmark/live-shadow data and `wsl.exe` reports no `/workspace/data/raw`.

- Observation: the frozen 2025/26 football-data file contains opening and closing columns, but neither is accepted as pre-FPL-deadline evidence because the row has no quote timestamp.
  Evidence: `control/manifests/datasets/benchmark-v0.json` excludes football-data odds without a timestamp before the FPL deadline. Odds remain a diagnostic comparator for historical replay and a live capture requirement in `FPL-dnr`.

- Observation: separating a forecast view from the chronological feature state gives a clean ablation boundary.
  Evidence: `src/forecasting/replay_adapter.py` now defaults to the unchanged rolling projection and uses a richer view only when its full player market, feature-state lineage and content hash validate.

- Observation: whole-market MAE overweights inactive zero-point players relative to the optimiser's ranking problem.
  Evidence: on locked 2024/25 GW2–5, raw rolling MAE is 1.135 versus 1.393 for the reliability model, while reliability improves RMSE from 2.237 to 2.039 and top-15 precision from 0.15 to 0.25. Promotion is recorded as a ranking/large-error trade-off, not an MAE win.

- Observation: individual per-90 priors require their own sample reliability shrinkage.
  Evidence: the first sealed candidate captained Vitor Reis and selected marginal players. Adding a training-selected 450-minute cohort shrinkage produces a maximum 8.89 EP and Salah captain without inspecting GW2 outcome.

- Observation: after forecast correction, transfer option value is the next material policy gap.
  Evidence: the corrected single-GW solver spends two free transfers for 3.36 immediate EP because banking has no future objective value. `FPL-k21` tracks this separately.

## Decision Log

- Decision: 2025/26 is an untouched test season, not a source of fitted weights.
  Rationale: repeatedly choosing parameters after viewing 2025/26 Gameweek outcomes would optimize the benchmark for the answer already known. Earlier seasons will train/calibrate the fixed specification; 2025/26 will exercise chronology, state and final decision quality.
  Date/Author: 2026-07-23 / Codex.

- Decision: preserve `historical-rolling-v1` unchanged as an explicit ablation and introduce a separately versioned live-faithful model.
  Rationale: the raw baseline is useful evidence of cold-start chasing. Replacing it in place would erase the comparator and make model-value attribution harder.
  Date/Author: 2026-07-23 / Codex.

- Decision: required components fail closed; optional market/evidence components degrade visibly.
  Rationale: player priors, minutes, fixture and team-strength lineage are core to a meaningful forecast. Timestamped odds and historical unstructured evidence are incomplete, so their absence must not invent values or prevent the structured replay.
  Date/Author: 2026-07-23 / Codex.

- Decision: use the stable FPL player `code` to bridge previous-season priors where available.
  Rationale: season-specific element IDs change. The frozen identity map already records `fpl_code`, which is the safest existing cross-season player key. Players without a match receive a declared fallback rather than a name-based guess.
  Date/Author: 2026-07-23 / Codex.

- Decision: do not download the missing historical files without explicit current-session authorization.
  Rationale: the machine policy requires sign-off for downloads. Implementation and fixture-based tests can proceed; real calibration and GW2 regeneration require the exact registered vaastav 2022/23–2024/25 and football-data 2019/20–2024/25 files or an approved equivalent.
  Date/Author: 2026-07-23 / Codex.

- Decision: ship the initial coefficients only as `provisional_pending_calibration`.
  Rationale: executable contracts and synthetic tests need concrete values, but those values have not passed the earlier-season train/locked-validation procedure. The model status is carried into every solver player and cannot be confused with a promoted benchmark model.
  Date/Author: 2026-07-23 / Codex.

## Outcomes & Retrospective

The cold-start forecast objective is complete. Registered sources were restored at vaastav commit `f2090d378ebd1b0c3d14884770dde95f38c50a0d` and fingerprinted. The model was trained before 2024/25, validated once on 2024/25, and applied to sealed GW2 without reading its outcome. Reliability shrinkage corrected both the raw GW1-chasing failure and a sparse-prior failure found during setup review.

The corrected GW2 proposal remains intentionally unfrozen. The forecast now yields plausible magnitude/captaincy and no hit, but the optimiser spends two free transfers for 3.36 one-week EP because it lacks banked-transfer option value. That is a new, separately scoped policy task (`FPL-k21`), rather than grounds to retune the forecast against GW2.

## Context and Orientation

The project lives at `C:/Users/Alastair/FPL`. A historical episode is an immutable Gameweek decision bundle under `data/benchmark-v0/episodes/v2/2025-26/gw-NN`. Its observed partition contains only information available before that Gameweek deadline; its hidden outcome must not be opened until a proposal is frozen.

`src/orchestration/historical_feature_state.py::build_feature_state` advances the observed player history. It aggregates Double Gameweek rows before lagging, carries market quotes through blanks and records content hashes. Its only supported model, `historical-rolling-v1`, averages the last three completed Gameweek point totals. At GW2 only one total exists.

`src/forecasting/replay_adapter.py::build_replay_solver_input` converts a feature state and one arm-owned policy state into the deterministic optimiser input. `src/optimisation/solver.py::solve` searches legal transfer sets and lineups under the active rules. The sealed GW2 setup in `reports/benchmarks/2025-26/gw-02/setup` proves all five arms currently receive identical structured engine data.

A player prior is the forecast before current-season evidence is observed. The new model will attach a prior expected event rate and expected minutes to each current FPL player. A matched returning player uses previous-season history bridged by FPL `code`. A promoted-team player or a player without an admissible previous-season match uses a position/price/team fallback with an explicit reason and uncertainty. Shrinkage means combining a prior sample with current observations so that one match cannot fully replace the prior. Expected points are then calculated from expected minutes, player event rates and fixture/team probabilities rather than copied directly from realised FPL totals.

Team strength will initially come from the repository's own walk-forward results model, not an unreviewed external rating. An Elo rating is a numerical estimate updated after each result; walk-forward means a fixture uses ratings calculated strictly before that fixture. A Poisson goal model represents each team's goals as a count distribution and converts attack/defence strength into expected goals and clean-sheet probabilities. Historical odds remain a labelled comparator unless a quote timestamp proves it was known before the FPL deadline.

## Plan of Work

First add a versioned model configuration and data contracts. The model configuration will state the prior season, equivalent-match shrinkage weight, price/position fallback parameters, minutes calculation, team-strength parameters, fixture adjustment bounds and optional-component policies. Every produced player forecast will include raw rolling EP, live-faithful EP, expected minutes, component values, prior source/fallback reason, sample sizes and the hashes of model/data inputs.

Add a prior builder in a focused module under `src/forecasting/`. It will accept previous-season player rows and their identity data as caller-supplied immutable inputs rather than reaching into global raw directories. It will aggregate player rates only from completed prior-season data and join by FPL code. It will calculate position and launch-price fallback groups using training data, cap implausible rates and expose promoted/new-player uncertainty explicitly. No name-only automatic join is permitted.

Add a team-strength builder that consumes match results strictly earlier than the episode cutoff. Reuse the current walk-forward Elo concepts, but emit home/away expected-goal and clean-sheet components keyed by canonical club. For early-season promoted teams, initialize from their prior-division evidence when supplied; otherwise shrink a declared fallback toward the promoted-team/league mean. The historical episode adapter will accept a prebuilt, hashed team-prior artefact. It will not open football-data odds or current fixture outcomes.

Compose expected points from expected minutes and scoring-event components. The first production candidate should remain interpretable: appearance points from minutes, goal/assist rates by expected minutes and position, team clean-sheet probability, conservative bonus/defensive-contribution residuals, and fixture count. The model may use bounded corrections learned on earlier seasons, but it must not hand-tune a 2025/26 player result.

Build a time-ordered evaluator. Training and parameter selection use seasons no later than 2023/24; 2024/25 is the locked validation season. Report player-week MAE/RMSE, start Brier score, calibration by predicted-points bin, top-k ranking stability, transfer churn and the frequency with which a four-point hit is recommended after one exceptional match. Compare raw rolling, prior-only, prior-plus-minutes, prior-plus-team and full structured variants. Odds are diagnostic-only unless timestamped.

Finally regenerate only the sealed GW2 setup. Persist raw and live-faithful engine inputs/outputs side by side and update the HTML review with their component differences. The setup must still contain no hidden outcome, validated plan or transition. Review the proposal before reactivating the replay bead.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the existing baseline and focused contracts:

    .\.venv\Scripts\python.exe -m pytest tests/test_forecasting_baselines.py tests/historical-replay/test_replay_feature_adapter.py tests/historical-replay/test_gw2_setup.py -q

Add red contract tests and run them until green:

    .\.venv\Scripts\python.exe -m pytest tests/forecasting/test_live_faithful_forecast.py tests/historical-replay/test_replay_feature_adapter.py -q

When registered raw data is available, run time-ordered calibration:

    .\.venv\Scripts\python.exe -m scripts.calibrate_live_faithful_forecast --train-through 2023-24 --validate-season 2024-25

The command must write a versioned report under `reports/forecasting/` and a reviewed configuration under `control/models/`. It must not read 2025/26 outcomes.

Rebuild GW2 only after the configuration is locked:

    .\.venv\Scripts\python.exe -m scripts.prepare_replay_gameweek --season 2025-26 --gameweek 2

Run complete validation:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

A synthetic returning-player test must show that a 17-point first match cannot become 17 EP when a multi-match prior exists. The forecast must reproduce under reordered input rows and its hash must change when any prior, model or team-strength input changes.

Players joined by FPL code must use the correct prior even when their element ID, display name or club changes. An unmatched transferred player must receive a declared fallback and uncertainty; an ambiguous identity must fail closed. A promoted-team player must use a supplied promoted prior or an explicit league-mean shrinkage fallback.

Expected minutes must alter expected points. A likely non-starter with a strong per-90 prior must not be treated as a guaranteed 90-minute player. Blank Gameweeks must produce zero fixture points without removing the player from the market. Double Gameweeks must sum separately projected fixtures without using the first result as evidence for the second.

Team-strength inputs must be cutoff-safe. Changing a post-cutoff result must not change the forecast. Odds without a qualifying timestamp must never enter the production historical forecast.

The locked 2024/25 validation report must compare ablations and demonstrate that the chosen model improves or provides a documented trade-off against raw rolling. If it does not, the richer component is not promoted merely because it sounds plausible.

The regenerated GW2 setup must report both forecasts, their hashes and component lineage. It must contain no hidden outcome, realised outcome, validated plan or state transition. The user reviews the resulting transfer/captain proposal before freeze.

## Idempotence and Recovery

All builders are pure over caller-supplied inputs and write content-addressed JSON. Existing artefacts are verified and reused when identical; a differing existing artefact causes a fail-closed error rather than deletion or overwrite. Raw data remains outside Git and is never modified.

No package installation is required. Missing registered historical data blocks only real calibration and GW2 promotion; it does not justify downloading, substituting a new source or using 2025/26 outcomes without authorization. Synthetic tests and model-contract work remain safe to rerun.

## Artifacts and Notes

The current unstable GW2 decision is retained as evidence:

    raw rolling candidate count: 102,391
    no-transfer objective: 68
    selected objective: 110
    selected transfers: João Pedro -> Wood; Bruno -> Semenyo; Murillo -> Ballard
    selected captain: Ballard, 17 EP
    transfer hit: 4 points

Existing earlier-season evaluation reports rolling-points MAE of 1.1063, 1.0083 and 1.1098 for 2022/23, 2023/24 and 2024/25. Those aggregate metrics do not prove early-season or transfer-decision quality, so the new evaluator must report Gameweek-stratified and decision-level diagnostics.

## Interfaces and Dependencies

No new dependency is planned. Use the existing Python, pandas, NumPy, PyYAML and JSON-schema stack.

Add a stable forecast entry point under `src/forecasting/`, with a caller-supplied contract similar to:

    def build_live_faithful_forecast(
        *,
        feature_state: Mapping[str, Any],
        identity_map: Mapping[str, Any],
        player_prior: Mapping[str, Any],
        team_prior: Mapping[str, Any],
        model_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        ...

The returned object must carry `model_version`, `model_sha256`, `player_prior_sha256`, `team_prior_sha256`, `feature_state_sha256`, component-level player forecasts, limitations and its own `content_sha256`.

The historical feature builder remains responsible for chronological observed history. The new forecast composer reads its output but does not mutate it. The replay adapter will accept a selected forecast view explicitly rather than silently replacing `player["projection"]["expected_points"]`. This preserves the raw rolling ablation and makes arm inputs auditable.

Revision note (2026-07-23): Initial ExecPlan created after the user approved a live-faithful structured forecast and asked that 2026/27 capture lessons be preserved. It records the sealed-GW2 boundary, existing disconnected modules, the missing raw-data prerequisite and the no-2025/26-tuning rule.
