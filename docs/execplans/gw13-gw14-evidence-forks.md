# Research and run sequential Sol evidence forks for GW13 and GW14

This ExecPlan is a living document. `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be updated as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

Continue the inspected GW12 agent fork for exactly two weeks. For each historical deadline, research only information published beforehand, preserve its truthful 2026 recovery time, ask a proposal-only GPT-5.6 Sol evidence role to interpret it, ask an independent challenger to review every proposal, and let a deterministic adapter decide whether any projection change is permitted. GW13 must advance the altered GW12 squad and finances into GW14; the experiment stops before GW15.

This is both a replay and an orchestration test. GW13 deliberately contains evidence that may justify no negative adjustment, while GW14 contains a definitive suspension plus weaker rotation opinion. A useful result is not necessarily more points: it is a correctly weighted, reproducible decision path with abstention, application, state transition, and limitations visible.

## Progress

- [x] (2026-07-26 13:14+01:00) Create and claim Bead `FPL-7n2`; confirm no file conflict.
- [x] (2026-07-26 13:16+01:00) Confirm exact cutoffs: GW13 `2025-11-29T13:30:00Z`; GW14 `2025-12-02T18:00:00Z`.
- [x] (2026-07-26 13:25+01:00) Research and freeze minute-precise BBC pre-deadline records for Semenyo/Gabriel in GW13 and Senesi/Joao Pedro in GW14.
- [x] (2026-07-26 13:36+01:00) Generalise the host-bundle and isolated-fork seams without altering sealed GW12 artifacts.
- [x] (2026-07-26 13:45+01:00) Add sequential state, abstention, challenger, freeze-before-reveal, immutability, same-state attribution and idempotence contracts.
- [x] (2026-07-26 13:55+01:00) Run the two evidence/challenger pairs and materialise GW13 then GW14.
- [x] (2026-07-26 14:05+01:00) Pass 31 focused and 456 full-suite tests; reproduce both comparison files byte-identically.

## Surprises & Discoveries

- Observation: GW13 research does not reveal a new confirmed absence in the carried fork squad.
  Evidence: the strongest relevant update says Iraola is hopeful Semenyo will be available. The other injury item concerns Gabriel, whom the GW12 fork already sold.

- Observation: GW14 has a crisp test of unstructured evidence correcting structured state.
  Evidence: at 16:32 GMT, 88 minutes before the deadline, BBC listed Marcos Senesi under yellow-card suspensions. The locked structured input still assigns him 82.9 expected minutes and 0.91 start probability.

- Observation: the same GW14 source page contains materially weaker information about Joao Pedro.
  Evidence: an expert reports competing fan views about a rest and says they would sell, but provides no manager confirmation. The bundle preserves that distinction instead of pre-assigning an adjustment.

- Observation: the challenger prevented weak secondary evidence from entering GW13.
  Evidence: the evidence role proposed Gabriel expected minutes `68 -> 50` at the minimum 0.60 confidence, but the challenger returned `confidence_downgrade`; the deterministic adapter preserved the exact structured input.

- Observation: the agent correctly separated two evidence strengths in GW14.
  Evidence: it proposed Senesi expected minutes `82.9 -> 0` at 0.99 confidence and made no João Pedro adjustment because the contested opinion remained below threshold.

- Observation: correcting a factual availability error did not improve realised points.
  Evidence: from the identical GW14 fork state, structured control made two transfers and scored 61. The evidence decision added Porro to Chalobah, kept suspended Senesi benched, and scored 60. The isolated evidence effect is therefore -1, while the -3 versus canonical includes -2 from earlier state divergence.

## Decision Log

- Decision: use the BBC live posts with minute-level timestamps for temporal proof.
  Rationale: PremierLeague.com corroborates Senesi's suspension but exposes only the publication date in the rendered page. The BBC post proves availability at 16:32, before the 18:00 cutoff.
  Date/Author: 2026-07-26 / Codex.

- Decision: include evidence about both owned and unowned market players.
  Rationale: an unowned player's availability still affects the optimiser's buy pool. Gabriel's continuing injury remains decision-relevant even though the fork sold him in GW12.
  Date/Author: 2026-07-26 / Codex.

- Decision: treat a no-adjustment GW13 proposal as a successful agent abstention, not a provider failure.
  Rationale: positive/uncertain evidence should not be forced into the reduction-only application policy.
  Date/Author: 2026-07-26 / Codex.

- Decision: advance state from the actual GW12 agent plan and outcome, then from the actual GW13 fork into GW14.
  Rationale: using canonical starting states would erase the transfer, bank, purchase-price and free-transfer consequences being tested.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The two-week extension is complete and stops before GW15.

GW13 began from the legal successor of the sealed GW12 agent plan, with Muñoz owned and Gabriel sold. The evidence role abstained on positive Semenyo evidence but proposed a modest Gabriel minutes reduction based on secondary expert advice. The challenger downgraded it, so the adapter applied nothing. The fork made no transfer, captained Salah and scored 37 versus canonical 36. Its same-state structured control was identical, proving zero evidence effect.

GW14 began from GW13 successor state `a36acb0d34170e572e0912c2124493667a60f5cdd64566a93b428afdf0ae3d03`. The evidence role proposed only Senesi expected minutes `82.9 -> 0`; it abstained on João Pedro rotation opinion. The challenger dismissed the Senesi challenge and the adapter applied the coherent zeroing. The optimiser made João Pedro to Haaland, Salah to Eze, and Porro to Chalobah, captained Haaland, took no hit, and scored 60. Canonical scored 63. The paired same-state control made only the first two transfers and scored 61, so accepted evidence itself cost one realised point; the other two points of canonical difference came from prior fork state.

Across GW12-14, the agent fork scored 140 versus canonical 128, retaining a cumulative +12 despite GW14. This remains exploratory: sources were recovered later and cases were selected retrospectively. Both canonical tree hashes remained unchanged, both comparison files reproduced byte-identically, 31 focused tests passed and the full repository passed 456 tests.

## Context and Orientation

The sealed GW12 run is under `reports/benchmarks/2025-26-agent-forks/gw-12/sol-v1`. Its validated plan sold Gabriel for Daniel Muñoz and scored 43. `transition_policy_state` is the only legal way to derive the GW13 state.

Canonical features and locked forecasts for each later week remain valid observed inputs, but canonical policy state does not: the fork has a different squad and purchase history. `build_replay_solver_input` must combine each week's canonical observed feature/forecast with the fork-owned state.

`agent_fork_adapter.py` currently has GW12-named preparation and execution functions. Generalisation must retain wrappers or byte behaviour for the sealed GW12 workflow.

## Plan of Work

Generalise host-bundle construction to accept a gameweek, evidence bundle and solver input. Keep the existing GW12 wrapper. Source documents expose exact immutable passages and truthful publication/observation/availability times. Do not include prior realised scores, hidden outcome references, or the manual fork.

Add a sequential week executor that accepts an already-derived policy state, constructs the week-specific solver input from observed feature/forecast artifacts, applies reviewed reductions or an unchanged abstention, solves and freezes, and only then reads the hidden outcome. Transition to the next week using the next feature market. Persist every state, plan and transition hash below the agent-fork root.

For each week, construct and run the evidence role first. Only a completed, hash-bound evidence artifact may enter the challenger request. The challenger reviews every exact adjustment ID. The deterministic adapter continues to forbid increases, unsupported targets, multiple changes per player, baseline mismatches, unresolved challenges and excessive start-probability deltas.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

    .\.venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_gw13_gw14.py tests/agent-evals/test_agent_fork_adapter.py -q
    .\.venv\Scripts\python.exe -m scripts.run_gw13_gw14_agent_forks --mode prepare --gameweek 13
    .\.venv\Scripts\python.exe -m scripts.run_gw13_gw14_agent_forks --mode prepare --gameweek 14

After the four approved Sol responses are captured:

    .\.venv\Scripts\python.exe -m scripts.run_gw13_gw14_agent_forks --mode complete
    .\.venv\Scripts\python.exe -m scripts.run_gw13_gw14_agent_forks --mode complete
    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

Every cited post timestamp is before its exact deadline. Later recovery is explicit. Agent requests recursively contain no hidden/realised outcome reference. GW13's starting state must equal the legal successor of the sealed GW12 agent fork. GW14's starting state must equal the legal successor of the new GW13 fork.

Both plans must validate and freeze before outcome access. Canonical GW13 and GW14 tree hashes must remain unchanged. A repeated complete run must be byte-identical. No GW15 state or directory may be written.

## Idempotence and Recovery

Writers fail on differing existing bytes. A changed source, policy, response or prompt needs a new versioned experiment root. Provider or challenger failure yields an unchanged solver input for that week and still records the degradation. No partial adjustment may be carried into the state chain.

## Artifacts and Notes

Research sources:

    GW13 BBC live post, 2025-11-28 15:54 GMT: Iraola hopeful Semenyo available
    GW13 BBC live post, 2025-11-28 15:59 GMT: expert still treats Gabriel injury as a sell
    GW14 BBC live post, 2025-12-02 16:32 GMT: Senesi yellow-card suspension
    GW14 BBC live post, 2025-12-02 16:36 GMT: contested Joao Pedro rotation opinion

## Interfaces and Dependencies

No new package is required.

The generalised executor returns the week's comparison plus its legal successor state and transition. The CLI owns the fixed order GW12 successor derivation, GW13 execution, then GW14 execution, and refuses any terminal week beyond 14.

Revision note (2026-07-26): Initial plan written after cutoff verification and pre-deadline source research established a deliberate GW13 abstention/GW14 application contrast.

Revision note (2026-07-26): Completed both sequential forks and added same-state attribution after the raw canonical comparison showed a -3 GW14 delta. The paired control established that accepted evidence accounted for -1 and earlier state divergence for -2.
