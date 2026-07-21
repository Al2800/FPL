# ADR-0010: Plain Python as the initial orchestration substrate

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 12 (`docs/plan.md` Section 25)
**Accepted by:** project owner, 21 July 2026

## Context

Section 13 requires a deterministic orchestrator in the initial build (not an LLM). Open Decision 12 asks which substrate runs the pipeline and how agent traces are captured.

## Decision

The initial orchestration substrate is **plain Python** modules under `src/orchestration/`, invoked by scripts under `scripts/`. No workflow engine or agent framework is introduced in Phase 0/1. Agent traces (when agents arrive) will be JSONL files versioned by run ID alongside the Gameweek Decision Record; until then, deterministic pipeline steps write structured run metadata only.

This is optimal for the current phase: it keeps the agent-versus-non-agent comparison uncontaminated, minimises moving parts, and matches the effort budget. It is not a permanent commitment — revisit if multi-step scheduling, retries or distributed runs become limiting (Phase 9).

## Consequences

- Walking-skeleton and snapshotter scripts remain ordinary Python entry points.
- An LLM-driven orchestrator remains a Phase 3 experimental condition, distinguishable from this substrate.
- Framework adoption later requires a superseding ADR; it must not silently replace this path mid-experiment.
