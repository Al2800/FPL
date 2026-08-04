# Local operational estate

**Date:** 3 August 2026  
**Owns:** create-only audit, consolidation and private archive of machine-local FPL evidence  
**Ticket:** `.scratch/operationalisation/issues/00-local-operational-estate-consolidation.md`

## What Git can restore

Pulling this repository restores versioned definitions only:

- `src/`, `scripts/`, `config/`, `control/`, `prompts/`, `schemas/`, `tests/`, `docs/`
- committed indexes such as `control/manifests/2026-27-preseason.json`
- scheduler *installers* and policy JSON

Git does **not** restore raw captures, live reports, SQLite stores, Windows Task
Scheduler registration, or user-scoped secrets.

## What remains local

| Class | Typical paths | Rule |
|---|---|---|
| Immutable evidence | `data/snapshots/**`, `reports/live/**` | create-only; hash-verify; never backfill |
| Mutable ops state | `data/operational-state/**`, `data/live-shadow/scheduler/**` | local machine state |
| Databases | `*.sqlite`, DuckDB files | gitignored |
| Secrets | `THE_ODDS_API_KEY` user env var | presence checks only |
| Scheduler | Task Scheduler registrations | verify action targets active root |

## Audit before a live checkpoint

```powershell
cd C:\Users\Alastair\FPL
.\.venv\Scripts\python.exe -m scripts.audit_local_operational_estate
```

The command writes
`data/operational-state/machine-manifest.json` (gitignored) with root inventory,
retained-family counts/hashes, preseason-manifest reference status, knowledge-store
path presence, scheduled-task actions, and secret presence flags. It never prints
secret values.

Exit codes:

- `0` — every committed preseason reference is locally resolved or explicitly
  acknowledged as unavailable; expected tasks are present and target the active root
- `2` — at least one preseason reference is missing/mismatched and unacknowledged
- `3` — a required scheduled task is absent or its action does not target the active root
- `1` — configuration or I/O failure

## Consolidate from legacy worktrees

Copy-only. Identical destination bytes are accepted; differing bytes fail closed.
Nothing is deleted, moved, rewritten or backdated.

```powershell
cd C:\Users\Alastair\FPL
.\.venv\Scripts\python.exe -m scripts.consolidate_local_operational_estate `
  --acknowledge-unavailable
```

This copies the retained 30 July preseason checkpoint and initial-squad report from
`C:\Users\Alastair\FPL-pr-review` when those trees are absent from the active
checkout, then acknowledges any still-missing committed references (notably the
31 July checkpoint when no authentic local bytes exist).

## Private archive and restore verification

```powershell
.\.venv\Scripts\python.exe -m scripts.consolidate_local_operational_estate `
  --acknowledge-unavailable `
  --archive-root D:\Private\FPL-operational-estate-backup
```

The archive is create-only, writes
`operational-estate-archive-manifest.json` with per-file SHA-256 digests, and
refuses to overwrite differing destination bytes. Restore verification is the same
hash comparison: re-run the archive command against the backup root and confirm
`identical_existing` / `identical_file_set` statuses.

## Recover without weakening provenance

1. Restore code from Git.
2. Re-install scheduled tasks with the installers in `scripts/`, pointing at
   `C:\Users\Alastair\FPL`.
3. Restore ignored evidence only from a hash-verified private archive or an
   immutable legacy worktree copy.
4. Re-run the audit. If a historical observation is gone, record
   `unavailable_local_artifact` — never reconstruct it from a later snapshot.

See also `docs/data-sources/deadline-capture-scheduler.md` for capture-task
install and Odds-key presence checks.
