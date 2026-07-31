# 01 — Apply admitted launch context in the initial-squad packet

**Blocked by:** None

**Status:** resolved

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Wire promoted-team, new-signing and World Cup fatigue fields from
the admitted `launch_context` composite into `build_initial_squad_packet`, so
policy shrinkage actually fires instead of defaulting every player to false/0.

### Acceptance criteria

- [x] When `launch_context` is admitted on the verified manifest, eligible
      players receive `promoted_team`, `new_signing` and `world_cup_fatigue`
      from `apply_launch_context` (GW1 fade).
- [x] When it is absent, defaults remain false/0 and the gap is explicit.
- [x] Forecast quality remains `operational_baseline_only` until ticket 02
      binds a live-faithful six-GW surface (do not pretend EP is decision-grade).
- [x] Focused tests cover applied and unavailable paths.
- [x] No network; no registry enablement of `world-cup-2026` bulk collection.

## Answer

Implemented `_apply_launch_context_to_players` in
`src/orchestration/initial_squad_checkpoint.py`. Optional family fallbacks for
promoted / WC / transfers note derivation from admitted launch_context when
applied. Tests:
`tests/orchestration/test_initial_squad_launch_context.py` (2 passed with the
existing checkpoint suite).

The 2026-07-31 live bootstrap has a different hash from the reviewed
2026-07-27 context, so the fresh checkpoint correctly leaves this family
degraded rather than reusing stale classifications. Re-derivation is supported
by `scripts/build_launch_context.py` but still requires a supplied, cutoff-safe
2025/26 stable-code roster; no roster is fabricated in this ticket.
