# 05 — Monte Carlo simulation layer

Status: resolved
Type: task
Track: Phase 2 (distributional forecasting)
Blocked by: 02

Activation gate: Phase 2 authorised by owner on 4 August 2026 (tickets 04–05).

## Context

Plan §11.3 component 4 calls for distributions, but no simulation exists anywhere in `src/forecasting/`. Downstream consumers see deterministic expected points plus a q80 shrinkage band (`reliability_shrinkage.py`). Captaincy risk, chip EV and hit decisions all change under full distributions with intra-team correlation.

## Scope

- Sample per-player outcomes by composing existing pieces: appearance distribution (`appearance_distribution.py`) × event rates (`player_events.py`) conditioned on shared team scorelines from the Elo/team-context model, so teammates' clean sheets and goals are correlated.
- Score sampled events through the season-aware scoring engine (`src/scoring/engine.py`) — never through hard-coded points.
- Emit P10/P50/P90 per player and full plan-level distributions for candidate plans; seed-controlled for reproducibility.
- Calibration check against a finalised historical GW sample using existing evaluation utilities.

## Done when

- The GDR's projections summary carries P10/P50/P90 and each candidate plan carries a points distribution, reproducible from a recorded seed; calibration is documented under `reports/forecasting/`.

## Boundaries

Keep it deterministic-given-seed and cheap enough for replay volumes (§17.6). No ML fitting required in this ticket — composition of existing calibrated pieces is the deliverable.

Improving the underlying fitted forecast components is a separate concern
(ticket 17); simulation must not disguise weak or uncalibrated marginals.

## Answer

Implemented:

- `src/forecasting/monte_carlo.py` — appearance × per-90 rates on shared
  Poisson scorelines; scoring exclusively via `score_match_stats`; seed-stable
  P10/P50/P90; plan distributions with captain multiplier
- `run_gameweek(..., monte_carlo=...)` / `--monte-carlo` attaches distributions
  to GDR `projections_summary` and `candidate_plans[].points_distribution`
- Adapter plans now expose `starting_xi` / `captain_id` for simulation attach
- Calibration smoke under `reports/forecasting/monte-carlo-calibration.{json,md}`
- Schema: `control/schemas/decisions/simulation_runs.json` gains `seed` +
  player percentiles

Tests: `tests/forecasting/test_monte_carlo.py` and the Monte Carlo integration
case in `tests/integration/test_run_gameweek.py`.
