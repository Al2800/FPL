# 05 — World Cup fatigue weight: keep cautious until calibrated

**Blocked by:** None

**Status:** open

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

- [ ] Short written recommendation in `## Answer`: keep / lower / raise weight,
      with rationale.
- [ ] If recommending horizon-aware fade only, specify vector shape and that
      total early-GW penalty must not increase without calibration.
- [ ] No production weight increase in this ticket unless a cited sensitivity
      result supports it.
- [ ] Cross-link any follow-on implementation ticket.

## Comments

- 2026-08-01 owner: “cautious as to how much weight”; “underusing is not
  necessarily bad.”
