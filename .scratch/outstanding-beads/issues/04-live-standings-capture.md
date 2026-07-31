# 04 — Capture 2026/27 official global standings snapshots

**Blocked by:** None for the owner decision; implementation is gated inside this
ticket by prospective source approval.

**Status:** ready-for-human

**Next status:** Change to `ready-for-agent` only after the prospective
Overall-league source/endpoint has confirmed licence status and allowed use.

**Category:** enhancement

**Former bead:** `FPL-762`

## Handoff Brief

**Summary:** Approve and then implement a prospective, immutable
post-finalisation Overall-standings capture that supplies exact/bounded
2026/27 rank thresholds without affecting deadline decisions.

### Current behaviour

The rank-calibration evaluator can consume threshold rows, but there is no
2026/27 Overall-standings collector, capture configuration, focused ingestion
suite or post-finalisation schedule. The registered official FPL endpoint family
does not yet explicitly authorise league-id-314 standings pagination for this
purpose.

This work is technically independent of whether ticket 02 finds historical
2025/26 data. It needs its own prospective rights/retention decision.

### Desired behaviour

After owner approval, each 2026/27 Gameweek can produce an immutable snapshot at
a defined post-finalisation checkpoint. Raw page/rank/total-points observations
retain their point-in-time/provenance metadata and deterministically yield
`rank-thresholds-v1` exact or bounded rows. Missing pages/checkpoints remain
explicit gaps.

Capture is downstream-only: it must never alter a pre-deadline episode,
forecast, optimiser input or policy state.

### Key interfaces

- Source governance: the exact Overall standings endpoint, pagination
  parameters, league id 314, licence status, allowed use, retention and owner
  approval.
- Capture configuration: season, disabled-by-default switch, checkpoint
  finalisation rule, endpoint parameters, page limits and governed artifact
  root.
- Snapshot record: page, rank, total points, field-size metadata,
  `published_at` where available, `observed_at`, `available_at`,
  `effective_at`, `finalised_at`/finalisation state, endpoint parameters,
  source ID and artifact SHA-256.
- Threshold transformation: deterministic mapping to exact/bounded rows
  accepted by the existing rank-calibration validator, with explicit gaps.
- Operational schedule: one documented post-finalisation trigger and
  retry/degraded behaviour that cannot reconstruct an earlier checkpoint from
  later live standings.

### Acceptance criteria

- [ ] Before implementation begins, the registry explicitly covers league-id-314 Overall standings with confirmed licence status, allowed use, retention and owner approval.
- [ ] Before approval, any placeholder config remains disabled and no network collector is written or enabled.
- [ ] After approval, a disabled-by-default collector records the full snapshot fields and canonical SHA-256 provenance defined above.
- [ ] The capture schedule defines how finalisation is established and how late corrections, missing pages, rate limits and endpoint failures are retained as evidence.
- [ ] Missing pages/checkpoints are explicit gaps; historical values are never inferred from a later live response.
- [ ] The deterministic transformation emits only validator-accepted exact/bounded rows and records source artifact hashes/derivation.
- [ ] Focused tests cover governance-disabled/no-network behaviour, paginated happy path, missing-page degradation, temporal fields, hash integrity and threshold transformation.
- [ ] `python3 -m pytest -q tests/ingestion/test_official_global_standings.py` passes once that suite is introduced.
- [ ] No secret, credential, manager-specific endpoint, raw data dump or pre-deadline rank input is committed.

### Out of scope

- Backfilling 2025/26 from current standings.
- Manager, rival or mini-league analysis.
- Feeding overall rank into the deadline decision path.
- Enabling collection before registry approval.
- Guessing field size, tie handling or missing pages.
