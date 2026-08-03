# 12 — Consolidate the lab: orchestration split and fork-runner unification

Status: needs-triage
Type: task
Track: Structural proposal

Activation gate: first demonstrate the navigation/coupling problem with an
import graph and duplicate-runner inventory, then accept an ADR. Do not move
packages before that decision.

## Context

`src/orchestration/` holds ~30 modules mixing the live decision path with replay/experiment apparatus, and `scripts/` holds ~80 entries including a family of one-off runners (`run_gw12_agent_fork.py`, `run_gw13_gw14_agent_forks.py` … `run_gw30_gw38_agent_forks.py`). There is no legible snapshot-to-recommendation path for a newcomer.

## Scope

- Inventory imports, entry points and duplicate per-GW runner logic; record the
  measurable maintenance problem and the smallest viable change.
- Draft an ADR comparing: no package move plus navigation documentation;
  compatibility wrappers; and a live/experiments package split.
- If the ADR is accepted, replace the per-GW fork scripts with one
  parameterised runner (`scripts/run_agent_fork.py --gws 30-38 ...`) and apply
  only the package changes selected by the ADR.

## Done when

- An import/entry-point inventory and accepted ADR define the exact migration.
- The parameterised runner reproduces every existing committed fork fixture
  byte-identically; any intentional schema change requires a separately
  versioned migration rather than an unexplained output diff.
- Repository architecture tests and the portable CI suite pass, and the
  handover brief links the canonical live entry point.
