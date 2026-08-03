# 09 — Distributional chip EV and horizon ratification

Status: ready-for-agent
Type: task
Track: C (real solver)
Blocked by: 05, 08

## Context

Chips are season-scale assets with a GW19 first-half expiry; plan §12.3 warns against greedy chip use. Current chip selection (`chips.py`) compares deterministic EPs plus a heuristic reserve. With the simulation layer (05) and MILP (08) available, chip EV should be computed against distributions over future fixtures (e.g. Bench Boost now versus the best remaining Double Gameweek).

## Scope

- Chip-timing evaluation using simulated plan distributions across the multi-week horizon, including blank/double scenarios from the fixture-revision ledger.
- Surface chip recommendations with a distributional justification in the GDR (probability chip-now beats best-later).
- Draft the ADR evidence needed to ratify or revise ADR-0012 (planning horizon) — replay the 2025-26 benchmark set under single-GW versus multi-week policies and report the paired difference.

## Done when

- Chip candidates in the GDR carry distribution-based EV comparisons, and a written horizon comparison exists for the owner to ratify ADR-0012.
