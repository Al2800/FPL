# Replace the synthetic pilot with checkpointed genuine replay

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, the repository can process the real 2025/26 benchmark episodes chronologically rather than relabelling one synthetic optimiser fixture. Every policy arm receives the same immutable observed episode, uses only its own longitudinal squad and finances, freezes one canonical validated plan, sees official outcomes only afterwards, and advances to the next Gameweek with deterministic artefacts.

The user has chosen an incremental operating mode. The runner will stop at an explicit Gameweek boundary. The first milestone runs and reports Gameweek 1 only; it may construct the opening Gameweek 2 feature market to calculate the post-GW1 successor states, but it will not produce a Gameweek 2 decision until Gameweek 1 has been reviewed.

## Progress

- [x] (2026-07-23 21:32Z) Confirmed `FPL-kcc` was closed, no other bead was in progress, claimed `FPL-bsw.13`, and recorded the stop-after-GW checkpoint policy in Beads.
- [x] (2026-07-23 21:35Z) Mapped historical episode bundles, feature-state construction, controlled seed, policy-state initialization/transition, canonical plans, outcome scoring, GDRs, and the synthetic pilot scripts.
- [x] (2026-07-23 21:35Z) Confirmed optimiser commit `0702ed1` passed GitHub CI before genuine replay implementation.
- [x] (2026-07-23 22:21Z) Added the explicit canonical identity bridge, identity-map provenance, and raw hidden-outcome hash preservation.
- [x] (2026-07-23 22:25Z) Added genuine GW1 contracts covering shared action, five isolated arms, deterministic rerun, CLI execution, and refusal to cross the unreviewed GW2 boundary.
- [x] (2026-07-23 22:25Z) Implemented the historical episode reader, feature-state advancement, controlled GW1 plan, scoring, transition, GDR, and fail-on-difference persistence.
- [x] (2026-07-23 22:26Z) Replaced the synthetic pilot loop and added season/start/stop/episode-root options to the module CLI.
- [x] (2026-07-23 22:27Z) Ran GW1 only: all arms scored 56, used no transfers/chip/substitutions, retained £0.0m, banked two free transfers, and advanced independently to opening GW2 states.
- [x] (2026-07-23 22:30Z) Passed 42 historical-replay tests and 303 complete repository tests; `git diff --check` also passed.
- [x] (2026-07-23 22:33Z) Committed/pushed the GW1 checkpoint and confirmed GitHub CI on Python 3.11–3.14.
- [x] (2026-07-23 22:39Z) Rendered a self-contained GW1 HTML review and verified it through a read-only server bound to the Tailscale interface.
- [x] (2026-07-23 22:46Z) Implemented the sealed GW2 preparation boundary: identical engine input/output, five isolated opening states, explicit policy briefs, no hidden-outcome read, and no frozen proposal/transition.
- [x] (2026-07-23 22:46Z) Stopped GW2 at review after diagnostics exposed severe single-Gameweek outcome chasing; created `FPL-5iu` for early-season prior/shrinkage calibration.
- [x] (2026-07-24 00:49Z) Resumed the bead after `FPL-5iu`, the structured-data gate, and `FPL-k21` closed; the reviewed GW2 setup now uses the locked live-faithful forecast and explicit transfer-option policy.
- [x] (2026-07-24 01:00Z) Freeze all five GW2 arm plans from the reviewed setup before opening the hidden partition, score the official outcome, and advance five independent states to GW3.
- [x] (2026-07-24 01:03Z) Prove GW2 rerun determinism and the fail-closed outcome-access boundary, then persist and review the real checkpoint.
- [x] (2026-07-24 01:25Z) Generalise the sealed preparation boundary for GW3+: one common cutoff-safe forecast plus state-bound optimiser inputs/outputs for every arm.
- [ ] Commit the reusable setup builder, generate the tracked sealed GW3 proposal from that commit, and pause for human review without opening GW3 outcomes.
- [ ] Continue Gameweeks 2–38 one at a time after explicit review checkpoints; close `FPL-bsw.13` only after the chronological replay and rerun acceptance criteria are complete.

