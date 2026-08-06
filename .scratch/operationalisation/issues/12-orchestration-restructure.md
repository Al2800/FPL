# 12 — Consolidate the lab: orchestration split and fork-runner unification

Status: resolved
Type: task
Track: Structural proposal

Activation gate: first demonstrate the navigation/coupling problem with an
import graph and duplicate-runner inventory, then accept an ADR. Do not move
packages before that decision.

Owner authorised implementation on 6 August 2026 (inventory + ADR draft;
package moves only after ADR acceptance).

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

## Answer

Owner accepted **ADR-0026** on 6 August 2026: Option A now, Option B as the
recorded destination via ticket 22.

Shipped under Option A (no package move):

- Inventory: `docs/architecture/orchestration-inventory-2026-08-06.md`
  (36 orchestration modules; 6 duplicate fork runners; 90 scripts)
- Accepted ADR: `docs/decisions/0026-orchestration-layout-and-agent-fork-runner.md`
- Dispatcher: `scripts/run_agent_fork.py --gws 30-38 -- --mode prepare …`
  (delegates to existing range runners; committed fixtures stay byte-identical)
- Handover brief links `src.orchestration.run_gameweek` as the canonical live
  entry; live automation must never invoke the fork-runner scripts
- Import audit (zero live→replay imports) recorded in the ADR; it de-risks and
  pre-plans the Option B move list

Follow-on: ticket 22 executes the Option B package split once early 2026/27
live Gameweeks are stable (never in a deadline week).
