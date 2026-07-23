# Build immutable live-shadow FPL episodes from manual manager state

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It follows `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a user can take one immutable capture of the public official FPL endpoints and one manually completed manager-state file, then run a local command that produces a schema-valid live-shadow benchmark episode. The episode binds the exact source bytes, season rules, manager finances, deadline-safe feature view, resource budget and fixed five policy arms into reproducible content hashes. The same inputs reproduce the same episode; stale, inconsistent, post-cutoff, unauthenticated or altered inputs fail with actionable errors.

This work is deliberately read-only. It does not call authenticated manager endpoints, use browser state, expose credentials or modify an FPL team. The resulting episode is a decision input for advisory and shadow evaluation. Its future Gameweek outcome does not yet exist at build time, so the builder creates an immutable pending-outcome envelope containing no realised values. A later post-Gameweek process may link a separate revealed outcome only after proposals have been frozen.

## Progress

- [x] (2026-07-23 08:06Z) Imported the 28-record Beads JSONL, confirmed no other Bead is in progress, created `agent/fpl-bsw-10-live-episodes`, and claimed `FPL-bsw.10`.
- [x] (2026-07-23 08:18Z) Read the project plan, ADR-0005, benchmark protocol, episode schema, snapshot acquisition boundary, data-quality and deadline-view code, rules activation, squad validation and the historical episode builder.
- [x] (2026-07-23 08:25Z) Resolved the live-outcome and manager-state contract decisions in this plan.
- [x] (2026-07-23 08:30Z) Added red integration contracts covering valid construction, source and cutoff integrity, manager-state validation, rules activation, outcome isolation, determinism and immutable reruns; the intended initial failure was the missing builder module.
- [x] (2026-07-23 08:35Z) Implemented the normalised manager-state schema and validator, including snapshot-resolved identity, rules-derived selling price, strict squad/finance/chip checks and secret-bearing field rejection.
- [x] (2026-07-23 08:39Z) Implemented official capture verification, governed temporal observations, enforced quality evaluation, deadline feature materialisation and immutable live-episode construction.
- [x] (2026-07-23 08:41Z) Implemented the sealed pending-outcome schema and local-only command-line interface.
- [x] (2026-07-23 08:42Z) Expanded the manual template to all 15 position slots, both chip halves, pseudonymous identity and explicit no-secret guidance.
- [x] (2026-07-23 08:42Z) Exercised the CLI twice against an offline capture with identical results, proved current live rules fail before output creation, compiled all Python, passed 220 applicable repository tests and recorded the two full-suite environment-only Parquet failures.

## Surprises & Discoveries

- Observation: The live 2026/27 rules catalogue intentionally cannot activate yet.
  Evidence: `python -m scripts.verify_ruleset_activation control/rules/2026-27.yaml` reports one malformed provisional chip-boundary value plus ten unapproved inherited rules. The builder must therefore work with validated fixture rules while continuing to fail closed for real 2026/27 episodes.
- Observation: `materialise_deadline_view` selects one latest quality report per source, while a live capture contains separate bootstrap and fixtures endpoint manifests with the same source ID.
  Evidence: `src/features/deadline_view.py::_select_quality_reports` keys reports by `source_id` and rejects equal-time ambiguity. The live builder must quality-check the capture as one aggregate source snapshot while retaining both endpoint artefact hashes in the episode manifest.
- Observation: A live pre-deadline outcome cannot have the hash of final points because those values do not exist yet.
  Evidence: `control/schemas/benchmark/episode-manifest.json` requires a hidden outcome content hash, while the historical builder can satisfy it only because replay outcomes already exist. Live construction needs a content-addressed pending envelope with no result fields.
- Observation: ADR-0005 requires manager-state capture from Gameweek 1 so purchase and selling prices are never reconstructed from incomplete history.
  Evidence: `docs/decisions/0005-manual-manager-state-entry.md` explicitly chooses manual entry starting at Gameweek 1 and defers authenticated automation.
- Observation: A source label and body hash alone do not prove an endpoint came from the official service.
  Evidence: The capture command accepts a configurable base URL for offline tests. The builder now requires `https://fantasy.premierleague.com`, validates the source-manifest schema, and recomputes each manifest identity from origin, body hash, status and schema fingerprint.
- Observation: Freshness must measure when manager state was observed, not merely when the file became available to the pipeline.
  Evidence: A deliberately old `observed_at` with a recent `available_at` now fails the six-hour gate; otherwise delayed transcription could make stale account state appear fresh.
- Observation: The local Python 3.14 environment lacks the declared Parquet engine.
  Evidence: The authoritative full run produced 214 passing tests and two walking-skeleton failures at `pandas.to_parquet` because neither `pyarrow` nor `fastparquet` is installed. The complete applicable run excluding that pre-existing dependency-only file passed 220 tests; CI installs declared dependencies.

