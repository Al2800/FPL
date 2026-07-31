# FPL-760 — Explicit supersession for official FPL availability updates

This is a living implementation plan. `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` are updated as work proceeds.

## Purpose / Big Picture

The official FPL bootstrap collector emits an immutable availability claim for
each point-in-time news value. Repeated captures with unchanged player news
must remain idempotent, while a changed status or news value for the same exact
player must form a chain: the new claim explicitly supersedes the prior active
official availability claim. Without that edge, the live evidence projection
correctly sees two competing values and the persistent availability bridge
cannot observe an official recovery.

This change is deliberately narrow. It changes neither source admission nor
the default evidence policy, and it does not mutate historical/sealed replay
artefacts. It only derives supersession metadata at collection time and adds
fail-closed validation/tests for malformed or unsafe chains.

## Progress

- [x] 2026-07-31: Claimed FPL-760 after checking Beads and confirming no active
  task owns the collector/ledger/test files.
- [x] 2026-07-31: Audited the collector, live-ledger validation/projection,
  persistent availability bridge and existing collection tests.
- [ ] Define a deterministic same-player official-claim frontier for new
  observations; unchanged claim IDs remain idempotent.
- [ ] Add explicit supersedes metadata to changed official claims, with
  fail-closed guards for source, identity, timestamp and hash mismatches.
- [ ] Add focused integration/ledger/challenger tests covering status changes,
  recovery, unrelated players, duplicate bootstrap changes and invalid input.
- [ ] Run focused and broader regressions, document outcomes, update Beads,
  commit and push the completed bead.

## Surprises & Discoveries

- `append_live_evidence_claim` already enforces append ordering and same
  subject/claim-type supersession, so the collector should supply only a
  validated predecessor edge rather than weakening ledger validation.
- The collector's claim ID includes the published timestamp and claim value,
  so unrelated bootstrap changes are naturally idempotent while a changed
  status/news value creates a new claim ID.
- A claim must supersede the current frontier, not every historical claim:
  chaining only the latest active predecessor keeps the immutable history
  auditable and avoids unnecessary transitive references.

## Decision Log

- **Official source only.** The collector may supersede only claims whose
  `source_id` is `fpl-official-endpoints`, `claim_type` is
  `player_availability`, and whose exact `player_uid` binding matches.
- **Strictly earlier observations.** A predecessor must have an earlier
  `available_at` than the incoming observation. Equal-time changed values are
  refused rather than arbitrarily ordered.
- **Active frontier.** Only prior official claims not already superseded by a
  later official claim for the same player are candidates. The newest valid
  frontier claim is the sole predecessor; ambiguous or malformed frontiers
  fail closed.
- **Hash and identity binding.** Existing ledger validation remains the final
  admission gate. The collector never trusts a caller-supplied supersession
  list and does not cross player boundaries.
- **No silent recovery policy change.** This enables the existing availability
  bridge to see a valid official recovery; it does not enable upward evidence
  adjustments or promote any policy by itself.

## Context and Orientation

`src/ingestion/live_evidence_collector.py` constructs claims from the governed
`bootstrap-static` payload and appends them through
`src/evidence/live_evidence_ledger.py`. The live ledger records an append-only
claim list, validates identity/timestamps/source hashes, and projects claims
by excluding explicit superseders from the active view. The persistent
availability bridge consumes that projection and already handles recovery when
the official claim chain is valid.

## Plan of Work

1. Add small collector helpers to extract the exact player UID and compute the
   eligible official predecessor frontier from the existing ledger. Keep the
   result deterministic and side-effect free.
2. Pass the computed predecessor ID into `_player_claim` only for a genuinely
   new claim. If the same claim ID already exists, leave the ledger byte-
   identical; if the predecessor is invalid or out of order, surface a
   collection gap/refusal without appending.
3. Add tests for: unchanged news despite unrelated bootstrap hash changes;
   changed status/news appending one explicit predecessor; a second change
   chaining from the frontier; recovery through the persistent bridge; an
   unrelated player remaining untouched; and unknown identity, cross-player,
   source/hash and out-of-order failures.
4. Run the focused integration/evidence tests, then the repository's normal
   test command if practical. Verify no canonical replay hash or policy file
   changes.
5. Record implementation/test details in this plan and the FPL-760 Beads
   completion comment before closing the bead.

## Validation and Acceptance

From `C:\Users\Alastair\FPL-pr-review`:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q ^
      tests/integration/test_live_evidence_collection.py ^
      tests/integration/test_live_evidence_collection_dedup.py ^
      tests/evidence/test_live_evidence_ledger.py ^
      tests/evidence/test_persistent_availability_challenger.py

Acceptance requires that unchanged captures remain byte-identical; changed
official values append with only the exact same-player predecessor; the live
projection accepts the newer value; recovery reaches the availability bridge;
and malformed identity, source, hash, timestamp or cross-player references
fail closed. No network, browser, account, secret or new source capability is
introduced.

## Idempotence and Recovery

The output remains content-addressed. Re-running a capture with the same
bootstrap player observation produces the existing claim ID and no ledger
change, even if unrelated bootstrap fields alter the document hash. A changed
official observation receives a new claim ID and a single predecessor edge. A
later valid recovery supersedes that edge and restores the existing structured
baseline through the already implemented named challenger bridge.

## Artifacts and Notes

Only code, tests and this ExecPlan are tracked. Raw endpoint captures remain
under ignored operational paths. Canonical benchmark and sealed replay trees
are not modified.

## Outcomes & Retrospective

Pending implementation and validation.

## Implementation update — 2026-07-31

The collector now computes explicit same-player official supersession edges only
for newly observed claim IDs. Unchanged status/news remains a byte-identical
no-op even when unrelated bootstrap fields change. The frontier includes all
currently unsuperseded official claims for that player, so a recovery can repair
legacy branches while manual claims and other players remain untouched.

The live ledger now validates stored source hashes, exact identity bindings,
complete temporal ordering and strictly earlier supersession edges. Invalid
hashes, identities, cross-player references and equal/out-of-order timestamps
fail closed. The persistent availability bridge therefore receives the
collector's recovery edge and restores the existing named challenger state
without changing default policy behaviour.

Validation: 32 focused collector, ledger, persistent-availability and checkpoint
regression tests passed. A full repository run remains pending.