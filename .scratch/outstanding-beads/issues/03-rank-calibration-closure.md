# 03 — Close historical score-to-overall-rank calibration

**Blocked by:** 02 — Approve or decline a historical overall-rank threshold source

**Status:** resolved

**Category:** enhancement

**Former bead:** `FPL-2xu`

## Agent Brief

**Summary:** Apply ticket 02's owner decision to the existing rank-calibration
contract and produce a reconciled 2025/26 exact/bounded/unavailable outcome.

### Current behaviour

The evaluator already validates immutable artifacts, rejects hash mismatches and
extrapolation, resolves exact/bounded/unavailable outcomes, produces safe labels
and reconciles a 38-Gameweek season. Its focused suite currently passes nine
tests. The disabled default configuration represents all 38 Gameweeks as
unavailable because no historical source has been approved.

### Desired behaviour

After ticket 02's unavailable decision: preserve the 38 unavailable rows, align
the owner decision/config/docs and close without modifying the evaluator or
inventing ranks.

### Key interfaces

- `rank-thresholds-v1`: unavailable rows contain no rank.
- Season reconciliation: exactly GW1–GW38 with explicit mode labels.
- Reporting label: consumers must distinguish unavailable from exact/bounded.

### Acceptance criteria

- [x] Ticket 02's dated owner decision is referenced and exactly one closure branch is applied.
- [x] All 38 Gameweeks resolve to exact, bounded or unavailable with no silent gap.
- [x] Exact rows have equal bounds; bounded rows have `rank_lower < rank_upper`; unavailable rows contain no invented rank.
- [x] Tie handling, field size, snapshot/finalisation state, auto-sub state, source ID, derivation and SHA-256 provenance remain explicit where applicable.
- [x] Approved thresholds, if any, reject extrapolation and fail closed on hash mismatch.
- [x] Config, documentation and the governed season summary agree on selected source/status and all 38 modes.
- [x] `python3 -m pytest -q tests/evaluation/test_rank_calibration.py` passes (nine tests at handoff).
- [x] No production path imports rank calibration before outcome reveal or uses it in forecasts, optimisation or policy transitions.

### Out of scope

- Reimplementing the existing evaluator when ticket 02 selects unavailable.
- Adding a 2024/25 extension.
- Deriving exact ranks from average-score data or current standings.
- Treating post-finalisation revisions as pre-final evidence.
- Wiring rank into pre-deadline reports, forecasts or optimiser objectives.
- Blocking the core replay when rank evidence is unavailable.

## Answer

Closed on ticket 02's **permanent unavailable** branch. No evaluator rewrite.
Docs/config now cite the 2026-07-31 decision. Focused suite: 9 passed.
Rank annotation remains downstream-only.
