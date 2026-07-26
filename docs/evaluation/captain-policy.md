# Captain and vice-captain policy

`captain-v1` is an additive captain-only challenger. Every comparison fixes the
canonical transfers, 15-player squad, starting XI and ordered bench. Only the
captain and vice-captain IDs may change. The alternative is then frozen and
scored through the unchanged FPL validator and realised-outcome scorer.

## Model

The control captains the starter with the highest expected points and gives
vice-captaincy to the second highest. The challenger ranks every ordered pair
within the fixed XI.

For captain `c` and vice `v`:

```text
expected extra = EP(c) + P(c gets zero minutes) × EP(v)

policy score =
    expected extra
  + 0.1 × captain position positive-residual q90
  - 0.1 × captain position absolute-residual q80
```

The zero-minute probability comes from the pre-2024/25
`appearance-distribution-v1` calibration. Position residual distributions use
only target seasons 2022/23 and 2023/24. Their frozen values are recorded in
`control/policies/captain-v1.json`.

The expected-points term is unconditional, so the vice contribution is added
only when the captain receives zero minutes. Under-60 captain appearances do
not trigger vice fallback. Double-Gameweek zero probabilities use the existing
appearance-distribution aggregation.

## Selection and held-out gate

The ceiling and uncertainty weights were selected as a balanced non-zero
candidate among policies tied for the best training total. No 2024/25 or
2025/26 outcome was used to retune them.

| Split | Control captain points | Challenger | Delta |
| --- | ---: | ---: | ---: |
| Training: 2022/23 + 2023/24 | 263 | 281 | +18 |
| Locked validation: 2024/25 | 352 | 343 | -9 |

The predeclared rule requires the challenger to exceed control on locked
2024/25. It fails and is therefore rejected before the 2025/26 replay is
examined.

## Sealed 2025/26 result

The report is
`reports/benchmarks/2025-26-captain/evaluation.json`. GW1 is excluded because
the cold-start replay has no shared locked forecast; GW2–GW38 are evaluated.

- Control expected captain extra: 317.34.
- Challenger expected captain extra: 321.84.
- Control realised captain extra: 208.
- Challenger realised captain extra: 215.
- Realised delta: +7 points.
- Captain/vice pair changed in 8 of 37 Gameweeks.
- Outcomes: 5 wins, 31 ties and 1 loss.

The positive final-season result does not reverse the rejection. It is based on
few changed decisions and includes a single −11-point loss. Selecting the
policy because 2025/26 happened to finish +7 would violate the locked
promotion rule.

## Interpretation

This experiment shows that vice fallback is worth modelling explicitly, but
the simple position-level ceiling and uncertainty adjustment is not stable
enough for live promotion. A future captain model should use player- and
fixture-specific scoring distributions—goal, assist, clean-sheet and bonus
probabilities—rather than broad position residuals.

The rejected policy remains in the final challenger matrix. The control
highest-EP captaincy rule remains active unless a later predeclared model passes
held-out validation.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m scripts.run_captain_counterfactual
.\.venv\Scripts\python.exe -m pytest tests/optimisation/test_captaincy.py -q
```
