# Integrate Chip Valuation into Weekly Longitudinal Decisions

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections must
remain current throughout implementation.

## Purpose / Big Picture

After this change, an enabled weekly policy can choose Wildcard, Free Hit,
Bench Boost or Triple Captain through the same pre-outcome decision boundary
that chooses transfers, lineup and captain. It compares every currently legal
chip with no-chip alternatives using identical observed inputs, a declared
future horizon, declining reserve value near chip expiry and explicit
uncertainty penalties.

The selected chip is not merely reported in a counterfactual. A hash-bound
weekly chip decision can enter both the genuine replay and agent-fork
orchestrators, become the active chip on the frozen plan, affect scoring, and
advance the correct policy state. Existing canonical 2025/26 files are never
rewritten; legacy calls without an enabled chip decision reproduce their
existing behavior.

## Progress

- [x] (2026-07-26 22:50+01:00) Claimed `FPL-bsw.33`, searched prior agent
  conversations, and traced chip generation, GW31 projection, plan validation,
  outcome scoring and policy-state transition.
- [x] (2026-07-26 23:05+01:00) Added regression tests for partial chip
  inventories, expiry pressure, terminal deployment, decision binding and
  orchestrator integration.
- [x] (2026-07-26 23:12+01:00) Generalised candidate generation and selection
  for currently eligible longitudinal inventory.
- [x] (2026-07-26 23:22+01:00) Added a sealed weekly chip decision contract and
  consumed it in genuine replay and both agent-fork entrypoints.
- [x] (2026-07-26 23:28+01:00) Updated the chip policy configuration,
  self-hash and documentation.
- [x] (2026-07-26 23:42+01:00) Passed 28 focused integration tests and the full
  repository suite of 497 tests; verified the policy hash and diff hygiene.
- [x] (2026-07-26 23:48+01:00) Added the implementation record, closed
  `FPL-bsw.33`, and committed the implementation as `ca136e0`.

## Surprises & Discoveries

- Observation: the GW31 machinery generates legal chip candidates and correctly
  restores Free Hit state, but `genuine_replay.py` and
  `agent_fork_adapter.py` always pass `active_chip=None`.
  Evidence: the three live plan-freeze call sites in those modules hard-code
  no chip.
- Observation: `generate_chip_candidates` requires all four chip bases to be
  present, which is true for the isolated GW31 case but false after any chip is
  used or a first-half set expires.
  Evidence: it raises `missing available chip candidates` whenever one base is
  absent.
- Observation: the fixed reserve never decays, so a valuable chip can remain
  unused in the terminal week even though it has no future option value.
  Evidence: `select_chip_candidate` subtracts the same configured reserve in
  every Gameweek and has no Gameweek or expiry input.
- Observation: policy state can contain both the current and future half-season
  chip sets, so raw inventory is not the same as current eligibility.
  Evidence: the GW12 state contains both `_fh` and `_sh` variants. Weekly
  generation now receives the eligible subset and verifies its half-season
  window against the active rules.

## Decision Log

- Decision: Keep chip-aware execution opt-in through a reviewed, hash-bound
  weekly chip decision.
  Rationale: new replay/live-shadow trajectories should use the policy, while
  immutable canonical artifacts and legacy reproduction tests must not change
  merely because source code was upgraded.
  Date/Author: 2026-07-26, Codex.
- Decision: Treat an absent or expired chip as an unavailable alternative, not
  a policy error.
  Rationale: longitudinal state deliberately removes used and expired chips.
  Date/Author: 2026-07-26, Codex.
- Decision: Decay each chip's reserve over a declared final-six-Gameweek window
  and make it zero at the chip deadline.
  Rationale: reserve represents future option value; that value approaches zero
  as opportunities disappear. Six weeks matches the declared planning horizon
  and avoids hindsight-based special dates.
  Date/Author: 2026-07-26, Codex.
- Decision: Keep future trajectory values and uncertainty penalties explicit
  inputs to the sealed decision.
  Rationale: the optimiser must not invent missing future data, and evaluation
  must be able to ablate these terms independently.
  Date/Author: 2026-07-26, Codex.
- Decision: Keep the naive baseline permanently no-transfer/no-chip.
  Rationale: allowing its chip use would change the meaning of the control arm.
  Chip-aware genuine replay therefore requires decisions for every other arm
  and rejects one for the naive arm.
  Date/Author: 2026-07-26, Codex.

## Outcomes & Retrospective

The reusable chip policy is now part of the ordinary decision boundary rather
than an isolated GW31 report. It supports depleted inventories, exact
half-season eligibility, future trajectory values, expiry-adjusted reserve and
explicit uncertainty. Its sealed decision can be revalidated from source
inputs and is consumed before plan freeze by both genuine replay and agent
forks.

The end-to-end agent test selected Triple Captain, froze it on the validated
plan, scored it through the normal outcome scorer and persisted the chip
decision. Existing static GW31 tests continue to prove Free Hit restores squad,
purchase prices, bank and banked transfers. Legacy no-chip replay remains
byte-compatible because chip mode is additive and absent fields are not emitted
when disabled.

## Context and Orientation

