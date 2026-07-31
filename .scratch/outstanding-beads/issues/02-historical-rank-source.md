# 02 — Approve or decline a historical overall-rank threshold source

**Blocked by:** None — can start immediately.

**Status:** ready-for-human

**Category:** enhancement

**Former bead:** `FPL-761`

## Human Handoff

**Summary:** Record the owner decision that determines whether 2025/26
score-to-rank calibration acquires real thresholds or remains explicitly
unavailable.

### Current behaviour

The calibration contract and tests already support exact, bounded and
unavailable outcomes. The historical-rank configuration is deliberately
disabled with no selected source, and its season summary contains 38
unavailable Gameweeks.

Prior research found no defensible archived GW1–GW38 global distribution:

- the official Overall league (league id 314) exposes current paginated
  standings, not archived checkpoints;
- public manager histories expose individual season rows, not the global
  distribution; and
- average/highest-Gameweek datasets are not overall-rank thresholds.

The official endpoint registry also does not currently authorise Overall-league
standings pagination for this purpose.

### Desired behaviour

The historical calibration has a durable, explicit owner decision and no
longer remains ambiguous or indefinitely blocked.

#### Decision required

Choose and record exactly one branch:

1. **Permanent unavailable for 2025/26.** Accept that no approved source exists,
   retain all 38 rows as unavailable, and close the calibration without guessed
   ranks.
2. **Approve and acquire.** Name a reproducible source, approve its rights and
   retention terms, register it, and authorise measured acquisition before any
   collector or import is written/enabled.

This historical decision does **not** automatically approve prospective
2026/27 Overall-league capture; ticket 04 carries that separate gate.

### Key interfaces

- The historical-rank source configuration: selected source, disabled/enabled
  status, artifact reference and source-registry version.
- The source-registry record: exact source/endpoints, licence status,
  `allowed_use`, retention, access/finalisation semantics and approval.
- The `rank-thresholds-v1` artifact contract: season, Gameweek, score, exact or
  bounded rank, field size, tie rule, finalisation/auto-sub state, source
  identifier, derivation method and SHA-256 provenance.
- The owner decision record: dated rationale and explicit branch, sufficient
  for ticket 03 to proceed without re-researching rejected sources.

### Acceptance criteria

- [ ] The owner records either “permanent unavailable for 2025/26” or approval of one named source; ambiguity is not an acceptable outcome.
- [ ] The decision record summarises the completed research and explains why rejected candidates cannot provide defensible GW1–GW38 thresholds.
- [ ] For the unavailable branch, config/docs remain disabled, all 38 Gameweeks remain explicitly unavailable, and ticket 03 is authorised to close on that basis.
- [ ] For the acquisition branch, the registry confirms licence status, allowed use, retention and finalisation semantics **before** collection/import code is written or enabled.
- [ ] An approved acquisition covers GW1–GW38 or records each missing checkpoint as unavailable; every retained artifact has SHA-256 provenance.
- [ ] `python3 -m pytest -q tests/evaluation/test_rank_calibration.py` remains green under the chosen branch.

### Out of scope

- Scraping or reconstructing 2025/26 ranks from an unapproved source.
- Treating average or highest Gameweek scores as global rank thresholds.
- Inferring historical checkpoints from current Overall-league standings.
- Combining prospective 2026/27 capture approval with this decision unless the
  owner explicitly records both scopes.
