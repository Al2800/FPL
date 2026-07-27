# Build the official set-piece role ledger

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

This work turns official FPL set-piece order fields into immutable,
point-in-time role evidence. A live decision can see who FPL listed for
penalties, direct free kicks, and corners before its cutoff, while stale,
conflicting, missing, or later observations remain visible and cannot silently
alter an earlier episode.

## Progress

- [x] (2026-07-27 14:36Z) Claimed `FPL-bsw.38.7` after closing and pushing the
  Football-Data odds bead.
- [x] (2026-07-27 14:40Z) Verified the current official bootstrap exposes
  player/team identity plus all three set-piece order fields.
- [ ] Implement the immutable snapshot normaliser and longitudinal ledger.
- [ ] Add configuration, tests and operator documentation.
- [ ] Validate the current live capture, run regressions and close the bead.

## Surprises & Discoveries

- Observation: no editorial-page scraper is necessary.
  Evidence: `api_bootstrap-static.json` contains `penalties_order`,
  `direct_freekicks_order`, and `corners_and_indirect_freekicks_order` on each
  official player row.
- Observation: the same payload supplies official player and team IDs.
  Evidence: each element carries `id` and `team`, so identity resolution does
  not depend on fuzzy names.

## Decision Log

- Decision: use the immutable official bootstrap as the primary structured
  source and the official Set-Piece Takers page as manual corroboration.
  Rationale: this avoids fragile HTML extraction and binds role and identity to
  one content hash.
  Date/Author: 2026-07-27 / Alastair and Codex.
- Decision: replace roles at the team-and-role snapshot boundary.
  Rationale: a player disappearing from a later official list must invalidate
  the earlier entry rather than remain active indefinitely.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

Implementation is in progress. The intended output is a self-hashed snapshot
and a self-hashed as-of ledger with explicit active, expired, unknown,
conflicted and superseded states. No forecast weight is promoted by this bead.

## Context and Orientation

`src/ingestion/snapshot_fpl.py` already captures the public bootstrap
immutably. The new `src/ingestion/set_piece_roles.py` consumes that payload and
its source hash without making a network request. An observation is one
player's ranked role inside one official snapshot. A ledger is the latest
admissible state for every club-and-role pair at a requested time.

The three canonical roles are `penalty`, `direct_free_kick`, and
`corner_or_indirect_free_kick`. Missing means the latest snapshot listed no
player for that club and role. Expired means the configured freshness window
ended. Superseded means a later admissible snapshot replaced an older complete
club-and-role list.

## Plan of Work

Create `config/data_sources/2026-27-set-pieces.json` and
`control/manifests/2026-27-set-pieces.json` to freeze the source fields,
confidence-by-rank mapping, expiry, fallback and shadow-only promotion status.

Implement `normalise_official_set_piece_snapshot` to validate exact timestamps,
source hash, identities, ranks and conflicts. It will emit all twenty clubs by
all three roles, including explicit empty groups. Implement
`build_set_piece_role_ledger` to select only snapshots available by the as-of
time, replace whole role groups, expire stale groups and preserve supersession.
Implement `build_set_piece_feature_payload` so an empty/degraded ledger returns
zero adjustments and a declared byte-identical-baseline fallback.

Add `tests/data/test_set_piece_roles.py` and
`docs/data-sources/2026-27-set-pieces.md`. Exercise the existing live bootstrap
locally and run the complete suite.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

    .venv/Scripts/python.exe -m pytest tests/data/test_set_piece_roles.py -q
    .venv/Scripts/python.exe -m pytest tests/integration/test_live_episode_builder.py tests/unit/test_registry.py -q
    .venv/Scripts/python.exe -m pytest -q

No command downloads data or writes to an FPL account.

## Validation and Acceptance

The same bootstrap bytes and timestamps must reproduce the same snapshot and
ledger hashes. A future snapshot must not enter an earlier as-of ledger. A
later official list must supersede the entire earlier club-and-role list.
Duplicate ranks remain visible as conflicts and yield no promoted feature.
Expired or entirely missing evidence must produce an empty adjustment list and
the exact fallback `byte_identical_baseline`.

## Idempotence and Recovery

The builders are pure and content-addressed. Raw official payloads remain in
the existing gitignored immutable capture. No overwrite, deletion, network
fetch, package installation, browser action or account mutation is required.

## Artifacts and Notes

Current primary input:

    source_id=fpl-official-endpoints
    endpoint=bootstrap-static
    capture=20260727T100527Z
    roles=penalty,direct_free_kick,corner_or_indirect_free_kick

## Interfaces and Dependencies

`src.ingestion.set_piece_roles` will expose:

    def normalise_official_set_piece_snapshot(
        bootstrap, *, source_sha256, observed_at, available_at, expiry_hours
    ) -> dict[str, Any]: ...

    def build_set_piece_role_ledger(
        snapshots, *, as_of
    ) -> dict[str, Any]: ...

    def build_set_piece_feature_payload(
        ledger
    ) -> dict[str, Any]: ...

The module uses only the Python standard library and existing hashing
conventions.

Revision note (2026-07-27): created after inspecting the immutable 2026/27
launch capture and choosing the official bootstrap over HTML scraping.
