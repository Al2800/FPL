# Finish the audited GW30-GW38 trajectory and review the season

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current. It is maintained in accordance with `C:\Users\Alastair\.codex\.agent\PLANS.md`.

## Purpose / Big Picture

This work continues the accepted experimental policy state from terminal GW29 through the end of 2025/26. Each week freezes strictly pre-deadline evidence, asks fresh GPT-5.6 Sol evidence and challenger roles to assess it, applies only completed governed adjustments, scores a same-state control, and carries the resulting manager state forward. The final report will distinguish the deterministic engine, the incremental evidence effect, inherited state, and hosted-model reliability so that lessons improve the future 2026/27 live process rather than overfit the historical season.

## Progress

- [x] (2026-07-26 19:13Z) Create and claim Bead `FPL-0sz`; confirm no conflicting in-progress work.
- [x] (2026-07-26 19:28Z) Verify deadlines, canonical scores, the legally reconstructed GW30 state, and pre-deadline research windows.
- [x] (2026-07-26 19:18Z) Freeze the nine evidence bundles and add the sequential runner.
- [x] (2026-07-26 20:13Z) Run and preserve fresh evidence/challenger gates sequentially for GW30-GW38.
- [x] (2026-07-26 20:18Z) Add focused contracts for provenance, state chaining, attribution, terminal state, and hard completion gating.
- [x] (2026-07-26 20:25Z) Produce the deep season review with recommendations for the 2026/27 live engine.
- [x] (2026-07-26 20:35Z) Run focused and full tests, verify canonical immutability and byte-identical reruns (`484 passed`; GW38 tree hash unchanged).
- [x] (2026-07-26 20:40Z) Close Bead `FPL-0sz`; commit and push the completed block to `main`.

## Surprises & Discoveries

- Observation: GW31 is a blank gameweek for Arsenal, Crystal Palace, Manchester City, and Wolves.
  Evidence: the fixture structure is already present in the frozen episode and must not be duplicated as an evidence adjustment.

- Observation: Final-day team news contains unusually high rotation uncertainty, while confirmed starting line-ups were published only after the GW38 deadline.
  Evidence: only the May 21-22 press-conference reports are eligible; the May 24 line-up article is explicitly excluded as leakage.

- Observation: The final block scored 558 gross versus 509 canonical, with both policies incurring an eight-point hit, but all nine same-state evidence deltas were zero.
  Evidence: accepted `comparison.json` and `same-state-attribution.json` artifacts for GW30-GW38.

- Observation: The model's semantic judgements were generally conservative, but exact protocol compliance was fragile.
  Evidence: eight rejected versions in the final block cover nested schemas, invalid expiry, missing required fields, wrong role/key literals, fractional timestamps, hash mismatch, and challenger ID mismatch.

- Observation: A degraded GW33 challenger could reach fallback scoring before the runner enforced an explicit gate.
  Evidence: GW33 `sol-v2` is preserved as an unaccepted diagnostic; the runner now raises before scoring any non-completed evidence or challenger gate, and accepted GW33 is `sol-v3`.

- Observation: All second-half chips remained available entering GW38.
  Evidence: GW38 `starting-policy-state.json` lists Wildcard, Free Hit, Triple Captain, and Bench Boost; no chip appears in the accepted plan.

## Decision Log

- Decision: Begin GW30 by legally deriving the successor from terminal GW29 `sol-v1`.
  Rationale: GW29 was deliberately terminal, so reconstructing the transition from its sealed plan and outcome preserves the accepted experimental trajectory.
  Date/Author: 2026-07-26 / Codex

- Decision: Treat all historical evidence as exploratory and ineligible for headline agent-performance claims.
  Rationale: Publication precedes each deadline, but the cases were recovered after outcomes were known and were not preregistered.
  Date/Author: 2026-07-26 / Codex

- Decision: Complete one week before freezing the next hosted request.
  Rationale: The evidence target and its baseline must reflect the actual carried squad and transfer market produced by the preceding experimental decision.
  Date/Author: 2026-07-26 / Codex

- Decision: Stop state transition after GW38 and represent the sealed GW38 plan/outcome as the explicit terminal season state.
  Rationale: There is no GW39 market or decision episode. Inventing one would create a false state transition.
  Date/Author: 2026-07-26 / Codex

- Decision: Treat GW33 `sol-v2` as an unaccepted orchestration diagnostic and restart the entire week at `sol-v3`.
  Rationale: Its challenger reviewed a non-existent adjustment ID and degraded. The accidentally generated fallback comparison must not enter the accepted trajectory.
  Date/Author: 2026-07-26 / Codex