## Surprises & Discoveries

- Observation: Gameweek 1 is not an optimiser cold-start decision.
  Evidence: `control/seeds/2025-26/official-scout-gw1.json` contains the official published 15-player squad plus an explicit XI, ordered bench, captain Palmer, vice-captain Salah, and no chip. Its `seed_policy` says policy divergence begins in GW2.

- Observation: official hidden outcomes identify players by numeric FPL `element`, while policy state and validated plans use canonical IDs such as `player:2025-26:381`.
  Evidence: the first GW1 hidden row uses `element: 1`; the episode identity map resolves it to `player:2025-26:1`. Without this bridge, the realised-outcome scorer would treat every controlled-seed player as absent and score zero.

- Observation: a complete post-GW1 state transition needs Gameweek 2 market quotes.
  Evidence: `transition_policy_state` refreshes every persistent squad player against `next_market`. Building the GW2 feature state uses GW2's observed partition, whose lagged rows are completed GW1 outcomes, but does not require or create a GW2 decision.

- Observation: the existing pilot is explicitly synthetic.
  Evidence: `scripts/run_replay_pilot_set.py` loops over labels while calling `replay_gameweek` on one configured solver fixture, causing several labelled Gameweeks to share the same underlying decision input.

- Observation: the episode builder and outcome scorer previously used different Unicode canonicalisation for source hashes.
  Evidence: the first genuine checkpoint compared the scorer hash `28d29c…` with the manifest hash `b82f4f…` for the same hidden payload. The scorer now uses the episode builder's UTF-8 canonical JSON contract, and the two hashes match.

- Observation: the governed XI scored 56 points, while first unused outfield substitute Rodon scored 7.
  Evidence: every starter played, so no automatic substitution was legal. Palmer scored 3 and therefore added 3 captain points; Reijnders led the XI with 10.

- Observation: the first GW2 rolling forecast is not decision-grade.
  Evidence: only completed GW1 is available, so `historical-rolling-v1` assigns Ballard 17 EP, Semenyo 15 and Wood 13 by carrying their single realised score forward. The optimiser searches 102,391 valid candidates, captains Ballard and recommends three transfers including a four-point hit, raising its objective from 68 to 110. This is mechanically consistent but statistically unstable.

- Observation: checkpoint provenance must be generated after the producing code is committed.
  Evidence: the first successful GW2 development run correctly scored and transitioned every arm but recorded parent commit `68ec402`, because the finaliser itself was still uncommitted. That run was preserved as ignored development evidence; the tracked checkpoint is generated only from the implementation commit.

- Observation: the historical episode does not contain deadline availability flags.
  Evidence: GW3 observed data contains fixtures, lagged player features and prior results but no status/news field. The structured forecast can infer reduced expected minutes from Palmer's GW2 zero minutes, but it cannot know the contemporaneous injury explanation. The sealed review therefore records that every market row remains available and that historical unstructured evidence was not reconstructed.

- Observation: banked-transfer value materially changes the GW3 action.
  Evidence: the development setup gives zero/one/two/three transfers immediate objectives 59.81/61.43/63.23/64.51. After valuing the retained transfer bank they become 65.21/65.03/65.03/64.51, so the reviewed policy narrowly banks and would carry four transfers to GW4.

## Decision Log

- Decision: GW1 uses the official Scout seed's `initial_plan` unchanged for all five policy arms.
  Rationale: the seed is the governed pre-deadline starting-team benchmark and explicitly postpones policy divergence until GW2. Re-optimising zero-valued cold-start projections would replace published evidence with arbitrary player-ID tie order.
  Date/Author: 2026-07-23 / Codex.

