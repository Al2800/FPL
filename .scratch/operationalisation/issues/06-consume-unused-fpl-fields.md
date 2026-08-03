# 06 — Promote captured-but-unused FPL fields into models

Status: ready-for-agent
Type: task
Track: B (free data)

## Context

Tier 1 fields are snapshotted but never consumed: ICT components appear only in historical lag sums; the set-piece ledger (`src/ingestion/set_piece_roles.py`) has `effect_weights: None` (shadow-only); official `ep_next`/FDR were never benchmarked as WP-05 requires; `selected_by_percent` is episode metadata only.

## Scope

- **Set pieces:** define governed `effect_weights` (penalty/direct free kick/corner shares of goal and assist rates) and wire them into `live_faithful` event rates; promote from `shadow_only` behind an explicit policy flag.
- **ICT:** evaluate influence/creativity/threat as features in the player-event baseline under time-based evaluation; adopt only if they beat the existing baseline, and record the result either way (plan §11.2 — a null result is a result).
- **Benchmark `ep_next`/FDR:** complete the deferred WP-05 residual — benchmark official `ep_next` and FDR against the odds-implied and naive baselines on pre-deadline snapshots; document under `docs/data-sources/wp05/`.
- **Ownership:** surface `selected_by_percent` in the GDR (captaincy-risk framing) without building Phase-5 effective-ownership strategy.

## Done when

- Each field has either a consuming feature with measured marginal value or a documented negative result; set-piece weights are active (or explicitly rejected) with tests.
