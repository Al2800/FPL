# 01 — Manager-state → SolverInput + GDR adapter

Status: ready-for-agent
Type: task
Track: A (close the live loop)

## Context

`docs/handover-brief.md` lists this as the next implementation step and it is still missing. Manager state is entered manually via `control/templates/manager-state-entry.json` and validated by `src/orchestration/manager_state.py`, but nothing converts a validated entry into an optimiser `SolverInput` (`src/optimisation/types.py` / `io.py`) and onwards into a Gameweek Decision Record (`src/reporting/decision_record.py`).

## Scope

- A small adapter module (suggested: `src/orchestration/live_solver_adapter.py`) taking a validated manager-state entry plus the latest live forecast outputs and producing a `SolverInput` with actual selling prices, bank, free transfers and chip state.
- A thin script wrapper so the step is runnable standalone.
- Unit tests using the template plus fixture forecasts.

## Done when

- A filled `manager-state-entry.json` plus a forecast artefact round-trips to a `SolverInput` whose plans validate against the 2026/27 ruleset via `src/scoring/validator.py`.
- The adapter output feeds `decision_record.py` without manual JSON surgery.

## Boundaries

Manual entry remains the mechanism (ADR-0005); do not build authenticated capture.