## Decision Log

- Decision: Treat a complete capture summary plus its exact bootstrap and fixtures bodies as the only official source input for v1 live episodes.
  Rationale: The existing capture process is registered, public, immutable, unauthenticated and already records endpoint hashes. Re-fetching during episode construction would destroy reproducibility and introduce network and timing variance.
  Date/Author: 2026-07-23 / Codex
- Decision: Parse the public bodies into governed temporal observations, evaluate them as one aggregate FPL capture, and pass them through `materialise_deadline_view`.
  Rationale: Bead `FPL-bsw.20` already defines source precedence, cutoff filtering, quality lineage and degraded optional features. Reusing that boundary makes live and historical feature provenance consistent without pretending the two endpoint bodies are different sources.
  Date/Author: 2026-07-23 / Codex
- Decision: Add `control/schemas/benchmark/manager-state.json` for the normalised artefact and retain `control/templates/manager-state-entry.json` as the human input example.
  Rationale: Manual input may contain notes and friendly names, but policy arms need a strict, minimal, content-addressed state with validated identities, prices and ruleset provenance.
  Date/Author: 2026-07-23 / Codex
- Decision: Recalculate current and selling prices from the snapshot and purchase price, rejecting any conflicting manual derived values.
  Rationale: Selling-price errors compound across decisions. Derived financial truth must come from exact source prices and the active versioned selling rule, not unverified transcription.
  Date/Author: 2026-07-23 / Codex
- Decision: Require a pseudonymous `manager_id`, full remaining chip inventory and chip history in manual state; never include entry IDs, credentials, cookies or personal names.
  Rationale: The live cohort needs stable experimental clustering without storing account identifiers or secrets. Full chip provenance is needed for later longitudinal transitions.
  Date/Author: 2026-07-23 / Codex
- Decision: Build Gameweek 1 as the controlled primary path. Later Gameweeks are permitted only when chip history, purchase prices and current financial state validate completely; nothing is inferred from incomplete history.
  Rationale: This honours ADR-0005 while making the validator useful for subsequent weekly manual updates.
  Date/Author: 2026-07-23 / Codex
- Decision: Add `control/schemas/benchmark/pending-outcome.json`; hash that envelope for `hidden_outcome_ref`, and forbid realised points, player outcomes, scores or result payloads.
  Rationale: This satisfies the episode reference contract honestly. The pending envelope is a commitment to isolation and reveal order, not a false commitment to unknown future values.
  Date/Author: 2026-07-23 / Codex
- Decision: The episode `created_at` is the deterministic latest availability time of its input artefacts rather than wall-clock build time.
  Rationale: An immutable rebuild must not conflict merely because it ran later. The observed pairing hash already excludes `created_at`, but deterministic artefact bytes are still preferable.
  Date/Author: 2026-07-23 / Codex

## Outcomes & Retrospective

Bead 10 is implemented as a complete local, read-only live-shadow construction path. A complete official public capture and strict manual manager entry now produce seven immutable artefacts: normalised manager state, deadline feature view, forecast-uncertainty record, pending-outcome envelope, canonical rules bytes, schema-valid episode manifest and a row-safe episode index. The same CLI invocation safely reuses byte-identical artefacts and returns identical hashes.

The implementation is deliberately stricter than the initial happy path. It recomputes endpoint manifest identities, pins the official HTTPS host, rejects altered body/schema/hash evidence, measures freshness from observation time, refuses numeric account-like manager IDs and unsupported secret-bearing fields, recalculates selling prices, enforces exact chip inventory/history and keeps all result values outside the observed episode. Current 2026/27 construction remains fail-closed until the rules catalogue is activatable.

Validation evidence: 22 live builder/CLI tests passed; the combined capture slice passed 25 tests; the full applicable repository suite passed 220 tests; `compileall` and `git diff --check` passed. A literal full `python -m pytest` run reached 214 passing tests and failed only the two pre-existing walking-skeleton Parquet writes because the local environment lacks the declared `pyarrow` dependency. No dependency was installed and no network or authenticated FPL action occurred.

## Context and Orientation

An FPL snapshot is the exact body and metadata captured from a public endpoint by `scripts/capture_fpl_live_shadow.py` and `src/ingestion/acquisition.py`. A capture summary points to two required endpoint artefacts: `/api/bootstrap-static/`, containing players, teams, positions, events and deadlines, and `/api/fixtures/`, containing the fixture schedule. Every body has a SHA-256 hash and an observed timestamp. Episode construction reads these files; it never performs a network request.

