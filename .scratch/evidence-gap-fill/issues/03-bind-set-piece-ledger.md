# 03 — Bind set-piece ledger from official bootstrap

**Blocked by:** None

**Status:** resolved

**Type:** task

## Summary

Auto-derive and bind the set-piece role ledger from the checkpoint’s admitted
bootstrap (`normalise_official_set_piece_snapshot`). Keep effect weights null /
shadow-only until live ablation (W17).

## Answer

Implemented automatic derivation in `capture_preseason_snapshot` when no
explicit set-piece artifact is supplied:

- official bootstrap role fields are normalised and hashed;
- the latest as-of ledger and feature payload are stored as one immutable
  checkpoint artifact;
- the family is admitted only when the registered official FPL source is
  collectable and the roles validate;
- `effect_weights` remains `null` and promotion remains
  `shadow_only_pending_point_in_time_ablation`.

Malformed/synthetic bootstrap payloads degrade with an explicit reason rather
than inventing roles. Focused preseason snapshot tests cover the admitted
ledger path.
