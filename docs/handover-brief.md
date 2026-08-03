# Handover brief: post–WP-10 (live advisory prep)

**Date:** 21 July 2026  
**Context:** Work packages WP-01…WP-10 are on `main`. This brief replaces the original “first implementation” brief for the next agent.

## Read first

`AGENTS.md`, `docs/plan.md` §§15–17 and 25–26, `docs/architecture/deferred/README.md`, Proposed ADRs 0011–0016.

## What is done

- Rules catalogue + golden runner: `python3 -m scripts.run_rules_golden`
- Source registry (FPL enabled); snapshotter; schemas; WP-05 baselines; optimiser; evidence lifecycle; GDR + replay harness; deferred interface notes
- Structured replay pilot set: `evals/replay-set/structured-pilot-gameweeks.yaml` → `python3 -m scripts.run_replay_pilot_set`
- Manual manager-state template: `control/templates/manager-state-entry.json`
- Benchmark Kernel v1.0 contract audit and residual closure:
  `docs/evaluation/benchmark-kernel-closure.md`. The contract is accepted;
  governed historical episode artefacts remain a local prerequisite for the
  artifact-backed replay suite.

## What to do next (implementation)

**Full operationalisation plan (3 Aug 2026 review):**
`.scratch/operationalisation/spec.md` with tickets 01–20 under
`.scratch/operationalisation/issues/`. The current Phase 0/1 implementation
queue is tickets 01 → 02 → 03; start at ticket 01. Later-phase tickets are
deliberately marked `needs-triage` or `needs-info` until their activation gates
are met.

1. **Day-one live capture** — keep `scripts.run_snapshot` on a schedule; treat
   403/empty bodies as retained evidence; promote schema notes when bootstrap
   is stable. This is an ongoing owner operation; ticket 04 covers later Phase
   2 portability and alerting, not the initial capture itself.
2. **Wire manager state** — fill the template each GW; convert to optimiser `SolverInput` + GDR (small adapter script).
3. **Attach post-GW outcomes** — `replay_gameweek(..., attach_outcome_points=...)` or equivalent on live GDRs.
4. Keep evidence agents proposal-only and inside the attested
   `gpt-5.6-sol` subscription-host boundary; do not add API keys or execution
   authority.

## Owner-only (do not invent)

- Ratify Proposed ADRs 0011–0016  
- Recruit ~5 cohort managers (ADR-0009)  
- Open Decision 8 is resolved: `gpt-5.6-sol` via ChatGPT-subscription Codex;
  no API secret is required or permitted for this arm.

## Hard boundaries

Same as `AGENTS.md`: rules-as-data, no unregistered collection, point-in-time
discipline, LLMs propose only, no secrets in Git, and no deferred execution
implementation.
