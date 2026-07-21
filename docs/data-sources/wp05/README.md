# WP-05 — Baseline forecasting

**Status:** Baselines implemented and evaluated on 2022-23 … 2024-25  
**Code:** `src/forecasting/`  
**Eval script:** `python3 -m scripts.run_wp05_eval`  
**Results:** [`baseline-eval.json`](baseline-eval.json)

## Baselines (plan §11.2)

| Baseline | Module | Metric (mean across 3 seasons) |
|---|---|---|
| Naive start-prob (“started last GW”) | `minutes.py` | Brier **0.123** |
| Rolling start-prob | `minutes.py` | Brier **0.099** (beats naive) |
| Expected minutes (rolling × 75) | `minutes.py` | MAE reported per season in JSON |
| Rolling points / fixture adj | `player_events.py` | MAE **~1.07** pts |
| Elo team-strength | `team_strength.py` | Home-win log-loss **~0.61** |
| Odds-implied 1X2 | `odds_implied.py` | Multiclass log-loss **~0.95** |
| Official `ep_next` / FDR | — | **Deferred** — needs pre-deadline snapshots (not in vaastav `xP`) |
| World Cup fatigue prior | `minutes.apply_world_cup_prior` | Priors CSV joined by `fpl_code`; no historical WC season to back-test yet |

## Time-based discipline

- Player features use lagged minutes/points (`add_lagged_features`); same-GW `xP` / `total_points` are never used as inputs.
- Elo ratings update walk-forward; each match uses only pre-match ratings.
- Odds rows are labelled `closing_or_unspecified` (football-data.co.uk) — not guaranteed pre-deadline.

## Calibration notes

- Rolling start-prob improves on naive Brier in all three evaluated seasons → soft minutes history has marginal value before news/line-up sources are added.
- Simple home/away ×1.05/0.95 barely moves points MAE vs raw rolling points — fixture adjustment needs team-strength coupling next.
- Odds multiclass log-loss is the match-outcome reference; player-level odds-implied points need clean-sheet / anytime props (thin historically — CS proxy helper only).
- vaastav same-GW `xP` MAE is reported for curiosity only; it must not be treated as a live `ep_next` benchmark.

## Reproduce

```bash
# Requires local downloads (gitignored):
#   data/raw/vaastav/...  via scripts/download_historical.py
#   data/raw/football-data/E0_*.csv
PYTHONPATH=. python3 -m scripts.run_wp05_eval
PYTHONPATH=. python3 -m pytest tests/test_forecasting_baselines.py -q
```

## Open follow-ups

1. Capture official `ep_next` and FDR in pre-deadline FPL snapshots; add to eval.
2. Map vaastav `team` ↔ football-data club names for player-level Elo/odds join.
3. Back-test WC fatigue multipliers only after 2026/27 GW1–5 outcomes exist.
4. Open Decision 7 (solver) → WP-07 optimiser consuming these expected points.
