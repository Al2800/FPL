# WP-05 — Baseline forecasting

**Status:** Evaluation contract corrected; local multi-season report must be regenerated
**Code:** `src/forecasting/`
**Eval script:** `python3 -m scripts.run_wp05_eval`
**Results:** [`baseline-eval.json`](baseline-eval.json)

> `baseline-eval.json` was produced by the earlier v0.1 definitions. It remains
> as historical evidence but must not be quoted as a result from the corrected
> v1 evaluation until it is regenerated from the local, gitignored datasets.

## Baselines (plan §11.2)

| Baseline | Module | Metric (mean across 3 seasons) |
|---|---|---|
| Naive start-prob (“started last GW”) | `minutes.py` | Brier, log-loss and calibration; target is recorded starting XI |
| Rolling start-prob | `minutes.py` | Brier, log-loss, ECE and calibration table |
| Expected minutes (rolling × 75) | `minutes.py` | MAE reported per season |
| Goal / assist / clean-sheet events | `player_events.py` | Binary Brier, log-loss, ECE and calibration tables |
| Rolling points / fixture adjustment | `player_events.py` | MAE for raw and prior-round walk-forward adjustment |
| Elo team-strength | `team_strength.py` | Three-way multiclass log-loss and Brier |
| Odds-implied 1X2 | `odds_implied.py` | Multiclass log-loss; timing labelled separately |
| Official `ep_next` / FDR | — | **Deferred** — needs pre-deadline snapshots (not in vaastav `xP`) |
| World Cup fatigue prior | `minutes.apply_world_cup_prior` | Priors CSV joined by `fpl_code`; no historical WC season to back-test yet |

## Time-based discipline

- Player features use lagged starts, minutes, points and events
  (`add_lagged_features`); same-GW `xP` / `total_points` are never inputs.
- Starting XI is taken from an explicit `started`, `starts` or `is_starting`
  field. Missing start data remains unknown and is never inferred from a
  60-minute threshold.
- Fixture multipliers for a Gameweek are estimated from completed prior rounds;
  outcomes from that Gameweek cannot alter its own multiplier.
- Elo ratings update walk-forward; each match uses only pre-match ratings.
- Odds rows are labelled `closing_or_unspecified` (football-data.co.uk) — not guaranteed pre-deadline.

## Calibration notes

- The earlier start-probability figures used a minutes-threshold target and are
  superseded pending regeneration against recorded starts.
- The fixed home/away ×1.05/0.95 multiplier has been removed. The replacement is
  estimated walk-forward and its MAE is reported beside the unadjusted baseline.
- Goal, assist and clean-sheet expected counts are converted to at-least-one
  probabilities before proper scoring and calibration.
- Elo now allocates positive probability to draws and normalises the complete
  home/draw/away distribution before scoring.
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
5. Regenerate `baseline-eval.json` from the governed local datasets under the
   corrected v1 definitions.
