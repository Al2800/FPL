# FPL-2xu: historical rank calibration

## Goal

Provide a deterministic, point-in-time-safe annotation from revealed
2025/26 cumulative FPL score to an exact rank, a conservative rank band, or an
explicit unavailable result. Do not allow rank evidence to feed the replay
decision path.

## Current state

The source registry has no approved historical overall-rank threshold source.
This implementation therefore seeds a 38-gameweek unavailable artifact and
keeps collection disabled. A separate source-acquisition bead is required
before the parent bead can close.

## Invariants

1. Every season artifact has exactly one row for GW1-GW38 and a SHA-256 over
   canonical rows.
2. Exact rows have equal bounds; bounded rows have a non-zero interval and are
   labelled non-exact; unavailable rows contain no rank.
3. Score resolution never extrapolates beyond observed support and rejects
   tampered artifacts before reporting.
4. Rank labels are explicit in JSON/UI consumers and rank calibration is
   downstream of outcome reveal.

## Verification

`tests/evaluation/test_rank_calibration.py` covers schema validation, the
38-week unavailable reconciliation, conservative interpolation, no
extrapolation, hash mismatch fail-closed behaviour, and explicit labels.
