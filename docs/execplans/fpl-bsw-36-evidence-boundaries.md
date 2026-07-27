# Persist availability and target evidence at decision boundaries

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a weekly FPL decision can use an absence report for as long as that report remains valid without copying it into every gameweek. A recovery must be explicit, expired and conflicting evidence remains auditable, and silence is treated as “unknown” rather than “available”. The evidence pack presented to an agent will also rank evidence by whether it can plausibly change a close transfer, lineup, captaincy, or chip decision. Tests will demonstrate a Timber-style absence persisting from GW34 through GW36 and deterministic ranking around declared decision margins.

## Progress

- [x] (2026-07-27 08:46Z) Inspected the evidence lifecycle, historical weekly programme, availability schema, Timber evidence bundles, and schema contract tests.
- [x] (2026-07-27 08:46Z) Chose an append-only, content-hashed ledger with explicit supersession and conservative recovery semantics.
- [x] (2026-07-27 09:05Z) Implemented the availability ledger and lifecycle validation.
- [x] (2026-07-27 09:05Z) Implemented deterministic boundary-aware retrieval and shadow-effect attribution.
- [x] (2026-07-27 09:07Z) Added the weekly programme adapter, backward-compatible schema extension, policy documentation, and tests.
- [x] (2026-07-27 10:08Z) Ran focused and full regression suites, recorded evidence, closed the Bead, and prepared the verified change for commit and push.

## Surprises & Discoveries

- Observation: The existing `player_availability` entity is a point-in-time official-feed observation, not an evidence claim lifecycle.
  Evidence: Its schema requires only player, status, observation/availability timestamps, and provenance. The extension must preserve that existing example and contract.

- Observation: Historical Timber bundles repeat the absence in GW34, GW35, and GW36, each with a new expiry.
  Evidence: The replay worked only because each bundle manually restated the condition; a live process needs ledger persistence between deadlines.

## Decision Log

- Decision: Keep every claim append-only and compute active state at a supplied decision cutoff.
  Rationale: This makes replay reproducible and lets reviewers see stale, superseded, conflicting, and active records without mutating history.
  Date/Author: 2026-07-27 / Codex

- Decision: Treat absence, doubt, and recovery as claims; never infer recovery from missing news.
  Rationale: Missing evidence is not positive availability evidence. A recovery claim must name the claims it supersedes and state the recovery condition that was observed.
  Date/Author: 2026-07-27 / Codex

- Decision: Block conflicted players from accepted evidence rather than automatically choosing the latest or highest-confidence claim.
  Rationale: Automated conflict resolution could silently turn source disagreement into a material FPL action. Visibility and abstention are safer.
  Date/Author: 2026-07-27 / Codex

- Decision: Rank boundaries deterministically by ability to flip, then smaller margin, larger estimated swing, confidence, and stable identifiers.
  Rationale: The order focuses limited agent attention on decisions that evidence can change while remaining reproducible.
  Date/Author: 2026-07-27 / Codex

## Outcomes & Retrospective

The implementation now carries cutoff-safe availability across weeks, requires explicit evidence for recovery from an active absence, preserves stale/superseded/conflicting history, de-duplicates corroborating same-status claims, and creates a bounded decision-margin evidence pack. The weekly adapter and shadow-effect artifact keep state, evidence acceptance, plan changes, transfer changes, and outcome changes independently inspectable. The focused suite passed 13 tests, the historical and temporal regressions passed 11 tests, and the complete repository suite passed all 521 tests in the existing Python 3.13 virtual environment. The main limitation is deliberate: boundary swing values are engine inputs and are not learned or calibrated by this bead.

## Context and Orientation

`src/evidence/lifecycle.py` validates evidence timestamps and confidence at a decision cutoff. It currently treats claims independently and does not carry a player’s state across weeks. The new `src/evidence/availability_ledger.py` will own the append-only state and will reuse lifecycle timestamp and eligibility rules.

`src/orchestration/weekly_evidence_programme.py` replays selected historical evidence bundles. It currently applies only the bundle supplied for a particular week. An additive helper will build a live-shaped weekly context without changing sealed historical replay output.

`src/orchestration/boundary_retrieval.py` will create a bounded evidence pack. A “decision boundary” is a choice with an incumbent, an alternative, and a projected-points margin, such as captain A leading captain B by 0.4 points. An evidence claim has an estimated maximum swing. When that confidence-adjusted swing equals or exceeds the margin, it can plausibly flip the choice.

The existing `control/schemas/performance/player_availability.json` and its example describe official FPL feed observations. The schema will gain optional ledger fields while retaining the existing required fields and valid example.

## Plan of Work

First, add ledger construction, append, integrity validation, and cutoff projection in `src/evidence/availability_ledger.py`. Validate temporal ordering, unique claim identifiers, explicit supersession, and recovery conditions. Preserve all claim history and return active, stale, superseded, conflicting, and abstained player views.

