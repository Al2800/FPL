# 08 — Owner decision: optimiser and planning-horizon upgrade

Status: resolved
Type: task
Track: Owner/ADR gate

## Context

`src/optimisation/solver.py` is an enumerative same-position search — explicitly "not globally optimal" (`docs/optimisation/wp07-status.md`) — and full-squad Wildcard/Free Hit rebuild is stubbed (hit accounting only). The two highest-leverage decisions of a season cannot currently be optimised. WP-07 anticipated assessing `open-fpl-solver` adaptation versus internal build (ADR-0011, Proposed).

ADR-0011 currently chooses the transparent internal enumerator and explicitly
requires a superseding ADR before introducing PuLP, OR-Tools or
`open-fpl-solver`. ADR-0012 is amended by ADR-0020; it does not authorise a
3–6 GW live horizon.

## Decision required from the owner

1. Keep the internal enumerator and add bounded full-squad rebuild search, or
   authorise a MILP dependency (internal formulation versus a governed
   `open-fpl-solver` adaptation).
2. Keep single-GW live optimisation with the ADR-0020 option-value bridge, or
   authorise a specific multi-week horizon and discount policy once cutoff-safe
   forecasts exist.
3. Accept a superseding ADR recording solver dependency, determinism,
   maintenance, licensing, performance and fallback trade-offs.

## Done when

- The owner accepts a superseding ADR for ADR-0011 and, if the horizon changes,
  a further amendment to ADR-0012/0020.
- Ticket 18 is updated with the selected solver, horizon, dependency version,
  fallback and objective before it may become `ready-for-agent`.

## Boundaries

Do not implement a new solver or live horizon under this ticket.

## Answer

Owner decisions 5 August 2026:

1. **Solver:** keep internal enumerator; add bounded Wildcard/Free Hit full-squad
   rebuild. No MILP / PuLP / OR-Tools / `open-fpl-solver` (ADR-0022).
2. **Horizon:** destination live horizon **4 Gameweeks**, discount **0.9**
   (aligns with `transfer-horizon-v1`). Live weekly optimiser stays **single-GW
   + ADR-0020** until cutoff-safe 4-GW forecasts exist (ADR-0023). Initial-squad
   GW1–GW6 remains preseason-only (`initial-squad-2026-27.json`).
3. ADRs accepted: `docs/decisions/0022-*.md`, `docs/decisions/0023-*.md`.
   Ticket 18 updated accordingly.
