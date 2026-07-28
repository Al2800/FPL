# Squad-contingency default: W10 promotion decision

## Outcome

Do not promote `probabilistic_v1` to the production default.

The paired evaluation is valid and operationally useful, but it fails its
predeclared locked-season decision-value gate. The production default remains
`none`; the appearance model and contingency objective remain available as an
explicit challenger.

## Evidence

The immutable report is
`reports/evaluation/squad-contingency-v1.json`. Its two scopes are deliberately
separate:

| Scope | Pairs | Changed weeks | Net delta | Interpretation |
|---|---:|---:|---:|---|
| Locked 2024/25 same-squad lineup | 38 | 17 | -10 | Promotion gate |
| 2025/26 sealed same-state lineup forks | 37 | 26 | +22 | Descriptive only |

All 75 control and challenger plans passed the active rules and were scored by
the official reveal-gated scorer against the same hidden outcome. No canonical
episode, plan, outcome, policy state or production configuration was modified.

The locked loss was concentrated rather than uniform. Only seven weeks had a
non-zero realised delta: GW2 -4, GW10 +1, GW13 +2, GW20 -5, GW34 +6, GW36 -6,
and GW37 -4. The policy changed bench order in 17 weeks and the starting XI in
10. It produced six more realised autosub points overall, but those gains did
not compensate for worse XI decisions.

The descriptive 2025/26 path is encouraging but cannot rescue the failed
locked gate. It changed bench order in 22 weeks, the XI in 11, and
captain/vice in eight. The isolated net result was +22, while realised autosub
points were two lower than control; much of the gain therefore came from
captaincy and XI choices rather than substitution value alone.

## Runtime boundary

With transfers held at zero for both arms, the challenger averaged about
75 ms per locked lineup and 65 ms per sealed 2025/26 lineup. That is suitable
for weekly advisory use.

An exploratory attempt to place contingency evaluation inside the unrestricted
three-transfer search did not complete a single fork within ten minutes. The
search can expand to 151,672 three-transfer candidates, each requiring lineup
and bench valuation. W10 therefore holds transfers at zero for both arms and
does not claim evidence about transfer-selection interaction.

## Required work before reconsideration

1. Ablate the objective into bench-order-only, XI/formation, and
   captain/vice-fallback components. The current aggregate hides which term
   causes the locked loss.
2. Revisit appearance/minutes calibration at the decision boundary, including
   correlations between teammates and rotation events.
3. Add an efficient, equivalence-tested contingency integration for bounded
   transfer candidates before any default can affect transfer selection.
4. Re-run the locked gate under a preregistered v2 policy. A positive final
   season or live anecdote must not override another locked failure.

Any future flag flip must be one reversible owner-ratified policy-data change.
No owner approval is requested for v1 because the evidence gate failed.
