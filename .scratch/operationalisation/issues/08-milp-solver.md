# 08 — MILP optimiser (Wildcard/Free Hit rebuild, true multi-week)

Status: ready-for-agent
Type: task
Track: C (real solver)

## Context

`src/optimisation/solver.py` is an enumerative same-position search — explicitly "not globally optimal" (`docs/optimisation/wp07-status.md`) — and full-squad Wildcard/Free Hit rebuild is stubbed (hit accounting only). The two highest-leverage decisions of a season cannot currently be optimised. WP-07 anticipated assessing `open-fpl-solver` adaptation versus internal build (ADR-0011, Proposed).

## Scope

- A MILP formulation (PuLP + CBC/HiGHS, or adapt `open-fpl-solver`) covering all §12.1 hard constraints: squad/positions/club limit, budget with actual selling prices, XI/formation, captain/vice, ordered bench, free-transfer balance and hits, chip interactions, blanks/doubles.
- Full-squad rebuild for Wildcard and Free Hit candidates.
- Multi-week variant over the 3–6 GW horizon with discounting, replacing (or cross-checking) the beam search in `multiweek.py`.
- Keep it deterministic and auditable: saved solver input reproduces output exactly (WP-07 done-criterion); validate every emitted plan through `src/scoring/validator.py`.
- Cross-check against the enumerative solver on golden cases — the old solver becomes a regression oracle.

## Done when

- MILP plans satisfy all golden-case constraints, match or beat enumerative EV on every fixture case, WC/FH rebuild produces valid full squads, and an ADR records the solver decision (supersedes/ratifies ADR-0011).

## Boundaries

Rules stay in YAML — constraint constants must be read from `control/rules/2026-27.yaml`, never hard-coded in the formulation.
