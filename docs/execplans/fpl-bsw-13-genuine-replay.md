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
- [x] (2026-07-24 01:31Z) Commit the reusable setup builder, generate the tracked sealed GW3 proposal from that commit, and pause for human review without opening GW3 outcomes.
- [x] (2026-07-24 02:35Z) Generalise the finaliser to verify and consume arm-specific reviewed setups while retaining the legacy GW2 contract.
- [x] (2026-07-24 02:36Z) Prove in an isolated run that all five GW3 plans persist before outcome access, score 59 points, auto-substitute Konsa for Palmer, and advance isolated states to GW4 with four free transfers.
- [x] (2026-07-24 02:43Z) Commit/push generic finaliser `4356ea7`, generate the canonical GW3 checkpoint from that exact commit, prove an idempotent rerun, and stop with no GW4 directory or decision.
- [x] (2026-07-24 03:38Z) Generate GW4 in isolation, expose the first policy divergence, and correct setup review so each arm's `selected` candidate is exactly the candidate the finaliser will freeze.
- [x] (2026-07-24 03:45Z) Commit/push selector `b9d095b`, generate the canonical sealed GW4 setup from that exact commit, prove idempotence and zero outcome/plan/transition artifacts, and pause before reveal.
- [x] (2026-07-24 20:45Z) Diagnose the user-questioned four-transfer state as a season-start off-by-one: the seed supplied one pre-GW1 transfer and the normal transition awarded another.
- [x] (2026-07-24 21:20Z) Correct the controlled seed to zero pre-deadline transfers, migrate GW2 to the generic reviewed-setup contract, and prove the full corrected chain in isolation: GW2/GW3/GW4 open with 1/2/3 transfers while points and football actions remain unchanged.
- [x] (2026-07-24 21:34Z) Commit producing correction `bbbba85`, preserve the invalid lineage in Git commit `365587a` plus the ignored local archive named by `superseded-lineages.json`, regenerate 225 canonical GW1–GW4 files, prove byte-identical rerun, and pass 57 historical plus 350 applicable repository tests.
- [x] (2026-07-24 21:43Z) Reproduce and fix the GW4→GW5 state failure caused by Marc Guiu's Sunderland→Chelsea club refresh: record the official temporary club-limit exception, permit no-transfer carry, and require the next transfer action to restore the three-player limit.
- [x] (2026-07-24 21:46Z) Finalise GW4 after all five plans froze: the four active arms scored 57 and reached 231 cumulative points; the naive bank arm scored 62 and reached 236, while carrying the explicit four-Chelsea exception into GW5.
- [x] (2026-07-24 22:08Z) Extend the solver's zero-transfer seam for the official club-change exception without weakening any non-empty transfer candidate, then prove the real five-arm GW5 setup succeeds in isolation.
- [x] (2026-07-24 22:10Z) Generate the canonical 41-file sealed GW5 setup from commit `d1302c4`, prove a byte-identical rerun, and pass 353 applicable repository tests without accessing the hidden outcome.
- [x] (2026-07-24 22:29Z) Finalise GW5 from the reviewed bank actions: active arms scored 46 and reached 277 cumulative; naive scored 49 and reached 285, with the expected 3/5 opening-GW6 transfer banks.
- [x] (2026-07-24 22:34Z) Generate the canonical sealed GW6 setup from committed GW5 checkpoint `115e4cf`, prove a byte-identical 41-file rerun, and pass 353 applicable tests without opening GW6 outcomes.
- [x] (2026-07-24 23:19Z) Finalise GW6 from the sealed bank actions: active arms scored 31 and reached 308 cumulative; naive scored 35 and reached 320, with no automatic substitutions and 4/5 opening-GW7 transfer banks. Prove the completed checkpoint is byte-identical on rerun and pass 97 focused replay/state/scoring tests.
- [x] (2026-07-24 23:23Z) Generate the canonical sealed GW7 setup from committed GW6 checkpoint `81424f0` and prove a byte-identical 41-file rerun. Active arms select Murillo→Gabriel by a narrow planning margin; naive banks at the five-transfer cap.
- [x] (2026-07-24 23:25Z) Finalise GW7 from the sealed plans: active arms scored 40 and reached 348 cumulative; naive scored 32 and reached 352. Gabriel's 9 versus Rodon's 1 accounts for the complete eight-point weekly swing. Prove the completed checkpoint is byte-identical on rerun.
- [x] (2026-07-24 23:28Z) Generate the canonical sealed GW8 setup from committed GW7 checkpoint `6fa0847` and prove a byte-identical 41-file rerun. Active arms select free Tarkowski→Timber and Bruno→Semenyo transfers; naive remains the no-transfer control.
- [x] (2026-07-24 23:30Z) Finalise GW8 from the sealed plans: active arms scored 52 and reached 400 cumulative; naive scored 36 and reached 388. Prove the completed checkpoint is byte-identical on rerun and separate the latest-transfer return from the accumulated trajectory return.
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

