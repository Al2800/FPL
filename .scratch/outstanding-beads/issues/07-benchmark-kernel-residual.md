# 07 — Close the Benchmark Kernel programme

**Blocked by:** None — ticket 06 resolved (policy ratified; live proposal deferred)

**Status:** resolved

**Category:** enhancement

**Former bead:** `FPL-bsw`

> Do not claim this ticket until ticket 06 is resolved. This is an evidence-led
> programme closure, not permission to add new benchmark features.

## Agent Brief

**Summary:** Verify the completed Benchmark Kernel against its governing
contracts, update active handoff/status documentation and resolve the local
programme ticket without mutating the Beads archive.

### Current behaviour

Thirty-seven of the former Benchmark Kernel epic's 38 direct children are
closed. The only residual child is the early-season/live-squad policy represented
by ticket 06. Episode contracts, replay, longitudinal state, policy arms and
evaluation already exist; this ticket must not rebuild them.

Focused benchmark-schema, registry and replay checks currently pass where
tracked-safe inputs are available. The genuine-replay suite intentionally skips
artifact-backed cases when governed Benchmark v0 episodes are absent; ticket 01
owns the broader portable/artifact CI boundary.

### Desired behaviour

Once ticket 06 records the owner outcome, the active docs and local tracker
state accurately say whether the Benchmark Kernel programme satisfies:

- immutable point-in-time episode manifests;
- no hidden-outcome access before proposal/GDR freeze;
- paired comparisons only when observed episode hashes match;
- deterministic validation and longitudinal state transitions;
- source-registry-gated collection; and
- advisory-only operation with browser/account execution deferred.

Any failed contract becomes a new focused ticket; it is not silently waived to
close this programme.

### Key interfaces

- Episode pairing key: byte-identical observed episode hash and cutoff-safe
  inputs (`available_at <= cutoff <= deadline`).
- Freeze/reveal order: validated proposal and GDR freeze before the evaluation
  process can reveal hidden outcomes.
- Run record: episode/snapshot/source hashes, code/rules/model/prompt/tool
  versions, budgets, validation, proposal/outcome, cost/latency, safety and
  degraded-mode evidence.
- Source gate: no source is collectible unless its registry record and
  governance permit it.
- Execution boundary: proposals remain advisory; no authenticated FPL or
  browser execution path is activated.
- Tracker closure: acceptance boxes ticked, `Status: resolved`, migration
  status updated; `.beads/issues.jsonl` remains untouched.

### Acceptance criteria

- [x] Ticket 06 records owner approval of the policy gate. The live proposal remains explicitly unapproved, so `ready_for_manual_entry` stays false.
- [x] Contract/schema checks confirm immutable episode/run records retain the required identities, versions, resource-use and safety fields.
- [x] Replay checks demonstrate proposal/GDR freeze occurs before hidden-outcome reveal. The portable transition guard passes; the full episode replay checks remain artifact-backed.
- [x] Evaluation documentation states that only equal observed episode hashes form paired comparisons and reports uncertainty plus resource use.
- [x] Registry checks confirm disabled/unapproved sources cannot collect; no browser/account execution path is enabled.
- [x] The portable acceptance command passes: `python3 -m pytest -q -m "not artifact_backed" tests/contracts/test_benchmark_schemas.py tests/historical-replay/test_genuine_replay.py tests/unit/test_registry.py` → 18 passed, 13 deselected. The governed replay subset reports 13 collected tests when artifacts are available.
- [x] No contract failure was found. Missing governed episode artifacts are an explicit provisioning limitation, not a waived contract failure.
- [x] Active handoff/migration docs no longer describe Beads as authoritative and accurately mark the programme outcome.
- [x] This ticket is set to `Status: resolved`; the archived Beads file is not edited.

### Out of scope

- Adding new policy arms, datasets or evaluation metrics.
- Re-running or tuning sealed historical trajectories.
- Resolving ticket 01's repository-wide artifact boundary inside this ticket.
- Enabling lineup providers, cloud infrastructure, rival analysis,
  live-match agents or computer-use execution.
- Closing or modifying the historical Bead.

## Answer

**Benchmark Kernel v1.0 contract verified and programme residual closed.**

- Ticket 06's owner outcome ratifies the prospective policy gate, but does not
  approve a live starting squad or grant manual-entry readiness.
- The fixed episode and policy-result schemas preserve the observed episode
  hash, source/manager/feature/uncertainty references, rules and code
  identities, tool/resource budgets, trace and proposal/GDR hashes, validation,
  freeze timestamp and sealed-outcome boundary.
- `docs/evaluation/benchmark-kernel-closure.md` records the audit evidence,
  paired-comparison rule, uncertainty/resource reporting and the explicit
  artifact-backed replay limitation.
- The `.beads/` archive and `.beads/issues.jsonl` were not changed.
