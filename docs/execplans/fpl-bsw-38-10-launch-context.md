# FPL-bsw.38.10 — 2026/27 launch context

This execution plan is a living record for the governed cold-start context used by
the prospective 2026/27 initial-squad lab.

## Purpose

Convert already captured, point-in-time inputs into a deterministic launch-context
artifact. Every official player must receive exactly one primary cold-start class,
while World Cup participation remains an orthogonal expected-minutes risk. Unknown
or late inputs must never be silently treated as neutral evidence.

## Inputs

- Official FPL bootstrap observed at `2026-07-27T10:05:27Z`.
- The completed 2025/26 player catalogue, joined only by stable FPL `code`.
- The 176-row World Cup 2026 prior ledger observed at
  `2026-07-21T17:21:28Z`.

Raw source bodies remain immutable and are bound by SHA-256 in the committed
control artifact.

## Policy decisions

- Primary-class precedence is `promoted_team`, `new_to_fpl`,
  `transferred_player`, then `established`.
- A player may retain orthogonal flags such as `is_new_to_fpl` and
  `changed_club`; precedence only prevents double counting in the primary class.
- The initial-squad policy's existing shrinkage values remain authoritative:
  promoted-team risk `0.10`, new-signing/new-club risk `0.08`.
- World Cup fatigue tiers map deterministically to `[0.0, 0.35, 0.7, 1.0]` and
  fade `[1.0, 1.0, 0.5, 0.5, 0.25, 0.0]` over GW1–GW6. This is a named,
  logged multiplier input, not an outcome-tuned forecast.
- Missing return-to-training dates are expected and degrade visibly. A cited
  return date that became available after a decision cutoff is rejected.
- Blank or no-longer-current World Cup player identities remain in coverage
  metrics and cannot join to an official player by name.

## Implementation

- [x] Audit current official, historical and World Cup identity coverage.
- [x] Add the committed launch-context control artifact and bind source hashes.
- [x] Add a pure forecasting adapter that validates identities, assigns exactly
  one class, joins World Cup priors by stable code, and reports degradation.
- [x] Add synthetic contract tests including duplicate, unknown and late data.
- [x] Document provenance, interpretation and live update procedure.
- [x] Run focused and complete tests, update Beads, commit and push.

## Validation

The committed artifact expects 558 official players split into 83 promoted-team,
26 other new-to-FPL, 25 transferred-player and 424 established classifications.
The current World Cup ledger contains 176 rows: 140 stable codes join the current
official universe, 33 valid historical codes no longer join, and three identities
remain blank. All 176 return-to-training dates are currently missing and therefore
reported as a non-blocking degradation.


## Outcome

The production-shaped local audit passed at the official GW1 cutoff. It emitted
artifact SHA-256 `876cf50960c0deec5fc0094cd6ca81cedd209d3927351ccefddbbed6d7b0f643`,
classified all 558 players exactly once and reported 36 excluded World Cup
identity rows rather than guessing joins. Focused launch/live integration tests
passed 30/30 and the complete repository suite passed 595/595 in 433.38 seconds.