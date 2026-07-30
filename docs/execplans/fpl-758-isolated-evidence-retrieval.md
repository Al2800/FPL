# FPL-758 — Isolated temporal FPL evidence-retrieval overlay

This is a living implementation plan. `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` are updated as work progresses.

## Purpose / Big Picture

FPL live evidence is currently an immutable ledger: it is correct and
point-in-time safe, but a growing ledger cannot be passed wholesale to an agent.
This work adds a separate, rebuildable SQLite/FTS retrieval layer. It never
becomes a source of truth: source acquisition manifests, ledger claims,
availability state, structured forecasts, manager state and optimiser state
remain in their existing FPL stores.

The local `knowledge` project supplies only reusable profile/configuration
infrastructure. Its company, store, email and Teams corpora are an explicit
negative boundary: this feature does not open, copy, federate, query or point
at them. The FPL profile resolves to an FPL-owned root, intake directory and
SQLite index only.

An agent will receive a bounded packet containing cited ledger claims and
source hashes. It cannot read raw material, retrieval omissions, or arbitrary
text outside that packet.

## Progress

- [x] 2026-07-30 16:20Z: Claimed FPL-758 after checking no active Bead owns the
  listed overlay files.
- [x] 2026-07-30 16:25Z: Audited the FPL evidence ledger, its decision-time
  projection semantics, candidate-boundary packet, source policy and the
  reusable knowledge configuration/index APIs. No corpus data was opened.
- [ ] Add the isolated FPL profile and a generic profile resolver without
  changing the default company runtime.
- [ ] Add a ledger-to-SQLite materializer with immutable source/context binds.
- [ ] Add cutoff- and entity-scope-bound lexical retrieval plus packet audits.
- [ ] Add isolated, temporal, redaction, idempotence and latency tests.
- [ ] Validate, document, close the Bead and push FPL changes to `main`.

## Surprises & Discoveries

- The knowledge project's existing `ProjectRegistry` is a company-document
  alias registry, not a reusable project-runtime profile resolver. A small new
  `project_registry.py` is therefore required; it must not modify the existing
  document alias semantics.
- The `knowledge` working tree contains extensive unrelated uncommitted work.
  Changes here will be isolated to a new overlay YAML, a new resolver module,
  a narrow append-only config/service export, and its dedicated test. Existing
  edited paths will not be rewritten.
- `project_live_evidence` already defines the required historical state rule:
  a claim is known only when published/observed/available are all at or before
  the cutoff; only unexpired, non-quarantined known claims supersede earlier
  claims. The index will reproduce that exact rule rather than inventing a
  second lifecycle model.

## Decision Log

- **Derived FTS is lexical only for the first live overlay.** SQLite FTS5
  provides deterministic local ranking with no embedding service, network
  dependency or unmeasured model latency. Semantic retrieval remains an
  explicitly optional future ablation.
- **Source records are copied as derived metadata, never raw content.** The
  materializer accepts an approved context, ledger and acquisition manifests;
  it stores the derived claim text already permitted by the ledger, source and
  manifest hashes, identifiers and temporal metadata. It does not retain raw
  snapshots or crawl any source.
- **Materialisations are additive by input hash.** Repeating exact bytes is
  idempotent; changed source/ledger/context input creates a separate immutable
  materialisation within the derived SQLite database. No raw input is edited or
  deleted.
- **State is reconstructed before ranking.** The SQL candidate set applies
  cutoff, authority and entity predicates; deterministic lifecycle evaluation
  then suppresses future, expired, quarantined and superseded claims before
  FTS scores are considered.

## Context and Orientation

`src/evidence/live_evidence_ledger.py` supplies `validate_live_evidence_ledger`
and the canonical cutoff rule. `src/evidence/candidate_boundary_retrieval.py`
identifies entity-bound decision candidates before evidence is considered.
`config/data_sources/2026-27-evidence-coverage.json` defines current source
families and packet limits.

