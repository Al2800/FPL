# 06 — Approve the live initial-squad policy

**Blocked by:** None — can start immediately.

**Status:** resolved

**Category:** enhancement

**Former bead:** `FPL-bsw.38`

## Human Handoff

**Summary:** Verify the completed early-season/live-squad programme and record
hash-bound owner approval for the prospective 2026/27 starting 15.

### Current behaviour

All 14 implementation children of the former epic are closed. The repository
already contains:

- a prospective live initial-squad policy;
- a versioned policy configuration with an owner-approval gate;
- deterministic, robust and selected-arm checkpoint/rehearsal paths; and
- focused optimisation/integration coverage.

The residual is **not** to design or implement the policy again. It is to
confirm the parent acceptance criteria and record owner approval against an
exact frozen packet/proposal. Without that approval, outputs remain inspectable
but `ready_for_manual_entry` must stay false.

### Desired behaviour

The owner reviews a cutoff-safe proposal and records:

- the selected policy arm;
- the exact frozen evidence packet and proposal hashes;
- the active 2026/27 ruleset/hash;
- the decision cutoff and approval timestamp; and
- an explicit approve/reject outcome.

Approval is advisory/manual-entry only. It grants no FPL account, browser or
execution authority.

### Key interfaces

- Policy `approval_gate`: owner approval required, active ruleset required, and
  deterministic/robust/selected arms completed.
- Checkpoint result: frozen packet/proposal hashes, selected arm, cutoff,
  validation status and explicit blocked reasons.
- `ready_for_manual_entry`: true only when every gate passes and approval
  occurred no later than the cutoff.
- Parent evidence boundary: GW1 seed selection is distinct from GW2–GW11 weekly
  evidence; retrospective isolated/longitudinal comparisons cannot alter the
  canonical 2025/26 trajectory.

### Acceptance criteria

- [x] The existing policy/config are verified as prospective, point-in-time and reproducible; no retrospective outcome is used to tune the live selection.
- [x] Closed-child evidence confirms GW1 seed selection is separated from GW2–GW11 evidence and both isolated and longitudinal comparisons remain documented.
- [x] The active ruleset/hash, completed arms and deterministic validation all pass before approval is accepted.
- [x] The owner sign-off names the selected arm and binds the exact packet/proposal hashes, cutoff and approval timestamp.
- [x] A missing, late or hash-mismatched approval leaves `ready_for_manual_entry: false` with explicit reasons.
- [x] Canonical 2025/26 artifacts and hashes are unchanged.
- [x] `python3 -m pytest -q tests/optimisation/test_initial_squad.py tests/integration/test_initial_squad_checkpoint.py tests/integration/test_live_readiness_rehearsal.py` passes (21 tests at handoff).
- [x] The ticket records the approval or rejection outcome so ticket 07 can close after approval, or remain blocked with a focused remediation ticket after rejection, without consulting Beads.

### Out of scope

- Re-opening or duplicating the 14 closed implementation children.
- Re-running, retuning or amending the canonical 2025/26 trajectory.
- Writing to an FPL account or adding authenticated/browser execution.
- Weakening the separate 2026/27 rules activation/sign-off requirement.
- Treating optimiser output as owner approval.

## Answer

**Outcome: policy ratified; live proposal approval deferred.**

The policy contract is approved and hash-bound. No specific starting-15 proposal
is approved because the current live checkpoint remains degraded pending a
decision-grade six-GW forecast packet. `ready_for_manual_entry` stays false.

- Sign-off: `docs/evaluation/2026-27-initial-squad-policy-signoff.md`
- Policy: `control/policies/initial-squad-2026-27.json`
- Policy SHA-256: `39e3b6303203d89e053cdb9af2c2f8b5f7f3cb62cf2a823c686803284b234069`
- Preferred arm when decision-grade: `robust`
- Focused tests: 21 passed
- Ticket 07 may proceed on policy ratification; it must not treat this as squad approval