- Observation: the reviewed GW3 banking plan scores the same 59 points as GW2, but through a different realised path.
  Evidence: Palmer records no appearance and Ezri Konsa, the first legal outfield substitute, enters automatically. Salah remains captain, João Pedro vice-captain, no hit is charged, cumulative points reach 174, and every arm opens GW4 with four free transfers.

- Observation: GW4 is the first checkpoint where the naive and optimiser policies prescribe different actions.
  Evidence: banking produces 56.12 immediate plus 7.20 option value for 63.32 planning points and five future transfers. Palmer-to-Gakpo plus Anderson-to-Szoboszlai produces 61.43 immediate plus 3.60 option value for 65.03 planning points and three future transfers. The latter wins by 1.71 without a hit.

- Observation: the generic setup initially displayed the solver-selected transfer plan as `selected` for the naive arm even though the finaliser correctly freezes the no-transfer policy.
  Evidence: the isolated GW4 summary labelled two transfers for all arms while `finalise_historical_gameweek` branches the naive arm to `plans.no_transfer`. A shared `select_policy_candidate` contract now drives both preparation and finalisation.

- Observation: the initial controlled seed treated the normal GW2 transfer as if it already existed before GW1.
  Evidence: `official-scout-gw1.json` set `free_transfers: 1`, then `_next_free_transfers` correctly added the official weekly award during GW1→GW2. The resulting 2/3/4 opening counts contradicted the official rule that the first transfer is given only after the first deadline.

- Observation: correcting the transfer count does not change the reviewed actions through GW4.
  Evidence: the isolated corrected replay scores 56/59/59 and still banks in GW2 and GW3. GW4 still prefers Palmer→Gakpo plus Anderson→Szoboszlai without a hit; only option-value levels and successor transfer counts change.

- Observation: a real-world player move can make an already-owned FPL squad temporarily exceed the ordinary three-per-club limit.
  Evidence: the GW5 market refresh changes Marc Guiu from Sunderland to Chelsea. The naive arm still owns Sánchez, Palmer and João Pedro, so its successor contains four Chelsea players. The official FPL help contract permits this state but requires the manager to return under the limit when next making a transfer.

- Observation: the first policy divergence lost five immediate points.
  Evidence: Palmer and Anderson scored 7 and 4 in the naive XI, while their replacements Gakpo and Szoboszlai scored 3 each. Captain Salah and every other effective starter were shared, producing 62 for naive versus 57 for the other four arms.

- Observation: an exceptional four-club state still has an officially legal zero-transfer action, even though every non-empty transfer action must restore the normal limit.
  Evidence: the first GW5 preflight produced no naive `no_transfer` candidate and failed while building its policy brief. Allowing the exception only in the solver's unchanged-squad evaluation restores that candidate; transfer enumeration and post-transfer evaluation remain strictly capped at three.

- Observation: all five reviewed GW5 policies currently bank, but from different squads and objectives.
  Evidence: active arms project 61.17 immediate and 64.77 planning points, carrying three transfers to GW6. Naive projects 56.64 immediate and 63.84 planning points, carrying the five-transfer cap while retaining the declared Chelsea exception.

- Observation: GW5 extended the naive arm's realised lead from five to eight points.
  Evidence: active arms scored 46 after Tarkowski replaced zero-minute Murillo; naive scored 49 after Rodon replaced Murillo. All arms banked, Salah remained captain, and no hit or chip affected the comparison.

- Observation: the active GW6 bank decision is clear, while the naive policy deliberately ignores a costless-at-cap transfer improvement.
  Evidence: active bank scores 66.52 planning points versus 66.14 for Sánchez→Pickford. Naive bank scores 65.14, but Palmer→Semenyo scores 67.79 because using one of five transfers still replenishes to the five-transfer cap for GW7. Naive nevertheless banks by benchmark definition.