A manual manager-state entry is the owner-completed JSON template at `control/templates/manager-state-entry.json`. It describes the pseudonymous manager, season, Gameweek, timestamps, bank, free transfers, remaining chips, chip history and the 15 players with their purchase and displayed selling prices. The normaliser in new file `src/orchestration/manager_state.py` checks that input against the exact snapshot catalogue and active rules. Its output is the strict content-addressed manager-state artefact validated by new schema `control/schemas/benchmark/manager-state.json`.

A deadline-safe feature view is the result of `src/features/deadline_view.py::materialise_deadline_view`. It admits only quality-approved temporal observations whose `available_at` is at or before the episode cutoff. The live adapter will expose official ownership percentage, fixture state and player status observations. Player status is optional and produces an explicit degraded record when absent; ownership and the current Gameweek fixture slate are required.

The public episode manifest is validated by `control/schemas/benchmark/episode-manifest.json`. It contains hashes and references rather than embedding manager state, raw source bodies or outcomes. Its `mode` is `live_shadow`, its five fixed policy arms match ADR-0017, and every source artefact must be available no later than the cutoff. The observed episode hash is SHA-256 over canonical JSON excluding the pending hidden-outcome reference and deterministic creation timestamp.

Rules remain data. `src/scoring/rules_loader.py` loads the selected YAML and computes canonical bytes; `src/scoring.rules_activation.assert_ruleset_activatable` blocks unresolved live rules; `src/scoring.validator` supplies squad and selling-price validation. Tests use the fully validated 2025/26 catalogue as an offline fixture. The default CLI points at 2026/27 and is expected to refuse real construction until launch verification promotes its blockers.

## Plan of Work

First create `tests/integration/test_live_episode_builder.py`. Build a realistic 15-player public snapshot through the existing immutable capture function and a matching manual Gameweek 1 state. The initial test must fail because `src.orchestration.episode_builder` does not exist. Add cases for schema-valid output, exact source hashes, recalculated selling prices, stable observed hashes, pending-outcome isolation, identical reruns, conflicting immutable output, post-cutoff snapshots, stale manager entry, deadline mismatch, raw-body tampering, partial capture, wrong player identity, invalid squad composition, wrong selling price, invalid transfers/chips and non-activatable live rules.

Then create `control/schemas/benchmark/manager-state.json` and `src/orchestration/manager_state.py`. Define `ManagerStateError`. Parse timezone-aware timestamps into canonical UTC; require `observed_at <= available_at <= decision_cutoff <= deadline`; enforce the configured six-hour maximum manual-state age; load and activate the ruleset; resolve every manual player against bootstrap ID, optional code, team and position; convert official integer tenths to millions; calculate selling price from purchase and current price; validate unique players, positions, club limits, bank, free-transfer range, chip inventory/history and the Gameweek 1 initial budget. Emit sorted squad and chip records, useful financial totals, provenance `manual_entry`, authentication `none`, the ruleset identity and a content hash.

Create `control/schemas/benchmark/pending-outcome.json` for an envelope containing version, ID, episode ID, season, Gameweek, status `pending`, `reveal_after: proposal_frozen`, `contains_outcome_values: false` and a content hash. The schema must use `additionalProperties: false`, so adding realised points or scores fails validation.

Create `src/orchestration/episode_builder.py`. Define `LiveEpisodeError`, canonical JSON helpers and immutable writers. Load and verify the capture summary and both endpoint bodies, including no-authentication/no-execution flags, success status, individual SHA-256 hashes, capture identity and observed timestamp. Parse bootstrap and fixtures shapes, cross-check the season Gameweek deadline, build temporal observations, evaluate one aggregate quality report in enforce mode, and materialise the deadline-safe feature view. Normalise manager state, create an explicit forecast-uncertainty artefact from feature degradation, create the pending outcome, assemble and validate the episode manifest, calculate the observed episode pairing hash, and write all derived JSON plus canonical rules bytes without overwriting different content.

Create `scripts/build_live_episode.py`. It accepts `--capture-summary`, `--manager-state`, `--rules`, `--out`, optional `--code-commit`, and optional compatibility-policy JSON. It prints a safe summary containing episode ID, observed episode hash, ruleset hash, manager-state hash, feature-view hash, pending-outcome hash and degraded features. It never prints raw player state or snapshot bodies. Normal validation failures return a non-zero status with a concise `refused:` message.

Finally expand `control/templates/manager-state-entry.json` to be a complete pseudonymous 15-player example shape with all required state fields and an explicit warning that values must be copied manually from the current account. Keep placeholders rather than real manager or player data. Run the offline fixture command twice, inspect the artefacts, and update this plan and Beads evidence.

