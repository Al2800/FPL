# FPL-nxq — Content-addressed replay payloads

This ExecPlan is a living document. Keep Progress, Decisions, Discoveries, and
Outcomes current while the payload migration is active.

## Purpose

Deduplicate identical GW4 reviewed solver inputs and outputs without changing
any resolved payload, arm-owned state, or consumer behavior. GW3 remains sealed
and inline. Every migrated reference must fail closed on malformed metadata,
wrong kind, missing manifest membership, or changed bytes.

## Progress

- [x] Store one immutable payload per solver input/output content hash.
- [x] Replace GW4 arm copies with independently self-sealed references.
- [x] Validate reference schema, kind, digest, manifest membership, and payload hash.
- [x] Preserve inline GW3 loading through the same central boundary.
- [x] Migrate every known evaluation/orchestration consumer.
- [x] Add executable consumer-specific loading boundaries and Windows UTF-8 coverage.
- [ ] Close the Bead and merge after focused and compatibility suites pass.

## Decisions

- `payload_sha256` identifies stored payload bytes; `content_sha256` seals the
  reference envelope itself. The two meanings are never interchangeable.
- Consumers own small named loading boundaries, but every boundary delegates to
  `load_reviewed_payload`; this makes migrations testable without duplicating
  resolver logic.
- Store manifests are verified at read time. A payload existing on disk is not
  sufficient admission evidence.
- Prior sealed artifacts are not rewritten or deleted.

## Discoveries

- Importing the central loader in every module was insufficient proof: the first
  cross-consumer test only relabelled one resolved dictionary and never executed
  consumer-owned boundaries.
- Windows' default text encoding exposed three test-only JSON reads that omitted
  explicit UTF-8 even though production readers were correct.

## Validation

    python -m pytest -q tests/historical-replay/test_replay_payload_store.py tests/historical-replay/test_gw3_forecast_setup.py
    python -m pytest -q tests/evaluation/test_challenger_matrix.py tests/optimisation/test_multiweek.py tests/optimisation/test_squad_contingency.py tests/optimisation/test_transfer_counterfactual.py tests/integration/test_enhanced_season_replay.py

## Outcomes

GW4 stores one unique input and one unique output for identical arm trajectories.
Every arm reference remains state-bound and self-validating. All named consumers
resolve references through their actual loading boundary, while GW3 inline
payloads retain byte-compatible behavior.