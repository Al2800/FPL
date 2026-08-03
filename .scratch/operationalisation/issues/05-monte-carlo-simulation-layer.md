# 05 — Monte Carlo simulation layer

Status: ready-for-agent
Type: task
Track: B (distributional forecasting)

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
