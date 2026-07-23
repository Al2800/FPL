# Build the canonical validated plan and realised outcome scorer

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, every benchmark policy will cross the same deterministic boundary before its decision is recorded or scored. An optimiser or future agent may propose a candidate, but only one closed, rules-validated and content-addressed Gameweek plan can enter a Gameweek Decision Record, receive a hidden outcome, or advance that policy's season state. A reviewer will be able to run focused tests and see illegal squads, line-ups, transfers, finances, chips, stale predecessors, altered hashes, and outcomes revealed before freeze fail closed.

The realised outcome scorer will consume official per-fixture FPL rows only after the plan is frozen. It will aggregate a player's rows across the complete Gameweek before deciding whether the player appeared, so Double Gameweeks cannot distort captain fallback or automatic substitutions. It will then apply ordered bench substitutions, normal or triple captaincy, and Bench Boost deterministically and return gross points in the exact small interface already consumed by the longitudinal policy-state transition.

## Progress

- [x] (2026-07-23 18:27Z) Closed and published prerequisite `FPL-1qi`; all 265 local tests passed.
- [x] (2026-07-23 18:28Z) Re-checked Beads, confirmed `FPL-5i9` was ready and unowned, and claimed it.
- [x] (2026-07-23 18:43Z) Mapped optimiser candidates, Gameweek Decision Records, policy-result freezes, scoring primitives, historical hidden outcomes, and longitudinal state transitions.
- [x] (2026-07-23 19:02Z) Added contract-first tests for canonical plan validation and tamper detection; observed the expected missing-module collection failures.
- [x] (2026-07-23 19:21Z) Implemented the strict validated-plan schema and pure validation/freeze module.
- [x] (2026-07-23 19:21Z) Added realised outcome golden cases for doubles, ordered autosubs, Bench Boost, and Triple Captain, plus fail-closed boundary cases.
- [x] (2026-07-23 19:21Z) Implemented the reveal-gated realised outcome scorer and result schema.
- [x] (2026-07-23 19:48Z) Migrated the GDR, walking skeleton, replay smoke harness, retrospective metrics, and policy-state transition to consume the canonical plan.
- [x] (2026-07-23 19:48Z) Updated deterministic transition hashes intentionally changed by the stronger proposal binding.
- [x] (2026-07-23 19:58Z) Ran 56 integrated focused tests, all 290 repository tests, and a real GW2 historical-outcome scoring smoke; documented the evidence for closure.

## Surprises & Discoveries

- Observation: the current optimiser candidate contains a line-up and self-reported validation booleans, but no rules hash, predecessor state, audited transfer finance, freeze time, or plan hash.
  Evidence: `src/optimisation/solver.py` emits `transfers`, `hit_cost`, `bank_after`, `lineup`, and three Boolean validation flags only.

- Observation: the current Gameweek Decision Record accepts any object under `recommendation.lineup`.
  Evidence: `control/schemas/decisions/gameweek_decision_records.json` declares `lineup` as an unconstrained object and leaves `recommendation` open, so an arbitrary line-up can validate.

- Observation: the longitudinal state engine currently consumes a thin decision mapping and trusts an unrelated `proposal_sha256`; it does not prove that the transferred squad, selected line-up, captain, bench, rules, and predecessor were hashed together.
  Evidence: `src/orchestration/policy_state.py::transition_policy_state` reads transfers and chip from the decision, but never receives the line-up.

- Observation: historical outcomes contain one row per player and fixture. Double Gameweeks therefore contain multiple rows for a player, while captain fallback and substitutions are defined over total Gameweek minutes.
  Evidence: `hidden-outcome.json` contains `player_outcomes` keyed by `element` and `fixture`; the historical feature adapter already observed 896 fixture rows for 817 players in Gameweek 26.

- Observation: the existing automatic-substitution helper iterates absent starters before ordered bench players.
  Evidence: `src/scoring/engine.py::apply_automatic_substitutions` can make starter list order influence which outfield substitute is used, although FPL substitution priority belongs to the bench order.

## Decision Log

