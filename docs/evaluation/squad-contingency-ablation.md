# Squad contingency component ablation

## Purpose

W10 rejected promotion of `probabilistic_v1` after a locked 2024/25 same-squad
lineup gate of **−10** realised points. This study decomposes that joint
objective into three preregistered single-component challengers so the locked
loss can be attributed without fitting a new policy on 2024/25 or 2025/26.

The sealed report is
`reports/evaluation/squad-contingency-ablation-v1.json`. Production remains
`none`; no `control/policies/` change is performed.

## Reference

| Binding | Value |
|---|---|
| W10 report | `reports/evaluation/squad-contingency-v1.json` |
| Appearance calibration | `control/models/appearance-distribution-v1.json` |
| Locked scope | 38 same-squad 2024/25 lineup pairs, transfers held at zero |
| Descriptive scope | 37 sealed 2025/26 same-state lineup forks, transfers held at zero |

W10 decision hashes remain unchanged. This report references them but does not
rewrite them.

## Component arms

Each arm reuses the W10 same-state inputs and official validator/scorer. Only
one planning term is enabled; the other levers stay at the policy-off control
baseline for that scope.

| Arm | Enabled term | Fixed at control |
|---|---|---|
| `bench_order_only` | expected legal goalkeeper/outfield substitutions | starting XI, captain, vice |
| `xi_formation` | nominal XI expected points plus captain/vice fallback | bench contingency value (zero in objective) |
| `captain_vice_fallback` | captain multiplier and vice fallback | starting XI, bench order |

`xi_formation` still searches formation, bench permutations and captain pairs,
but excludes bench-contingency value from the objective. That isolates lineup
choices driven by starter and captaincy terms rather than substitution value
alone.

## Locked 2024/25 attribution of the −10 gate

| Arm | Changed weeks | Net delta | Primary lever |
|---|---:|---:|---|
| `probabilistic_v1` (W10) | 17 | **−10** | joint bench, XI and captain |
| `bench_order_only` | 13 | −3 | bench order only |
| `xi_formation` | 30 | −3 | bench permutations under XI+captain objective |
| `captain_vice_fallback` | 0 | 0 | none on locked neutral squads |

Interpretation:

1. **Captain/vice fallback alone does not explain the locked loss.** On the
   locked neutral reference squads, contingency captaincy matches the
   deterministic control in every week.
2. **Bench-order-only and XI/formation arms each cost about three points in
   isolation**, but neither reproduces the full −10. The seven non-zero v1
   weeks all changed the starting XI as well as the bench; marginal arms held
   XI fixed cannot match those joint decisions.
3. **The locked −10 is therefore a joint interaction effect**, not a single
   additive term. Autosub valuation changes bench order, which in turn changes
   which formation and starters look optimal when all terms are optimised
   together.

Non-zero v1 weeks (locked): GW2 −4, GW10 +1, GW13 +2, GW20 −5, GW34 +6,
GW36 −6, GW37 −4. The largest single-week losses (GW2, GW20, GW36, GW37)
involve both bench and XI movement under the combined objective.

## Descriptive 2025/26 (non-gating)

Descriptive forks are reported separately and must not override the locked gate
or select a v2 policy.

| Arm | Changed weeks | Net delta |
|---|---:|---:|
| `probabilistic_v1` (W10) | 26 | +22 |
| `bench_order_only` | 18 | +3 |
| `captain_vice_fallback` | 8 | +18 |
| `xi_formation` | 37 | +5 |

Captain/vice fallback explains much of the descriptive +22 in isolation, but that
evidence is holdout-only. It cannot rescue the failed locked gate.

## v2 preregistration (not fitted here)

No parameter or policy weight is fit on 2024/25 or 2025/26 in this bead. A
future `probabilistic_v2` must use:

| Role | Season(s) |
|---|---|
| Appearance calibration fit | 2022/23, 2023/24 only (unchanged) |
| Component/objective design | informed by this ablation, locked before replay |
| Promotion gate | locked 2024/25 same-squad lineup replay |
| Descriptive holdout | 2025/26 same-state forks (no selection) |

Candidate v2 directions suggested by the ablation, to be specified and frozen
before any replay:

1. Retain bench contingency only if a joint locked replay shows non-negative
   realised value when XI and captain remain control-equivalent.
2. Treat captain/vice fallback as optional or control-default on neutral
   historical squads unless a separate gate passes.
3. Require joint objective evaluation; marginal component sums are not
   sufficient promotion evidence.

## Reproducibility

```bash
.venv/bin/python scripts/run_squad_contingency_ablation.py
.venv/bin/python -m pytest -q \
  tests/evaluation/test_squad_contingency_ablation.py \
  tests/evaluation/test_squad_contingency_evaluation.py
```

Each component scope carries an independent `decision_sha256` excluding wall
time. The report `content_sha256` covers the full sealed packet.

## Limitations

- Marginal component deltas do not sum to the joint `probabilistic_v1` delta.
- Locked neutral squads are optimiser constructs, not observed human teams.
- Descriptive 2025/26 forks are isolated lineup comparisons, not a
  longitudinal season path.