- Decision: Add an explicit runner-level refusal before any non-completed evidence or challenger gate can be scored.
  Rationale: Validation status must be a hard safety boundary, not merely metadata.
  Date/Author: 2026-07-26 / Codex

## Outcomes & Retrospective

The accepted final block scores 558 gross and 550 net versus canonical 509 gross and 501 net, a +49 finish. Across GW12-GW38 the accepted fork totals 1,530 gross, 1,522 net, and +65 versus canonical. Same-state evidence attribution across GW13-GW38 totals +16, but every GW30-GW38 evidence delta is zero. The review therefore attributes the late result to carried state and deterministic policy, not direct prose intervention. The largest newly exposed functional gap is chip planning: all chips remained unused. The largest protocol gap is host/model responsibility: wrappers, timestamps, IDs, and hashes should be host-generated. The accepted state chain terminates explicitly at GW38 with no fabricated successor.

## Context and Orientation

Canonical controls are under `reports/benchmarks/2025-26/gw-XX`; they are immutable. Experimental append-only versions are under `reports/benchmarks/2025-26-agent-forks/gw-XX/sol-vN`. Evidence bundles are under `evals/evidence-forks/2025-26/gw-XX/evidence-bundle.json`.

The manager policy state includes the 15-player squad, bank, free transfers, price basis, and chips. `derive_next_state_from_agent_fork` reconstructs the legal successor of a deliberately terminal week. `run_sequential_agent_fork_week` applies governed adjustments, solves, scores, and normally transitions. `build_same_state_control_attribution` reruns the unadjusted deterministic engine from the same experimental starting state to isolate the current week's evidence effect.

## Plan of Work

Add `scripts/run_gw30_gw38_agent_forks.py`, adapting the verified GW23-GW29 runner. Its GW30 state comes from the GW29 accepted fork; GW31-GW38 read only the preceding accepted successor. Prepare, validate-evidence, validate-challenger, and complete-week remain separate write-once stages. GW38 completes without a next-gameweek transition.

For each gameweek, freeze a source whose publication precedes the decision cutoff. Run a fresh GPT-5.6 Sol evidence role against only the host request, validate it locally, then run a separate fresh challenger. Failed versions remain unscored and a new `sol-vN` is created.

Add focused tests proving provenance, both gates, exact adjustment propagation, state hashes, same-state attribution, canonical comparison scores, the GW38 terminal boundary, and rerun stability. Then aggregate all accepted evidence-fork weeks into a deep review of points, transfers, captaincy, evidence reach, state drift, and reliability failures.

## Concrete Steps

Run from `C:\Users\Alastair\FPL` with the repository virtual environment:

    .venv\Scripts\python.exe scripts/run_gw30_gw38_agent_forks.py --mode prepare --gameweek 30
    .venv\Scripts\python.exe scripts/run_gw30_gw38_agent_forks.py --mode validate-evidence --gameweek 30
    .venv\Scripts\python.exe scripts/run_gw30_gw38_agent_forks.py --mode validate-challenger --gameweek 30
    .venv\Scripts\python.exe scripts/run_gw30_gw38_agent_forks.py --mode complete-week --gameweek 30

Repeat sequentially through GW38, passing the accepted preceding version when it is not `sol-v1`. Then run:

    .venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_gw30_gw38.py -q
    .venv\Scripts\python.exe -m pytest -q

## Validation and Acceptance

Acceptance requires a legal GW30 start, strictly pre-deadline sources, completed accepted gates, exact proposed/applied adjustment identity, state-hash continuity through GW38, nine same-state comparisons, no fabricated GW39, immutable canonical artifacts, and byte-identical accepted reruns. The deep review must report deterministic, evidence, inherited-state, and reliability effects separately.

## Idempotence and Recovery

All artifacts are write-once. Repeating a successful stage must reproduce the same object or refuse incompatible mutation. A failed hosted output is preserved under its original version and never repaired in place. Recovery advances to the next version. No cleanup is required or permitted.

## Artifacts and Notes

Verified canonical gross scores are GW30 45, GW31 63, GW32 53, GW33 79, GW34 36, GW35 44, GW36 89, GW37 70, and GW38 30. GW30 reconstructs with bank 0.4 and five free transfers.

## Interfaces and Dependencies

Use existing dependencies only. The core interfaces are `build_fork_solver_input`, `build_agent_host_bundle`, `run_agent_arm`, `run_sequential_agent_fork_week`, `build_same_state_control_attribution`, `derive_next_state_from_agent_fork`, and `artifact_hash`.