- Decision: finalising a Gameweek includes constructing the next observed feature market solely for successor-state price refresh, but the next Gameweek's proposal remains outside the checkpoint.
  Rationale: a scored Gameweek is incomplete without its arm-specific successor state. The next observed partition contains only information available after the completed Gameweek and before the next deadline.
  Date/Author: 2026-07-23 / Codex.

- Decision: raw hidden outcomes remain unchanged; identity resolution is supplied explicitly to the outcome scorer.
  Rationale: transformed outcome files would obscure source provenance. The realised outcome must hash the raw partition while recording the identity-map hash that governed player resolution.
  Date/Author: 2026-07-23 / Codex.

- Decision: replay artefacts are organized by season, Gameweek, and policy arm, with shared episode/feature references in a Gameweek summary.
  Rationale: this exposes parity across arms, prevents state borrowing, and makes one-Gameweek review possible without scanning a monolithic season result.
  Date/Author: 2026-07-23 / Codex.

- Decision: GW2 consumes the committed, hash-bound option-value setup as a reviewed pre-deadline model cache.
  Rationale: forecast calibration and data completeness have already been locked without 2025/26 outcomes. Recomputing them inside the outcome runner would blur the freeze/reveal boundary and make the replay depend on ignored raw training directories.
  Date/Author: 2026-07-24 / Codex.

- Decision: evidence-agent and human arms use an explicit structured fallback in GW2 when no admissible cached historical proposal exists.
  Rationale: inventing retrospective news or a human choice would introduce leakage. Each arm still freezes a plan bound to its own state and records the degraded fallback; agent capability is evaluated later with timestamped evidence.
  Date/Author: 2026-07-24 / Codex.

- Decision: Gameweek setup persists a shared forecast but arm-specific solver inputs, outputs and reviews.
  Rationale: model evidence is common by experimental design, while squad, purchase history, bank, free transfers and chips belong to each arm. GW3 inputs happen to be identical, but the artifact layout must permit divergence without changing the contract.
  Date/Author: 2026-07-24 / Codex.

## Outcomes & Retrospective

The first genuine checkpoint is complete locally. It contains one shared official-Scout action bound independently to five arm states, five frozen plans and realised outcomes, and five successor states at the opening of GW2. Every arm scored 56 net points and banked a second free transfer. No GW2 proposal, outcome, or policy choice exists.

The checkpoint exposed and fixed one provenance mismatch between episode and scorer canonicalisation. It also demonstrates why the replay must preserve actual decisions: Rodon's 7 bench points remain unused because all XI players appeared. The result is reproducible across two output roots and the full repository suite passes. Policy divergence and solver inputs intentionally begin at the reviewed GW2 checkpoint.

GW2 is complete and the replay is stopped before GW3. The tracked checkpoint
was generated from implementation commit `eb65cef`. Every arm used the same
reviewed structured action—zero transfers, Salah captain and Palmer
vice-captain—but each plan, outcome, transition and successor is bound to its
own arm state. Palmer did not play, so first forward substitute Marc Guiu
entered. The squad scored 59 gross/net points, reached 115 cumulative points,
retained £0.0m and advanced with three free transfers.

There is intentionally no policy-performance divergence yet. The evidence,
challenger and human arms explicitly fell back to the structured plan because
no admissible historical unstructured proposal or recorded human decision was
available. Treating that parity as an agent result would be incorrect; it is a
chronology/state/reproducibility result. GW3 has not been prepared or decided.

## Context and Orientation

Each local episode directory under `data/benchmark-v0/episodes/v2/2025-26/gw-NN/` contains `episode-manifest.json`, `observed.json`, `identity-map.json`, `hidden-outcome.json`, `ruleset.yaml`, and supporting uncertainty/placeholder files. Raw data is ignored by Git. The manifest hashes its observed and hidden partitions and says hidden outcomes may be revealed only after proposal freeze.

