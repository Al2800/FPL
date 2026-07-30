# FPL-757 — Re-derive immutable launch context for a changed official universe

This ExecPlan is a living document. It is maintained under `C:\Users\Alastair\.codex\.agent\PLANS.md`; its `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections must be updated as implementation proceeds.

## Purpose / Big Picture

The reviewed 27 July 2026 launch context is intentionally tied to one exact FPL bootstrap hash. When the official player universe changes, the live checkpoint must not reuse it. After this work, an operator can run one offline command over an immutable official bootstrap, a completed-2025/26 stable-code roster and the reviewed World Cup CSV. The command will create a new, self-hashed context plus a manifest under an ignored content-addressed snapshot directory. It will state what changed in player and team identity terms. The result can be passed explicitly to the FPL-756 preseason-capture CLI; it will be admitted only to the exact same bootstrap bytes.

No source is collected by this task. It only processes supplied local files, creates no account action, and does not mutate the existing `control/identities/2026-27-launch-context.json`.

## Progress

- [x] 2026-07-30 14:49Z: Claimed the now-unblocked Bead after FPL-756 was closed and pushed; confirmed no active file overlap.
- [x] 2026-07-30 14:52Z: Read the project plan, previous context, forecast adapter, historic design notes, World Cup schema and existing contracts.
- [x] 2026-07-30 14:52Z: Established that no `scripts/build_launch_context.py` exists in the tracked tree, and raw FPL/Vaastav data are intentionally absent from this linked worktree.
- [x] 2026-07-30 15:11Z: Added pure context derivation, strict input parsing, temporal gates, content-addressed immutable writer and output manifest verification.
- [x] 2026-07-30 15:18Z: Added the offline CLI, strict prior-roster documentation and deterministic unit/integration/CLI contracts.
- [x] 2026-07-30 15:23Z: Demonstrated matching admission and mismatched degradation; focused suite passed 43 and broader data/forecasting suite passed 138 with one expected private-data skip. Commit/push and Bead closure follow final tracker update.

## Surprises & Discoveries

- Observation: the pre-existing context was built from an unavailable-to-this-worktree raw data estate and exposes only final class lists/counts, not the complete earlier bootstrap roster needed to calculate additions/removals.
  Evidence: `control/identities/2026-27-launch-context.json` binds the earlier bootstrap hash but has no complete `elements` array; `.gitignore` excludes all `data/**` content.

- Observation: there is no tracked builder despite previous documentation describing derivation.
  Evidence: `rg --files` finds `src/forecasting/launch_context.py`, its tests and documentation, but no `scripts/build_launch_context.py`.

## Decision Log

- Decision: accept a strict, caller-supplied CSV prior roster with `code` and `team_code` as the rederivation input contract.
  Rationale: stable FPL code is the only allowed automatic player join, and prior team code is needed to distinguish a same-player club move from a new player. Mapping display names would make rederivation non-reproducible and risks an incorrect class.
  Date/Author: 2026-07-30 / Codex.

- Decision: write each result under `data/snapshots/2026-27/launch-context/<context-content-sha256>/` with a self-hashed manifest, input copies and a delta report.
  Rationale: the directory is ignored operational evidence, permits several reviewed contexts, and makes divergent inputs additive rather than an overwrite. The exact output path is determined only after the context is self-hashed.
  Date/Author: 2026-07-30 / Codex.

- Decision: calculate visible player-universe delta against the supplied 2025/26 roster, not by guessing an earlier 2026/27 universe.
  Rationale: the earlier full bootstrap is not available as a tracked dependency. The supplied roster supplies a deterministic baseline for added player codes, removed prior codes, changed team codes and promoted teams. A later point-to-point delta can be added only when both immutable bootstraps are present.
  Date/Author: 2026-07-30 / Codex.

- Decision: reject duplicate/blank official or prior stable codes and post-cutoff input availability. Retain blank, non-current or late World Cup rows only in deterministic degradation counts because the consumer already exposes them as excluded rows rather than silently joining them.
  Rationale: ambiguous player identity is unsafe, while the World Cup ledger has an established explicit degradation policy that preserves auditability.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

Completed implementation: `build_launch_context` now creates a new context directory at `data/snapshots/2026-27/launch-context/<context-content-sha256>/` containing raw bootstrap, prior roster, World Cup CSV, context and manifest. Tests prove add/remove/team-change deltas, duplicate/late/tampered failure paths, CLI output, byte-identical restart and FPL-756 exact-match admission. The only remaining live operational prerequisite is supplied local official bootstrap plus approved `code,team_code` 2025/26 roster bytes and their timestamp metadata; the builder intentionally does not fabricate or fetch either.

## Context and Orientation

`src/forecasting/launch_context.py` currently validates and applies an already-built context. `apply_launch_context` uses the four-class precedence `promoted_team`, `new_to_fpl`, `transferred_player`, then `established`, and uses only stable FPL player code for joins. `control/identities/2026-27-launch-context.json` is a reviewed historical control artifact. It binds bootstrap hash `605dd760…399b5`; it must remain byte-identical.

A bootstrap is the official `bootstrap-static` JSON object. It must include `teams` entries with `id`, `code`, `name`, and `elements` entries with `id`, `code`, `team`. A prior roster is a UTF-8 CSV with a header containing `code` and `team_code`; every row must have integer values. The World Cup file follows `control/identities/world-cup-2026-priors-template.csv` and retains its per-row `observed_at` timestamp. The operator gives all input observations and availability timestamps in ISO-8601 UTC form plus a decision cutoff. “Available” means the system was permitted to use the data; it must be strictly before the cutoff.

FPL-756, in `src/orchestration/preseason_snapshot.py`, binds the output only after its JSON self-hash, the World Cup raw hash and official bootstrap raw hash match. Its CLI accepts `--launch-context-path` and `--world-cup-priors-path` for this purpose.

## Plan of Work

Add a narrow builder API to `src/forecasting/launch_context.py`. `build_launch_context` will parse and validate input bytes, timestamps and identities; derive the four class lists; produce `universe_delta` and World Cup coverage; copy the exact three raw inputs to an ignored content-addressed output tree; and return a sealed manifest and context. Supporting errors will distinguish invalid inputs from immutable-path conflicts. The existing apply path will not be rewritten.

The context will include root `observed_at` and `available_at`, and `source_bindings` entries for `official_bootstrap`, `previous_season_players` and `world_cup_priors`. Each binding records source ID, raw SHA-256, observed timestamp and available timestamp. The produced `world_cup_policy`, risks, precedence and unknown policy preserve the existing reviewed policy rather than fitting historical outcomes.

Create `scripts/build_launch_context.py` as a no-network command. It must require all timestamp/cutoff inputs, read paths supplied by the user, invoke the pure builder, and print only output path, content hashes and deltas. It must not print file contents, credentials or unseen data.

Extend `tests/forecasting/test_launch_context.py` with fixture files and direct builder tests for exact repeatability, player addition/removal/team move classification, duplicate/tampered/late input rejection, additive output on changed inputs, immutable output verification and FPL-756 matching/mismatching checkpoint integration. Update `docs/data-sources/2026-27-launch-context.md` with the exact prior-roster schema and operator command.

## Concrete Steps

From `C:\Users\Alastair\FPL-pr-review`, implement and then run:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q tests\forecasting\test_launch_context.py tests\data\test_preseason_snapshot_capture.py

Expected outcome: all tests pass, including a successor context admitted by an FPL-756 matching fixture checkpoint and rejected as a named degraded family by a different bootstrap.

A live operator will later use this no-network form after a reviewed change:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe scripts\build_launch_context.py ^
      --season 2026-27 ^
      --bootstrap-file C:\path\to\bootstrap-static.json ^
      --bootstrap-observed-at 2026-08-03T12:00:00Z ^
      --bootstrap-available-at 2026-08-03T12:00:00Z ^
      --prior-roster-file C:\path\to\2025-26-prior-roster.csv ^
      --prior-roster-observed-at 2026-05-25T12:00:00Z ^
      --prior-roster-available-at 2026-05-25T12:00:00Z ^
      --world-cup-priors-file control\identities\world-cup-2026-priors.csv ^
      --world-cup-observed-at 2026-07-21T17:21:28Z ^
      --world-cup-available-at 2026-07-21T17:21:28Z ^
      --context-observed-at 2026-08-03T12:05:00Z ^
      --context-available-at 2026-08-03T12:05:00Z ^
      --decision-cutoff 2026-08-21T17:30:00Z

The command should print a `context_path`, `manifest_path`, `context_content_sha256`, exact input hashes and `universe_delta`. That context path is then explicitly passed to the checkpoint capture command; it never replaces the old control artifact.

## Validation and Acceptance

The tests must prove that an added current code appears in `new_player_codes`, a prior code absent from current appears in `universe_delta.removed_player_codes`, a common code with a changed team code appears in `transferred_player_codes`, and a current team code absent from prior roster appears in `promoted_teams`. Duplicate or blank stable codes, a JSON self-hash mismatch, a prior CSV header gap, and a timestamp at or after cutoff must fail without writing an output directory.

An identical build must return byte-identical context and manifest. Changed source bytes must produce a different content-addressed directory while retaining old bytes unchanged. A tampered copied output must fail a same-input re-run. A matching builder context must be `admitted` by a FPL-756 checkpoint; changing official bootstrap bytes must yield `official_bootstrap_hash_mismatch` with no bindable paths.

## Idempotence and Recovery

A build does not overwrite a named output. On a rerun the builder verifies the existing immutable context, manifest and input copies against their hashes; it returns the same result only if all bytes match. If a prior operation stopped halfway, rerun is safe because each immutable file is content-addressed. A conflict or invalid input means stop, preserve the earlier output and prepare a new reviewed input; never edit an old context to force admission.

## Artifacts and Notes

The output directory is intentionally ignored by Git because it contains local official/historical evidence. Commit only source code, tests, documentation, this ExecPlan and Bead metadata. The output manifest is the durable audit link from source data to the selected context. No raw source body belongs in the repository.

## Interfaces and Dependencies

At completion `src.forecasting.launch_context` exposes:

    class LaunchContextBuildError(LaunchContextError): ...
    class LaunchContextBuildConflict(LaunchContextBuildError): ...
    def build_launch_context(... ) -> dict[str, Any]: ...

It uses only the Python standard library and `src.ingestion.acquisition.content_hash`; no network client, database or new dependency is introduced. `scripts/build_launch_context.py` imports the function after adding repository root to `sys.path`. FPL-756 remains the sole admission gate; this builder supplies its context and World Cup paths.

Revision note (2026-07-30): initial plan created after inspecting the actual tracked tree. It resolves the missing-builder and unavailable-raw-data discoveries by using strict caller-supplied inputs and an ignored content-addressed operational output.

Revision note (2026-07-30 15:23Z): implementation completed. Added exact raw-byte FPL-756 integration after discovering that semantic JSON re-serialisation must not bypass the bootstrap-hash gate.
