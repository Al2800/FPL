# Historical score-to-overall-rank calibration

Rank calibration is a reporting annotation applied after a replay score has
been revealed. It never changes forecasts, transfers, optimisation, chips or
longitudinal manager state.

The contract in `src/evaluation/rank_calibration.py` has three explicit modes:

- `exact`: an approved source supplies an exact rank and `rank_lower == rank_upper`.
- `bounded`: sampled thresholds bracket the score; the returned band is marked
  non-exact and retains the observed support. A score outside support is
  rejected rather than extrapolated.
- `unavailable`: no approved source is available. Rank fields remain null; the
  report says “rank unavailable” rather than inventing a global position.

The 2025/26 artifact currently contains one explicit `unavailable` row for each
of GW1-GW38. This is intentional: the source registry has no approved
historical overall-rank threshold source yet, and no acquisition is enabled.
The artifact carries a SHA-256 over its canonical rows and each row records the
source/derivation state. It must not be replaced by a scrape, an average-score
estimate, or a post-finalisation reconstruction.

Before enabling collection, add a source-registry entry with the exact source,
access date, rights/retention decision, finalisation state, field size, tie
rule, and an immutable artifact hash. The source-acquisition blocker in Beads
tracks that owner decision separately from this downstream evaluator.

Validation:

```powershell
& 'C:\Users\Alastair\FPL\.venv\Scripts\python.exe' -m pytest -q tests/evaluation/test_rank_calibration.py
```