`src/orchestration/historical_feature_state.py::build_feature_state` validates the manifest, observed partition, identity map, and previous feature hash. For GW1 it combines the observed fixture schedule with `control/seeds/2025-26/official-scout-gw1.json`. For later weeks it aggregates the exact prior Gameweek rows before rolling projections.

`src/orchestration/policy_state.py::initialise_policy_states` clones the controlled 15-player seed into five independent arms. `src/orchestration/validated_plan.py` binds a proposed action to one arm's predecessor state and rules. `src/evaluation/outcome_scorer.py` aggregates official fixture rows and scores substitutions, captaincy, and chips. `transition_policy_state` then applies transfers, hit costs, bank/free-transfer/chip changes, points, and next-market prices.

`src/orchestration/replay_harness.py` currently contains a synthetic single-fixture WP-09 harness. Genuine replay will be added alongside or beneath its public surface without losing the existing small compatibility tests. `scripts/run_replay_pilot_set.py` and `scripts/run_replay.py` will route genuine historical requests to the new path.

## Plan of Work

First extend `score_revealed_outcome` with an explicit element-to-canonical-player mapping and identity-map hash. Validate that every official outcome row relevant to the plan resolves uniquely, preserve the raw hidden partition hash, and include the identity hash in the realised outcome schema. Add regression tests proving canonical plans receive the correct official points and unresolved plan players fail closed rather than silently scoring zero.

Add `tests/historical-replay/test_genuine_replay.py`. Use the local real GW1/GW2 episode bundles where present, with a small committed fixture fallback only for clean-clone unit contracts. Assert that GW1 consumes the official initial plan, all arms share observed and feature hashes, all plans freeze before the derived reveal time, each realised outcome belongs to its plan, each transition belongs to one arm, and successor hashes are distinct by arm. Assert that stop-after-GW1 creates no GW2 decision artefact. Run twice into separate temporary directories and compare deterministic content after excluding measured wall time.

Implement an episode loader and `run_historical_replay` in `src/orchestration/replay_harness.py` or a narrowly named adjacent module. It will verify raw partition hashes, build one feature state per Gameweek, initialize or load arm states, select the governed arm action, validate/freeze, reveal/score, transition, construct a GDR, and write canonical JSON. It will accept `start_gameweek`, `stop_after_gameweek`, input episode root, output root, and code commit. Resume mode will require exact predecessor hashes rather than guessing state.

For GW1, build the candidate from `seed["initial_plan"]`, calculate formation from the selected XI, and use no transfers. For GW2 onward, the structured deterministic arms will use `build_replay_solver_input` plus the explicit 2025/26 rules. Evidence-dependent arms must record their historical evidence limitation and use a declared deterministic fallback until a cached admissible agent proposal exists. That later policy behavior will be reviewed before GW2 runs.

Persist a hash-bound shared context and Gameweek summary. Under each arm persist `policy-state-before.json`, `validated-plan.json`, `decision-record.json`, `realised-outcome.json`, `state-transition.json`, and `next-policy-state.json`. Solver inputs/outputs begin in GW2 because GW1 uses the governed seed plan. No elapsed time is included in the deterministic checkpoint artefacts; runtime profiling remains in the separate performance reports.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Add red contracts and run:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_genuine_replay.py tests/historical-replay/test_realised_outcome_scorer.py -q

After implementation, run the real first checkpoint:

    .\.venv\Scripts\python.exe -m scripts.run_replay --season 2025-26 --start-gameweek 1 --stop-after-gameweek 1 --out reports/benchmarks/2025-26

Expect one `gw-01` directory, five arm directories, five plans/outcomes/transitions, five opening-GW2 states, and no `gw-02/decision-record.json`.

Run focused tests:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_genuine_replay.py tests/historical-replay/test_replay_feature_adapter.py tests/unit/test_policy_state.py tests/test_decision_record_replay.py -q

At the GW1 checkpoint run:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