- Decision: A validated plan is an immutable action document, not an optimiser result. It contains audited transfers, the complete post-transfer squad identity/position set, ordered starting XI and bench, captain and vice-captain, chip, financial result, rules identity, predecessor state hash, validation evidence, freeze time, and one content hash.
  Rationale: Expected points and strategy labels are explanatory model outputs. The action semantics must be stable across deterministic, agent, challenger, human, GDR, scoring, and state-transition seams.
  Date/Author: 2026-07-23 / Codex.

- Decision: Candidate-supplied hit cost, bank-after value, and validation flags are never authoritative.
  Rationale: The deterministic boundary recomputes transfers, selling prices, purchase prices, bank, hits, squad legality, line-up legality, and chip legality from the predecessor state, decision market, and explicit rules.
  Date/Author: 2026-07-23 / Codex.

- Decision: The GDR embeds the validated plan unchanged at `validated_plan`; `recommendation` retains only display and strategy metadata plus the same plan hash.
  Rationale: This preserves the human-readable decision record while ensuring no second transfer, line-up, captain, bench, or chip representation can drift into scoring.
  Date/Author: 2026-07-23 / Codex.

- Decision: The outcome scorer aggregates `minutes` and `total_points` by player across all fixture rows before any selection rule is applied.
  Rationale: A player with minutes in either Double Gameweek fixture played in the Gameweek. Row-wise captain fallback or substitution would be wrong and could make fixture ordering change the score.
  Date/Author: 2026-07-23 / Codex.

- Decision: Gross points exclude transfer hits; the existing policy-state transition subtracts the plan's recomputed hit cost to produce net points.
  Rationale: This keeps scoring and season finance responsibilities separated and preserves the established state-transition accounting.
  Date/Author: 2026-07-23 / Codex.

## Outcomes & Retrospective

The implementation establishes a single fail-closed plan seam and an official-outcome scorer, making genuine replay a chronological composition problem rather than a place where action or scoring semantics are invented. All 290 repository tests pass. A controlled legal plan scored against the real 2025/26 GW2 hidden partition aggregated 705 official fixture rows into its 15 squad players, applied two ordered substitutions, retained the captain at multiplier two, and produced 39 gross points. Its plan hash was `280f97a19903f6b6b8599d70c89eeb0beafccde900914dbb0eaa4eda315222ab`; its realised-outcome hash was `415cb84d9a616246dbbf1d196967a45b5d0dcfa48cf04568db31a6525c11f212`.

Transition content hashes intentionally changed because the proposal binding now covers the full action document. Squad, finance, transfer-hit, chip, and cumulative-point semantics remain independently asserted by the longitudinal tests. The new GDR contract rejects a second arbitrary line-up and requires display metadata to reference the embedded plan hash.

## Context and Orientation

`src/optimisation/solver.py` produces candidate dictionaries. These are proposals, not trusted plans. `src/orchestration/validated_plan.py` will be the only module allowed to convert such a candidate into a frozen plan. It will receive the current arm-owned policy state from `src/orchestration/policy_state.py`, a complete decision-time player market, the active rules mapping, the exact rules file hash, and a freeze timestamp.

The policy state contains the permanent 15-player squad, purchase/current/selling prices, bank, free transfers, chip inventory, arm identity, Gameweek, rules identity, and its own `content_sha256`. The validated plan must name that state hash as `previous_state_sha256`. This prevents a plan created for one arm or one earlier squad from being reused on another.

`control/schemas/benchmark/validated-plan.json` will define the closed plan document. “Closed” means JSON Schema rejects unknown fields. The plan's `content_sha256` is SHA-256 over canonical JSON with only `content_sha256` omitted. Its validation hash is separately computed over the rules identity, predecessor, audited transfers, resulting squad, line-up, chip, and finance.

`src/evaluation/outcome_scorer.py` will accept only a valid frozen plan, one historical hidden-outcome mapping for the same episode, and an explicit reveal timestamp. The raw hidden outcome has no reveal timestamp because it is an immutable data partition; the replay harness supplies the time at which the partition becomes available. The scorer rejects a reveal at or before `frozen_at`.

`src/orchestration/policy_state.py::transition_policy_state` will accept the validated plan directly. It will still recompute transfer finance against the decision market and will verify that its recomputed moves, bank, hit cost, chip, predecessor, and rules equal the plan. This deliberate duplication is an equivalence guard: plan construction proves legality before freeze; transition recomputation proves the frozen plan was not altered before state mutation.