The FPL retrieval config will name the `fpl` overlay from
`C:/Users/Alastair/knowledge/config/project-overlays/fpl.yaml`. The profile uses
`FPL_KB_ROOT`, `FPL_KB_INTAKE_DIR` and `FPL_KB_EVIDENCE_DB` overrides but has
safe FPL-owned defaults. Its resolver refuses known company, store, email and
Teams roots.

## Plan of Work

1. Add a profile resolver in the portable knowledge runtime. With no profile it
   returns `None` and leaves `KB_ROOT`, company index and existing services
   unchanged. With `fpl`, it resolves only the FPL overlay and validates all
   configured paths against the denied corpus roots.
2. Add `fpl_knowledge_materializer.py`. It validates the ledger's self hash,
   immutable acquisition manifests (matching source ID/hash) and an approved
   derived context. It then writes a versioned, additive SQLite/FTS
   materialisation preserving full provenance and temporal fields.
3. Add `fpl_evidence_retrieval.py`. A query must include ISO cutoff and at
   least one stable player/team/fixture ID. It selects only candidate rows that
   are temporally known, authority-allowed and entity-scoped before lexical
   ranking; it calculates supersession/expiry against the materialisation;
   then emits a bounded self-hashed cited packet and audit/omission ledger.
4. Add test fixtures that prove default runtime preservation, profile isolation,
   idempotence, immutable-input rejection, absent cutoff/scope refusal,
   post-cutoff/disallowed/cross-entity exclusion, historical supersession and
   expiry, deterministic packet bytes and lexical p95 measurement.
5. Document the operational boundary, rebuild command/API, source-of-truth
   rule, and the promotion limits for live use.

## Validation and Acceptance

Run from `C:\Users\Alastair\FPL-pr-review`:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q ^
      tests\evidence\test_fpl_evidence_retrieval.py ^
      tests\integration\test_fpl_knowledge_overlay.py

Run the knowledge profile tests with its existing virtual environment, without
installing anything:

    C:\Users\Alastair\knowledge\.venv\Scripts\python.exe -m pytest -q ^
      C:\Users\Alastair\knowledge\tools\kb\tests\test_project_registry.py

The FPL suite must demonstrate no network or browser access. A synthetic active
corpus latency report will include p50/p95/p99 and must stay below the
configured local packet budget; a mandatory embedding service is prohibited.

## Idempotence and Recovery

The materializer computes its identity from the ledger hash, ordered manifest
hashes and approved-context hash. If that identity already exists, it returns
`unchanged`; otherwise it appends a new derived index namespace in a single
SQLite transaction. If validation fails, it rolls back before any namespace is
visible. Source snapshots, ledger files and approved contexts are only read.

## Artifacts and Notes

Only code, tests, configuration, documentation and Bead metadata belong in the
FPL repository. The FPL retrieval SQLite database, intake and source captures
are operational data under `data/` and remain ignored. No current or historical
company knowledge, email, Teams content or paths are a valid FPL artefact.

## Interfaces and Dependencies

The core FPL interfaces will be:

    materialize_fpl_evidence_index(... ) -> dict[str, Any]
    retrieve_fpl_evidence_packet(... ) -> dict[str, Any]
    measure_fpl_retrieval_latency(... ) -> dict[str, float]

They use only the Python standard library plus the already-installed YAML
support used by the local knowledge profile resolver. No network, credential,
model, browser or package installation is required.

## Implementation update — 2026-07-30 17:10Z

Completed the portable profile resolver in the knowledge runtime and added the
isolated `fpl` profile. It is opt-in and validates FPL-owned root/intake/index
paths against the company, email and Teams denial roots; the normal company
runtime is unchanged when no profile is selected. Implemented the FPL
materializer and cutoff-bound adapter with additive materialisation identities,
manifest/context hash binds, SQLite FTS5 lexical search, pre-ranking lifecycle,
authority and stable-entity filters, deterministic packet hashes and host-only
omission audit. Added focused tests, including a 256-claim local latency corpus.

Focused FPL overlay suite: 7 passed in 3.52s. Portable knowledge profile suite:
4 passed in 0.38s using the existing FPL test environment because the knowledge
virtual environment does not currently contain pytest; no dependency was
installed. No corpus or raw evidence was opened during implementation.
