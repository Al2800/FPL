# 12 — Consolidate the lab: orchestration split and fork-runner unification

Status: ready-for-agent
Type: task
Track: E (structure and surfaces)

## Context

`src/orchestration/` holds ~30 modules mixing the live decision path with replay/experiment apparatus, and `scripts/` holds ~80 entries including a family of one-off runners (`run_gw12_agent_fork.py`, `run_gw13_gw14_agent_forks.py` … `run_gw30_gw38_agent_forks.py`). There is no legible snapshot-to-recommendation path for a newcomer.

## Scope

- Split `src/orchestration/` into a live pipeline package (episode building, manager state, capture scheduling, live shadow, the ticket-02 orchestrator) and an experiments package (replay harness, forks, counterfactuals, historical builders), preserving import compatibility or updating all call sites and tests.
- Replace the per-GW fork scripts with one parameterised runner (`scripts/run_agent_fork.py --gws 30-38 ...`), keeping old outputs untouched.
- Update `docs/handover-brief.md` and the tests' import paths; CI stays green.

## Done when

- The live path is followable module-by-module; the GW-range fork runner reproduces one previously generated fork output byte-identically (or with explained diffs); all tests pass.
