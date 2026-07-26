# Run the audited GW23-GW29 evidence trajectory

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:\Users\Alastair\.codex\.agent\PLANS.md`.

## Purpose / Big Picture

This work continues the repaired historical evidence-agent trajectory from the exact state produced by GW22 `sol-v3`. After it is complete, a reviewer can inspect seven consecutive, legally chained gameweeks in which a deterministic FPL engine and two GPT-5.6 Sol roles considered only information published before each deadline. Every proposed minutes adjustment, challenger judgement, selected plan, realised score, and state transition will be preserved. The run deliberately stops after GW29 so the user can review the seven-week behaviour before authorising the final GW30-GW38 block.

## Progress

- [x] (2026-07-26 18:06Z) Create and claim Bead `FPL-2h9`; confirm no conflicting in-progress work.
- [x] (2026-07-26 18:20Z) Verify the GW23-GW29 deadlines, canonical scores, exact GW23 starting squad, and pre-deadline source windows.
- [x] (2026-07-26 18:38Z) Select one decision-relevant evidence case per week, covering positive, negative, and uncertain availability signals.
- [x] (2026-07-26 18:10Z) Add the seven immutable evidence bundles and the sequential runner.
- [x] (2026-07-26 18:43Z) Add focused contracts for provenance, completed gates, state chaining, attribution, failure preservation, score totals, and the GW29 stop boundary.
- [x] (2026-07-26 18:42Z) Run fresh evidence and challenger roles for GW23-GW29, preserving five rejected versions and advancing only completed gates.
- [x] (2026-07-26 18:50Z) Run focused and full tests, complete byte-identical reruns, and finalise the seven-week review.
- [x] (2026-07-26 18:55Z) Close Bead `FPL-2h9` with implementation and verification evidence.
- [ ] Commit and push the completed block.

## Surprises & Discoveries

- Observation: The exact successor of GW22 `sol-v3` owns both Bruno Guimarães and Jurriën Timber, so the GW23 and GW24 press-conference reports are directly relevant rather than hypothetical market examples.
  Evidence: `derive_next_state_from_agent_fork(gameweek=22, fork_root=.../gw-22/sol-v3)` produces GW23 with 0.6 bank, four free transfers, and player IDs 488 and 8 in the squad.

- Observation: GW26 is a double gameweek for Arsenal and Wolves, but the availability evidence remains an adjustment to player minutes rather than a special scoring override.
  Evidence: the episode fixture data already represents both fixtures; Jean-Philippe Mateta's confirmed absence supplies a clean negative-evidence case without altering fixture or scoring rules.

- Observation: The first frozen GW23 request recorded a recovery timestamp 24 minutes ahead of the actual UTC clock.
  Evidence: the `sol-v1` request used `2026-07-26T18:35:00Z` while the system clock was `2026-07-26T18:11:19Z`; it was rejected before any response or solver adjustment was persisted.

- Observation: The first GW25 challenger returned the unrecognised outcome `no_escalation`.
  Evidence: the canonical enum permits `dismissed`, `confidence_downgrade`, `forced_re_run`, or `escalation`; local validation records the `sol-v1` gate as failed and no solver artifacts are created from it.

- Observation: The second GW25 evidence role set claim expiry exactly equal to the decision cutoff.
  Evidence: eligibility requires `expires_at` to be strictly later than the cutoff, so `sol-v2` degrades with `expired` and never reaches a challenger or solver.

- Observation: GW26 needed two rejected versions before a compliant challenger could be attempted.
  Evidence: `sol-v1` exceeded the 0.25 start-probability delta cap; `sol-v2` evidence passed with only expected minutes adjusted, but its challenger omitted every required schema field except notes and an unrecognised `outcome` key.

- Observation: The machine-wide Python 3.14 environment lacked a Parquet engine, while the repository's existing Python 3.13 virtual environment contained `pyarrow 25.0.0`.
  Evidence: machine-wide pytest produced two unrelated Parquet import failures; `.venv\Scripts\python.exe -m pytest -q` completed with `477 passed in 210.62s`.

## Decision Log

- Decision: Start GW23 by legally deriving the successor from terminal GW22 `sol-v3`, even though GW22 intentionally contains no persisted `next-policy-state.json`.
  Rationale: `derive_next_state_from_agent_fork` reconstructs the successor from the sealed plan and realised outcome, preserving the repaired trajectory without reading canonical manager state.
  Date/Author: 2026-07-26 / Codex

- Decision: Use a single strong, player-specific pre-deadline case per gameweek rather than padding bundles with weakly relevant reports.
  Rationale: This isolates the agent's weighting behaviour and reduces the risk that irrelevant prose creates accidental adjustments. Across seven weeks the selected cases still cover positive, negative, and unresolved signals.
  Date/Author: 2026-07-26 / Codex

- Decision: Treat all recovered historical evidence as exploratory and ineligible for headline model-performance claims.
  Rationale: The sources were recovered after outcomes were known and the cases were not preregistered, even though each publication date strictly precedes its decision deadline.
  Date/Author: 2026-07-26 / Codex

- Decision: Persist a next state through GW29's score but do not create any GW30 artifact.
  Rationale: GW29 must be fully scored and reviewable while the user explicitly asked to pause before the final season block.
  Date/Author: 2026-07-26 / Codex

- Decision: Preserve the invalid GW23 `sol-v1` host bundle and restart that week at `sol-v2` after correcting all recovery timestamps to `2026-07-26T18:05:00Z`.
  Rationale: Recovery time does not affect historical eligibility, but accepting knowingly false provenance would weaken the audit. Versioning preserves the diagnostic without destructive cleanup.
  Date/Author: 2026-07-26 / Codex

- Decision: Retarget GW25 from Bruno Guimarães to Jurriën Timber before freezing the request.
  Rationale: GW24's deterministic plan sold Bruno, while Timber remained owned. The same pre-deadline article contains Arteta's explicit "Jurrien is fine" update, making the case directly relevant to the carried state.
  Date/Author: 2026-07-26 / Codex

## Outcomes & Retrospective

The complete seven-week chain scores 410 versus canonical 390. Every accepted gate completed, two strong absence adjustments were applied, and paired same-state attribution remained zero in all seven weeks because neither adjusted player affected the selected plan. Five invalid versions were preserved without reaching a solver. The accepted chain is byte-stable on rerun, canonical trees are unchanged, the project-environment suite passes all 477 tests, and the final-season block remains untouched.

## Context and Orientation

The canonical historical replay lives under `reports/benchmarks/2025-26/gw-XX`. It contains frozen feature data, forecasts, plans, and realised outcomes for each gameweek. Canonical files are immutable controls.

The experimental trajectory lives under `reports/benchmarks/2025-26-agent-forks/gw-XX/sol-vN`. A version directory is append-only. If a hosted response fails schema validation or a gate does not complete, that version remains as diagnostic evidence and a new version is created.

An evidence bundle under `evals/evidence-forks/2025-26/gw-XX/evidence-bundle.json` records the historical source URL, publication day, exact short excerpt, claim, affected player ID, and known retrospective limitations. A host bundle combines that evidence with the frozen episode and deterministic candidate. The evidence role may propose bounded changes to expected minutes or start probability. The independent challenger reviews those proposals. Only validated and accepted changes reach the solver.

A policy state is the manager information carried between weeks: the 15-player squad, bank, free transfers, purchase and sale values, and chip state. A same-state control runs the unchanged deterministic engine from exactly the experimental state's weekly starting point. It separates the current week's evidence effect from differences accumulated in earlier weeks.

The main implementation references are `src/orchestration/agent_fork_adapter.py`, `src/orchestration/agent_arm.py`, and `scripts/run_gw18_gw22_agent_forks.py`.

## Plan of Work

Create seven evidence bundles, each with a publication day strictly before its episode deadline. Add `scripts/run_gw23_gw29_agent_forks.py` by adapting the existing sequential runner. Its `_state(23)` path must derive from GW22 `sol-v3`; later weeks must read only the prior experimental successor. Its prepare mode freezes the exact host request, validate-evidence mode validates the evidence response and emits the challenger request, and complete-week mode validates the challenger, applies accepted adjustments, solves, scores, attributes, and transitions. GW29 must be invoked with `transition_to_next=False`.

Add `tests/agent-evals/test_agent_fork_gw23_gw29.py`. The tests must prove the GW23 start equals the legally reconstructed state, every source predates its cutoff, both hosted gates completed, proposed and applied adjustments agree, state hashes chain through GW29, same-state attribution exists, no GW30 artifact exists, canonical trees did not change, and rerunning a completed version is byte-identical.

For every gameweek, run a fresh GPT-5.6 Sol evidence role against only the frozen host bundle. Store the exact hosted response and validate it locally. Then run a separate fresh GPT-5.6 Sol challenger against the resulting challenger request. Never repair a failed response in place. Complete and inspect the week before preparing the next one because each decision changes the next manager state.

## Concrete Steps

Run all commands from `C:\Users\Alastair\FPL`.

Prepare a weekly request:

    python scripts/run_gw23_gw29_agent_forks.py --mode prepare --gameweek 23

After storing the evidence response, validate it and emit the challenger request:

    python scripts/run_gw23_gw29_agent_forks.py --mode validate-evidence --gameweek 23

After storing the challenger response, complete and score the week:

    python scripts/run_gw23_gw29_agent_forks.py --mode complete-week --gameweek 23

Repeat sequentially through GW29. Then run:

    python -m pytest tests/agent-evals/test_agent_fork_gw23_gw29.py -q
    python -m pytest -q

Expected focused output is all tests passing. Expected artifacts include a `comparison.json` and `same-state-attribution.json` for each of GW23-GW29, a chained `next-policy-state.json` through GW28, and no directory for GW30.

## Validation and Acceptance

The run is accepted when a reviewer can begin with GW22 `sol-v3`, independently derive the same GW23 state, follow state hashes across all seven comparisons, and verify that every applied adjustment originated in a completed evidence response reviewed by a completed challenger. Each evidence publication day must sort before its gameweek deadline. Each comparison must include the experimental and canonical score, while each same-state attribution must expose the current-week incremental effect.

Running the focused test twice must pass twice without changing any artifact bytes. The full repository suite must pass. `git diff` must show no modification beneath `reports/benchmarks/2025-26`, and no path beneath `reports/benchmarks/2025-26-agent-forks/gw-30` may be created by this bead.

## Idempotence and Recovery

The runner uses write-once artifact creation. Repeating a successful command either reproduces the same value or refuses incompatible mutation. Hosted failures are preserved under their original `sol-vN` directory; recovery advances to `sol-vN+1`. No cleanup command is required or permitted. Canonical artifacts are hashed before and after each experimental week.

## Artifacts and Notes

The verified canonical gross scores for this block are GW23 41, GW24 60, GW25 58, GW26 68, GW27 43, GW28 67, and GW29 53. These are comparison references, not inputs to the agent roles.

The GW23 reconstructed start has bank 0.6 and four free transfers. The evidence cases are Bruno Guimarães uncertainty in GW23, Timber fitness in GW24 and GW25, Mateta's confirmed absence in GW26, Haaland's fitness in GW27, Wirtz's expected absence in GW28, and Haaland's unresolved assessment in GW29.

## Interfaces and Dependencies

Use only existing repository dependencies. `build_fork_solver_input(gameweek, state, canonical_root)` combines frozen weekly features with fork-owned manager state. `build_agent_host_bundle(...)` constructs the bounded request. `run_agent_arm(...)` validates a hosted response. `run_sequential_agent_fork_week(...)` applies governed adjustments, solves, scores, and optionally transitions. `build_same_state_control_attribution(...)` creates the weekly causal comparison. `artifact_hash(...)` is the only valid content-hash implementation for hosted JSON.

Revision note (2026-07-26): Initial plan created after verifying the terminal GW22 state, deadlines, canonical scores, and seven pre-deadline evidence cases. Updated after rejecting the first GW23 request for a future recovery timestamp and restarting it as `sol-v2`, then retargeting unfrozen GW25 evidence after Bruno left the experimental squad.