- Observation: GW6 extended the naive arm's realised lead from eight to twelve points.
  Evidence: active arms scored 31 and reached 308 cumulative; naive scored 35 and reached 320. No arm needed an automatic substitution, took a hit, played a chip, or made a transfer.

- Observation: the active GW7 transfer decision is positive but unusually close to adjacent transfer counts.
  Evidence: Murillo→Gabriel scores 64.98 planning points, versus 64.96 for also upgrading Sánchez→Raya, 64.88 for the three-transfer route adding Semenyo, and 64.80 for banking. The selected one-transfer action preserves four transfers for GW8 and avoids spending extra option value for a lower total objective.

- Observation: GW7 recovered eight of the active arm's twelve-point cumulative deficit.
  Evidence: active scored 40 versus naive's 32. Gabriel scored 9 in the active effective XI while Rodon scored 1 for naive; Gakpo/Porro both scored 7 and Szoboszlai/Anderson both scored 1, so the Gabriel/Rodon slot accounts for the whole arm-to-arm swing.

- Observation: the active GW8 two-transfer action clears the option-value hurdle, but the incremental second transfer remains a sensitivity point.
  Evidence: bank scores 66.14 planning points, Bruno→Semenyo 66.47, and adding Tarkowski→Timber 66.71; the selected second transfer contributes 0.24 planning points. A three-transfer route reaches 64.39 immediate but only 66.19 planning after spending another retained transfer.

- Observation: GW8's sixteen-point active gain came from accumulated trajectory divergence, not the latest two transfers.
  Evidence: Timber scored 6 versus Tarkowski's 3, while Semenyo scored 4 versus Bruno's 8, making the current transfers net −1. Earlier divergent slots Gabriel/Gakpo/Szoboszlai scored 23 versus naive's Rodon/Porro/Anderson on 6, net +17; together these produce the observed +16.

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

- Decision: checkpoint finalisation reads, verifies and records solver lineage per arm even when all arm payloads currently hash identically.
  Rationale: shared hashes are an observed property of the current state, not a licence to share mutable policy state. This preserves correct execution once transfers, chips or evidence make the trajectories diverge.
  Date/Author: 2026-07-24 / Codex.

- Decision: setup review and outcome finalisation use one policy-candidate selector.
  Rationale: a reviewed proposal must be the exact proposal later frozen. The naive arm selects no transfer by definition; other arms currently use the reviewed solver selection or declared structured fallback.
  Date/Author: 2026-07-24 / Codex.

- Decision: represent the pre-GW1 controlled state with zero free transfers and let the ordinary transition award the first GW2 transfer.
  Rationale: this matches the official timing rule without adding a hidden Gameweek special case to otherwise-correct transition arithmetic.
  Date/Author: 2026-07-24 / Codex.

- Decision: regenerate GW2 with the same generic reviewed-setup format used by GW3+.
  Rationale: one loader and one lineage contract reduce special-case drift while preserving the locked pre-season forecast and option-value policy.
  Date/Author: 2026-07-24 / Codex.

- Decision: represent a club-change overflow explicitly on policy state rather than weakening the ordinary squad validator.
  Rationale: official FPL permits the exceptional squad to persist only until the manager next makes a transfer. Explicit metadata lets no-transfer banking remain legal, forces any later transfer set to restore the limit, and preserves strict validation for ordinary and initial squads.
  Date/Author: 2026-07-24 / Codex.

- Decision: allow a club-limit overflow only in the optimiser's zero-transfer base evaluation.
  Rationale: this mirrors the official rule and preserves the baseline's meaning. Every enumerated transfer still flows through the unchanged strict club validator, and the plan-freeze boundary additionally requires matching exception metadata on the predecessor state.
  Date/Author: 2026-07-24 / Codex.

## Outcomes & Retrospective

The first genuine checkpoint is complete locally. It contains one shared official-Scout action bound independently to five arm states, five frozen plans and realised outcomes, and five successor states at the opening of GW2. Every arm scored 56 net points and banked a second free transfer. No GW2 proposal, outcome, or policy choice exists.

The checkpoint exposed and fixed one provenance mismatch between episode and scorer canonicalisation. It also demonstrates why the replay must preserve actual decisions: Rodon's 7 bench points remain unused because all XI players appeared. The result is reproducible across two output roots and the full repository suite passes. Policy divergence and solver inputs intentionally begin at the reviewed GW2 checkpoint.