GW1 must use the exact XI, ordered bench, captain, vice-captain, and chip from the official seed. Every arm's validated plan must bind its own predecessor hash even though the action is shared. Every arm must receive the same episode, observed partition, feature state, rules, and raw outcome.

The outcome cannot be scored with a reveal timestamp at or before freeze. Numeric FPL elements must resolve to canonical IDs through the episode identity map. Plan players with official rows must not disappear silently. Gross points are calculated before transfer hits; the transition subtracts hits and records net/cumulative points.

Each opening-GW2 state must retain only its arm's prior hash and transition. Rerunning GW1 with the same commit and inputs must reproduce all action, outcome, transition, state, and summary hashes. The filesystem must contain no GW2 proposal or outcome artefact.

The Gameweek summary must clearly report data limitations, arm strategy/fallback, transfers, chip, captain, substitutions, gross/net/cumulative points, bank, free transfers, and plan/outcome/transition/next-state hashes.

## Idempotence and Recovery

The runner writes each Gameweek through a temporary staging directory and only publishes a completed summary after all arms succeed. Re-running an existing Gameweek verifies or replaces only the designated output directory; it never mutates raw episode data. Because the global safety policy forbids deletion without explicit approval, implementation must avoid deletion-based replacement and instead write files atomically or fail if incompatible artefacts already exist.

No network or dependency installation is needed. If GW1 fails, no later Gameweek is attempted. Resume requires the previous completed summary and all arm successor hashes.

## Artifacts and Notes

The controlled GW1 plan is:

    XI: Sanchez; Murillo, Pedro Porro, Tarkowski;
        Salah, Palmer, B.Fernandes, Anderson, Reijnders;
        Watkins, Joao Pedro
    Bench: Dubravka, Marc Guiu, Rodon, Senesi
    Captain: Palmer
    Vice-captain: Salah
    Chip: none

The episode cutoff/deadline is `2025-08-15T17:30:00Z`. The raw GW1 hidden outcome contains 690 player-fixture rows and is sealed by manifest hash `b82f4f2288426d905da7c28fc9148374eca9c02e9d18cb30b181a7747cfff549`.

## Interfaces and Dependencies

No new package is required.

Extend `src/evaluation/outcome_scorer.py`:

    def score_revealed_outcome(
        plan: Mapping[str, Any],
        hidden_outcome: Mapping[str, Any],
        *,
        revealed_at: str,
        rules: Mapping[str, Any],
        ruleset_sha256: str,
        player_identity_map: Mapping[int | str, str] | None = None,
        identity_map_sha256: str | None = None,
    ) -> dict[str, Any]

Add a genuine replay entry point:

    def run_historical_replay(
        *,
        season: str,
        episode_root: Path,
        output_root: Path,
        start_gameweek: int = 1,
        stop_after_gameweek: int,
        code_commit: str,
    ) -> dict[str, Any]

The return value is a deterministic run summary plus non-hash timing metadata. The runner does not invoke network or agent services.

Revision note (2026-07-23): Initial ExecPlan created after claiming the replay bead and mapping the real GW1 seam. It records one-Gameweek checkpoints, controlled shared GW1 action, canonical identity resolution, and the distinction between opening the next state and making the next decision.

Revision note (2026-07-23): Updated after the first genuine checkpoint. Records the 56-point result, the Unicode source-hash defect found by the contract test, the exact persisted artefacts, and the explicit separation of deterministic replay output from performance timing.

Revision note (2026-07-23): Added the GW1 HTML review and GW2 sealed-setup boundary. Records the early-season forecast instability found before freeze, the resulting `FPL-5iu` calibration bead, and the decision not to reveal or score GW2 until the forecast treatment is reviewed.

Revision note (2026-07-24): Resumed after forecast/data/transfer-option review. The GW2 finaliser will consume the committed reviewed setup, freeze every arm before hidden-outcome access, and advance one reviewed Gameweek only.