Second, add boundary pack construction and shadow-effect attribution in `src/orchestration/boundary_retrieval.py`. Validate decision types and numeric inputs, calculate confidence-adjusted impact, rank deterministically, enforce a fixed evidence limit, and separate accepted evidence from plan, transfer, and realised-score changes.

Third, add an adapter in `src/orchestration/weekly_evidence_programme.py` that combines a ledger projection with boundaries for a deadline. Extend `src/evidence/lifecycle.py` with availability status constants and recovery-condition validation used by the ledger. Expand the availability schema without invalidating the official-feed example.

Finally, add focused tests and `docs/evaluation/evidence-boundary-policy.md`. Run the focused suites, schema contracts, historical replay regressions, and the complete test suite.

## Concrete Steps

All commands run from `C:\Users\Alastair\FPL`.

Run focused tests:

    python -m pytest tests/evidence/test_availability_ledger.py tests/agent-evals/test_boundary_retrieval.py tests/contracts/test_schemas.py -q

Run historical programme regressions:

    python -m pytest tests/historical-replay/test_weekly_evidence_programme.py -q

Run the complete suite:

    python -m pytest -q

Expected focused behavior includes an active Timber absence at three successive decision cutoffs from one claim, an abstention after its expiry, blocked automatic recovery without a recovery condition, visible unresolved conflicts, and identical boundary ordering for identical inputs.

## Validation and Acceptance

The ledger test must show that one unexpired absence remains active across GW34, GW35, and GW36 without reinsertion. At a cutoff equal to or later than expiry, the claim must appear under stale history and the player must be an abstention.

A recovery must fail validation unless it explicitly supersedes the active absence and records a supported recovery condition. Conflicting active statuses must remain in the pack and must not appear as accepted evidence.

Boundary retrieval must return the same sealed artifact for the same logical inputs regardless of input order. It must rank evidence capable of flipping the narrowest material boundary before evidence that cannot alter any supplied choice. Missing player news must produce a named abstention rather than an availability assumption.

The attribution artifact must expose four distinct facts: accepted evidence identifiers, whether the plan changed, whether transfers changed, and realised score change or a pending value before reveal.

## Idempotence and Recovery

Ledger operations return new dictionaries and never rewrite an input ledger. Appending an existing claim identifier is rejected. Sealed artifacts can be regenerated from the same inputs and should produce the same content hash. Test and documentation commands are safe to repeat.

No migration or destructive operation is required. If a test fails, retain the append-only input fixtures, correct the smallest responsible function, and rerun the focused suite before the full suite.

## Artifacts and Notes

The principal proof artifacts are deterministic `content_sha256` values on ledger views, boundary packs, weekly contexts, and shadow-effect records. Validation produced:

    python -m pytest tests/evidence/test_availability_ledger.py tests/agent-evals/test_boundary_retrieval.py tests/contracts/test_schemas.py -q
    13 passed in 0.95s

    python -m pytest tests/historical-replay/test_weekly_evidence_programme.py tests/contracts/test_temporal_observation.py -q
    11 passed in 29.79s

    .\.venv\Scripts\python.exe -m pytest -q
    521 passed in 286.81s

A first full run under the machine-wide Python 3.14 produced 519 passes and two unrelated failures because that interpreter lacked a Parquet engine. No dependency was installed; rerunning under the repository's existing environment, which already contains `pyarrow`, proved the full suite clean.

## Interfaces and Dependencies

No new package is required. The implementation uses Python’s standard library and the repository’s existing hash and evidence-policy helpers.

`src.evidence.availability_ledger` will expose:

    new_availability_ledger(*, season: str, created_at: str) -> dict[str, Any]
    append_availability_claim(ledger, claim) -> dict[str, Any]
    project_availability(ledger, *, decision_at: str, player_uids=()) -> dict[str, Any]
    validate_availability_ledger(ledger) -> None

`src.orchestration.boundary_retrieval` will expose:

    build_boundary_evidence_pack(*, availability_view, boundaries, max_evidence=12) -> dict[str, Any]
    build_shadow_effect_record(*, accepted_evidence_ids, control_plan, evidence_plan, control_score=None, evidence_score=None) -> dict[str, Any]

`src.orchestration.weekly_evidence_programme` will expose:

    build_weekly_evidence_context(*, ledger, decision_at, boundaries, player_uids=(), max_evidence=12) -> dict[str, Any]

Plan revision note (2026-07-27): Initial plan created after repository and historical-fixture inspection. It records the conservative persistence and deterministic retrieval design selected for `FPL-bsw.36`.


Plan revision note (2026-07-27): Recorded the implemented de-duplication and expired-claim behavior plus complete validation evidence; only Bead and Git publication steps remain.

Plan revision note (2026-07-27): Marked the implementation and Bead lifecycle complete after the recorded 521-test clean run; the verified tree is ready for Git publication.
