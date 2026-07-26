# Run sequential evidence forks for Gameweeks 15 to 17

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

Continue the inspected 2025-26 evidence-agent trajectory through exactly Gameweeks 15, 16, and 17. Each week receives only information published before its historical deadline, an independent GPT-5.6 Sol evidence proposal, a separate challenger review, and the same deterministic optimiser used by the replay. The visible result is a three-week, stateful comparison that distinguishes the effect of unstructured evidence from the effect of the already-diverged squad.

This slice also exercises the season's exceptional AFCON rule. The legal transition after GW15 must give the manager five free transfers in GW16 regardless of how many were previously banked. The run stops after scoring GW17 and must not create any GW18 state.

## Progress

- [x] (2026-07-26 13:40+01:00) Create and claim Bead `FPL-ys9`; confirm no overlapping in-progress work.
- [x] (2026-07-26 13:43+01:00) Confirm the three cutoffs and identify deadline-safe GW15, GW16, and GW17 evidence.
- [x] (2026-07-26 13:45+01:00) Derive the intended GW15 starting squad and finances from the actual GW14 fork artifacts.
- [x] (2026-07-26 13:48+01:00) Generalise successor derivation and add three-week orchestration.
- [x] (2026-07-26 13:59+01:00) Capture six independent Sol responses and run GW15, GW16, and GW17 sequentially.
- [x] (2026-07-26 14:04+01:00) Prove state binding, top-up behavior, temporal safety, same-state attribution, canonical immutability, terminal behavior, and byte-identical reruns.
- [x] (2026-07-26 14:09+01:00) Pass 14 cross-slice focused contracts and 461 full-suite tests.
- [x] (2026-07-26 14:10+01:00) Record implementation evidence and close Bead `FPL-ys9`.
- [x] (2026-07-26 14:12+01:00) Commit the complete slice on `main`.
- [x] (2026-07-26 14:13+01:00) Push `main` and verify the remote head.

## Surprises & Discoveries

- Observation: the GW15 fork begins with three free transfers and £0.8m in the bank.
  Evidence: a direct legal transition from GW14 plan `e3cc7372...` produces GW15 state from the fork's own squad, prices, and outcome.

- Observation: a Friday GW17 Liverpool update is unsuitable despite containing useful Gakpo and Szoboszlai news.
  Evidence: the source gives only the date and “Friday morning”, while the deadline is 11:00 UTC. A separate VG article is precisely timestamped 12:32 UTC and is definitively too late.

- Observation: the grounding validator caught two errors in the first GW15 evidence response before optimisation.
  Evidence: the model initially copied document hashes into passage-hash fields, then used expiries equal to the decision cutoff. Both attempts degraded safely; corrected, independently computed hashes and source-record expiries passed.

- Observation: factually correct evidence can reduce realised points.
  Evidence: the GW16 Muñoz surgery correction changed the transfer from Eze-to-Rice to Muñoz-to-Guéhi. The evidence plan scored 58 and the identical-state control scored 59.

- Observation: confirmed absence evidence materially improved GW17.
  Evidence: correcting Mbeumo from 88.8 expected minutes to zero produced Mbeumo-to-Foden plus Gakpo-to-Rogers and 92 points. The same-state structured control left Mbeumo in the XI and scored 79.

## Decision Log

- Decision: use positive Senesi and Semenyo evidence in GW15 as a deliberate abstention case.
  Rationale: the evidence can prevent an unjustified reduction but the reduction-only adapter should not manufacture an uplift.
  Date/Author: 2026-07-26 / Codex.

- Decision: use Muñoz's surgery as the GW16 strong correction.
  Rationale: he is owned entering GW15, the source predates the deadline, and the structured forecast may otherwise retain expected minutes.
  Date/Author: 2026-07-26 / Codex.

- Decision: use Mbeumo's confirmed AFCON unavailability from GW17 and reject uncertain-timestamp Friday news.
  Rationale: the AFCON report was published on 13 December, a full week before the GW17 cutoff, and directly concerns a carried player.
  Date/Author: 2026-07-26 / Codex.

- Decision: preserve abstention as a completed, independently reviewed evidence result.
  Rationale: GW15's two positive claims were valid but supported no reduction. Zero proposed adjustments is the correct result, not a provider failure.
  Date/Author: 2026-07-26 / Codex.

- Decision: narrow the older GW13-GW14 terminal test to assert that GW14 itself emitted no successor.
  Rationale: its global “GW15 directory never exists” assertion became stale when this approved continuation created GW15; ownership of the earlier slice ends at GW14's artifacts.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The three-week continuation is complete and stops after GW17.

GW15 began from the legal successor of the actual GW14 fork with £0.8m and three free transfers. Positive Senesi and Semenyo evidence produced a reviewed abstention. The optimiser made no transfer, captained Haaland, and scored 53 versus canonical 55. Its same-state control was identical, so evidence effect was zero and prior trajectory state accounted for the two-point deficit. The transition then applied the official AFCON rule and produced exactly five GW16 free transfers.

GW16 applied the reviewed Muñoz expected-minutes correction from 70.7 to zero. It sold Muñoz for Marc Guéhi, captained Haaland, and scored 58 versus canonical 59. The same-state structured control instead sold Eze for Declan Rice and scored 59; accepted evidence therefore had a minus-one realised effect while prior state had zero effect.

