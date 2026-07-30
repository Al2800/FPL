# FPL-jm0 — GW1 live-readiness rehearsal

## Purpose

Prove that an immutable preseason manifest can be turned into a complete,
advisory-only initial-squad Decision Record before the final GW1 deadline. The
rehearsal owns orchestration, timing, immutability, and the go/no assessment;
it delegates validation and selection to the existing initial-squad checkpoint
runner. It never loads a browser automation or an FPL account-write path.

This is deliberately separate from the work that turns the flat official
`ep_next` baseline into the decision-grade six-GW forecast. A baseline run may
exercise the process but must remain blocked from approval.

## Inputs and outputs

Input is one self-hashed preseason manifest captured no later than T-48h before
the official GW1 deadline. The manifest must bind admitted official bootstrap,
fixtures, and ruleset bytes. Optional-family gaps are carried through exactly
as degraded coverage; they are never silently filled.

The runner writes an immutable directory per checkpoint under
`evals/live-readiness/2026-27-gw1/<checkpoint-id>/`:

- `input-manifest.json` — byte-for-byte manifest copy and binding;
- `source-coverage.json` — admitted/degraded family states;
- `recommendation.json` and `checkpoint.json` from the initial-squad runner;
- `gameweek-decision-record.json` — initial-squad advisory decision record;
- `rehearsal-report.json` and `rehearsal-report.md` — stage timings, host/runtime,
  hashes, degraded state, and go/no result;
- `rerun-comparison.json` — exact artifact digest comparison for the unchanged
  request.

The optional final-checkpoint comparison writes only a new comparison artifact
outside the frozen rehearsal directory. It cannot modify T-48h bytes.

## Go/no rules

- Missing mandatory input, source-hash mismatch, invalid chronology, illegal
  squad, an attempted immutable overwrite, or a stage/budget failure is
  **no-go** and writes no frozen recommendation in the requested run directory.
- Missing optional sources are **degraded**, not a no-go, provided the legal
  structured recommendation can be produced.
- A baseline-only forecast remains **not approval eligible** even when the
  operational rehearsal is otherwise go. It is reported as an operational
  go-with-approval-blockers.
- Whole-run budget is 30 minutes; checkpoint generation budget is 10 minutes.
  Timings are recorded, never fabricated.

## Implementation outline

1. Validate the required literal checkpoint label and derive T-48h from the
   manifest-bound official GW1 deadline. A captured manifest must have been
   observed at or before the target; a later manifest is refused rather than
   substituted.
2. Verify the manifest with `verify_preseason_manifest`, then copy the verified
   bytes immutably into the rehearsal directory.
3. Invoke `run_initial_squad_checkpoint` into a private child directory, time
   it, and validate its legal squad / first XI outputs.
4. Construct an initial-squad Gameweek Decision Record binding the selection,
   coverage, checkpoint, and recommendation hashes. It remains manual-entry
   only and `account_writes=false`.
5. Seal report and comparison hashes. A second unchanged invocation compares
   the complete file tree byte-for-byte.
6. Provide an additive final-checkpoint comparator that writes nowhere beneath
   the T-48h frozen directory.

## Verification

Focused tests cover happy path, identical rerun, missing mandatory source,
optional degradation, manifest hash mismatch, late/post-cutoff input, illegal
candidate pool, budget rejection, and immutable overwrite conflict.

Run:

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q `
  tests/integration/test_live_readiness_rehearsal.py `
  tests/integration/test_initial_squad_checkpoint.py `
  tests/integration/test_evidence_checkpoint_runner.py
```

## Progress

- [x] Contracts and existing checkpoint runner mapped.
- [x] Rehearsal orchestration and CLI.
- [x] Failure-injection integration tests.
- [x] Documentation and focused verification (22 focused integration tests passed).
