# 03 — Close historical score-to-overall-rank calibration

**Blocked by:** 02 — Approve or decline a historical overall-rank threshold source

**Status:** ready-for-agent

**Category:** enhancement

**Former bead:** `FPL-2xu`

> Do not claim this ticket until ticket 02 is resolved. The implementation is
> already contract-complete; this is a branch-dependent closure, not a rewrite.

## Agent Brief

**Summary:** Apply ticket 02's owner decision to the existing rank-calibration
contract and produce a reconciled 2025/26 exact/bounded/unavailable outcome.

### Current behaviour

The evaluator already validates immutable artifacts, rejects hash mismatches and
extrapolation, resolves exact/bounded/unavailable outcomes, produces safe labels
and reconciles a 38-Gameweek season. Its focused suite currently passes nine
tests. The disabled default configuration represents all 38 Gameweeks as
unavailable because no historical source has been approved.

The season artifact lives in governed, gitignored data; a fresh clone relies on
tests and committed config/docs rather than a committed raw threshold dump.

### Desired behaviour

After ticket 02:

- **Unavailable branch:** preserve the 38 unavailable rows, align the owner
  decision/config/docs and close without modifying the evaluator or inventing
  ranks.
- **Acquisition branch:** validate/import the approved immutable thresholds,
  preserve explicit gaps, update the config/provenance references and reconcile
  all 38 Gameweeks through the existing evaluator.

In both branches, rank is ex-post annotation only and never enters forecasting,
optimisation or policy state.

### Key interfaces

- `rank-thresholds-v1`: exact rows have equal lower/upper bounds; bounded rows
  have a non-zero interval; unavailable rows contain no rank.
- Artifact validation/loading: canonical SHA-256 integrity and fail-closed
  behaviour.
- Rank resolution: no extrapolation outside observed score support.
- Season reconciliation: exactly GW1–GW38 with explicit mode labels.
- Reporting label: consumers must distinguish “exact”, “bounded estimate” and
  “unavailable”; an estimated rank must never be displayed as exact.

### Acceptance criteria

- [ ] Ticket 02's dated owner decision is referenced and exactly one closure branch is applied.
- [ ] All 38 Gameweeks resolve to exact, bounded or unavailable with no silent gap.
- [ ] Exact rows have equal bounds; bounded rows have `rank_lower < rank_upper`; unavailable rows contain no invented rank.
- [ ] Tie handling, field size, snapshot/finalisation state, auto-sub state, source ID, derivation and SHA-256 provenance remain explicit where applicable.
- [ ] Approved thresholds, if any, reject extrapolation and fail closed on hash mismatch.
- [ ] Config, documentation and the governed season summary agree on selected source/status and all 38 modes.
- [ ] `python3 -m pytest -q tests/evaluation/test_rank_calibration.py` passes (nine tests at handoff).
- [ ] No production path imports rank calibration before outcome reveal or uses it in forecasts, optimisation or policy transitions.

### Out of scope

- Reimplementing the existing evaluator when ticket 02 selects unavailable.
- Adding a 2024/25 extension.
- Deriving exact ranks from average-score data or current standings.
- Treating post-finalisation revisions as pre-final evidence.
- Wiring rank into pre-deadline reports, forecasts or optimiser objectives.
- Blocking the core replay when rank evidence is unavailable.
