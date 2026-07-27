# FPL-bsw.38.11 — 2026/27 ruleset activation and owner sign-off

## Purpose

Replace the provisional 2026/27 rule catalogue with a dated, official-source
verified catalogue, prove its operational semantics, and prepare a separate
owner approval packet. Approval is limited to advisory engine use; browser and
FPL account writes remain prohibited.

## Source policy

Only official Fantasy Premier League or Premier League pages may confirm a rule.
Each source is recorded with its publication date and the date observed for this
audit. Current 2026/27 launch/help pages may link to maintained FPL Basics pages
published in 2025; the evidence packet records that chain rather than pretending
the older publication date is new.

## Work

- [x] Claim the Bead and reproduce all 11 activation blockers.
- [x] Inspect current official 2026/27 launch, help, chip, scoring, BPS, squad,
  transfer and managing-team sources.
- [x] Upgrade every inherited/provisional operational rule to confirmed only
  where the official evidence supports its exact value.
- [x] Correct the chip-boundary structure and first-half expiry year.
- [x] Generate a zero-blocker activation artifact and semantic diff from
  2025/26.
- [x] Add boundary, transition, evidence-completeness and owner-gate tests.
- [x] Emit an owner-review packet with approval still pending.
- [x] Obtain explicit owner approval, record it, run the complete suite, commit,
  push and close the Bead.

## Decisions

- The chip boundary is a structured rule: Wildcard and Free Hit unavailable in
  GW1, with Free Hit unable to bridge GW19 to GW20.
- The first-half deadline is 2 January 2027, not 2026. The existing timestamp
  year is a catalogue error.
- Rule activation and owner approval are distinct. A catalogue may compile with
  zero semantic blockers while remaining ineligible for advisory use until the
  owner signs the review packet.
- Approval never authorises browser submission, login automation or account
  mutation.


## Validation log

- Focused rules and policy-state set: 79 passed.
- First full-suite activation run: 582 passed, 19 failed. All failures were
  stale migration expectations: 17 optimiser/replay paths still supplied
  `2026-27-v0.1`; two live-episode tests still expected the verified catalogue
  to be blocked.
- Migrated the optimiser golden input and regenerated both deterministic output
  artifacts. Selected transfers, objective (`60.4`), candidate count (`123`)
  and output fingerprint remained unchanged.
- Preserved the hard activation gate using an intentionally provisional rules
  copy and added the positive verified-live-rules path.
- Affected regression set after migration: 127 passed.
- Final complete repository suite after migration: 601 passed in 392.14s.
## Outcome

Alastair approved `2026-27-v1.0` at ruleset SHA-256
`3439006e5ad21d0e497732273ff9b674e599010df98f0104272c53cea6be0c5a`
on 27 July 2026 at 19:01:48 UTC for advisory engine use only. The approved,
self-hashed packet continues to deny browser execution and FPL account writes.