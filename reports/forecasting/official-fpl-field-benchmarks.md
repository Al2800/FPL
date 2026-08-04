# Official FPL field benchmarks

Live 2026/27 has preseason/pre-deadline captures but no finished Gameweek outcomes yet; metrics stay insufficient until paired.

- Status: `insufficient_sample`
- Pre-deadline snapshots: `23`
- Paired outcomes: `0` (minimum `38`)
- Content hash: `c1594a2926041ae22df63a0a82d0eace413e559f7c03d5c1ceabb67c0daea7b9`

## Fields

### ep_next

- Status: `insufficient_sample`
- Reason: Need at least 38 cutoff-safe player-Gameweek pairs with realised points; found 0. Pre-deadline snapshots observed: 23.
- Promoted: `False`

### fdr

- Status: `insufficient_sample`
- Reason: Need at least 38 cutoff-safe player-Gameweek pairs with realised points; found 0. Pre-deadline snapshots observed: 23.
- Promoted: `False`

### bootstrap_team_strength

- Status: `insufficient_sample`
- Reason: Need at least 38 cutoff-safe player-Gameweek pairs with realised points; found 0. Pre-deadline snapshots observed: 23.
- Promoted: `False`

### element_summary

- Status: `no_corpus`
- Duplication: No element-summary artifacts are present in the evaluation corpus. The governed vaastav merged_gw warehouse already supplies past-season player-match histories for priors.
- Leakage: element-summary history rows can include the current Gameweek once fixtures start; any adoption must filter strictly by kickoff/available_at <= decision cutoff. Without a cutoff-labelled corpus this leakage risk cannot be measured.
- Retention: Official element-summary payloads are restricted Tier-0 snapshots (ADR-0001/0002): private local retention only, no redistribution. Expanding capture without a proven prior gain increases retention surface for no decision benefit.
- Recommendation: Do not adopt. Re-run after a cutoff-safe element-summary corpus exists and a paired ablation vs vaastav priors is positive.
- Promoted: `False`

## Promotion

- Improved vs naive: `none`
- Promoted fields: `none`
- Policy: Null or positive results are recorded; promotion into the live forecast requires an explicit owner gate and retained source/transform versions (plan §11.2).
