# 03 — GW-specific start probability from structured + unstructured evidence

**Blocked by:** None

**Status:** resolved

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Start probabilities are currently a flat historical prior across
all six Gameweeks. Decision quality needs GW-varying minutes risk informed by
availability ledger claims and unstructured clues (press conferences, later
match ratings), with deterministic host application.

### Current behaviour

- Live-faithful `start_probability` ≈ 2025/26 prior start rate; identical for
  GW1–GW6 (509/509 flat).
- Uncertainty = `1 - start_p` (proxy only).
- Availability ledger is admitted (e.g. Rogers / Guéhi / Senesi / Anderson
  `doubtful`) but **not blended** into start_p or EP
  (`unstructured_evidence_absent`).
- Official `chance_of_playing_next_round` is seeded then overwritten by the
  live horizon.
- Model-run evidence admission (ADR-0023) can grow club-comms claims; handoff
  into the solver packet is still the missing host step.
- Persistent availability challenger exists but is default-disabled
  (`evidence-adjustments-v2` / W4).

### Desired behaviour

1. Host builds a **bounded relevant-evidence packet** from the latest admitted
   availability / role ledger (hash-bound, cutoff-safe).
2. Deterministic adjustment projects GW-specific `start_probability` /
   expected minutes for claimed players (unavailable / doubtful / recovering),
   with explicit expiry and recovery rules.
3. Unstructured clues that affect minutes (press: “managed minutes”, “not in
   squad”, “needs game time”) enter only as ledger claims with confidence,
   urls hashed, and never as free-text optimiser input.
4. Future hook: consistently low post-match ratings → elevated rotation risk
   **only** when a rights-cleared ratings family exists (see ticket 06 / prior
   ratings gap ticket). Do not scrape FotMob/Sofascore.
5. Packet limitations clear `unstructured_evidence_absent` when blend applied;
   remain explicit when no claims touch a player.
6. Strategy agent reasons over claim ids + adjusted start_p; host remains the
   only enforcer of numerical effects.

### Owner signals to encode

- Press conferences and club communications are first-class minutes clues.
- Low match ratings as a rotation prior are desirable later, not a reason to
  violate ratings gap discipline now.
- Prefer precise, evidence-tied depressions over blanket shrinkage.

### Acceptance criteria

- [x] Hash-bound handoff: ledger → relevant-evidence packet → start_p vectors.
- [x] Doubtful example players on a rebuilt checkpoint show depressed GW1
      start_p relative to unadjusted prior, with claim ids in lineage/audit.
- [x] Unaffected players remain byte-stable.
- [x] GW variation possible when claims have different horizons/expiries.
- [x] Tests for expiry, identity mismatch fail-closed, and disabled-challenger
      baseline invariance.
- [x] No LLM-applied numerical minutes without host validation.

### Out of scope

- Enabling automated club HTML scrape (still rights-gated).
- Promoting ratings effects before a 2026/27 envelope exists.

## Answer

Host blend `blend_availability_into_horizon_players` projects the admitted
availability ledger at packet `observed_at` and adjusts GW start_p / EP /
uncertainty.

- Doubtful: −0.25 start_p cap (v2 policy number); EP scaled by probability ratio.
- Unavailable: zero projection for affected GWs.
- Trusted for checkpoint-admitted ledgers (even without source_hashes).
- Mid-horizon expiry cuts later GWs when expires_at falls between kickoffs;
  preseason claims that expire before every kickoff still apply while live in
  the information set.
- Clears `unstructured_evidence_absent` when any claim is applied; writes
  `availability-blend.json`.
- Unaffected players remain byte-stable (tested).

