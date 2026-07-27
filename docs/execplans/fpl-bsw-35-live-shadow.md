# Run Paired Evidence and No-Evidence Live Shadows

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections must stay
current.

## Purpose / Big Picture

This change turns the live advisory path into a prospective experiment. For
each Gameweek, one deterministic control and one evidence-enabled arm share the
same official structured context, freeze before the same cutoff, and carry
separate squads, transfers and chips. The evidence arm also freezes a
no-evidence action from its own inherited state. After the outcome is available,
that third action separates the effect of current evidence from the effect of
state inherited from earlier evidence decisions.

The result is observable through immutable weekly artifacts. A fixture run can
be repeated byte-for-byte, cannot submit anything to FPL, and reports
deterministic points, current-evidence points and inherited-state points
separately.

## Progress

- [x] (2026-07-27 09:32+01:00) Checked Beads for conflicts and claimed
  `FPL-bsw.35`; Agent Mail reservation registration timed out, so no reservation
  was assumed.
- [x] (2026-07-27 09:39+01:00) Inspected live capture and episode construction,
  hosted-agent completion gates, validated plans, policy transitions, evidence
  forks and the live-shadow promotion policy.
- [x] (2026-07-27 10:01+01:00) Added tests for immutable unstructured capture,
  paired freeze, completion refusal, independent transition, attribution and
  deterministic reproduction.
- [x] (2026-07-27 10:08+01:00) Implemented unstructured capture and episode
  binding, including raw-byte verification.
- [x] (2026-07-27 10:14+01:00) Implemented paired weekly freeze,
  reveal/transition, attribution and a local bundle runner.
- [x] (2026-07-27 10:20+01:00) Updated the executable candidate policy,
  generator and operator documentation.
- [x] (2026-07-27 10:23+01:00) Passed 32 focused and 111 broader regression
  tests.
- [x] (2026-07-27 10:34+01:00) Passed the complete 512-test suite and clean
  diff hygiene.
- [ ] Record Beads implementation, close, commit and push.

## Surprises & Discoveries

- Observation: the existing live episode builder already freezes official
  structured inputs and an outcome-free pending envelope, but it does not bind
  unstructured documents.
  Evidence: `src/orchestration/episode_builder.py` includes only the two official
  endpoint manifests in `observed.source_artifacts`.
- Observation: a two-arm comparison is insufficient once their squads diverge.
  Evidence: comparing evidence actual directly with control combines this
  week's evidence effect with all decisions inherited from prior weeks.
- Observation: the repository already has the correct primitives for legal
  freeze and longitudinal isolation.
  Evidence: `validate_and_freeze_plan` recomputes legal actions, and
  `transition_policy_state` binds each successor to its owning arm and previous
  state hash.
- Observation: the capture-level FPL deadline and the advisory decision cutoff
  can be different.
  Evidence: the existing live fixture captures at a deadline of 11:00 with a
  manager decision cutoff of 10:00.

## Decision Log

- Decision: use `forecast_optimizer` as the no-evidence control state and
  `evidence_agent` as the evidence state.
  Rationale: these are existing schema-valid policy arms and avoid inventing a
  parallel state contract.
  Date/Author: 2026-07-27 / Codex.
- Decision: freeze three plans per week: control actual, evidence-arm
  no-evidence counterfactual, and evidence-arm actual.
  Rationale: the middle plan gives an exact same-state bridge for decomposing
  current evidence and inherited state.
  Date/Author: 2026-07-27 / Codex.
- Decision: define “byte-identical structured input” as one shared
  content-addressed market/forecast context, while arm-owned longitudinal state
  remains explicitly separate.
  Rationale: after a genuine divergence, identical squads would destroy the
  experiment; identical external context is the causal control required.
  Date/Author: 2026-07-27 / Codex.
- Decision: unstructured evidence is admitted only from an enabled registered
  source with exact publication, observation and availability timestamps.
  Rationale: missing evidence should degrade to the deterministic control, not
  bypass source governance.
  Date/Author: 2026-07-27 / Codex.