`control/schemas/decisions/gameweek_decision_records.json`, `src/reporting/decision_record.py`, `src/orchestration/walking_skeleton.py`, and the current smoke `src/orchestration/replay_harness.py` must migrate together. The genuine replay bead will later replace the smoke harness's synthetic episode adapter, but it must inherit the canonical plan rather than another line-up shape.

## Plan of Work

First add `tests/contracts/test_validated_plan.py`. Build a small legal 15-player state and market under `control/rules/2025-26.yaml`. Require the validation boundary to recompute an ordinary transfer's selling/purchase prices, bank and hit cost; preserve ordered XI and bench; bind the rules and predecessor; validate against the new schema; reproduce the same hashes; and reject a mutated transfer, line-up, captain, finance, chip, predecessor, rules hash, or content hash. Update the GDR example and contract tests so `validated_plan` is required and `recommendation.lineup`, `recommendation.transfers`, and `recommendation.chip` are rejected.

Implement `src/orchestration/validated_plan.py` using standard-library canonical JSON plus existing validators in `src/scoring/validator.py`. The module will normalise market and state player identifiers, audit same-position transfers and finance, validate the complete resulting squad, map ordered line-up identifiers to player records, validate formation/captain/bench rules, validate one available chip, and emit validation and content hashes. No optimiser, agent, GDR, or scorer may set these hashes itself.

Add `tests/historical-replay/test_realised_outcome_scorer.py` and small committed golden cases under `evals/golden-cases/outcomes/`. Cover a normal Gameweek, one player split across two Double Gameweek fixtures, a blank/no-minute starter replaced from ordered bench, formation-preserving outfield substitution, goalkeeper-only substitution, captain fallback based on total Gameweek minutes, Triple Captain, Bench Boost, duplicate fixture rows, mismatched episode identity, tampered plans, and reveal before freeze.

Implement `src/evaluation/outcome_scorer.py`. Aggregate rows by `element` after rejecting duplicate `(element, fixture)` pairs. Sum integer `minutes` and `total_points`, normalise `GK` to `GKP`, and check any reported position against the frozen plan squad. Treat absent rows as zero minutes and zero points, which covers blank clubs. Apply automatic substitutions from the frozen ordered bench. Add only the extra captain multiplier because the chosen captain or vice-captain's ordinary points are already included in the XI or Bench Boost base. Emit a closed, content-addressed realised-outcome document with `gross_points`.

Migrate the GDR and existing smoke surfaces. The root GDR embeds the plan unchanged and its display recommendation points to the same hash. Rendering reads XI, bench, captain, vice-captain, transfers, chip, and hit cost only from the plan. Retrospective metrics do the same. The walking skeleton and smoke replay harness create a policy-state view from their fixture input, validate/freeze their selected candidate, then build the GDR. Their reproducibility hash includes the validated plan hash.

Finally change `transition_policy_state` to require the canonical plan and use `plan["content_sha256"]` as the proposal hash. Recompute transfers and compare the audited move and finance fields to the plan before producing a successor. Update the two policy-state test helpers and the intentional historical transition-hash fixtures. State behavior—squad, bank, free transfers, chips, gross/net points—must remain the same even though hashes change because the proposal is now bound to more information.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Before implementation, add the contract tests and run:

    .\.venv\Scripts\python.exe -m pytest tests/contracts/test_validated_plan.py tests/historical-replay/test_realised_outcome_scorer.py -q

Expect import failures because the two new modules do not exist.

After the plan boundary is implemented, run:

    .\.venv\Scripts\python.exe -m pytest tests/contracts/test_validated_plan.py tests/contracts/test_schemas.py tests/test_decision_record_replay.py -q

After outcome scoring is implemented, run:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_realised_outcome_scorer.py tests/rules/test_scoring_engine.py -q

After policy-state migration, run:

    .\.venv\Scripts\python.exe -m pytest tests/unit/test_policy_state.py tests/unit/test_policy_state_seasons.py tests/historical-replay/test_walking_skeleton.py tests/test_decision_record_replay.py -q

At completion run:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

The complete suite should pass with the new contracts included. Run a representative real historical hidden outcome through the scorer using a legal controlled plan and record the resulting plan hash, aggregated player count, substitution trace, captain source, chip multiplier, and gross points.

