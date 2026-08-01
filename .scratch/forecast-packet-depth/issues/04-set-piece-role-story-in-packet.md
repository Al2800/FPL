# 04 — Include admitted set-piece roles in the packet story

**Blocked by:** None

**Status:** open

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Set-piece family is already admitted from official bootstrap on
`weekly-2026-08-02`, but the optimiser/strategy packet does not surface a role
story and `effect_weights` remain null (`shadow_only_pending_point_in_time_ablation`).
Include the roles for agent/human reasoning now; keep numerical EP effects
gated.

### Current behaviour

- Derived ledger bound under checkpoint optional family `set_pieces`.
- `effect_weights: null`, promotion shadow-only (W17 ablation still the
  production gate for point effects — see evidence-gap programme).
- Player rows have no penalty / DFK / corner taker flags.

### Desired behaviour

1. Expose per-player set-piece role flags (and claim/source hashes) on the
   decision packet or its audit companion:
   - penalty taker / contingency;
   - direct free kicks;
   - corners;
   - as-of timestamps.
2. Strategy prompts must be able to reason: “X is on pens; EP may understate
   attacking ceiling until effects are live.”
3. Do **not** silently enable EP effect weights. Either:
   - keep shadow-only with an explicit packet note, or
   - open a separate calibration sub-task once live shadow weeks exist.
4. If a safe zero-impact “include for ranking diagnostics only” path is added,
   it must be named and default-off for approval gating.

### Acceptance criteria

- [ ] Packet/audit lists set-piece roles for players present in the admitted
      ledger.
- [ ] Lineage records ledger sha and `effect_weights` status.
- [ ] Default numerical EP path unchanged while weights remain null.
- [ ] Tests cover admission present / absent / malformed degrade.

### Notes

Enabling pure visibility is unblocked. Enabling scoring effects remains
blocked-on-data by W17-style ablation unless the owner explicitly accepts a
provisional challenger weight.
