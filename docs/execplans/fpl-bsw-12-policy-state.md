# Implement isolated longitudinal policy state

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, each benchmark policy can play a genuine FPL season rather than solve disconnected Gameweeks. All five policies start from the same explicitly controlled synthetic squad, then own separate histories of squad, purchase prices, selling prices, bank, free transfers, chips and cumulative points. A reviewer can run unit tests and see that transfers made by one policy never affect another and that replaying identical decisions produces identical content hashes.

## Progress

- [x] (2026-07-22 18:34Z) Confirmed `FPL-bsw.12` is ready, unowned and file-isolated; claimed it in Beads.
- [x] (2026-07-22 18:45Z) Resolved 2025/26 transfer and chip transition semantics from the validated catalogue and official chip guidance.
- [x] (2026-07-22 19:10Z) Added failing schema and transition tests for initial-state isolation, prices, transfers, hits, banking, chips, exceptional events and deterministic replay.
- [x] (2026-07-22 19:25Z) Implemented closed policy-state and state-transition schemas.
- [x] (2026-07-22 19:48Z) Implemented the pure transition engine and isolated in-memory history ledger.
- [x] (2026-07-22 20:07Z) Passed 18 focused tests, 33 combined contract tests and 180 repository regression tests; recorded completion evidence.

## Surprises & Discoveries

- Observation: `src.scoring.validator.banked_transfers` is suitable for optimiser search but its operation order would give zero next-week transfers after making two transfers with one available.
  Evidence: it evaluates `min(cap, previous + 1) - used`; the season transition must instead evaluate `min(cap, max(0, previous - used) + 1)`.

- Observation: Since 2024/25, Wildcard and Free Hit preserve the exact banked free-transfer count instead of resetting it or awarding an extra transfer during that transition.
  Evidence: the official 2025/26 chip page says managers keep banked transfers, while the official change announcement illustrates five transfers remaining five for the following Gameweek.

- Observation: JSON Schema decimal `multipleOf: 0.1` rejects some valid one-decimal Python floats because of binary floating-point representation.
  Evidence: schema validation rejected `4.8`; transition boundaries now enforce one-decimal price steps semantically and the schemas retain numeric bounds without the unsafe `multipleOf` assertion.

## Decision Log

- Decision: Benchmark v0 uses one explicit controlled synthetic seed, cloned into all five policy arms, rather than inventing a historical manager account.
  Rationale: The historical dataset has no trustworthy archived personal squad, purchase-price, bank or chip history. A shared controlled seed preserves experimental comparability without mislabelling synthetic state as observed fact.
  Date/Author: 2026-07-22 / Codex.

- Decision: State snapshots are immutable content-addressed values. The hash covers all decision-relevant fields except the hash field itself.
  Rationale: Exact hashes make cross-arm borrowing, stale predecessors and nondeterministic reruns detectable.
  Date/Author: 2026-07-22 / Codex.

- Decision: A transition consumes a frozen decision and a separately timestamped revealed outcome; reveal must be later than freeze.
  Rationale: State cannot advance using results that were available before the proposal was frozen.
  Date/Author: 2026-07-22 / Codex.

- Decision: Free Hit transfers are validated against the decision market but the next state restores the old squad, purchase history and bank. Wildcard transfers persist. Both preserve the exact banked-transfer count.
  Rationale: These are materially different longitudinal effects and must not share a generic “unlimited transfers” implementation.
  Date/Author: 2026-07-22 / Codex.

## Outcomes & Retrospective

The longitudinal kernel is complete for benchmark v0. Five policy arms now start from one controlled £100.0m Gameweek 1 seed but receive independent, content-addressed histories. The transition engine deterministically applies purchase-history selling prices, hits, free-transfer banking and the Gameweek 16 top-up; distinguishes persistent Wildcards from reverting Free Hits; expires first-half chips; blocks adjacent Gameweek 19/20 Free Hits; and fails closed on stale, cross-arm, temporally invalid or financially impossible transitions. Validation finished with 18 policy-state tests, 33 combined benchmark/rules contracts and 180 applicable repository tests passing.

## Context and Orientation

