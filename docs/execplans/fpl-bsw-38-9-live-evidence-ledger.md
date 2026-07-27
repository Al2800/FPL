# Live 2026/27 Unstructured Evidence Ledger

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Operate a rights-aware, immutable and cutoff-safe evidence ledger for live
2026/27 decisions. Produce bounded evidence packets for agents while preserving
an independently frozen no-evidence control for causal attribution.

## Progress

- [x] (2026-07-27 17:08Z) Claimed `FPL-bsw.38.9` after checking active Beads
  and confirming no declared file overlap.
- [x] (2026-07-27 17:15Z) Audited the historical evidence lifecycle,
  availability ledger, boundary retrieval, source registry, live-shadow
  completion gate and paired attribution path.
- [ ] Implement live claim admission, expiry, supersession, conflict handling,
  source-rights visibility and immutable checkpoint packets.
- [ ] Implement the evidence arm with bounded schema validation, deterministic
  degradation and a frozen no-evidence bridge.
- [ ] Add configuration, tests, documentation and full-suite validation.

## Decision Log

- Decision: Reuse lifecycle and availability semantics but introduce a
  live-specific ledger contract rather than mutate historical schemas.
  Rationale: live checkpoints require immutable append-only snapshots,
  source-rights precision and stable packet hashes in addition to individual
  claim validation.
  Date/Author: 2026-07-27 / Codex

- Decision: Manual linked evidence is the only enabled initial collection path
  for sources whose automated collection rights remain unresolved.
  Rationale: the source registry currently disables official-club and editorial
  collection; a ledger may govern supplied citations without enabling a
  collector.
  Date/Author: 2026-07-27 / Codex

- Decision: The evidence arm may fail or time out without changing the frozen
  no-evidence candidate.
  Rationale: causal attribution requires a byte-stable same-state control.
  Date/Author: 2026-07-27 / Codex

## Validation

Focused command:

    .\.venv\Scripts\python.exe -m pytest tests/evidence/test_live_evidence_ledger.py tests/integration/test_live_evidence_arm.py -q

Full command:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

Pending.