`src/optimisation/chips.py` currently generates eight GW31 alternatives and
selects one from immediate expected points, a caller-provided future trajectory
and a fixed reserve. A reserve is the declared value of keeping a scarce chip
for later. `src/evaluation/chip_counterfactual.py` builds the six-week GW31
horizon and proves Free Hit restoration.

`src/orchestration/genuine_replay.py` freezes one reviewed candidate per policy
arm, then reveals the outcome and advances longitudinal state.
`src/orchestration/agent_fork_adapter.py` performs the same sequence after
reviewed evidence adjustments. A “weekly chip decision” will be a self-hashed
record binding the exact solver input, no-chip solver output, state, rules,
configuration, evaluated candidate matrix and selected candidate. This makes
chip choice reviewable before hidden outcomes become accessible.

## Plan of Work

Update `src/optimisation/chips.py` so candidate generation always emits the
complete no-chip transfer ladder plus only currently available chip
alternatives. Extend selection with current Gameweek, per-chip expiry, and
candidate uncertainty. Effective reserve remains at its declared maximum until
the final configured decay window, then declines linearly to zero at expiry.
Policy value becomes immediate expected net points plus discounted future value
minus effective reserve minus uncertainty penalty.

Add `build_weekly_chip_decision` and `validate_weekly_chip_decision`. The builder
will generate and select candidates, bind all inputs by hash, copy the chosen
candidate and seal the record. The validator will recompute the content hash
and all input bindings before an orchestrator can use it.

Extend `select_policy_candidate` and `finalise_historical_gameweek` in
`src/orchestration/genuine_replay.py` to accept an optional decision per arm.
When chip mode is enabled, require a decision for every non-naive policy arm;
the naive arm remains its defined no-transfer/no-chip control. Persist each
decision beside the frozen plan. Extend the shared agent-fork runners in
`src/orchestration/agent_fork_adapter.py` with the same optional contract.

Update `control/policies/chip-v1.json` with the reserve decay window and default
uncertainty penalties, refresh its self-hash, and expand
`docs/evaluation/chip-policy.md` to distinguish the isolated GW31 experiment
from the reusable weekly path.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`. Run:

    .venv\Scripts\python.exe -m pytest tests/historical-replay/test_chip_policy.py tests/agent-evals/test_agent_fork_adapter.py -q
    .venv\Scripts\python.exe -m pytest tests/historical-replay tests/agent-evals -q
    .venv\Scripts\python.exe -m pytest -q
    git diff --check

Record the exact test counts and important behavior here. Before any subsequent
bead, re-check Beads and claim only open work.

## Validation and Acceptance

A state containing only one unused chip must still produce the no-chip ladder
and that chip alternative. At a normal distance from expiry, a marginal gain
must retain the chip. At its terminal deadline, the same otherwise valuable
chip must have zero reserve and be selectable if it clears the declared minimum
gain after uncertainty.

A weekly decision must fail validation after any candidate, hash, state, rules,
expiry or selection field is changed. Passing it to genuine replay or an agent
fork must place its `selected_active_chip` on the frozen plan. A Free Hit
transition must restore the predecessor squad, purchase prices, bank and free
transfers; other chips must consume the chip and use ordinary persistent state.

Legacy calls without chip mode must still reproduce committed accepted replay
artifacts. Tests must hash the canonical tree before and after chip-aware
experiments and observe no change.

## Idempotence and Recovery

All builders and validators are pure until the existing orchestrators write to
their caller-selected output directory. Tests use temporary directories.
Nothing deletes or rewrites historical episodes or canonical reports. No
package install, download, model call, browser action or FPL account write is
required.

## Artifacts and Notes

The final validation evidence is:

    28 passed in 167.66s
    chip policy hash verified
    497 passed in 370.38s (0:06:10)

The existing GW31 canonical-integrity test recalculated the complete tree hash
and passed. The new agent integration test exercised a selected chip through
freeze, score and persisted output.

## Interfaces and Dependencies

In `src/optimisation/chips.py`, add:

    def build_weekly_chip_decision(
        base_input: SolverInput,
        canonical_output: Mapping[str, Any],
        *,
        state_sha256: str,
        config: Mapping[str, Any],
        rules: Mapping[str, Any],
        ruleset_sha256: str,
        current_gameweek: int,
        chip_expiry_gameweeks: Mapping[str, int],
        future_trajectory_values: Mapping[str, float],
        uncertainty_penalties: Mapping[str, float] | None = None,
    ) -> dict[str, Any]: ...

    def validate_weekly_chip_decision(
        decision: Mapping[str, Any],
        *,
        base_input: SolverInput,
        canonical_output: Mapping[str, Any],
        state_sha256: str,
        ruleset_sha256: str,
    ) -> None: ...

Use existing `artifact_hash`, `fingerprint`, `solve`, `SolverInput`,
`validate_and_freeze_plan`, `score_revealed_outcome`, and
`transition_policy_state`. No new dependency is needed.

Revision note (2026-07-26): created after tracing the isolated GW31 chip work
and identifying the missing weekly orchestration boundary.

Revision note (2026-07-26): updated after implementation with the eligibility
discovery, final decisions, end-to-end behavior and validation transcripts.

Revision note (2026-07-26): recorded the closed bead and implementation commit
after all acceptance evidence passed.
