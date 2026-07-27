# Gate Paid Transfers with Complete Counterfactual Ladders

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections must stay
current.

## Purpose / Big Picture

After this change, the policy cannot select a paid transfer merely because its
point estimate is fractionally higher after subtracting the nominal four-point
hit. Any paid plan must be accompanied by the legal zero-, one-, two- and
three-transfer alternatives plus currently relevant chip alternatives. The
artifact will show immediate pre-hit gain, nominal hit, multiweek value,
uncertainty, risk premium and the first projected payback Gameweek.

The gate selects a paid action only when its pre-hit multiweek advantage covers
the hit, uncertainty and a configured premium. GW34’s eight-point hit can then
be rerun from the sealed cutoff data to explain whether it passed this stronger
test, without modifying canonical replay files.

## Progress

- [x] (2026-07-27 07:25+01:00) Claimed `FPL-bsw.34`, searched prior
  conversations and inspected the solver, receding-horizon planner, chip
  projection, transfer policy and GW34 sealed artifacts.
- [x] (2026-07-27 07:33+01:00) Added red tests for ladder completeness,
  risk-premium refusal, acceptance, payback and chip comparison.
- [x] (2026-07-27 07:39+01:00) Implemented the immutable counterfactual ladder
  and solver application boundary.
- [x] (2026-07-27 07:49+01:00) Added same-cutoff fixed-squad horizon projection
  and the reproducible GW34 evaluator.
- [x] (2026-07-27 08:02+01:00) Updated configuration, self-hash and policy
  documentation with the sealed GW34 findings.
- [x] (2026-07-27 08:17+01:00) Passed 10 focused, 106 optimisation/historical
  and 502 full-suite tests; proved byte-deterministic report reproduction,
  policy hash integrity and clean diff hygiene.
- [x] (2026-07-27 08:24+01:00) Added the implementation record, closed
  `FPL-bsw.34`, and committed and pushed the implementation as `1fd3b56`.

## Surprises & Discoveries

- Observation: GW34 selected three transfers for an eight-point hit even though
  its one-week net objective was only 1.43 points above the best one-transfer
  alternative.
  Evidence: the reviewed objectives are 34.16 for one transfer and 35.59 for
  three transfers.
- Observation: the solver already records the best candidate for each transfer
  count when the option-value policy is enabled, but selection has no
  uncertainty or premium above nominal hit arithmetic.
  Evidence: `best_by_transfer_count` contains complete GW34 entries with hit
  costs 0, 0, 4 and 8; `selected` is simply the maximum objective.
- Observation: the existing multiweek planner can value a future tail from a
  same-cutoff horizon, and the chip counterfactual already projects separate
  post-action states.
  Evidence: these components can provide candidate-specific weekly values
  without reading realised outcomes.
- Observation: independently replanning every transfer and chip branch caused
  dozens of full transfer searches and did not complete at a useful review
  cadence.
  Evidence: the first background GW34 evaluation remained active after several
  minutes. It was stopped and replaced with a zero-future-transfer tail that
  completes deterministically in about 43 seconds.
- Observation: the GW34 hit looks marginal for one week but strong when the
  initial squad change is held over four weeks.
  Evidence: the three-transfer plan has 135.89 horizon net value versus 113.44
  for the best no-hit plan. Its 30.45 pre-hit advantage clears the 12.5 hurdle
  and pays back in GW35.

## Decision Log

- Decision: Apply the premium to each paid transfer, in addition to the nominal
  hit and forecast uncertainty.
  Rationale: an eight-point hit contains two independently uncertain paid
  moves and should require more evidence than a four-point hit.
  Date/Author: 2026-07-27, Codex.
- Decision: Define payback as the first horizon week where cumulative pre-hit
  advantage over the best no-hit action covers nominal hits, premium and
  uncertainty.
  Rationale: this directly answers when the paid action is expected to have
  compensated for all costs, rather than reporting an opaque aggregate.
  Date/Author: 2026-07-27, Codex.
- Decision: Keep raw solver generation available, then require a sealed gate
  artifact before a hit-aware policy consumes `selected`.
  Rationale: callers need the complete candidate matrix before they can project
  candidate-specific futures; legacy canonical generation remains reproducible.
  Date/Author: 2026-07-27, Codex.
- Decision: Refuse an incomplete transfer-count or eligible-chip ladder.
  Rationale: missing safer alternatives would systematically bias the gate
  toward a paid plan.
  Date/Author: 2026-07-27, Codex.
- Decision: Use a zero-future-transfer tail for the hit counterfactual rather
  than independently replanning each branch.
  Rationale: this isolates the value of the initial action, keeps later
  free-transfer flexibility as a separate reported term, and avoids both
  confounding and an unnecessary search explosion.
  Date/Author: 2026-07-27, Codex.

## Outcomes & Retrospective

The transfer-hit gate is complete. A sealed artifact now binds the exact solver
input/output, policy, weekly horizon values, complete transfer ladder and
eligible chips. It separates pre-hit, net, uncertainty, premium, option value
and payback, and the solver application boundary preserves the ungated choice
while exposing only the gate winner as `selected`.

The GW34 artifact contains all four transfer counts and four eligible
second-half chips without opening the hidden outcome. Contrary to the one-week
impression, the eight-point hit survives the declared four-week gate. This is
an exploratory process result, not a calibration claim: historical future
fixtures are reconstructed and player rates/prices are frozen at GW34.

## Context and Orientation

