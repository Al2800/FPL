# Squad contingency planning policy

## Purpose

`probabilistic_v1` changes planning value, not FPL scoring. It lets the
single-Gameweek optimiser value all 15 squad places when a nominal starter
might record zero minutes. The official realised scorer remains the sole
authority after outcomes are revealed.

The policy is opt-in. Existing solver inputs omit
`squad_contingency_policy` and therefore retain the previous output shape,
objective and fingerprints.

## Appearance states and calibration

Each player has three mutually exclusive Gameweek states:

- `zero`: no minutes and therefore eligible to be replaced;
- `under_60`: an appearance from one to 59 minutes;
- `60_plus`: at least 60 minutes.

The versioned model is
`control/models/appearance-distribution-v1.json`. Its input is the
deadline-safe start probability already produced by the forecast. Five fixed
probability bins were fitted on 2022/23 and 2023/24 player-Gameweeks with a
Dirichlet `(1, 1, 1)` prior. No 2024/25 or 2025/26 observation was used to
select the bins or their probabilities.

On the locked 2024/25 validation season (27,231 player-Gameweeks):

| Metric | Uncalibrated reference | Calibrated v1 |
|---|---:|---:|
| Multiclass Brier score | 0.37164044 | 0.36219467 |
| Log loss | 0.67668515 | 0.66324414 |

The observed state frequencies were 58.02% zero, 13.55% under 60, and
28.43% 60-plus. The calibrated mean predictions were 58.28%, 12.30%, and
29.42% respectively.

For a Double or larger Gameweek, the per-fixture distribution is compounded:
`P(zero in GW) = P(zero per fixture)^n`; `under_60` means at least one
appearance but no 60-plus appearance; `60_plus` means at least one 60-plus
appearance. This independence assumption is explicit and should later be
tested against fixture-specific availability.

## Planning calculation

The nominal XI expected points remain unchanged. Expected contingency value
is additive:

```text
planning value
  = nominal XI expected points
  + captain multiplier value
  + expected vice-captain fallback
  + expected legal goalkeeper/outfield substitutions
  + Bench Boost bench points when active
```

Captain fallback is valued only when the captain records zero minutes.
Vice-captain expected points are already unconditional, so the additional
fallback term is `P(captain zero) * vice expected points` (twice that
increment for Triple Captain's extra multipliers).

For outfield substitutions, a dynamic programme first computes the
probability of every `(missing DEF, missing MID, missing FWD)` state.
The three outfield bench appearance masks are then evaluated in bench order.
A structural lookup accepts the earliest maximum-size subset that can replace
missing starter positions while satisfying the active ruleset's formation
bounds. Goalkeepers are valued separately and can replace only the starting
goalkeeper.

The expected points of a bench player conditional on appearing are derived as
`unconditional expected points / P(appears)`. This preserves the forecast's
unconditional player total while avoiding double-discounting the player's
appearance chance.

## Chips

- With Bench Boost, all four bench projections count directly and automatic
  substitution value is zero.
- Triple Captain changes only the additional captain/fallback multiplier.
- Wildcard and Free Hit do not alter this one-Gameweek contingency
  calculation.

## Determinism and performance

Formation legality is sourced from the loaded versioned ruleset. Structural
substitution results are cached by formation, missing-position counts, bench
position order and appearance mask; player identities and point forecasts
are not part of that cache.

On the committed 123-candidate golden transfer search, the first implementation
took 65.09 seconds. Reusing player distributions and the isomorphic structural
lookup reduced the same run to 5.49 seconds with the same selected objective.
This is acceptable for weekly advisory execution, but should be profiled again
when the receding-horizon planner is introduced.

## Limitations and promotion boundary

- Appearance states are calibrated against the current rolling start feature,
  not a future confirmed-lineup feed.
- Under-60 and 60-plus states improve calibration and diagnostics; automatic
  substitution eligibility depends only on zero versus any appearance.
- Player appearances and captain/vice availability are treated as independent.
  Correlated rotation, postponement, and team-wide illness are not modelled.
- Conditional points use the existing expected-points forecast rather than a
  separate state-conditional event model.
- The lineup selector evaluates every legal formation and all six outfield
  bench orders, but retains the existing expected-points-ranked starter subset
  within each position. Robust selection is a later bead.

This policy may enter a historical challenger replay, but it must not replace
the frozen control merely because it increases expected planning value.
Promotion requires realised paired decision evidence under the benchmark
protocol.