`control/rules/2025-26.yaml` is the active historical rule catalogue. `src/scoring/validator.py` provides selling-price, squad, chip and hit validation primitives. `src/optimisation/transfers.py` applies candidate transfers for a single decision, but it does not own a season history. `control/schemas/benchmark/policy-result.json` proves a proposal was validated and frozen before outcome access. The new `src/orchestration/policy_state.py` will connect those pieces across Gameweeks without modifying the existing optimiser.

A policy state is the decision account visible at a Gameweek cutoff. It includes the 15 permanent squad members, each arm's purchase history, current and selling prices, cash bank, available free transfers, unused chips, prior chip uses and cumulative net points. A transition is the immutable audit record connecting one state to the next after a proposal freezes and its outcome is revealed. Gameweek 39 is permitted only as a terminal season-complete state after Gameweek 38.

## Plan of Work

First create `tests/unit/test_policy_state.py`. It will define a legal controlled seed and two price snapshots, then require independent initial states for every policy arm. It will test ordinary transfer finance and hits, correct next-week transfer banking, price changes based on arm-specific purchase price, Wildcard persistence, Free Hit reversion, chip consumption and expiry, the GW16 top-up, reveal-after-freeze, impossible transitions and deterministic hashes.

Create `control/schemas/benchmark/policy-state.json` and `control/schemas/benchmark/state-transition.json` with closed objects and content hashes. The state schema will distinguish an active state from the terminal state and require a complete 15-player squad. The transition schema will record predecessor, frozen proposal, reveal, applied transfer prices, chip, points and successor hash.

Then implement `initialise_policy_states`, `transition_policy_state`, `state_hash`, `transition_hash` and `PolicyStateLedger` in `src/orchestration/policy_state.py`. The implementation will receive the historical rules mapping explicitly, validate the ruleset identity and squad on every boundary, and use canonical JSON SHA-256. All public returns will be deep copies so callers cannot mutate stored history.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the new test before implementation:

    python -m pytest tests/unit/test_policy_state.py -q

Expect collection or missing-contract failures. After implementation run:

    python -m pytest tests/unit/test_policy_state.py tests/contracts/test_benchmark_schemas.py tests/rules/test_2025_26_rules.py -q
    python -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py

## Validation and Acceptance

All five initial states must share one seed hash but have distinct arm-specific state hashes. Two transfers made with one free transfer must cost four points and leave one free transfer for the next Gameweek. An owned player's selling price must derive from that arm's purchase price, including after later market movement. Wildcard must persist the new squad without a hit; Free Hit must validate its temporary squad and then restore the old permanent state. GW16 must start with five free transfers, unused first-half chips must disappear at GW20, and invalid arm, predecessor, finance, position, chip or time ordering must raise `PolicyStateError` without producing a successor. Identical inputs must produce byte-identical state and transition hashes.

## Idempotence and Recovery

The engine is pure: it does not write files or mutate its inputs. Repeating initialization or transition calls is safe and deterministic. `PolicyStateLedger` copies values on input and output and refuses nonconsecutive or cross-arm appends. A failed transition leaves every history unchanged.

## Artifacts and Notes

Official semantics used in addition to `control/rules/2025-26.yaml`:

    https://www.premierleague.com/en/news/2174900
    https://www.premierleague.com/en/news/4058895

## Interfaces and Dependencies

No dependency is added. Use Python standard-library `copy`, `datetime`, `hashlib` and `json`, plus existing `jsonschema`, PyYAML-loaded rules and scoring validators.

`initialise_policy_states(seed, policy_arms, rules, ruleset_sha256) -> dict[str, dict]` creates independent Gameweek 1 states. `transition_policy_state(state, decision, outcome, decision_market, next_market, rules, ruleset_sha256) -> tuple[dict, dict]` returns the next state and transition record. `PolicyStateLedger(initial_states).append(transition, next_state)` maintains isolated histories; `current` and `history` return copies.

Revision note (2026-07-22): Initial plan created after Beads ownership checks, repository inspection and resolution of 2025/26 Wildcard/Free Hit semantics.

Revision note (2026-07-22): Completed implementation and validation; documented the decimal-schema trap and exact passing test evidence.
