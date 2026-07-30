# FPL-756 — Bind immutable launch context into preseason checkpoints

This ExecPlan is a living document. Maintain `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` while executing it.

## Purpose / Big Picture

A preseason checkpoint already seals official bootstrap, fixtures, rules and optional evidence. The reviewed launch context in `control/identities/2026-27-launch-context.json` describes the 27 July official player universe, and its linked World Cup priors are in `control/identities/world-cup-2026-priors.csv`. It must become a first-class optional `launch_context` family only when the exact current checkpoint bootstrap has the same content SHA-256 as the context’s recorded bootstrap binding.

A successful matching checkpoint will contain three content-addressed files inside its immutable checkpoint directory: the context JSON, World Cup CSV and a generated provenance envelope. Its sealed manifest will state all three raw digests, the context self-hash, official-bootstrap binding and temporal fields. A changed universe, tampered context, invalid binding or late context is never silently applied. A universe mismatch is an explicit degraded optional family with no typed context bytes. This task captures and binds context; it neither re-derives context nor changes the initial-15 optimiser.

## Progress

- [x] 2026-07-30: Took over the stale in-progress Bead after confirming no other live agent or overlapping dirty work, under owner instruction.
- [x] 2026-07-30: Read the full prior preseason capture ExecPlan, capture module, CLI, focused tests, current launch-context metadata and source registry.
- [x] 2026-07-30: Added the `launch_context` configuration/family contract and pre-write request binding.
- [x] 2026-07-30: Implemented content-addressed context/World-Cup/envelope binding with exact-universe, hash and temporal validation.
- [x] 2026-07-30: Added CLI defaults/overrides, six focused contract tests and the operational runbook section.
- [x] 2026-07-30: Focused test suite passed (38); fixture mismatch paths explicitly degrade. Commit/push and Bead closure remain after final review.

## Surprises & Discoveries

- Observation: the current context is validly self-hashed but binds official bootstrap SHA-256 `605dd760…399b5` observed 2026-07-27; the live capture on 2026-07-30 observed bootstrap SHA-256 `725c7d04…aad2`.
  Evidence: `control/identities/2026-27-launch-context.json` and the verified scheduler bootstrap report. Therefore the current weekly checkpoint must degrade its `launch_context` family until FPL-757 produces a successor.

- Observation: `world-cup-2026` remains intentionally disabled for new automated collection, but the committed World Cup priors are a reviewed derived input. Binding existing bytes must not enable a collector.
  Evidence: `control/sources/source-registry.yaml` marks its collection method manual and enabled false.

- Observation: the generic optional-artifact binder handles one artifact plus one sidecar; this family must preserve an additional CSV and must therefore add a narrow specialised binder instead of overloading unrelated evidence semantics.

## Decision Log

- Decision: treat launch context as a derived, hash-bound optional family rather than a newly collectable source.
  Rationale: all raw sources were reviewed when the context was built; FPL-756 must only consume existing local artifacts and cannot enable World Cup collection.
  Date/Author: 2026-07-30 / Codex.

- Decision: verify the context’s semantic self-hash and its recorded World Cup raw digest before copying anything into a checkpoint.
  Rationale: a raw file hash alone cannot prove the JSON context has not been semantically tampered with, and a matching bootstrap alone is insufficient if the World Cup input has changed.
  Date/Author: 2026-07-30 / Codex.

- Decision: a context/bootstrap mismatch is a degraded optional family, while malformed or hash-invalid local input is quarantined with a named reason.
  Rationale: mandatory official state remains useful, but no downstream consumer receives context bytes unless all bindings validate.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

Matching fixtures admit exactly three copied artifacts and are byte-identical on restart. Bootstrap/World-Cup mismatch, self-hash tampering and context observed after the checkpoint degrade without bindable paths; a changed input or copied CSV conflict. Focused suite: 38 passed. The current reviewed context remains bound to the 27 July universe, so a later official universe must await FPL-757 rederivation.

## Context and Orientation

