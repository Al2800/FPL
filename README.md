# FPL Agentic Decision Laboratory

A reproducible decision laboratory that uses official Fantasy Premier League (FPL) as a controlled environment for studying how AI agents make decisions under uncertainty. It compares deterministic analytics, optimisation, single-agent reasoning and multi-agent orchestration using point-in-time evidence and auditable outcomes.

**Target season:** FPL 2026/27
**Current status:** Phase 1 packages WP-01…WP-10 complete; live advisory prep (snapshots, manager-state entry, Proposed ADR ratification).

## Start here

- [Project plan](docs/plan.md) — research questions, data strategy, architecture, evaluation and roadmap.
- [AGENTS.md](AGENTS.md) — permissions, source restrictions and work-package boundaries.
- [Handover brief](docs/handover-brief.md) — post–WP-10 live advisory prep.
- [Decisions](docs/decisions/) — accepted and proposed architecture decision records.
- [Tracker migration (Beads → GitHub Issues)](docs/operations/tracker-migration-beads-to-github.md) — active backlog is GitHub Issues; Beads are archive only.

## Core principle

> Build the trusted decision core first. Design for the larger vision now, but activate advanced retrieval, competitive intelligence, live agents, cloud infrastructure and computer-use automation only when their prerequisites are satisfied.

An LLM is never responsible for enforcing budget, formation or transfer rules — rules validation and optimisation are deterministic, and every recommendation must be reproducible from point-in-time snapshots.

## Quick start

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -q
python3 -m scripts.run_skeleton          # one synthetic historical Gameweek end-to-end
python3 -m scripts.run_snapshot          # capture bootstrap-static + fixtures into data/raw/fpl/
python3 -m scripts.run_wp05_eval         # baseline metrics → docs/data-sources/wp05/ (needs local historical data)
python3 -m scripts.run_optimiser evals/golden-cases/optimiser-gw3-input.json
python3 -m scripts.run_replay --season 2025-26 --stop-after-gameweek 1
python3 -m scripts.render_replay_report             # self-contained GW1 HTML review
python3 -m scripts.prepare_replay_gameweek --gameweek 2
python3 -m scripts.run_rules_golden            # 24 rules golden cases
python3 -m scripts.run_replay_pilot_set --stop-after-gameweek 1
python3 -m scripts.inventory_data_estate       # scan data/raw → data-estate inventory
python3 -m scripts.build_warehouse             # Parquet + DuckDB under data/warehouse/
```

Raw snapshots stay under `data/` (gitignored). The skeleton writes `reports/gameweeks/skeleton-gw3/`.

## Work package status

| Package | Status |
|---|---|
| WP-01 Rules audit | Draft complete — launch re-verification pending |
| WP-02 Source governance (Tier 1) | Complete for Section 6.1; only FPL endpoints enabled |
| WP-03 Canonical data model | Schemas + point-in-time contract + examples |
| WP-04 Historical-data assessment | Profiles + identity rates + news feasibility in `docs/data-sources/wp04/` |
| WP-06 Rules/scoring engine | Core scoring + validator families covered; official-points sample deferred |
| Snapshotter | Runnable (daily cadence documented) |
| Walking skeleton | Runnable and reproducible |
| WP-05 Baseline forecasting | Baselines + time-based eval — `docs/data-sources/wp05/` |
| WP-07 Optimisation | Transparent solver + golden case — `docs/optimisation/wp07-status.md` |
| WP-08 Evidence pipeline | Record lifecycle + escalation/injection — `docs/evidence/wp08-status.md` |
| WP-09 Decision record / replay | GDR schema + harness — `docs/evaluation/wp09-status.md` |
| WP-10 Deferred interfaces | Interface-only notes — `docs/architecture/deferred/` |
| Phase 1 packages | WP-01…WP-10 complete pending Proposed ADR ratifications |

## Repository layout

See [Section 20 of the plan](docs/plan.md#20-suggested-repository-structure). Raw data, credentials, browser state and generated secrets are excluded from version control.
