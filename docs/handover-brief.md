# Handover brief: first implementation agent

**Date:** 21 July 2026
**Scope:** Section 26 steps 1 and 2 only — the FPL-endpoint registry entry, the snapshotter, and the walking skeleton. Nothing else until these run.

## Read first

`AGENTS.md`, then `docs/plan.md` — especially Sections 6 (sources and registry), 10.1 (raw layer), 15 (operating cycle), 17.6 (why day-one capture is time-critical), 18 Phase 1 (walking skeleton) and 26 (sequencing). Decisions already taken are in `docs/decisions/` and are not to be relitigated.

## Task 1 — FPL-endpoint registry entry (WP-02, minimal)

- Create `control/sources/source-registry.yaml` with one enabled entry: the official FPL JSON endpoints, completing every Section 6.2 field.
- `licence_status` and `allowed_use` must reflect ADR-0001 and ADR-0002: private, non-commercial analysis; local retention; no redistribution.
- Other sources may be drafted but stay `enabled: false` until their terms are reviewed (WP-02 proper).

## Task 2 — Snapshotter

- Scheduled local capture of `bootstrap-static` and `fixtures` (add `event/{gw}/live` once the season runs) into `data/raw/fpl/`, per Section 10.1: immutable files carrying request URL, HTTP status, `observed_at`, content hash, source-registry version and schema-detection result.
- The endpoints may still be down pre-launch (Section 6.1): handle 404s and off-season resets gracefully and begin capturing the moment they return. Failed and unexpected responses are still operational evidence — keep them.
- Raw data stays out of Git (`.gitignore` already excludes `data/`).

## Task 3 — Walking skeleton (Phase 1 milestone)

One historical Gameweek end-to-end with crude components: historical snapshot in → normalised tables → naive projections → deterministic squad/transfer validation → one candidate plan → a rendered Gameweek Decision Record (Section 16), reproducible on rerun. Crude is expected; end-to-end is the point.

## Acceptance

- The registry entry satisfies the WP-02 "Done when" for this one source.
- The snapshotter runs on a schedule and its outputs carry all Section 10.1 metadata.
- The skeleton replays one historical Gameweek and its decision record reproduces on rerun (Section 3.2, criterion 6).

## Hard boundaries

- No other collectors enabled. No LLM calls and no API keys — nothing in this brief needs them.
- No credentials or raw data in Git. Python; Parquet and DuckDB; SQLite for operational state (ADR-0008).
- Rules are data (`control/rules/`) even in crude form — do not hard-code budget, formation or transfer values (AGENTS.md rule 1).
- Open Decisions 6–14 are not yours to settle: where the work forces a choice (for example the orchestration substrate), implement the simplest thing that works — plain Python — and record an ADR proposal for owner ratification.
