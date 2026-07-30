# FPL-756 — Immutable launch-context checkpoint binding

## Purpose

Expose the reviewed 2026/27 launch-context data to the prospective forecast
without allowing it to be read as mutable ambient control data. The context is
valid only for the exact official FPL bootstrap universe from which it was
derived. A later weekly bootstrap must not inherit it silently.

## Key decision

`control/identities/2026-27-launch-context.json` binds itself to the official
bootstrap SHA-256 `605dd…99b5` observed on 27 July. The current weekly snapshot
has a different official-bootstrap hash. Therefore this task will:

1. Admit and copy the context only when its bound official hash equals the
   checkpoint's mandatory official-bootstrap hash.
2. Bind the context JSON, World Cup CSV, and a timestamp/provenance envelope as
   independently verified immutable bytes.
3. Emit a named `launch_context_bootstrap_hash_mismatch` degraded family for a
   different current universe.

It will not weaken that check to use promoted/new/transferred player identities
from a stale roster. A successor task will rederive a new context for each
material roster change, then the six-GW forecast adapter can consume the typed
family.

## Implementation outline

1. Extend the preseason optional-family contract with `launch_context`, a
   dedicated multi-artifact binding rather than a generic one-file optional
   record.
2. Validate context self-hash, the World Cup CSV SHA referenced by context, the
   exact official-bootstrap SHA, sidecar source/timestamps and cutoff.
3. Copy every admitted component content-addressably; record each path and hash
   in the manifest and existing-artifact verifier.
4. Add CLI arguments for the context, World Cup CSV and envelope. No defaults
   may read control files implicitly.
5. Add matching, mismatched, tampered, late, missing, rerun and conflict tests.
6. Update the runbook with the matching-universe and degraded-current-universe
   workflows.

## Progress

- [x] Existing snapshot and context contracts mapped.
- [x] Exact-universe boundary identified; Bead scope corrected before code.
- [ ] Multi-artifact admission and CLI.
- [ ] Contract tests and runbook.
- [ ] Generate a new immutable matching-universe fixture/checkpoint.