GW3 is now complete as the third genuine chronological checkpoint. The reviewed bank/no-transfer plan scored 59: Palmer did not appear, Ezri Konsa legally auto-substituted for him and contributed 14, Salah's captaincy added 3, and João Pedro scored 9 without needing the vice-captain fallback. All arms remain action-equivalent at 174 cumulative points but retain distinct state, plan, outcome and transition hashes.

The corrected lineage opens GW2/GW3/GW4 with 1/2/3 free transfers. Scores, substitutions, squads and reviewed actions through GW3 are unchanged. The corrected GW4 setup still recommends Palmer→Gakpo plus Anderson→Szoboszlai for the optimiser/fallback arms, now carrying two transfers to GW5; the naive arm banks and would carry four. The superseded lineage is recoverable from its recorded Git commit and preserved in an ignored local archive; the corrected 225-file tree reproduces byte-for-byte.

GW4 is now complete. The active structured action made two free transfers and scored 57, leaving those arms on 231 cumulative points with £1.8m bank and two free transfers. The naive arm banked, scored 62, and leads on 236 with four free transfers. Its GW5 state explicitly records four Chelsea players because Marc Guiu's club identity refreshed from Sunderland to Chelsea; it may continue without a transfer, but its next transfer action must restore the three-per-club limit. No GW5 decision has been prepared.

GW5 is now complete. The active arms banked and scored 46, reaching 277 with three free transfers and £1.8m for GW6. Naive banked and scored 49, reaching 285 with the five-transfer cap and £0.0m. Murillo's zero minutes triggered legal but arm-specific automatic substitutions because the benches differ: Tarkowski entered for the active arms and Rodon for naive. No GW6 decision has yet been prepared.

GW6 is complete. Active arms banked, scored 31, and reached 308 cumulative with four free transfers and £1.8m for GW7. Naive banked, scored 35, and reached 320 with the five-transfer cap and £0.0m. No automatic substitutions were required. The completed checkpoint is byte-identical on rerun and the 97-test focused replay/state/scoring suite passes. No GW7 decision has yet been prepared.

GW7 is prepared and sealed from committed GW6 checkpoint `81424f0`. Active arms select the free Murillo→Gabriel transfer, project 59.58 immediate and 64.98 planning points, and would retain four transfers for GW8. Naive banks, projects 54.58 immediate and 61.78 planning points, and remains capped at five. All arms captain Salah and vice-captain Watkins. The 41 setup files reproduce byte-for-byte; no GW7 hidden outcome, validated plan, or state transition exists.

GW7 is complete. Active arms made the free Murillo→Gabriel transfer, scored 40, and reached 348 cumulative with four free transfers and £1.1m for GW8. Naive banked, scored 32, and reached 352 with five free transfers and £0.0m. Gabriel's 9 points versus Rodon's 1 produced the complete eight-point weekly recovery; no substitutions, hits, or chips intervened. The completed checkpoint is byte-identical on rerun. No GW8 decision has yet been prepared.

GW8 is prepared and sealed from committed GW7 checkpoint `6fa0847`. Active arms select the free Tarkowski→Timber and Bruno→Semenyo transfers, project 63.11 immediate and 66.71 planning points, and would retain three transfers for GW9. Naive banks, projects 53.13 immediate and 60.33 planning points, and remains capped at five. All arms captain Salah; active vice-captains Semenyo while naive vice-captains João Pedro. The 41 setup files reproduce byte-for-byte; no GW8 hidden outcome, validated plan, or state transition exists.

GW8 is complete. Active arms made the free Tarkowski→Timber and Bruno→Semenyo transfers, scored 52, and reached 400 cumulative with three free transfers and £2.0m for GW9. Naive banked, scored 36, and reached 388 with five free transfers and £0.0m. Active therefore moves from four points behind to twelve ahead, but the latest transfer pair returned −1 relative to the outgoing players; the gain came from earlier trajectory divergence. No substitutions, hits, or chips intervened, and the completed checkpoint is byte-identical on rerun. No GW9 decision has been prepared.

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
chronology/state/reproducibility result.

GW3 is now prepared from commit `1983707` and remains sealed. Its common
forecast uses only completed GW1–2 history; each of the five state hashes binds
its own optimiser review. The selected structured plan banks all three
available transfers, captains Salah, vice-captains João Pedro and would carry
four transfers into GW4. Its 65.21 planning objective leads the best one- and
two-transfer alternatives by only 0.18 points. No plan is frozen and no GW3
hidden outcome, realised outcome or state transition has been opened or
created.

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