## Concrete Steps

Work from `C:/Users/Alastair/FPL` on branch `agent/fpl-bsw-10-live-episodes`.

After adding the first test, run:

    python -m pytest tests/integration/test_live_episode_builder.py -q

The expected initial result is an import failure for `src.orchestration.episode_builder`. After implementation, every test in that file must pass.

Run the related contract slice:

    python -m pytest tests/integration/test_live_episode_builder.py tests/integration/test_live_shadow_capture.py tests/historical-replay/test_deadline_feature_view.py tests/contracts/test_benchmark_schemas.py tests/unit/test_policy_state.py -q

Run the full applicable repository suite:

    python -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py

The pre-change baseline was 198 passed. The final count must be higher with no regression. Also run:

    python -m compileall -q src scripts tests
    git diff --check

The CLI integration test must exercise `python -m scripts.build_live_episode` against temporary fixture files and observe exit code zero, a `live_shadow` episode manifest and identical hashes on rerun. A second invocation with `control/rules/2026-27.yaml` must fail before writing an episode and identify unresolved activation blockers.

## Validation and Acceptance

The feature is accepted when one complete public fixture capture plus one valid manual state produces `manager-state.json`, `feature-view.json`, `forecast-uncertainty.json`, `pending-outcome.json`, `ruleset.yaml`, `episode-manifest.json` and `episode-index.json`. All JSON artefacts validate against their schemas where a schema exists. The episode records the exact two endpoint manifest IDs and body hashes, and every source availability time is at or before cutoff.

The manager state contains 15 unique, snapshot-resolved players with rules-derived position and club constraints, exact current and selling prices, valid bank/free transfers/chips and no account identifier or secret. Altering a body after capture, entering a wrong player code, team, price or deadline, using an incomplete capture, or exceeding the staleness threshold must fail before any episode manifest is written.

The pending outcome contains no result values and the public manifest contains only its ID and hash. Attempting to add realised points or scores must fail schema validation. Identical inputs and code commit reproduce every content hash and safely reuse identical files; a different input targeting the same output directory raises `FileExistsError` rather than overwriting evidence.

The current unresolved 2026/27 catalogue must remain blocked. A validated catalogue used by fixtures must build successfully, proving that no code change will be needed when official launch verification completes.

## Idempotence and Recovery

All writes are create-once. Existing byte-identical files are reused and different files are never replaced. If a build stops halfway, rerunning with identical inputs completes missing artefacts and reuses finished ones. The command never deletes data, changes source captures, modifies the manager input, accesses a network or authenticates to FPL. If validation fails, correct the input or use a new versioned output directory; do not edit a frozen artefact.

## Artifacts and Notes

The live 2026/27 activation preflight currently returns `activatable: false` with eleven blockers. That failure is expected and is a launch gate, not a defect in the episode builder.

The source quality policy currently allows six hours before recommending FPL snapshot degradation. Manual manager-state age will use the same six-hour conservative default in v1 so the snapshot and personal financial state cannot silently represent different decision moments.

## Interfaces and Dependencies

Use only the standard library plus existing PyYAML and jsonschema dependencies. Do not install packages or perform network collection.

In `src/orchestration/manager_state.py`, provide:

    class ManagerStateError(ValueError): ...

    def normalise_manager_state(
        entry: Mapping[str, Any],
        *,
        bootstrap: Mapping[str, Any],
        rules: Mapping[str, Any],
        ruleset_sha256: str,
        compatibility_policy: Iterable[Mapping[str, Any]] = (),
        max_age_seconds: int = 21600,
    ) -> dict[str, Any]: ...

In `src/orchestration/episode_builder.py`, provide:

    class LiveEpisodeError(ValueError): ...

    def build_live_episode(
        *,
        capture_summary_path: Path,
        manager_state_path: Path,
        out_dir: Path,
        rules_path: Path,
        code_commit: str | None = None,
        compatibility_policy: Iterable[Mapping[str, Any]] = (),
    ) -> dict[str, Any]: ...

The return value is the safe episode index and must not include raw source bodies, the full manager squad or any outcome values. `scripts/build_live_episode.py` owns argument parsing and reporting only. `tests/integration/test_live_episode_builder.py` owns end-to-end behavioural proof.

Plan revision note (2026-07-23): Initial plan created after the owner approved full rather than narrowed Bead 10 scope. It adds explicit normalised manager-state and pending-outcome contracts because these are required for truthful live construction and were absent from the original file list.

Plan revision note (2026-07-23 08:42Z): Completed implementation and validation. Added official-host/source-manifest recomputation, strict unsupported-field rejection and observation-time freshness after adversarial review of the first green implementation.
