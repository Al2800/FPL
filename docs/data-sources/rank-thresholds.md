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

## 2025/26 status

The 2025/26 artifact contains one explicit `unavailable` row for each of
GW1–GW38. This is intentional and now covered by the formal decision in
`docs/data-sources/historical-rank-source-decision.md`: **permanent unavailable
for 2025/26**. Collection remains disabled. The artifact must not be replaced
by a scrape, an average-score estimate, or a post-finalisation reconstruction.

Prospective 2026/27 Overall-league capture is out of scope here; see ticket 04.

## Validation

```bash
python3 -m pytest -q tests/evaluation/test_rank_calibration.py
```
