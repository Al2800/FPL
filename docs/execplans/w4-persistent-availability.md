# FPL-uwu — Versioned persistent-availability projection challenger

This is a living implementation plan. `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` are updated as work proceeds.

## Purpose / Big Picture

Availability evidence must be capable of affecting more than the Gameweek in
which it was observed: an accepted absence should persist until it expires or
is explicitly superseded by valid recovery evidence. The immutable
availability ledger remains the longitudinal source of truth. This work adds a
named projection challenger that reads a cutoff-safe view of that ledger and
derives forecast overrides without modifying claims, the baseline forecast or
the sealed historical replay.

The new policy is default-disabled. In disabled mode, all public outputs for
the structured and frozen no-evidence arms must be byte-identical to their
current outputs. Enabled behaviour is limited to an additive GW33--GW36
historical challenger evaluation. It is not an approval to promote evidence
adjustments to live production.

## Progress

- [x] 2026-07-30: Claimed FPL-uwu after verifying no non-parent active Bead
  owns its files.
- [x] 2026-07-30: Audited the current availability ledger, evidence arm,
  forecast/replay adapters, existing tests and policy directory.
- [ ] Define `evidence-adjustments-v2.yaml` with a default-disabled named
  availability challenger and its stable policy identity.
- [ ] Add a deterministic active-claim-to-projection adapter, including
  identity, temporal, source-hash and conflict refusal paths.
- [ ] Wire the adapter by explicit dependency injection into only the enabled
  challenger path; retain exact baseline/control bytes when absent/disabled.
- [ ] Produce an additive, hash-bound GW33--GW36 evaluation report.
- [ ] Run the focused availability/evidence-arm tests, validate canonical
  preservation, record results, close FPL-uwu and push the isolated change.

## Surprises & Discoveries

- The repository presently contains `control/policies/evidence-adjustments.yaml`
  but no `evidence-adjustments-v2.yaml`; V2 must therefore be additive so that
  sealed V1 replay references remain untouched.
- `src/evidence/availability_ledger.py` already supplies immutable append,
  cutoff-safe projection, explicit stale/superseded/future history and
  conflict abstention. The challenger must consume that contract instead of
  duplicating its lifecycle rules.

## Decision Log

- **Projection, not mutation.** The adapter returns new forecast/player views
  and an auditable applied-claim ledger. It never writes a claim, rewrites a
  structured projection or re-seals an existing baseline artefact.
- **Only negative availability state may reduce a challenger.** `unavailable`
  or `doubtful` can apply the policy's deterministic suppression. `available`
  and recovery claims remove a prior challenger effect and restore the exact
  structured baseline; no evidence can raise a forecast in this work.
- **Conflict fails closed.** Multiple active statuses for a player, invalid
  identity/source/hash bindings, post-cutoff claims, or unrecognised policy
  data produce no override and an explicit quarantine/refusal audit row.
- **A historical result is mechanics evidence, not promotion evidence.** The
  report will distinguish claim mechanics, decision deltas and realised score;
  it cannot fit weights or recommend enabling live adjustment.

## Context and Orientation

`src/evidence/availability_ledger.py` owns append-only validity and
`project_availability(ledger, decision_at)` state reconstruction. Its accepted
claims retain player identity, status, availability/expiry timestamps,
supersession references and source hashes.

`src/orchestration/weekly_evidence_programme.py` creates cutoff-safe context;
`src/orchestration/live_evidence_arm.py` freezes reviewed candidate plans and
must retain the frozen no-evidence control exactly. `src/forecasting/live_capture.py`
and `src/forecasting/replay_adapter.py` turn typed forecasts into solver inputs.
The existing V1 policy stays immutable; the V2 policy will name this challenger
and remain disabled by default.

## Plan of Work

1. Define an additive V2 policy containing schema/version, disabled default,
   accepted statuses, deterministic suppression semantics and an explicit
   policy hash. Parse and validate it without altering V1 callers.
2. Extend the availability-ledger projection boundary with a deterministic
   challenger projection function. It accepts only a validated ledger, named
   policy, cutoff/checkpoint and stable player identity mapping; it emits
   applied, restored, abstained and quarantined audit rows with source and
   claim identities.
3. Add narrowly-scoped adapter hooks in live capture/replay construction and
   the live evidence arm. The baseline structured and frozen no-evidence paths
   do not receive the projected state. An enabled named challenger obtains a
   new derived projection and a hash-bound audit record.
4. Construct a synthetic plus governed historical GW33--GW36 fixture/evaluation
   that proves N+1 persistence, expiry, recovery, duplicate idempotence,
   conflict/cross-player/post-cutoff refusal and preserved canonical hashes.
5. Write an additive report containing input/policy/ledger identities,
   checkpoint outcomes, applied mechanics and score comparison; state clearly
   that promotion still requires owner ratification and an ADR.

## Validation and Acceptance

Run from `C:\Users\Alastair\FPL-pr-review`:

    C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q ^
      tests\evidence\test_availability_ledger.py ^
      tests\integration\test_live_evidence_arm.py

Additional focused tests will demonstrate that disabled mode returns exact
existing baseline/control bytes, a negative claim persists at N+1 until
expiry/supersession, recovery restores the unmodified baseline, and invalid
bindings fail closed. The GW33--GW36 report must be additive and reference
policy/ledger/manifest hashes. No network, account, browser, secret or raw
data collection is part of this work.

## Idempotence and Recovery

The V2 policy and projection audit are canonically serialised and content
addressed. Identical ledger, policy, identity map and checkpoint inputs produce
identical challenger bytes. A changed input produces a new report/artefact;
it never overwrites V1 policies, the ledger or canonical replay artefacts.
If any prerequisite cannot be validated, the challenger returns an explicit
degraded/refused audit and the caller retains the baseline projection.

## Artifacts and Notes

Committed outputs are code, policy, tests, the ExecPlan and a compact
mechanics/evaluation report only. Raw source captures, live ledger data,
credentials and historical private payloads remain under ignored operational
data paths. No sealed canonical replay tree is mutated.

## Outcomes & Retrospective

Pending implementation and validation.

## Implementation update — 2026-07-30

Implemented `availability-persistence-v1` as an additive V2 policy that remains
false by default. `apply_persistent_availability_challenger` projects only a
copied solver input: explicit unavailability sets its start probability,
minutes and points to zero; doubt applies the configured 0.25 start-probability
cap; explicit recovery returns the untouched structured baseline. Every audit
binds policy, ledger, decision view, checkpoint and input/output hashes.

Added `synchronise_availability_from_live_evidence`, a one-way bridge from the
already governed live evidence ledger. Only exact `player_uid` identities and
source hashes are carried forward; direct official availability status mapping,
expiry, recovery, idempotence and refusal paths are tested. The live and
no-evidence ledgers are never altered by the projection challenger.

The tracked GW33--GW36 evidence materials cannot enter this live-shaped ledger:
they were captured after their historical deadlines, use non-registry source
identifiers, have day-level publication precision, and have no immutable source
hash. `reports/evaluation/w4-persistent-availability-gw33-gw36.json` records
this as a no-injection qualification rather than fabricating a retrospective
score result. Its canonical benchmark tree remained unchanged.

Validation: 59 focused evidence, collection, checkpoint, boundary and W4
evaluation tests passed in 9.97 seconds. A separate P0 follow-up, FPL-760,
tracks explicit collector supersession for an official status/news update; it is
needed before the live bridge can handle a changing official status chain.
