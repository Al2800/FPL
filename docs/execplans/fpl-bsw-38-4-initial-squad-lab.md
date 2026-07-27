# Prospective 2026/27 Initial-Squad Selection Lab

This ExecPlan is a living document. The sections `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be updated as
implementation proceeds.

The repository does not contain `.agent/PLANS.md`; this plan follows the
structure of the existing plans in `docs/execplans/`.

## Purpose

Build a dedicated, prospective season-start path that selects a legal FPL
15-player squad from one immutable, deadline-bounded forecast packet. The lab
must compare deterministic and robust optimisation with externally supplied
evidence-agent, challenger and human/reference proposals without giving any
arm different structured inputs. It remains advisory-only, never writes to an
FPL account, and cannot become approval-ready until a human signs the selected
proposal and the active ruleset passes its launch gate.

## Progress

- [x] (2026-07-27 15:40Z) Rechecked Beads, confirmed `FPL-bsw.38.4` was already
  in progress, and found no overlapping active file scope or uncommitted work.
- [x] (2026-07-27 15:47Z) Read `docs/plan.md` and mapped the rules validator,
  lineup selector, robust objective, multiweek planner, hosted-response
  envelope, live-shadow completion gate and existing policy conventions.
- [x] (2026-07-27 16:00Z) Fixed the design boundary and recorded it in Beads.
- [ ] Implement the deterministic bounded initial-15 search and objective
  decomposition.
- [ ] Implement shared-packet orchestration, external-arm validation,
  sensitivity reporting and the human-approval gate.
- [ ] Add the preregistered policy, CLI, documentation and focused tests.
- [ ] Run focused and complete tests, update this plan, close the Bead and
  commit the completed slice.

## Surprises & Discoveries

- Observation: None of the seven target implementation files existed when the
  Bead was resumed.
  Evidence: the target-file existence audit returned `False` for every path.

- Observation: The transfer optimiser cannot construct an initial squad.
  Evidence: `SolverInput` requires an existing `squad_player_ids` collection
  and the transfer search only performs same-position replacements.

- Observation: Rules activation and owner sign-off are intentionally separate
  from squad generation.
  Evidence: `control/rules/2026-27.yaml` still contains inherited and
  provisional launch-verification rules, while `FPL-bsw.38.11` owns their
  verification and activation.

- Observation: Agent Mail timed out during both session registration and file
  reservation.
  Evidence: both calls reached the server's 300-second timeout without
  returning registration or reservation state. Beads and Git were therefore
  used as the safe coordination sources.

## Decision Log

- Decision: Use a deterministic bounded beam search rather than an undeclared
  external integer-programming dependency.
  Rationale: the repository has no optimisation-solver dependency, downloads
  require approval, and deterministic node budgets provide reproducible
  latency. Search limitations will be explicit.
  Date/Author: 2026-07-27 / Codex

- Decision: Derive squad size, budget, position counts, club cap and legal
  formations exclusively from the supplied versioned rules mapping.
  Rationale: project policy makes rules data and forbids hard-coded FPL
  constraints in optimiser code.
  Date/Author: 2026-07-27 / Codex

- Decision: Treat evidence-agent, challenger and human/reference outputs as
  host-supplied proposals or bounded player adjustments, then validate and
  score them with the same deterministic engine.
  Rationale: this preserves agent capability as an experimental variable while
  keeping legality, scoring, approval and execution outside the model.
  Date/Author: 2026-07-27 / Codex

- Decision: Refuse approval when the rules activation gate is not complete,
  any required arm fails validation, the selected proposal is not bound to the
  frozen packet, or owner approval is absent.
  Rationale: a useful shadow recommendation is not equivalent to an
  approval-ready live selection.
  Date/Author: 2026-07-27 / Codex

## Context and Orientation

`src/scoring/validator.py` is the authoritative legal squad and lineup
validator. `src/optimisation/simple_plan.py` selects a deterministic legal XI,
captain, vice-captain and ordered bench from a completed squad.
`src/optimisation/multiweek.py` demonstrates same-cutoff horizon validation and
bounded deterministic search. `src/orchestration/live_shadow.py` establishes
the no-execution and completion-gate conventions.

New `src/optimisation/initial_squad.py` will validate the frozen player packet,
construct legal squads and score each completed squad across the declared
horizon. New `src/orchestration/live_seed_selection.py` will run every arm
against one packet hash, validate external proposals, report alternatives and
sensitivity, and apply the human approval gate.

## Plan of Work

First define and validate the frozen packet contract. Every player must have a
unique identity, a legal position, a non-negative launch price, complete
per-Gameweek expected-points/start-probability/uncertainty vectors, and an
`available_at` no later than the decision cutoff. The packet must bind the
ruleset, forecast model, feature state and horizon.

Next implement bounded search. Build a deterministic shortlist per position
from high-value and cheap candidates. Fill the rules-derived position slots
without player permutations, reject club-cap and budget violations early,
retain a fixed-width beam, and exactly rescore completed squads. Exact scoring
will choose a legal XI for every horizon week and decompose starting points,
captaincy, bench/autosub value, uncertainty penalty, promoted/new-player
shrinkage, World Cup fatigue, transfer optionality and early-Wildcard risk.

Then build orchestration. Deterministic and robust arms run the optimiser with
declared policies. Evidence and challenger arms may apply bounded, cited
adjustments before running the same optimiser or submit a proposed 15.
Human/reference arms submit a declared 15. All external proposals are
rules-validated and scored against the unchanged base packet as well as their
declared adjusted view. Missing or invalid external arms remain visible and
cannot silently become the selected live proposal.

Finally add the preregistered JSON policy, an advisory CLI, documentation and
tests. The CLI reads local JSON only, writes no account state and refuses to
overwrite a conflicting artifact.

## Validation and Acceptance

Tests must prove:

- identical packets, policies and rules return identical squads and hashes;
- budget, squad size, position counts, club cap and formation come from rules;
- post-cutoff or incomplete player records fail before search;
- uncertainty, bench/autosub, context, fatigue and optionality affect the
  declared objective and appear in its decomposition;
- every arm records the same base packet hash;
- invalid or incomplete external proposals fail visibly;
- alternatives and one-factor sensitivity results are emitted;
- owner approval alone cannot bypass an incomplete rules activation gate;
- approval-ready output remains advisory-only with no account-write surface;
- changing a packet or policy changes the content hash;
- focused and complete test suites pass.

Focused command:

    .\.venv\Scripts\python.exe -m pytest tests/optimisation/test_initial_squad.py tests/integration/test_live_seed_selection.py -q

Full command:

    .\.venv\Scripts\python.exe -m pytest -q

## Idempotence and Recovery

The optimiser and orchestrator are pure functions. The CLI may write only a
new local advisory artifact. An identical rerun is allowed; a byte-different
rerun at the same path fails closed. No FPL credentials, browser state,
authenticated endpoints or account mutations are present.

## Outcomes & Retrospective

Pending implementation and validation.