The existing capture entrypoint is `scripts/capture_preseason_snapshot.py`; its implementation is `src/orchestration/preseason_snapshot.py`. It uses create-only checkpoint manifests under `data/snapshots/2026-27/preseason/<checkpoint-id>/` and a mutable safe index manifest. `OPTIONAL_FAMILIES` and the corresponding JSON config define the manifest surface. The request SHA already binds optional input digests before a checkpoint is opened; this new family must preserve that property.

`src/forecasting/launch_context.py` exposes `load_launch_context`, which verifies the context’s `content_sha256`, and defines the canonical hashing rules. It is the authoritative validator for the context JSON. Do not duplicate its semantic hash algorithm. The raw World Cup CSV is bound with the existing acquisition `content_hash` helper, and the context’s `source_bindings.world_cup_priors.sha256` must equal that raw digest.

## Plan of Work

1. Add `launch_context` to the data-source config and optional-family constants. Add default paths for the context JSON and World Cup CSV. Extend the request digest with both raw input digests and reject unknown override paths only through the existing explicit function/CLI parameters.

2. Implement a specialised pure-ish binding helper. It will load and self-hash the context, parse `observed_at`, validate season and source-binding shapes, compare the raw current official-bootstrap digest to the context binding, compare the raw World Cup CSV digest to the context binding, and ensure the context was available no later than the checkpoint observation and strictly before the decision deadline. On a valid result it writes context JSON, CSV and canonical provenance envelope under `optional/launch_context/`, then emits a family record with all paths/digests. On invalid/mismatch it emits a degraded family with a deterministic named reason and no bindable context artifact paths.

3. Extend existing-manifest restart verification to validate all three launch-context artifacts. The context/CSV/envelope digests enter the request SHA, so a changed input cannot reuse or overwrite a checkpoint.

4. Add `--launch-context-path` and `--world-cup-priors-path` CLI parameters. Their defaults are the reviewed local artifacts; supplying overrides is explicit and testable. The CLI does not create a collector and has no secret or account arguments.

5. Add fixture helpers and focused tests for: matching-universe admission; bootstrap mismatch degradation with no typed paths; World Cup digest mismatch; self-hash tampering; context observation after checkpoint; idempotent restart; changed context conflict; and CLI default/override wiring. Update the runbook with an explicit matching and mismatch transcript.

6. Run only the relevant focused tests plus syntax checks. Perform a local non-network current-bootstrap capture if needed solely to demonstrate the expected mismatch degraded family. Do not rederive the context here. On completion, record an implementation comment, close FPL-756, commit/push, then claim FPL-757 and begin its separate ExecPlan.

## Validation and Acceptance

Run:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q tests\data\test_preseason_snapshot_capture.py tests\forecasting\test_launch_context.py

Then run a no-network fixture capture twice with identical matching inputs; verify byte-identical family paths/digests and manifest. Change a bound input and verify immutable conflict. Run the mismatch fixture and verify the manifest remains valid but `families.launch_context.status == "degraded"`, `launch_context` is in `source_gaps`, its reason is `official_bootstrap_hash_mismatch`, and no context/CSV paths are present.

No test or live command may mutate a sealed older checkpoint, enable a disabled collector, include a secret, write a browser session, or change FPL account state.

## Idempotence and Recovery

This family is part of a create-only checkpoint. The exact same request returns the existing sealed manifest only after re-hashing all bound family paths. Different context, CSV or generated-envelope request bytes at the same checkpoint fail closed. If the current context does not bind the checkpoint universe, record degradation and wait for FPL-757; never work around the mismatch by comparing player names or partially applying categories.

## Interfaces and Dependencies

The specialised family record extends the ordinary optional-family fields with:

    context_content_sha256
    world_cup_priors_path
    world_cup_priors_sha256
    provenance_path
    provenance_sha256
    bound_official_bootstrap_sha256

Downstream FPL-guz must accept it only when `status == "admitted"` and all hashes verify. This task does not change FPL-guz; it establishes the source contract that FPL-757 will satisfy for the current universe.
