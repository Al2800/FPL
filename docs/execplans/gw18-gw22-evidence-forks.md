# Run sequential evidence forks for Gameweeks 18 to 22

This ExecPlan is a living document. `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current. It follows `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

Continue the inspected 2025-26 agent trajectory for five more historical decisions, from GW18 through GW22. Each decision uses the actual preceding fork state, only evidence published before its deadline, an independent GPT-5.6 Sol proposal and challenger, and a deterministic application boundary. The run shows whether unstructured evidence changes transfers and realised points without contaminating the canonical replay.

The experiment stops after GW22. It must not create a GW23 state or directory.

## Progress

- [x] (2026-07-26 15:39+01:00) Create and claim Bead `FPL-755`; confirm no file conflict.
- [x] (2026-07-26 15:41+01:00) Confirm deadlines, canonical scores, and the legal GW18 successor.
- [x] (2026-07-26 15:47+01:00) Select deadline-safe evidence cases for all five weeks.
- [x] (2026-07-26 15:49+01:00) Add evidence bundles, orchestration, and contracts.
- [x] (2026-07-26 16:03+01:00) Run five evidence/challenger pairs and score each week sequentially.
- [x] (2026-07-26 16:07+01:00) Prove attribution, immutability, idempotence, and terminal behavior.
- [x] (2026-07-26 16:14+01:00) Pass 465 repository tests.
- [x] (2026-07-26 16:15+01:00) Close Bead `FPL-755` and prepare the verified change set for commit and push to `main`.

## Surprises & Discoveries

- Observation: GW18 begins with £1.4m, four free transfers, and the actual GW17 fork squad.
  Evidence: the legal transition retains Foden and Rogers while Mbeumo and Gakpo remain sold.

- Observation: the festive deadlines have materially incomplete team news.
  Evidence: GW19 sources explicitly say five clubs would probably not speak before the deadline; GW21 Liverpool and Arsenal press conferences were scheduled after the deadline.

- Observation: accepted evidence changed the transfer identity in GW18 but not realised points; every same-state evidence delta in GW18-GW22 was zero.
  Evidence: the GW18 evidence arm sold suspended Szoboszlai for Rice while the control sold Eze for Rice; both scored 31. In GW19-GW22 the plans and scores matched their same-state controls.

- Observation: the deterministic solver returned `degraded_fallback` in GW20-GW22.
  Evidence: GW20 retained the squad, while GW21 and GW22 still produced legal one-transfer plans. The fallback status is preserved in every comparison artifact for later solver diagnosis.

## Decision Log

- Decision: use only information whose entire publication date precedes the cutoff when an exact time is unavailable.
  Rationale: this preserves temporal certainty without pretending day-level timestamps are more precise.
  Date/Author: 2026-07-26 / Codex.

- Decision: retain a mix of strong absence and abstention cases rather than force one adjustment every week.
  Rationale: live orchestration must know when evidence is insufficient or positive as well as when it should override stale minutes.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The five-week agent trajectory completed legally and stopped at GW22. It scored 214 points against the canonical arm's 236, a 22-point deficit for this slice. Combined with the already-frozen GW1-GW17 experimental trajectory, the running totals are 557 agent points versus 566 canonical points, a nine-point deficit.

GW18 scored 31 versus 33 and transferred Szoboszlai to Rice. GW19 scored 33 versus 36 and transferred Eze to Cunha. GW20 scored 49 versus 65 with no transfer. GW21 scored 57 versus 55 and transferred Woltemade to Igor Thiago. GW22 scored 44 versus 47 and transferred Cunha to Bruno Guimarães. Haaland was captain throughout and no hit was taken.

The evidence layer behaved conservatively: it accepted explicit exclusions for Szoboszlai, Rodon, Gvardiol, and Guéhi; abstained on uncertain Timber reporting; and avoided adding an unsupported Semenyo uplift. The isolated realised evidence effect was zero in all five weeks. This does not mean the layer was inert: GW18 evidence changed which player was sold, hence the successor squad, without changing that week's score.

All five canonical trees were unchanged, the state hashes form a continuous GW17-GW22 chain, an exact rerun preserved every comparison-file SHA-256, and no GW23 directory or successor was created. Focused tests passed 9/9 and the complete suite passed 465/465 in 227.65 seconds.

The principal follow-up is the recurring `degraded_fallback` status in GW20-GW22. It did not break legality or reproducibility, but it should be diagnosed before treating those plans as evidence of the solver's fully searched optimum.

## Context and Orientation

Canonical observed inputs live under `reports/benchmarks/2025-26/gw-NN`; hidden outcomes in the episode tree may be read only after a legal plan is frozen. Fork results live under `reports/benchmarks/2025-26-agent-forks/gw-NN/sol-v1`. `src/orchestration/agent_fork_adapter.py` combines weekly observed inputs with fork-owned policy state and exposes the general legal successor helper.

A same-state control runs the unchanged structured engine from the identical squad and finances. Agent minus control is the isolated evidence effect. Control minus canonical is the inherited state effect.

## Plan of Work

Add five source bundles below `evals/evidence-forks/2025-26`. Add `scripts/run_gw18_gw22_agent_forks.py`, structurally matching the prior runner but deriving GW18 from the terminal GW17 artifacts and chaining saved successors through GW22. Transition only GW18-GW21.

GW18 tests Szoboszlai's confirmed suspension. GW19 tests uncertain Timber availability after a missed match. GW20 tests Rodon's continuing absence. GW21 tests Gvardiol's long-term fracture alongside positive Semenyo availability. GW22 tests Guéhi's explicit exclusion during his transfer.

## Concrete Steps

From `C:/Users/Alastair/FPL` run:

    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --mode prepare --gameweek 18
    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --mode complete-week --gameweek 18
    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --mode complete
    .\.venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_gw18_gw22.py -q
    .\.venv\Scripts\python.exe -m pytest -q

## Validation and Acceptance

GW18 must equal the legal GW17 successor. Every following starting-state hash must equal the preceding next-state hash. All evidence publications precede the exact cutoff. All proposals are independently reviewed. Plans freeze before outcome reveal. Canonical trees remain unchanged. Same-state controls exist for all five weeks. A repeat run is byte-identical. GW22 has no next-state hash and no GW23 output exists.

## Idempotence and Recovery

Artifacts are write-once. Identical reruns succeed; changed bytes require a new versioned root. A provider, validator, or challenger failure records a deterministic unchanged-input fallback without breaking the state chain.

## Artifacts and Notes

Deadlines are GW18 `2025-12-26T18:30:00Z`, GW19 `2025-12-30T18:00:00Z`, GW20 `2026-01-03T11:00:00Z`, GW21 `2026-01-06T18:30:00Z`, and GW22 `2026-01-17T11:00:00Z`.

## Interfaces and Dependencies

No package is added. The new CLI supports `prepare`, `validate-evidence`, `complete-week`, and `complete` for gameweeks 18 through 22.

Revision note (2026-07-26): Initial plan written after state derivation and pre-deadline source selection. Updated after the complete deterministic run and regression suite.
