# 03 — Close historical score-to-overall-rank calibration

**What to build:** The rank-calibration evaluator annotates revealed 2025/26
cumulative scores as exact, bounded, or unavailable for every Gameweek 1–38,
with provenance and integrity checks, without ever feeding ranks into forecasts
or optimisation. Closure lands only after ticket 02's source decision.

**Blocked by:** 02 — Approve historical overall-rank threshold source

**Status:** ready-for-agent

**Category:** enhancement

**Former bead:** `FPL-2xu`

- [ ] All 38 Gameweeks resolve to exact, bounded, or unavailable — no silent gaps or point estimates labelled exact.
- [ ] Exact rows have equal bounds; bounded rows have a non-zero interval; unavailable rows invent no rank.
- [ ] Focused rank-calibration tests pass and the season summary reconciles all 38 Gameweeks.
- [ ] Rank annotation remains downstream of outcome reveal.