`src/optimisation/solver.py` generates one-week candidates and records the best
candidate by transfer count. `src/optimisation/multiweek.py` performs a bounded
same-cutoff beam search and exposes one executable action plus an advisory
tail. `src/optimisation/chips.py` and
`src/evaluation/chip_counterfactual.py` evaluate chip states. The new
`src/evaluation/transfer_counterfactual.py` will combine these inputs without
accessing hidden outcomes.

A “no-hit control” is the best horizon-valued candidate whose hit cost is zero;
depending on available free transfers this can contain several transfers. A
“paid transfer” is a transfer beyond the free allowance. The “pre-hit
advantage” adds the paid candidate’s hit back before comparing it with the
control. The “hurdle” is nominal hit plus premium plus uncertainty.

## Plan of Work

Add versioned hit-gate fields to
`control/policies/transfer-horizon-v1.json`: required transfer counts, premium
per paid transfer, uncertainty penalty per paid transfer, and completeness
rules. Refresh the policy self-hash.

Create `src/evaluation/transfer_counterfactual.py`. Its pure builder will
validate configuration and solver bindings, require the entire ladder, derive
each row’s immediate pre-hit and net values, combine caller-supplied weekly
same-cutoff values, calculate uncertainty and payback, include eligible chip
rows, and select the best action that clears its hurdle. The artifact will be
self-hashed and fully reproducible.

Add `apply_transfer_hit_gate` to `src/optimisation/solver.py`. It will validate
that the artifact belongs to the unmodified solver output and return a copied
output whose selected candidate is the gate winner. It will preserve the
ungated candidate and attach the gate’s identity and decision summary.

Use the existing same-cutoff fixture projector and candidate-state projection
to implement `evaluate_gw34_transfer_hit`. It will read only GW34 cutoff inputs
and stripped fixture schedules, project GW34–GW37, build transfer and chip
rows, and hash the canonical tree before and after. A small script will write
the report outside the canonical replay.

## Concrete Steps

Work from `C:/Users/Alastair/FPL` and run:

    .venv\Scripts\python.exe -m pytest tests/optimisation/test_transfer_counterfactual.py tests/historical-replay/test_chip_policy.py -q
    .venv\Scripts\python.exe -m scripts.run_gw34_transfer_counterfactual
    .venv\Scripts\python.exe -m pytest tests/optimisation tests/historical-replay -q
    .venv\Scripts\python.exe -m pytest -q
    git diff --check

Record exact results in this document before closure.

## Validation and Acceptance

An incomplete 0/1/2/3 matrix or missing eligible chip must raise instead of
selecting a paid plan. A marginal eight-point plan whose pre-hit advantage does
not cover eight points plus two premiums and uncertainty must lose to the
no-hit control. A stronger plan must pass, and its artifact must record the
first payback week.

Applying the gate to a different or mutated solver output must fail. Applying a
valid artifact must replace `selected`, retain `ungated_selected`, and expose
the exact premium and artifact hash.

The GW34 report must bind the reviewed state, input, output, forecast, rules,
horizon and policy; show all four transfer counts and all eligible second-half
chips; explain the eight-point verdict; and prove the canonical tree hash did
not change.

## Idempotence and Recovery

The evaluator is read-only and deterministic apart from observational runtime,
which is excluded from decision hashes by the existing multiweek contract.
The report command may be rerun to the same non-canonical destination. No file
is deleted, no package is installed, and no model, browser or FPL account is
used.

## Artifacts and Notes

The initial baseline was:

    GW34 one transfer: 34.16 net expected points, hit 0
    GW34 three transfers: 35.59 net expected points, hit 8
    ungated net advantage: 1.43

The final proof transcripts are:

    10 passed in 36.85s
    106 passed in 200.54s
    502 passed in 383.93s (0:06:23)
    deterministic report sha256=b6d82ebd5e8d88a0e83faa1a8acbc898a4e8de3ae2d04a29b277a40d810338d0
    transfer policy hash verified

The sealed verdict is:

    best no-hit horizon value = 113.443565
    three-transfer horizon value = 135.894121
    pre-hit horizon advantage = 30.450556
    eight-point-hit hurdle = 12.5
    projected payback = GW35
    selected = transfer_count:3

## Interfaces and Dependencies

`src/evaluation/transfer_counterfactual.py` will expose:

    def build_transfer_counterfactual_ladder(
        *,
        solver_input: SolverInput,
        solver_output: Mapping[str, Any],
        config: Mapping[str, Any],
        horizon_weekly_values: Mapping[str, Sequence[float]],
        eligible_chip_ids: Sequence[str] = (),
        chip_alternatives: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]: ...

    def validate_transfer_counterfactual_ladder(
        artifact: Mapping[str, Any],
        *,
        solver_input: SolverInput,
        solver_output: Mapping[str, Any],
    ) -> None: ...

`src/optimisation/solver.py` will expose:

    def apply_transfer_hit_gate(
        solver_output: Mapping[str, Any],
        gate_artifact: Mapping[str, Any],
    ) -> dict[str, Any]: ...

No new dependency is required.

Revision note (2026-07-27): created after inspection of GW34 and the reusable
same-cutoff projection components.

Revision note (2026-07-27): updated after implementation to record the
fixed-squad projection decision, GW34 verdict and all final validation
evidence.

Revision note (2026-07-27): finalized after closing `FPL-bsw.34` and pushing
implementation commit `1fd3b56` to `main`.
