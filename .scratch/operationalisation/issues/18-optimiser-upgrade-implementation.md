# 18 — Implement the owner-selected optimiser upgrade

Status: needs-info
Type: task
Track: Solver implementation
Blocked by: 08

Missing information: the accepted superseding ADR must select the solver,
dependency/version, live horizon, discount policy and fallback. Update this
ticket from that decision before changing its status to `ready-for-agent`.

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

Do not infer MILP versus bounded internal search, choose a dependency, or change
the live horizon inside this ticket; those are ticket-08 owner decisions.