GW17 applied the reviewed Mbeumo AFCON correction from 88.8 expected minutes to zero. It sold Mbeumo for Phil Foden and Gakpo for Morgan Rogers, captained Haaland, and scored 92 versus canonical 88. The same-state control sold Gakpo for Foden, retained Mbeumo, and scored 79. Evidence therefore contributed plus 13, while earlier state divergence contributed minus nine, yielding a net plus four versus canonical.

Across GW15-17 the agent fork scored 203 versus canonical 202. Same-state evidence effects sum to plus 12; inherited state effects sum to minus 11. Across the full experimental GW12-17 fork, the agent has 343 versus canonical 330, a cumulative plus 13.

All three canonical trees remained byte-identical. Repeating the complete three-week run reproduced all three comparison files byte-for-byte. Fourteen cross-slice focused contracts passed and the complete repository passed 461 tests in 215.40 seconds. No GW18 directory or successor state was created.

## Context and Orientation

Canonical replay artifacts live under `reports/benchmarks/2025-26/gw-NN`. They contain observed features and locked forecasts that every arm may use, plus hidden outcomes that may be opened only after a plan is frozen. Fork artifacts live under `reports/benchmarks/2025-26-agent-forks/gw-NN/sol-v1`.

The policy state is the manager's longitudinal memory: squad, purchase prices, bank, free transfers, and chip availability. `src/orchestration/policy_state.py` is the only legal state-transition implementation. `src/orchestration/agent_fork_adapter.py` combines a fork-owned state with the week's canonical observed inputs, applies only independently reviewed forecast reductions, freezes a legal plan, reveals and scores the outcome, and optionally advances state.

A same-state control solves the same week from the identical fork state without unstructured evidence. Comparing it with the agent plan isolates evidence effect; comparing the agent plan with canonical includes both evidence and earlier trajectory divergence.

## Plan of Work

Add a general successor helper to `src/orchestration/agent_fork_adapter.py` while retaining the GW12 wrapper unchanged for compatibility. Add `scripts/run_gw15_gw17_agent_forks.py`, whose state resolver derives GW15 from the completed GW14 fork, reads GW15's successor for GW16, and reads GW16's successor for GW17.

Freeze three evidence bundles below `evals/evidence-forks/2025-26`. GW15 contains only positive return/role evidence. GW16 contains the confirmed Muñoz surgery and an explicitly weaker Timber doubt if useful. GW17 contains confirmed Mbeumo AFCON absence. Each source records publication time precision and the much later recovery time.

For every gameweek, prepare the evidence request, capture the evidence response, build a hash-bound challenger request, capture its independent response, apply the governed adapter, freeze the plan, score the hidden outcome, and produce same-state attribution. Transition GW15 and GW16 only.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

    .\.venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_gw15_gw17.py tests/agent-evals/test_agent_fork_adapter.py -q
    .\.venv\Scripts\python.exe -m scripts.run_gw15_gw17_agent_forks --mode prepare --gameweek 15
    .\.venv\Scripts\python.exe -m scripts.run_gw15_gw17_agent_forks --mode complete
    .\.venv\Scripts\python.exe -m scripts.run_gw15_gw17_agent_forks --mode complete
    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

The first complete run should print three comparisons. The second must reproduce sealed files byte-for-byte.

## Validation and Acceptance

Every evidence publication timestamp must precede its exact decision cutoff. Agent requests must contain no hidden or realised outcome reference. GW15 must start from the legal GW14 fork successor. GW16 must start from GW15's successor with exactly five free transfers, and its transition audit must identify the rule-derived top-up. GW17 must start from GW16's successor and finish without a GW18 directory or next-state file.

Every evidence proposal must receive an independent challenger disposition. Adjustments may only reduce expected minutes or start probability from the exact locked baseline. Plans must validate and freeze before outcomes are read. Same-state controls must isolate evidence effects. Canonical GW15, GW16, and GW17 tree hashes must remain unchanged. Repeating the run must leave all sealed outputs byte-identical.

## Idempotence and Recovery

All artifact writers are write-once: an identical rerun is accepted, while different bytes fail rather than silently replacing evidence. A changed source, prompt, model response, or policy requires a new versioned experiment root. Provider or challenger failure produces a recorded unchanged-input fallback for that week and must not corrupt later state.

## Artifacts and Notes

The exact cutoffs are GW15 `2025-12-06T11:00:00Z`, GW16 `2025-12-13T13:30:00Z`, and GW17 `2025-12-20T11:00:00Z`.

The intended evidence cases are Senesi's return and Semenyo's unchanged role on 5 December; Muñoz's operation and absence through at least mid-January reported at 09:16:20 UTC on 12 December; and the 13 December report that AFCON players including Mbeumo are unavailable from GW17 onward.

## Interfaces and Dependencies

No new package or network client is required. `derive_next_state_from_agent_fork` accepts a gameweek, canonical root, episode root, fork root, and optional starting state, and returns the sealed successor state plus transition audit. The new CLI supports `prepare`, `validate-evidence`, `complete-week`, and `complete` for gameweeks 15, 16, and 17.

Revision note (2026-07-26): Initial self-contained plan written after state inspection and deadline-safe source selection.

Revision note (2026-07-26): Completed the three sequential forks, documented validator-caught response defects, decomposed evidence and state effects, and recorded final idempotence and regression proof.