- Decision: an empty degraded evidence capture may be reused when its inferred
  deadline differs from the advisory cutoff, but any complete capture must
  match the exact advisory cutoff.
  Rationale: an empty index contains no late information; admitted documents
  require exact point-in-time binding.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

The paired path now runs one complete fixture Gameweek, reproduces the same
frozen and revealed bytes, advances only the control and evidence actual
states, and reports an additive three-plan attribution. Real 2026/27 execution
remains correctly gated on rules activation and source review.

## Context and Orientation

`scripts/capture_fpl_live_shadow.py` captures unauthenticated official FPL
state. `src/orchestration/episode_builder.py` turns that capture and a manually
entered manager state into an immutable episode. `src/orchestration/validated_plan.py`
is the only legal action boundary. `src/orchestration/policy_state.py` owns
longitudinal squad, bank, free-transfer and chip state. The new
`src/orchestration/live_shadow.py` will compose these primitives rather than
duplicate their rules.

“Current evidence effect” means the evidence-arm actual result minus the result
of the no-evidence plan frozen from that same evidence-arm state. “Inherited
state effect” means that same-state no-evidence result minus the control result.
Their sum is the total evidence-trajectory difference.

## Plan of Work

Add a pure unstructured snapshot builder to `src/orchestration/live_shadow.py`.
Extend the capture CLI to copy operator-staged evidence bytes immutably and
write a self-hashed index. Extend the episode builder to verify that index,
reject late or changed bytes, and add admitted documents to the observed source
artifacts.

Add a paired weekly freeze function that accepts one shared structured context,
the two arm-owned states, and three candidate actions. It will enforce the
episode cutoff, evidence completion gate and no-account-write policy before
using the existing plan validator. Add a reveal function that accepts the three
scored outcomes, transitions only the two actual arms, and produces an additive
attribution artifact.

All files will use immutable writes and content hashes. The fixture runner will
exercise one full Gameweek without network access or an FPL account.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run focused tests:

    .venv/Scripts/python.exe -m pytest tests/integration/test_live_shadow_capture.py tests/integration/test_live_shadow_pairing.py -q

Run the complete suite:

    .venv/Scripts/python.exe -m pytest -q

No live capture, model call or account interaction is required.

## Validation and Acceptance

Tests must prove that enabled pre-cutoff evidence is immutable and bound to the
episode, while late, changed or disabled evidence is refused or explicitly
degraded. Both arms must reference the same structured-context hash. An
incomplete hosted-agent envelope must fall back to the evidence arm's
no-evidence plan. All plans must freeze no later than the cutoff.

After reveal, the control and evidence successors must have independent state
hashes and correct predecessor bindings. The attribution identity
`total = current evidence + inherited state` must hold exactly. Repeating the
fixture run must return identical artifacts and never set browser actions or
account writes.

## Idempotence and Recovery

Identical writes are reusable and differing bytes are refused. The code does
not delete data, install dependencies, fetch unapproved sources, authenticate,
or execute an FPL action. A missing evidence feed leaves the deterministic
trajectory available.

## Artifacts and Notes

Current proof transcripts:

    32 passed in 6.21s
    111 passed in 9.73s
    512 passed in 379.65s (0:06:19)
    fixture current evidence = +6
    fixture inherited state = 0
    fixture total evidence trajectory = +6

## Interfaces and Dependencies

`src/orchestration/live_shadow.py` will expose:

    def build_unstructured_evidence_capture(...) -> dict[str, Any]: ...
    def freeze_live_shadow_week(...) -> dict[str, Any]: ...
    def reveal_live_shadow_week(...) -> dict[str, Any]: ...

`src/evaluation/shadow_attribution.py` will expose:

    def attribute_shadow_outcomes(...) -> dict[str, Any]: ...

No new dependency is required.

Revision note (2026-07-27): created after inspecting the existing legal freeze,
state transition and hosted-agent gates; chose a three-plan weekly design to
make causal attribution valid after arm divergence.
