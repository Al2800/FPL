# FPL-k21: value retained free transfers

## Purpose

The sealed 2025/26 GW2 forecast produces credible player projections but the
single-Gameweek optimiser assigns no value to retaining a free transfer. This
plan adds a small, explicit planning term without pretending that a full
multi-Gameweek forecast exists. The current-Gameweek projection remains
visible and unchanged.

## Policy

For ordinary transfers, calculate next-Gameweek free transfers from the loaded
rules catalogue:

`min(max_banked, max(0, available - transfers_used) + free_per_gameweek)`.

Only transfers above the ordinary weekly award are treated as banked option
units. Each unit is valued as:

`hit_cost * probability_extra_transfer_needed * future_discount`.

The initial reviewed assumptions are 0.50 and 0.90. They are policy inputs,
not fitted on GW2. The GW2 artifact must also publish the action breakpoints
and a sensitivity sweep, so the recommendation cannot hide dependence on the
assumptions.

Wildcard and Free Hit retain the existing bank under the historical rule and
therefore receive an action-invariant option term.

## Implementation

- Extend `SolverInput` with an opt-in, round-trippable transfer-value policy.
  Omit inactive defaults from serialized legacy inputs so sealed artifacts
  remain reproducible.
- Keep immediate expected points separate from the planning objective.
- Retain the best legal candidate for every transfer count, independent of the
  top-50 reporting truncation.
- Add focused tests for rule-era banking, invalid assumptions, exact objective
  decomposition, and zero-policy backward compatibility.
- Generate new GW2 option-value artifacts alongside, never over, the sealed
  feature-complete artifacts.
- Document the policy as a bridge to—not a substitute for—multi-Gameweek
  forecasts.

## Validation

Run focused optimiser and GW2 setup tests, regenerate the GW2 setup twice to
prove idempotence, run the full suite, and verify artifact hashes plus
`git diff --check`.

## Progress

- [x] Inspect current solver, rules and sealed GW2 objectives.
- [x] Implement policy and per-transfer-count candidates.
- [x] Add GW2 sensitivity/review artifacts.
- [x] Run focused and full validation.
- [x] Close bead, commit and push.

## Results

The sealed comparison selects zero transfers at the declared 1.80 option-unit
value. Immediate/planning objectives are 58.23/61.83 for zero transfers,
59.90/61.70 for one and 61.33/61.33 for two. Adjacent breakpoints are 1.43
(two versus one) and 1.67 (one versus zero).

Focused optimiser and GW2 tests pass (27 tests). The complete suite excluding
the unrelated Parquet walking-skeleton module passes (340 tests). The two
walking-skeleton tests cannot start in this environment because neither
optional Pandas Parquet engine is installed; no dependency was installed.
Artifact generation is idempotent, all content hashes verify and
`git diff --check` passes.
