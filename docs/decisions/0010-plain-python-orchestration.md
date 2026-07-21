# ADR-0010: Plain Python as the initial orchestration substrate

**Status:** Proposed (awaiting owner ratification)
**Date:** 2026-07-21
**Decides:** Open Decision 12 (`docs/plan.md` Section 25)

## Context

Section 13 requires a deterministic orchestrator in the initial build (not an LLM). Open Decision 12 asks which substrate runs the pipeline and how agent traces are captured. The handover brief instructs the first implementation agent to choose the simplest working option and propose an ADR.

## Decision (proposed)

The initial orchestration substrate is **plain Python** modules under `src/orchestration/`, invoked by scripts under `scripts/`. No workflow engine or agent framework is introduced in Phase 0/1. Agent traces (when agents arrive) will be JSONL files versioned by run ID alongside the Gameweek Decision Record; until then, deterministic pipeline steps write structured run metadata only.

## Consequences

- Walking-skeleton and snapshotter scripts are ordinary Python entry points.
- An LLM-driven orchestrator remains a Phase 3 experimental condition, distinguishable from this substrate.
- Revisit if multi-step scheduling, retries or distributed runs become limiting (Phase 9).