## Validation and Acceptance

A valid plan built twice from identical inputs must be byte-identical and pass `control/schemas/benchmark/validated-plan.json`. Reordering the input market must not change it. Changing one transfer, XI position, bench position, captain, vice-captain, chip, rules hash, predecessor state, or finance value without rebuilding must make integrity validation fail.

A validated GDR must contain exactly one action representation. `validated_plan` is authoritative; the display recommendation's hash must equal the plan hash. Adding an arbitrary `recommendation.lineup`, transfer list, or chip must fail schema or semantic validation and cannot reach `score_revealed_outcome`.

For a Double Gameweek player with fixture minutes 0 and 30, the scorer must aggregate to 30 and must not trigger captain fallback or an automatic substitution. For a player with zero total Gameweek minutes, the scorer must use the ordered eligible bench under the active formation rules. Bench Boost must count all 15 ordinary player totals exactly once. Triple Captain must make the chosen captain or fallback vice-captain contribute three times in total. Gross points must enter `transition_policy_state`; the transition alone subtracts hits and updates cumulative net points.

An outcome for another episode, a duplicate player/fixture row, a position conflict, a tampered plan, or a reveal timestamp at or before plan freeze must raise a typed error and produce no score or state successor.

## Idempotence and Recovery

Plan construction, integrity validation, outcome aggregation, scoring, and state transition are pure functions. They do not write governed data and do not mutate inputs. Repeating them with identical mappings returns identical content and hashes. A failed validation or score raises before any artefact or state is produced.

No package or download is required. If migration reveals a still-used legacy line-up representation, keep the repository green by converting that producer to the canonical boundary; do not add a second scoring adapter. The only acceptable temporary compatibility is inside fixture-building test helpers, and it must produce a complete validated plan before calling production consumers.

## Artifacts and Notes

The historical hidden-outcome shape is:

    hidden_outcome_version, episode_id, season, gameweek,
    reveal_after="proposal_frozen", player_outcomes, fixtures, match_results

Each player row contains `element`, `fixture`, `position`, `minutes`, and official `total_points`. Official `total_points` is the outcome source of truth; the scorer must not attempt to reconstruct BPS.

The existing state-transition outcome seam already expects:

    outcome_id, revealed_at, gross_points

The realised-outcome result will retain those fields so it can pass unchanged into the transition while adding plan/source hashes and scoring audit detail.

## Interfaces and Dependencies

No new dependency is required.

In `src/orchestration/validated_plan.py`, define:

    class ValidatedPlanError(ValueError)

    def validated_plan_hash(plan: Mapping[str, Any]) -> str

    def validate_plan_integrity(
        plan: Mapping[str, Any],
        *,
        expected_state: Mapping[str, Any] | None = None,
        rules: Mapping[str, Any] | None = None,
        ruleset_sha256: str | None = None,
    ) -> None

    def validate_and_freeze_plan(
        *,
        episode_id: str,
        policy_arm: str,
        state: Mapping[str, Any],
        candidate: Mapping[str, Any],
        decision_market: Mapping[str, Any] | Iterable[Mapping[str, Any]],
        active_chip: str | None,
        frozen_at: str,
        rules: Mapping[str, Any],
        ruleset_sha256: str,
    ) -> dict[str, Any]

In `src/evaluation/outcome_scorer.py`, define:

    class OutcomeScoringError(ValueError)

    def realised_outcome_hash(outcome: Mapping[str, Any]) -> str

    def score_revealed_outcome(
        plan: Mapping[str, Any],
        hidden_outcome: Mapping[str, Any],
        *,
        revealed_at: str,
        rules: Mapping[str, Any],
        ruleset_sha256: str,
    ) -> dict[str, Any]

`src/orchestration/policy_state.py::transition_policy_state` keeps its keyword markets and rules parameters but its second positional mapping is the complete validated plan. The scorer result is passed as the third positional mapping without adaptation.

Revision note (2026-07-23): Initial plan created after claiming `FPL-5i9` and mapping every existing producer and consumer. The plan records the decision to embed one canonical plan in the GDR and to preserve gross-versus-net point responsibility.

Revision note (2026-07-23): Completed the implementation, recorded the intentional transition-hash migration, full-suite result, and real historical GW2 scoring evidence.
