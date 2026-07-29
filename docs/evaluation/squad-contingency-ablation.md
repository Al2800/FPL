# Squad contingency component ablation

## Purpose

W10 rejected promotion of `probabilistic_v1` after a locked 2024/25 same-squad
lineup gate of **−10** realised points. This study decomposes that joint
objective into two identified single-component challengers plus an explicit
XI/formation identification diagnostic. This bounds what can be attributed without
fitting a new policy on seasons whose outcomes are already known.

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

Each arm reuses the W10 same-state inputs and official validator/scorer. The
bench and captain arms enable one separable planning term while holding the
other levers at the policy-off control baseline.

| Arm | Identification | Term / diagnostic |
|---|---|---|
| `bench_order_only` | identified | expected legal goalkeeper/outfield substitutions; XI and captaincy fixed |
| `captain_vice_fallback` | identified | captain zero-minute vice fallback; XI and bench fixed |
| `xi_formation` | **not identified** | exact policy-off no-op proving there is no independent XI probability term in `probabilistic_v1` |

XI changes in the joint policy arise from interaction with bench and captain
optimisation. Inventing an appearance-weighted XI heuristic would test a new
policy, not ablate `probabilistic_v1`, so this study records the component as
structurally unidentified instead.

## Locked 2024/25 attribution of the −10 gate

| Arm | Changed weeks | Net delta | Interpretation |
|---|---:|---:|---|
| `probabilistic_v1` (W10) | 17 | **−10** | joint policy result |
| `bench_order_only` | 13 | −3 | identified bench-order marginal |
| `captain_vice_fallback` | 0 | 0 | identified captain/vice marginal |
| `xi_formation` | 0 | 0 | no-op diagnostic; **not** an XI causal estimate |

The identified marginal sum is −3. The remaining −7 is a joint interaction
plus the structurally unidentified XI contribution; it is deliberately labelled
`residual_unattributed`, not assigned to XI. The exact W10 bindings are verified
for every component and gameweek: episode, observed state, hidden outcome,
ruleset, control plan, control outcome and locked reference squad.

Non-zero joint-policy weeks remain GW2 −4, GW10 +1, GW13 +2, GW20 −5,
GW34 +6, GW36 −6 and GW37 −4.

## Descriptive 2025/26 (non-gating)

| Arm | Changed weeks | Net delta |
|---|---:|---:|
| `probabilistic_v1` (W10) | 26 | +22 |
| `bench_order_only` | 18 | +3 |
| `captain_vice_fallback` | 8 | +18 |
| `xi_formation` | 0 | 0 (unidentified diagnostic) |

The identified marginal sum is +21 and the residual interaction is +1.
These historical findings are exploratory because the outcomes were already
available; they cannot select or promote a production policy.

## v2 preregistration (not fitted here)

No parameter or policy weight is fit on 2024/25 or 2025/26 in this bead. A
future `probabilistic_v2` must use:

| Role | Season(s) |
|---|---|
| Historical analysis | 2024/25 and 2025/26 are exploratory and production-ineligible |
| Candidate design | trained only on predeclared earlier seasons and frozen before GW1 |
| Prospective promotion gate | 2026/27, with owner approval |
| Midseason selection | prohibited for the frozen candidate |

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
