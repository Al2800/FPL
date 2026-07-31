# 02 — Approve or decline a historical overall-rank threshold source

**Blocked by:** None — can start immediately.

**Status:** resolved

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

Prior research found no defensible archived GW1–GW38 global distribution.

### Desired behaviour

The historical calibration has a durable, explicit owner decision and no
longer remains ambiguous or indefinitely blocked.

### Key interfaces

- The historical-rank source configuration: selected source, disabled/enabled
  status, artifact reference and source-registry version.
- The owner decision record: dated rationale and explicit branch.

### Acceptance criteria

- [x] The owner records either “permanent unavailable for 2025/26” or approval of one named source; ambiguity is not an acceptable outcome.
- [x] The decision record summarises the completed research and explains why rejected candidates cannot provide defensible GW1–GW38 thresholds.
- [x] For the unavailable branch, config/docs remain disabled, all 38 Gameweeks remain explicitly unavailable, and ticket 03 is authorised to close on that basis.
- [x] For the acquisition branch, the registry confirms licence status, allowed use, retention and finalisation semantics **before** collection/import code is written or enabled.
- [x] An approved acquisition covers GW1–GW38 or records each missing checkpoint as unavailable; every retained artifact has SHA-256 provenance.
- [x] `python3 -m pytest -q tests/evaluation/test_rank_calibration.py` remains green under the chosen branch.

### Out of scope

- Scraping or reconstructing 2025/26 ranks from an unapproved source.
- Treating average or highest Gameweek scores as global rank thresholds.
- Inferring historical checkpoints from current Overall-league standings.
- Combining prospective 2026/27 capture approval with this decision unless the
  owner explicitly records both scopes.

## Answer

**Branch chosen: permanent unavailable for 2025/26.**

Decision recorded in `docs/data-sources/historical-rank-source-decision.md`.
Config reason updated; collection remains disabled; prospective 2026/27 capture
is explicitly not approved by this decision. Rank calibration tests: 9 passed.
Ticket 03 is authorised to close on the unavailable branch.
