# 00 — Consolidate and verify the local operational estate

Status: resolved
Type: task (AFK)
Track: A0 (make the live machine authoritative)
Blocked by: none

## Context

The 2026/27 engine is intentionally split between versioned code and private,
gitignored operational state. The active Windows machine is now the execution
host, but its point-in-time evidence is fragmented:

- `C:\Users\Alastair\FPL` is the active checkout and contains the running
  scheduled captures, historical data, current official observations and the
  2025/26 player prior;
- `C:\Users\Alastair\FPL-pr-review` still contains the immutable 30 July
  preseason checkpoint and its initial-squad output;
- `control/manifests/2026-27-preseason.json` also references a 31 July
  checkpoint whose raw manifest was not found in any local FPL worktree; and
- Windows task registration, secrets, SQLite stores and raw snapshots are local
  machine state and cannot be restored by pulling Git.

This ticket makes the active checkout authoritative without deleting,
overwriting or retrospectively reconstructing evidence. It must leave a
repeatable audit and recovery path for later agents.

## What to build

Provide one create-only local-estate workflow that inventories the active and
legacy FPL roots, validates immutable hashes and committed manifest references,
copies missing retained artifacts into the active checkout, and records any
irrecoverable reference as an explicit local gap. The workflow must also audit
the three Windows scheduled tasks against their expected names and active-root
actions, without reading or emitting secret values.

The workflow must distinguish:

1. versioned definitions that belong in Git (scripts, configuration, prompts,
   schemas, tests and runbooks);
2. local operational evidence that must remain ignored (raw captures,
   checkpoint outputs, reports, SQLite databases and scheduler state); and
3. machine registration or secrets that must be verified by presence and
   metadata only.

Consolidation is copy-only. Existing destination bytes are accepted only when
they are identical. Differing bytes fail closed. No source or destination file
may be deleted, moved, rewritten or backdated. In particular, the missing
31 July checkpoint must be reported as unavailable local evidence rather than
recreated from a later observation.

## Acceptance criteria

- [x] A read-only audit command produces a local, gitignored machine manifest
  covering active/legacy data roots, immutable checkpoint/report families,
  committed preseason-manifest references, configured knowledge-store paths,
  and the expected Windows task names/actions.
- [x] The manifest records counts, byte sizes, latest observation times and
  available content hashes without retaining secrets, Odds API key values or
  authenticated browser state.
- [x] A create-only consolidation command copies the 30 July preseason
  checkpoint and initial-squad output from `FPL-pr-review` into the equivalent
  ignored paths under `FPL`, then proves every copied byte/hash is identical to
  its source.
- [x] The 31 July checkpoint reference is either resolved from authentic
  matching bytes or recorded as `unavailable_local_artifact`; it is never
  reconstructed, backfilled or silently removed from history.
- [x] Every retained reference in
  `control/manifests/2026-27-preseason.json` is classified as locally
  resolvable or explicitly unavailable, with a non-zero audit exit when an
  unresolved reference has not been acknowledged.
- [x] The audit verifies that `FPL Deadline-Aware Capture`,
  `FPL ChatGPT Unstructured Capture` and `FPL ChatGPT Strategy Review` target
  `C:\Users\Alastair\FPL`; task absence, stale actions and non-zero last results
  are visible but do not expose credentials.
- [x] A create-only archive option can copy the private operational estate to
  an operator-supplied local/private backup root, with a hash manifest and
  restore verification. It refuses to overwrite differing bytes and performs
  no deletion or pruning.
- [x] The active runbook explains what Git can restore, what remains local,
  how to audit before a live checkpoint, how to verify a backup, and how to
  recover without weakening point-in-time provenance.
- [x] Offline tests cover identical copy, conflicting destination, missing
  reference, acknowledged historical gap, scheduler-action drift, secret
  redaction and backup/restore hash verification.
- [x] No raw data, live reports, databases, secrets or Task Scheduler exports
  are added to Git.

## Verification handoff

The implementation report must include:

- the audit command and its terminal status;
- source/destination hashes for the copied 30 July checkpoint and report;
- the explicit status of the 31 July reference;
- scheduled-task health and target-root results;
- the chosen private archive root, if supplied by the operator; and
- the focused offline test command and result.

## Files

Expected ownership (the implementing agent may refine names while preserving
this scope):

- `src/orchestration/local_operational_estate.py`
- `scripts/audit_local_operational_estate.py`
- `scripts/consolidate_local_operational_estate.py`
- `config/operations/local-operational-estate.json`
- `tests/orchestration/test_local_operational_estate.py`
- `docs/operations/local-operational-estate.md`
- `docs/data-sources/deadline-capture-scheduler.md`

Local outputs only:

- `data/operational-state/**`
- `data/snapshots/2026-27/preseason/**`
- `reports/live/2026-27/**`
- operator-supplied private archive root

## Boundaries

- Never delete or move a file or directory.
- Never overwrite differing destination bytes.
- Never infer or regenerate a historical observation that is no longer
  available locally.
- Never print, persist or compare secret values; presence checks only.
- Do not change FPL account state or open an authenticated browser.
- Do not commit local operational outputs.

## Answer

Implemented the create-only local-estate workflow and ran it on the active
Windows host on 3 August 2026.

### Audit

```powershell
.\.venv\Scripts\python.exe -m scripts.audit_local_operational_estate
```

Terminal status: **exit 0**. Machine manifest written to
`data/operational-state/machine-manifest.json` (gitignored).

### Copied 30 July artifacts (source == destination SHA-256)

| Relative path | SHA-256 |
|---|---|
| `data/snapshots/2026-27/preseason/weekly-2026-07-30/manifest.json` | `a9bedc1c85235b57f004fe1e220eac81313cd533fea5bc2d5ff3506971f5bcd0` |
| `reports/live/2026-27/initial-squad/weekly-2026-07-30/checkpoint.json` | `b9e707160081b4c6894741812ea541a4f1404b342d3829168a7bd0547f12710c` |
| `reports/live/2026-27/initial-squad/weekly-2026-07-30/recommendation.json` | `20acec67ae31b8994888f368b8b606bfeadbf098f45aa425767a88b4cb45c82d` |

Committed index binding for the 30 July checkpoint resolves via sealed
`content_sha256` / `manifest_sha256`:
`eca9b64aa0c57be08480b0183fd00ca1738e0ed7e59fedcc2bd71d35443ddb30`.

### 31 July reference

`unavailable_local_artifact`, acknowledged in
`data/operational-state/acknowledged-unavailable-artifacts.json`. Expected
sealed hash
`5ad6773222113a185ca8a8c3c1a29014a8792019012d1915631c914162f636e7`.
No bytes were reconstructed.

### Scheduled tasks

| Task | Present | Targets `C:\Users\Alastair\FPL` | Last result |
|---|---|---|---|
| FPL Deadline-Aware Capture | yes | yes | 0 |
| FPL ChatGPT Unstructured Capture | yes | yes | 1 (visible) |
| FPL ChatGPT Strategy Review | yes | yes | 1 (visible) |

Odds API key: present (value not emitted).

### Private archive

Not run — no operator-supplied backup root was provided. Use
`--archive-root <private-path>` on
`scripts.consolidate_local_operational_estate` when ready.

### Offline tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/orchestration/test_local_operational_estate.py -q
```

Result: **7 passed**.
