# 2026/27 FPL evidence retrieval overlay

## Status and boundary

The FPL evidence ledger is authoritative. The overlay is an opt-in, local,
derived SQLite FTS5 index that makes the ledger searchable at a decision
boundary; it cannot collect, rewrite, approve or apply evidence. It stores only
already-admitted FPL derived claim text and the minimum provenance required to
cite it. It never stores source pages, RSS bodies, API responses, screenshots,
company documents, email, Teams messages or credentials.

The reusable runtime profile lives at
`C:/Users/Alastair/knowledge/config/project-overlays/fpl.yaml`. It resolves to
an FPL-owned root, intake directory and `fpl_evidence.sqlite` path, controlled
by the optional `FPL_KB_ROOT`, `FPL_KB_INTAKE_DIR` and
`FPL_KB_EVIDENCE_DB` environment variables. The profile resolver rejects paths
inside the company knowledge store, the email corpora and Teams-related stores.
No profile selection leaves the existing knowledge runtime unchanged.

## Materialisation contract

`materialize_fpl_evidence_index` accepts exactly:

1. a self-validating immutable `live_evidence_ledger`;
2. accepted immutable acquisition manifests, one matching each claim's source
   ID and source hash; and
3. an approved, self-hashed derived decision context.

The index identity is the ledger hash, ordered manifest hashes, approved-context
hash and index-schema version. Repeating exact inputs returns `unchanged`.
Changed inputs add a new materialisation namespace in one SQLite transaction;
the ledger, manifests and context are never altered. The operational database
is a local ignored artefact, not a Git-tracked replay input.

## Retrieval contract

`retrieve_fpl_evidence_packet` requires all of the following:

- a materialisation identity;
- an ISO-8601 decision cutoff with timezone;
- at least one stable player, team/club or fixture ID; and
- bounded query text (which may be empty for an entity-only view).

Before FTS ranking it reconstructs the state known at the cutoff and excludes
future, expired, quarantined and effectively superseded claims. It then applies
allowed source authority and stable entity scope. Only the remaining rows are
lexically ranked. A later superseder cannot rewrite an earlier historical
answer, and a cross-player/team claim never reaches ranking for an unrelated
candidate.

The returned self-hashed packet contains cited ledger claim IDs, source hashes,
manifest IDs, timestamps, stable identity bindings and derived claim text. The
agent-visible view strips the host-only retrieval audit and omission lists.
Every agent arm must receive the same visible packet; the frozen no-evidence
control remains mandatory.

## Runtime and performance

The first overlay deliberately uses local SQLite FTS5 lexical ranking.
`semantic_dependency` is explicitly `disabled`: no embedding or external model
is a live prerequisite. `measure_fpl_retrieval_latency` records p50/p95/p99 and
checks repeated packet hashes. The focused test uses a 256-claim active corpus
and asserts p95 below the configured 250 ms local packet budget; this is a
regression guardrail, not a claim about a future full-season corpus.

## Operator sequence

1. Capture registered FPL sources and admit only governed claims to the
   immutable ledger.
2. Assemble the accepted manifest bindings and approved checkpoint context.
3. Resolve the explicit `fpl` profile; do not point it at the existing company
   profile or any email/Teams path.
4. Materialise the ledger into the profile's local derived SQLite database.
5. Build candidate scope from the structured solver/manager state and retrieve
   one bounded packet at the exact decision cutoff.
6. Preserve the packet hash, materialisation hash and omission audit with the
   decision record. Treat a degraded packet as no additional evidence—not
   confirmation of a player's availability.

## Verification

- `tests/evidence/test_fpl_evidence_retrieval.py` covers immutable bind checks,
  additive/idempotent materialisation, cutoff-state supersession and expiry,
  source/entity hard filters, fail-closed missing cutoff/scope, deterministic
  packets, audit stripping and local p50/p95/p99 measurement.
- `tests/integration/test_fpl_knowledge_overlay.py` proves the FPL runtime
  resolves a separate profile without opening any corpus.
- `C:/Users/Alastair/knowledge/tools/kb/tests/test_project_registry.py` proves
  the reusable profile is explicit, isolated, rejects forbidden roots and does
  not change the default knowledge runtime.
