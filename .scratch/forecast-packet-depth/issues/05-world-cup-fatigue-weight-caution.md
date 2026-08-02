# 05 — World Cup fatigue weight: keep cautious until calibrated

**Blocked by:** None

**Status:** resolved

**Type:** research

**Category:** research

## Handoff Brief

**Summary:** Fatigue flags are present and directionally useful, but the owner
is cautious about how much weight to apply. Under-use is acceptable; do not
raise shrinkage or push fatigue into EP without evidence.

### Current behaviour

- `world_cup_fatigue` ∈ {0, 0.35, 0.7, 1.0} from launch-context tiers.
- Applied as optimiser shrinkage only:
  `fatigue_weight = 0.25` in `control/policies/initial-squad-2026-27.json`.
- Not applied inside the forecaster (`launch_context_flags_applied_after_forecast`).
- Horizon fade schedule exists in launch-context policy
  `[1.0, 1.0, 0.5, 0.5, 0.25, 0.0]` but packet enrichment uses GW1 scalar and
  the optimiser applies that scalar to all six GWs.
- EP still looks full-strength for extreme-fatigue players (e.g. Haaland).

### Research questions

1. Is current 0.25 shrinkage already too strong, about right, or too weak for
   GW1–GW6 advisory squads?
2. Should fatigue remain optimiser-only, or also fade expected minutes?
3. Should the existing GW fade schedule be exposed as a 6-length fatigue vector
   without increasing total weight?
4. What ablation / sensitivity run would justify any change (including lowering
   the weight)?

### Owner prior

- Prefer under-using fatigue over over-penalising WC participants.
- Do not let strategy agents over-read coarse flags while EP is full-strength —
  fix explainability (ticket 02) and optionally horizon fade, before raising
  weight.

### Acceptance criteria

- [x] Short written recommendation in `## Answer`: keep / lower / raise weight,
      with rationale.
- [x] If recommending horizon-aware fade only, specify vector shape and that
      total early-GW penalty must not increase without calibration.
- [x] No production weight increase in this ticket unless a cited sensitivity
      result supports it.
- [x] Cross-link any follow-on implementation ticket.

## Answer

**Keep `world_cup_fatigue_weight = 0.25`. Do not raise it. Prefer under-use.**

Rationale:

1. Fatigue is a coarse tier flag, not minutes evidence. Raising shrinkage risks
   systematically under-weighting elite WC participants (Haaland at 1.0) while
   EP still looks full-strength — agents already need ticket 02 explainability
   more than a stronger hammer.
2. Keep fatigue **optimiser-only** for now. Pushing it into expected minutes/EP
   without a calibrated minutes model would double-count once availability
   blend (ticket 03) and real team news arrive.
3. **Recommended follow-on (no weight increase):** expose a 6-length fatigue
   vector using the existing launch-context fade
   `[1.0, 1.0, 0.5, 0.5, 0.25, 0.0]` so GW1–2 retain today’s effective
   penalty and later GWs fade. Early-GW total penalty must not exceed today’s
   scalar×0.25 product without a sensitivity run.
4. Justify any future change with a named sensitivity: rebuild the same
   checkpoint at weights `{0.0, 0.15, 0.25, 0.35}` and compare XV/chip path
   churn plus post-GW1–3 actual minutes for extreme/high tiers. Lowering is
   allowed if churn is dominated by fatigue flags rather than fixtures/odds.

No production policy edit in this ticket.

## Comments

- 2026-08-01 owner: “cautious as to how much weight”; “underusing is not
  necessarily bad.”
