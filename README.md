# FPL Agentic Decision Laboratory

A reproducible decision laboratory that uses official Fantasy Premier League (FPL) as a controlled environment for studying how AI agents make decisions under uncertainty. It compares deterministic analytics, optimisation, single-agent reasoning and multi-agent orchestration using point-in-time evidence and auditable outcomes.

**Target season:** FPL 2026/27
**Current status:** Phase 0 — governance and design. Advisory mode only; no automated collection or execution is enabled yet.

## Start here

- [Project plan](docs/plan.md) — the full plan: research questions, data-source strategy, architecture, agent design, evaluation framework and delivery roadmap.
- [AGENTS.md](AGENTS.md) — permissions, source restrictions and work-package boundaries for agents contributing to this repository.

## Core principle

> Build the trusted decision core first. Design for the larger vision now, but activate advanced retrieval, competitive intelligence, live agents, cloud infrastructure and computer-use automation only when their prerequisites are satisfied.

An LLM is never responsible for enforcing budget, formation or transfer rules — rules validation and optimisation are deterministic, and every recommendation must be reproducible from point-in-time snapshots.

## Repository layout (planned)

See [Section 20 of the plan](docs/plan.md#20-suggested-repository-structure). Raw data, credentials, browser state and generated secrets are excluded from version control.
