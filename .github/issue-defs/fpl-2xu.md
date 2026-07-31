## Parent / origin

Migrated from Bead `FPL-2xu` (was **in_progress**, priority 3).
Related to historical source ticket (`FPL-761`) and prospective capture (`FPL-762`).

## Status at migration

Implementation of the calibration **contract** is largely done; closure is
**blocked** on an approved historical overall-rank threshold source.

Delivered (per bead notes): `src/evaluation/rank_calibration.py`, focused tests,
`config/data_sources/historical-rank-thresholds.json`,
`docs/data-sources/rank-thresholds.md`, ExecPlan
`docs/execplans/fpl-2xu-rank-calibration.md`, and a 2025/26 summary with 38
**unavailable** rows (no invented ranks).

## What

Calibrate historical cumulative FPL scores to overall-rank bands without
presenting an estimate as an exact rank. Required scope: complete 2025/26 replay
GW1–GW38. Evaluation API must return one of `exact`, `bounded`, `unavailable`.

Rank calibration stays **downstream of replay scoring** and must never affect
forecasts, optimisation or policy state.

## Acceptance criteria

- [ ] Approved source registry entry and rights/retention decision exist before automated collection — **or** owner accepts permanent unavailable for 2025/26 and closes this ticket with that decision recorded.
- [ ] GW1–GW38 each resolve to exact, bounded or unavailable; no silent gap or point estimate disguised as exact.
- [ ] Every stored artifact has source provenance and SHA-256 integrity.
- [ ] Exact rows: `rank_lower == rank_upper`; bounded: `rank_lower < rank_upper`; unavailable: no invented rank.
- [ ] Tie handling, field size, finalisation and auto-sub state are explicit.
- [ ] `python -m pytest -q tests/evaluation/test_rank_calibration.py` passes; season summary reconciles all 38 Gameweeks.

## Blocked by

Historical overall-rank threshold source approval/acquisition ticket.

## Non-goals

Claiming a globally exact rank from average-score data; using post-finalisation
revisions as pre-final; blocking core replay when rank evidence is unavailable.
