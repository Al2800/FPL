# FPL-bsw.38.5 — Immutable 2026/27 preseason and launch snapshot capture

This ExecPlan is a living document. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

Create the immutable, point-in-time input checkpoints used to choose the live
2026/27 starting squad. This bead captures data; it does not optimise a squad
or write to an FPL account. Downstream beads `FPL-guz` and `FPL-jm0` must consume
only hash-verified manifests produced here.

## Progress

- [x] Claimed `FPL-bsw.38.5` and mapped the existing evidence-checkpoint and
  live-shadow launch contracts.
- [x] Added the preseason config, capture module, CLI, index manifest, focused
  tests and operator runbook.
- [x] Verified focused preseason and evidence-checkpoint suites.
- [x] Remediated review findings: non-overlapping checkpoint windows, pre-write
  official validation, registry-gated optional inputs, immutable artifact/sidecar
  binding, restart verification, and checkpoint-time temporal cutoffs.
- [ ] Operator continues scheduled live captures through the GW1 deadline under
  the sealed contract (operational, not a code change).

## Surprises & Discoveries

- Observation: a genuine official launch capture already exists under the
  gitignored live-shadow tree from 2026-07-27, before this storage contract.
  Evidence: capture `e2499ad7...2460` with bootstrap SHA
  `605dd760...399b5` and decision cutoff `2026-08-21T17:30:00Z`.
- Observation: the evidence checkpoint runner already derives T-48h through
  final-pre-deadline timestamps from the official event deadline.
  Evidence: `derive_deadline_checkpoints` in
  `src/orchestration/evidence_checkpoint_runner.py`.
- Observation: bead checkpoint ID `final` maps to runner ID
  `final_pre_deadline`; `launch` and `weekly-YYYY-MM-DD` are preseason-specific.
- Observation: optional evidence must be bounded by the checkpoint observation
  time, not merely by the later GW1 deadline; otherwise a historical T-48h
  capture can silently admit T-24h knowledge.
  Evidence: regression coverage in
  `test_optional_record_available_after_checkpoint_is_quarantined` and
  `test_sidecar_observed_after_capture_is_quarantined`.

## Decision Log

- Decision: reuse the evidence-checkpoint immutability contract rather than a
  second write protocol.
  Rationale: identical restarts, create-only paths and fail-closed overwrite
  refusal already exist and are tested.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: store preseason checkpoints under
  `data/snapshots/2026-27/preseason/<checkpoint-id>/` with a sealed per-checkpoint
  manifest and a mutable index at `control/manifests/2026-27-preseason.json`.
  Rationale: FPL-guz needs a stable hash-verified intake surface distinct from
  the live evidence ledger head.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: hash-bind the legacy 27 July launch capture instead of re-fetching
  or copying raw bytes into Git.
  Rationale: raw snapshots remain gitignored; differing bytes at an immutable
  path must fail closed.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: missing optional families degrade with named reasons; missing
  mandatory official bootstrap/fixtures/rules fail the checkpoint with no
  admitted manifest.
  Rationale: absence must never become an implicit zero feature.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: treat each checkpoint observation time as the latest admissible
  `available_at`, require binary optional inputs to carry a temporal/provenance
  sidecar, and hash-bind both files into the request and sealed manifest.
  Rationale: a replay checkpoint must be reproducible without future knowledge,
  and changing metadata must conflict exactly as changing data bytes does.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

The capture contract is implemented. Mandatory official state, ruleset hashing,
deadline-relative ID validation, non-overlapping execution windows, temporal
quarantine for evidence unavailable at the checkpoint, immutable sidecar
binding, idempotent restarts and fail-closed overwrite refusal are covered by
focused tests. Optional odds, ratings, World Cup priors,
set pieces and transfer context remain explicitly degradable until supplied.
Operational weekly and T-minus captures continue against this sealed interface
until GW1.

## Interface and location map

| Deliverable | Path |
|---|---|
| ExecPlan | `docs/execplans/fpl-bsw-38-5-preseason-capture.md` |
| Config | `config/data_sources/2026-27-preseason.json` |
| Capture module | `src/orchestration/preseason_snapshot.py` |
| CLI | `scripts/capture_preseason_snapshot.py` |
| Index manifest | `control/manifests/2026-27-preseason.json` |
| Runbook | `docs/evaluation/2026-27-preseason-capture-runbook.md` |
| Tests | `tests/data/test_preseason_snapshot_capture.py` |
| Snapshot root | `data/snapshots/2026-27/preseason/` (gitignored raw) |

## Validation commands

```bash
python -m pytest -q tests/data/test_preseason_snapshot_capture.py \
  tests/integration/test_evidence_checkpoint_runner.py
```

## Non-goals

Squad selection, retrospective backfill, policy promotion, browser automation,
live-account writes, and overwriting sealed 2025/26 or prior launch bytes.
