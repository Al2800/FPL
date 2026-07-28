# Event-Sourced Fixture State and DGW/BGW Detection

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Convert successive immutable official FPL fixture snapshots into a deterministic
revision history and reconstruct the schedule exactly as it was available at a
decision cutoff. Expose per-team Gameweek fixture counts so blank, single and
double Gameweeks flow into the existing same-cutoff multiweek projection without
changing sealed historical replay artifacts or v1 policy constants.

## Progress

- [x] (2026-07-28 18:29Z) Created and claimed `FPL-dah` after confirming no
  overlap with active Beads.
- [x] (2026-07-28 18:32Z) Audited immutable acquisition metadata, fixture
  schemas, live episode assembly, horizon projection and chip valuation.
- [x] (2026-07-28 18:51Z) Implemented deterministic snapshot normalization,
  revision events, point-in-time reconstruction and fixture-count artifacts.
- [x] (2026-07-28 18:58Z) Wired the fixture-state view into the existing
  same-cutoff horizon builder with complete/fallback lineage.
- [x] (2026-07-28 19:23Z) Added postponement, reschedule, cutoff, ambiguity,
  lineage, blank-current-week and projection contracts; all 708 tests pass.

## Discoveries

- Existing `fixtures.json` and `fixture_revisions.json` schemas already define
  current-view and revision identities, timestamps and provenance.
- Official acquisition stores the fixtures body beside immutable metadata with
  `observed_at` and a verified SHA-256.
- `build_same_cutoff_horizon` already sums one component per fixture, so it
  naturally produces 0/1/2 fixture projections when supplied the correct
  point-in-time schedule. The missing layer is schedule history and lineage.
- Historical multiweek/chip counterfactuals deliberately reconstruct schedules
  from stripped later episodes and are marked exploratory. W1 must not rewrite
  those sealed paths.
- The old future projection derived per-fixture minutes only by dividing the
  executable week's aggregate minutes by its fixture count. In a current blank,
  this silently propagated zero minutes into later non-blank weeks. The live
  forecast now exposes its already-computed per-fixture estimate, and the bound
  horizon refuses to project forward without it.

## Decisions

- Treat FPL fixture `id` as stable within a named season and derive a canonical
  `fixture:<season>:<id>` identity.
- Order snapshots by `available_at`, then `observed_at`; refuse two different
  snapshots with the same availability instant because their order is
  unknowable.
- Store full schedule state in each accepted revision event. This is slightly
  larger than a field diff but makes replay, hashing and audit straightforward.
- An absent fixture in a later full-season endpoint snapshot becomes a removal
  event; a later reappearance becomes a restoration event.
- Keep behavior changes out of chip deployment policy. W1 supplies and binds
  fixture counts; W2/W3 own valuation and deployment-policy changes.

## Implementation

Add `src/data/fixture_state.py` with:

- acquisition-manifest and in-memory snapshot normalization;
- deterministic revision-log construction;
- inclusive `available_at <= cutoff` reconstruction;
- per-team per-Gameweek count classification;
- conversion into the fixture-week contract used by multiweek projection.

Extend `src/orchestration/multiweek_challenger.py` with a wrapper that builds the
horizon from a fixture-state artifact and records its hash in every horizon
week. Extend `src/optimisation/multiweek.py` only to validate that bound
fixture-count/component fields agree; unbound legacy horizons remain unchanged.

## Validation

Focused:

    .\.venv\Scripts\python.exe -m pytest tests/data/test_fixture_state.py tests/optimisation/test_fixture_count_projection.py tests/optimisation/test_multiweek.py -q

Full:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

W1 now provides the production-shaped fixture input that W2 and W3 need. Raw
official endpoint snapshots are normalized to schedule-only rows, outcome fields
are discarded, changes become deterministic revision events, and reconstruction
uses inclusive `available_at <= cutoff`. The derived count table explicitly
classifies blanks, singles, doubles and higher multiples for every declared team
and Gameweek.

The live same-cutoff horizon binds both the reconstructed fixture-state hash and
the count-table hash. Counts must match projected components per player; the
reviewed executable week must agree with the same state; both normal and
deterministic-fallback plans retain the lineage. Existing unbound historical
replay paths and v1 policies reproduce unchanged.

Validation completed on 2026-07-28:

- W1 fixture, projection and existing multiweek contracts: 17 passed;
- live forecast plus W1 focused contracts: 31 passed;
- forecasting, chip, schema and optimisation regressions: 111 passed;
- complete repository suite: 708 passed in 471.06 seconds.
