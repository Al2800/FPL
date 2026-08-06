# 18 — Implement the owner-selected optimiser upgrade

Status: resolved
Type: task
Track: Solver implementation
Blocked by: 08

Selected by ticket 08 / ADR-0022 / ADR-0023 (5 August 2026):

- **Solver:** transparent internal enumerator; add **bounded** Wildcard / Free
  Hit full-squad rebuild. No MILP dependency.
- **Dependency / version:** none beyond current Python stack; solver version
  bump recorded on outputs when rebuild lands.
- **Live horizon (now):** `horizon_gameweeks=1` with ADR-0020 option-value
  bridge; fallback = current enumerator without rebuild.
- **Destination horizon:** 4 Gameweeks, discount 0.9 (`transfer-horizon-v1`
  alignment) — interface only until cutoff-safe 4-GW forecasts exist; do not
  invent future player points.
- **Objective:** highest EV in the declared candidate domain; retain enumerator
  as regression oracle.

## Invariant scope

Whatever implementation ticket 08 selects must:

- cover plan §12.1 hard constraints, including budget with actual selling
  prices, squad/line-up legality, captain/vice, bench order, transfer balance,
  hits, chips and blank/double fixtures;
- support valid full-squad rebuild candidates for Wildcard and Free Hit;
- load constraints and scoring from versioned control data rather than
  hard-coded constants;
- serialise solver inputs/outputs and reproduce identical output with the
  selected deterministic configuration;
- validate every emitted plan through `src/scoring/validator.py`;
- retain the current enumerator as a regression oracle and defined fallback.

## Done when

- Golden cases cover ordinary transfers, banked transfers, hits, Wildcard,
  Free Hit, Triple Captain, Bench Boost, blanks and doubles.
- The selected solver matches or improves the current objective within the same
  candidate domain and publishes runtime/resource bounds on the scale fixture.
- Saved input plus rules/policy/solver versions reproduces the output exactly.

## Boundaries

Do not introduce MILP or change the live default horizon to 4 GW inside this
ticket until cutoff-safe multi-GW forecasts are wired; expose the interface only.

## Answer

Implemented 5 August 2026 (ADR-0022 / ADR-0023):

- Solver version bumped to `wp07-wc-fh-rebuild-v0.3`.
- Bounded Wildcard / Free Hit full-squad rebuild via `src/optimisation/rebuild.py`,
  wired into `solve()` when `active_chip` is WC/FH. Hit cost remains 0; existing
  enumerator stays the regression path and deadline/budget fallback.
- Destination horizon interface recorded on every output
  (`destination_horizon_gameweeks=4`, `discount_factor=0.9`, `live_active=false`).
  Live `horizon_gameweeks` remains 1 (no invented multi-GW points).
- Golden input/output regenerated; rebuild-focused tests in
  `tests/optimisation/test_rebuild.py`.

