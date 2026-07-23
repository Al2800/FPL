# Complete the structured replay forecast before genuine replay

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current. It follows `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

The current replay forecast uses prior total points, starts, minutes and longitudinal EPL Elo. It is materially safer than copying GW1 points, but it leaves governed lagged event data unused and can carry a club's old EPL rating across seasons spent outside the league. After this change, the calibration report will show whether xG/xA and scoring-event decomposition, plus a recent-minutes trajectory, add predictive value over the existing points-per-90 model. A re-promoted club will receive the calibrated promoted fallback unless it appeared in the immediately preceding EPL season.

The user can inspect one locked 2024/25 ablation report and one still-sealed GW2 comparison. The accepted model must be chosen on 2022/23–2023/24 only. The 2024/25 validation is opened once for reporting, and no 2025/26 outcome is read.

## Progress

- [x] (2026-07-24 00:22Z) Created and claimed `FPL-cv1`; confirmed no conflicting in-progress bead.
- [x] (2026-07-24 00:24Z) Identified the current gaps: xG/xA/event columns are loaded but unused, recent minutes are reduced to cumulative starts, whole-market metrics mix inactive players with decisions, and historical Elo ratings do not expire after relegation.
- [x] (2026-07-24 00:30Z) Added leakage-safe event and recent-minutes calibration cases with zero-weight ablations.
- [x] (2026-07-24 00:31Z) Added immediate-prior-season recency to the team prior; Burnley, Leeds and Sunderland now use the promoted fallback.
- [x] (2026-07-24 00:33Z) Selected on 2022/23–2023/24 and reported locked 2024/25 all-market/actionable metrics; events were rejected and recent minutes selected.
- [x] (2026-07-24 00:34Z) Regenerated sealed GW2: maximum 8.78 EP, Salah captain, no hit, 3.10 EP two-transfer uplift.
- [x] (2026-07-24 00:39Z) Passed 333 tests, reproduced calibration/GW2 artifacts and hashes, documented the result, and prepared the bead for close and push.

## Surprises & Discoveries

- Observation: the local vaastav corpus contains `expected_goals`, `expected_assists`, `expected_goal_involvements` and `expected_goals_conceded` from 2022/23 onward, but `src/forecasting/live_faithful.py` uses only total points per 90.
  Evidence: the pinned 2022/23–2024/25 `merged_gw.csv` schemas contain those fields; the live composer calculates one posterior `points_per_90`.

- Observation: EPL absence is not represented in the current ratings dictionary.
  Evidence: `fit_longitudinal_elo` retains every historical team key, so Leeds and Burnley are treated as returning rated teams in 2025/26 even though they were absent from the immediately preceding EPL season.

## Decision Log

- Decision: event decomposition remains an ablation, not a mandatory sophistication upgrade.
  Rationale: a more detailed formula can be worse or miscalibrated. Training selects an event weight including zero; if zero wins, the event component is rejected and the evidence is retained.
  Date/Author: 2026-07-24 / Codex.

- Decision: actionable-player evaluation uses only information known before the target Gameweek.
  Rationale: filtering on realised target minutes would leak. The actionable pool is defined from prior start probability, prior/current minutes and known market state.
  Date/Author: 2026-07-24 / Codex.

- Decision: any club absent from the immediately preceding EPL season receives the promoted fallback even if an older rating exists.
  Rationale: a stale multi-season rating is not evidence of current top-flight strength. Lower-division evidence is not registered for this replay, so the explicit calibrated fallback is safer.
  Date/Author: 2026-07-24 / Codex.

## Outcomes & Retrospective

Implementation is in progress. The accepted outcome may be a richer model or a documented rejection of one or both candidate components. Either result improves the benchmark because the choice will be time-ordered and reproducible.

The structured-data gate is satisfied. Event decomposition was rejected by training selection at weight zero, avoiding unjustified complexity. Recent minutes was selected at 0.5 and improved locked validation error, including the actionable pool. Promoted-team recency corrected stale Leeds and Burnley ratings. The remaining GW2 issue is transfer option value, already scoped as `FPL-k21`.

## Context and Orientation

The repository is `C:/Users/Alastair/FPL`. `src/forecasting/calibrate_live_faithful.py` converts completed prior-season rows and strictly earlier target-Gameweek history into fixed calibration cases. `scripts/calibrate_live_faithful_forecast.py` selects parameters using target seasons 2022/23 and 2023/24, then evaluates once on 2024/25. `src/forecasting/live_faithful.py` applies the chosen model to a content-addressed historical feature state. `src/forecasting/team_prior.py` carries Elo ratings across EPL seasons and constructs cutoff-safe fixture multipliers. `scripts/prepare_live_faithful_gw2.py` creates a comparison without reading `hidden-outcome.json`.

An ablation is a controlled version with one component removed. Here the event weight may be zero, and the recent-minutes weight may be zero. Comparing those candidates tells us whether each component helps rather than assuming it does.

## Plan of Work

Extend season loading to preserve goals, assists, xG, xA, clean sheets, saves, bonus and cards, using zero only when a source season genuinely lacks the field and recording that limitation. Aggregate target rows by player and Gameweek before shifting, so two fixtures sharing a deadline remain one information period. Build prior and strictly lagged current event rates.

Calculate an interpretable event projection from expected appearance points, position-specific goal value, assists, clean sheets, saves, bonus and card deductions. Blend it with the reliability-shrunk points-per-90 projection using a training-selected weight that includes zero. Add the prior three-Gameweek minutes-per-fixture trajectory and a training-selected blend weight that includes zero.

Report metrics over the full known market and an actionable pool defined only from predeadline variables. Include early Gameweeks 2–5, MAE, RMSE, expected-minutes MAE, start Brier score, top-15 precision and forecast maxima.

Track each team's last active EPL season. At the start of a new season, reset entrants absent from the immediately previous EPL season to the promoted rating. The episode prior must receive the immediately previous season's active-team set and mark Leeds, Burnley and Sunderland as fallbacks for 2025/26.

Regenerate calibration to new immutable artifact names and build a new sealed GW2 comparison. Preserve prior rejected artifacts. Do not freeze a plan or inspect outcomes.

## Concrete Steps

From `C:/Users/Alastair/FPL`, run:

    .\.venv\Scripts\python.exe -m pytest tests\forecasting\test_live_faithful_calibration.py tests\forecasting\test_live_faithful_forecast.py tests\forecasting\test_team_prior.py -q

Run the time-ordered calibration with the pinned source:

    .\.venv\Scripts\python.exe scripts\calibrate_live_faithful_forecast.py --source-commit f2090d378ebd1b0c3d14884770dde95f38c50a0d

Regenerate only sealed GW2 setup:

    .\.venv\Scripts\python.exe scripts\prepare_live_faithful_gw2.py

Then run:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

A synthetic future-event mutation must not change any earlier calibration case. Double Gameweek events must aggregate before lagging. Setting event weight to zero must reproduce the points-rate ablation. Setting recent-minutes weight to zero must reproduce the existing minutes calculation.

The report must distinguish all-market from actionable-pool metrics without using target outcomes to define the pool. It must say whether each component was selected or rejected.

A team present historically but absent from the immediately preceding EPL season must receive the promoted fallback. The final sealed GW2 team prior should list Leeds, Burnley and Sunderland as fallbacks, not only Sunderland.

All forecast, configuration, calibration and comparison content hashes must reproduce. The GW2 artifact must explicitly contain no hidden outcome, validated plan or state transition.

## Idempotence and Recovery

Builders remain pure over caller-supplied data. Generated artifacts use new versioned names and refuse to overwrite differing files. Existing calibration and rejected GW2 evidence remains untouched. Raw approved data is gitignored and read-only.

## Artifacts and Notes

The baseline to beat or consciously trade off is the reliability model: locked 2024/25 GW2–5 MAE 1.393, RMSE 2.039, top-15 precision 0.25; sealed GW2 maximum 8.89 EP and Salah captain. Whole-market raw rolling MAE remains lower at 1.135, so metrics must remain segmented and honestly reported.

## Interfaces and Dependencies

No new package is required. Continue using pandas, NumPy, PyYAML and the repository's hashing utilities.

`ForecastParameters` in `src/forecasting/calibrate_live_faithful.py` will add declared `event_model_weight` and `recent_minutes_weight` fields. The live model configuration must carry the selected values.

`build_episode_team_prior` in `src/forecasting/team_prior.py` will accept `previous_active_teams: set[str]` (or an equivalent serialisable collection) and use it to distinguish a returning club from a re-promoted club.

Revision note (2026-07-24): Initial plan created after the owner approved a final structured-data completeness gate before transfer-option-value work and genuine replay.
