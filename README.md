# FPL Agentic Decision Laboratory

A reproducible decision laboratory that uses official Fantasy Premier League (FPL) as a controlled environment for studying how AI agents make decisions under uncertainty. It compares deterministic analytics, optimisation, single-agent reasoning and multi-agent orchestration using point-in-time evidence and auditable outcomes.

**Target season:** FPL 2026/27
**Current status:** Phase 0/1 — governance cleared; rules catalogue and source registry in place; FPL snapshotter and walking skeleton runnable.

## Start here

- [Project plan](docs/plan.md) — research questions, data strategy, architecture, evaluation and roadmap.
- [AGENTS.md](AGENTS.md) — permissions, source restrictions and work-package boundaries.
- [Handover brief](docs/handover-brief.md) — first implementation scope (registry, snapshotter, skeleton).
- [Decisions](docs/decisions/) — accepted and proposed architecture decision records.

## Core principle

> Build the trusted decision core first. Design for the larger vision now, but activate advanced retrieval, competitive intelligence, live agents, cloud infrastructure and computer-use automation only when their prerequisites are satisfied.

An LLM is never responsible for enforcing budget, formation or transfer rules — rules validation and optimisation are deterministic, and every recommendation must be reproducible from point-in-time snapshots.

## Quick start

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -q
python3 -m scripts.run_skeleton          # one synthetic historical Gameweek end-to-end
python3 -m scripts.run_snapshot          # capture bootstrap-static + fixtures into data/raw/fpl/
```

Raw snapshots stay under `data/` (gitignored). The skeleton writes `reports/gameweeks/skeleton-gw3/`.

## Work package status

| Package | Status |
|---|---|
| WP-01 Rules audit | Draft complete — launch re-verification pending |
| WP-02 Source governance (Tier 1) | Complete for Section 6.1; only FPL endpoints enabled |
| Snapshotter | Runnable |
| Walking skeleton | Runnable and reproducible |
| WP-03 onwards | Not started |

## Repository layout

See [Section 20 of the plan](docs/plan.md#20-suggested-repository-structure). Raw data, credentials, browser state and generated secrets are excluded from version control.
