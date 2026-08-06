# ADR-0026: Orchestration layout and unified agent-fork runner

**Status:** Accepted (Option A now; Option B destination via ticket 22)  
**Date:** 2026-08-06 (accepted by owner same day)  
**Decides:** Operationalisation ticket 12  
**Owners:** Alastair

## Context

`src/orchestration/` holds 36 modules mixing the live advisory path with
replay/experiment apparatus (~1.5k-line `genuine_replay.py` beside
`run_gameweek.py`). `scripts/` holds 90 Python entry points, including six
near-duplicate per-range agent-fork runners (`run_gw12_agent_fork.py` …
`run_gw30_gw38_agent_forks.py`). Inventory:
`docs/architecture/orchestration-inventory-2026-08-06.md`.

Ticket 12 requires an accepted ADR before any package move.

## Options

### A — No package move; navigation docs + parameterised dispatcher (recommended)

- Keep modules in `src/orchestration/`.
- Publish the inventory and point the handover brief at
  `src.orchestration.run_gameweek` as the canonical live entry.
- Replace day-to-day use of the six fork scripts with
  `scripts/run_agent_fork.py --gws …`, which **delegates** to the existing
  range runners so committed fixtures stay byte-identical.
- Leave historical scripts in place as thin compatibility shims or unchanged
  callees.

### B — Compatibility wrappers after a live/experiments package split

- Move replay modules to e.g. `src/orchestration_experiments/` (or
  `src/replay/`) with re-export shims in the old paths.
- Higher migration risk to import graphs and portable CI; only justified if
  Option A still leaves newcomers lost after one season of live use.

### C — Documentation only

- Inventory + handover links without a unified runner.
- Does not remove the duplicate argparse/maintenance surface.

## Decision

**Accept Option A now, with Option B as the recorded destination.** Do not move
packages in this ticket. Ship the inventory, handover link, and parameterised
dispatcher. Execute Option B as a follow-on migration
(`.scratch/operationalisation/issues/22-option-b-package-split.md`) once the
season's first live Gameweeks are stable.

An import-graph audit (6 August 2026) found **zero live→replay imports** in
`src/orchestration/`: dependencies already flow one way (replay → live). The
Option B split therefore formalises an existing boundary rather than untangling
one, which lowers its risk materially. The audit also resolved every previously
ambiguous "mixed" module placement (see ticket 22 for the file-by-file list).

## Consequences

- Ticket 12 implementation may unify runners immediately under Option A.
- Option B executes via ticket 22: move the replay/experiment modules to a
  dedicated package with one-season re-export shims, an architecture test
  enforcing the one-way dependency (live must never import replay), and byte
  parity on committed fork fixtures.
- Live automation must not invoke `scripts/run_agent_fork.py` or the
  `run_gw*_agent_fork*` scripts; those are retrospective-only surfaces.
- Per-GW scripts remain callable until explicitly deprecated after fixture
  parity is proven.
