# Sign-off: 2026/27 live initial-squad policy

**Ticket:** `.scratch/outstanding-beads/issues/06-live-squad-policy-residual.md`  
**Date:** 2026-07-31  
**Owner:** Alastair

## Outcome

**Policy ratified. Live squad proposal approval deferred.**

The prospective initial-squad policy contract is approved for advisory use.
No specific 15-player proposal is approved. `ready_for_manual_entry` remains
false until a decision-grade forecast packet exists and a hash-bound proposal
approval is recorded against that packet.

## Policy binding

| Field | Value |
| --- | --- |
| Policy path | `control/policies/initial-squad-2026-27.json` |
| Policy ID | `initial-squad-2026-27` |
| Policy version | `1.0` |
| Policy SHA-256 | `39e3b6303203d89e053cdb9af2c2f8b5f7f3cb62cf2a823c686803284b234069` |
| Mode | `advisory_only_no_fpl_execution` |
| Preferred arm (when decision-grade) | `robust` |
| Approval timestamp | `2026-07-31T18:00:00Z` |

## Verified programme properties

- Policy is prospective, point-in-time and reproducible; historical 2025/26
  outcomes are not used to tune the live selection.
- GW1 seed selection is separated from GW2–GW11 weekly evidence in the closed
  child programme and checkpoint docs.
- Approval gate requires completed deterministic and robust arms, active
  ruleset hash match, and owner approval bound to exact packet/proposal hashes
  no later than the decision cutoff.
- Missing, late or hash-mismatched approval leaves
  `ready_for_manual_entry: false` with explicit blockers.
- Current live checkpoint `weekly-2026-07-30` is intentionally degraded
  (`approval_status=blocked`) because the six-GW decision-grade
  `live-faithful` forecast packet is not yet materialised.

## Explicit non-approvals

- No proposal SHA-256 is approved.
- No base packet SHA-256 is approved for manual entry.
- No FPL account, browser or execution authority is granted.
- Canonical 2025/26 artifacts must remain unchanged by this sign-off.

## Ticket 07 implication

Ticket 07 may proceed on the basis that the live initial-squad **policy** is
ratified. It must not treat this document as approval of a starting 15.
