# Gate live rules and drive longitudinal transitions from typed semantics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, an FPL rules catalogue cannot enter the longitudinal season engine merely because it is the default file. A reviewer can run one command and receive a structured activation report showing the ruleset identity, exact file hash, normalized transition semantics, unresolved blockers and a semantic comparison with another season. Historical 2025/26 replay continues byte-for-byte with the same state and transition hashes, while the current unresolved 2026/27 candidate stops before Gameweek 1 with actionable diagnostics.

## Progress

- [x] (2026-07-22 20:31Z) Confirmed `FPL-83y` was ready and file-isolated; claimed it in Beads.
- [x] (2026-07-22 20:38Z) Audited the two catalogues and captured deterministic 2025/26 baseline hashes before refactoring.
- [x] (2026-07-22 20:52Z) Added failing activation, schema, differential and cross-season policy-state tests.
- [x] (2026-07-22 21:14Z) Implemented typed activation compilation, compatibility review and semantic diff reporting.
- [x] (2026-07-22 21:36Z) Refactored longitudinal transitions and benchmark schemas to consume compiled semantics instead of season constants.
- [x] (2026-07-22 21:44Z) Added and exercised the activation CLI for successful historical and blocked two-season runs.
- [x] (2026-07-22 21:55Z) Passed 45 focused tests and 196 full applicable repository tests; updated the plan and Beads evidence.

## Surprises & Discoveries

- Observation: The same rule ID has deliberately different value shapes across seasons: `transfers.afcon_exceptional_topup` is an object in 2025/26 and Boolean false in 2026/27.
  Evidence: `control/rules/2025-26.yaml` contains `{gameweek: 16, top_up_to: 5}`; `control/rules/2026-27.yaml` contains `false`. The current transition indexes the value as an object and would raise a type error.

- Observation: The boundary rule changed names while still unresolved.
  Evidence: 2025/26 uses confirmed `chips.boundary_restrictions` with a structured object; 2026/27 uses provisional `chips.gw1_and_boundary_restrictions` with the string `pending_launch_detail`. Activation must report both unresolved status and incompatible shape.

- Observation: Season length need not be added to the immutable historical YAML.
  Evidence: both catalogues declare two chip sets and a first-half expiry at Gameweek 19, which yields 38 regular Gameweeks when their consistency is validated. The compiled profile can derive the terminal marker as Gameweek 39 without changing historical ruleset bytes.

- Observation: The benchmark state schemas independently encoded GW38/39 and the eight known chip identifiers.
  Evidence: Rules-driven terminal and chip inventory tests initially remained constrained by JSON Schema. Structural schemas now use safe broad bounds and chip naming shape, while semantic validation enforces the exact compiled profile.

- Observation: Re-exporting activation from the loader created a direct-import cycle even though loader-first tests passed.
  Evidence: A direct `import src.scoring.rules_activation` review exposed the cycle. The activation module now owns a small private catalogue indexer; direct imports and 42 focused tests pass.

## Decision Log

- Decision: Compile raw catalogue rules into a typed transition profile before initialization or transition.
  Rationale: Raw YAML is evidence-oriented and permits provisional entries and season-specific value shapes. A compiled profile is the narrow operational contract the state engine needs and provides one fail-closed boundary.
  Date/Author: 2026-07-22 / Codex.

- Decision: Activation reports blockers as data; an assertion function raises a domain error before engine use.
  Rationale: Humans and CI need to inspect all blockers at once, while state creation must never proceed with a partial profile.
  Date/Author: 2026-07-22 / Codex.

- Decision: A reviewed compatibility policy may permit an inherited rule but never a provisional, disputed, retired, missing or malformed rule.
  Rationale: Inheritance can represent a deliberate temporary carry-forward. Unknown or structurally invalid semantics cannot safely drive state. Every exception must name its rule, expected status, rationale, approver and approval timestamp.
  Date/Author: 2026-07-22 / Codex.

- Decision: Do not edit either season YAML in this bead.
  Rationale: The 2025/26 file is embedded and content-addressed by historical episodes. The 2026/27 provisional boundary must remain visibly unresolved until official launch verification rather than being guessed for test convenience.
  Date/Author: 2026-07-22 / Codex.

- Decision: Keep activation compilation in `src/scoring/rules_activation.py` and re-export its public API from `rules_loader.py`.
  Rationale: The activation code is large enough to deserve an isolated module, while existing callers retain one stable rules-loader entry point. A private indexer avoids circular imports.
  Date/Author: 2026-07-22 / Codex.

## Outcomes & Retrospective

The activation gate and rules-driven longitudinal transition are complete. The exact five historical hashes remain unchanged. The 2025/26 catalogue activates with a normalized 38-Gameweek profile and its GW16 top-up; the current 2026/27 catalogue exits nonzero before state creation with 11 named blockers and a three-rule semantic diff. A confirmed test copy proves no AFCON event, dynamic chip expiry, dynamic terminal state, exact Free Hit restoration and the complete transfer recurrence matrix. Focused validation passed 45 tests; the full applicable repository suite passed 196 tests twice, including after the direct-import fix.

## Context and Orientation

`control/rules/2025-26.yaml` is the validated historical replay catalogue. Every rule is confirmed. `control/rules/2026-27.yaml` is the upcoming live candidate and intentionally contains inherited and provisional entries. A rule status describes evidence confidence: confirmed is directly verified, inherited is carried forward from a prior season, and provisional is incomplete.

`src/scoring/rules_loader.py` loads YAML, flattens rule lists and re-exports the activation API implemented in `src/scoring/rules_activation.py`. `src/orchestration/policy_state.py` owns immutable per-policy season state and consumes only a compiled transition profile. `tests/unit/test_policy_state.py` proves the original 2025/26 behavior, while `tests/unit/test_policy_state_seasons.py` pins its hashes and exercises cross-season semantics.

An activation report is a deterministic JSON object describing whether a ruleset may execute. It contains the source identity, a normalized transition profile if compilation succeeds, compatibility approvals, and blockers. A semantic diff compares normalized decision-relevant values rather than descriptions, dates or formatting.

## Plan of Work

First create `tests/rules/test_ruleset_activation.py` and `control/schemas/rules/ruleset-activation.json`. Tests will require 2025/26 activation to pass schema validation, require current 2026/27 activation to be blocked with all unresolved and malformed entries listed, exercise approved inherited compatibility, reject unreviewed or provisional compatibility, normalize AFCON object and false values, and compare the two seasons without metadata noise.

Create `tests/unit/test_policy_state_seasons.py` around a small independent legal squad fixture. It will pin the five pre-refactor historical hashes, exercise every free-transfer count from zero to five against zero to six moves, prove Wildcard and Free Hit retention/restoration, and use a test-only confirmed copy of the 2026/27 catalogue to prove no AFCON top-up. That copy does not change the source catalogue: it models the future state after official confirmation by converting only required inherited statuses to confirmed and replacing the provisional boundary entry with the already known structured historical shape.

Extend `src/scoring/rules_loader.py` with `build_ruleset_activation`, `assert_ruleset_activatable`, `ruleset_semantic_diff` and `RulesetActivationError`. Normalization validates exact primitive/object shapes, one-decimal monetary steps, cross-rule bounds and compatibility approvals. It converts the optional AFCON object or false value into an event list, derives chip identifiers and windows, and derives 38 regular Gameweeks from the two sets and the Gameweek 19 boundary.

Refactor `src/orchestration/policy_state.py` so initialization and each transition assert activation and consume the compiled profile. Chip inventory, first/second-half availability, expiry, unavailable Gameweeks, adjacency restriction, transfer award, retention and season terminal behavior come from the profile. Public state and transition representations do not change, preserving hashes.

Add `scripts/verify_ruleset_activation.py`. Given one or more rules YAML paths, it prints deterministic JSON and exits zero only when every candidate activates. With two paths it includes a semantic diff. The current 2026/27 invocation must exit nonzero with structured blockers; the 2025/26-only invocation must exit zero.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the red contracts before implementation:

    python -m pytest tests/rules/test_ruleset_activation.py tests/unit/test_policy_state_seasons.py -q

After implementation run:

    python -m pytest tests/rules/test_ruleset_activation.py tests/unit/test_policy_state_seasons.py tests/unit/test_policy_state.py tests/rules/test_2025_26_rules.py tests/rules/test_rules_catalogue.py -q
    python -m scripts.verify_ruleset_activation control/rules/2025-26.yaml
    python -m scripts.verify_ruleset_activation control/rules/2025-26.yaml control/rules/2026-27.yaml
    python -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py

The first CLI invocation must exit zero and print `activatable: true`. The two-season invocation must exit nonzero, identify `2026-27-v0.1`, list inherited/provisional blockers and still include a semantic diff.

## Validation and Acceptance

The 2025/26 engine must still produce these exact hashes for the existing forecast-optimizer fixture:

    initial state: 437dacf98473a42a5743ab4398966877938d40626625c63cc4a8d7a8d6ef6780
    Gameweek 2 state: 2c439118e69d6d730a8e76b9b978edd2bcb6388a15d3e81a3bb4709864083bed
    Gameweek 1 transition: 61930485b2a83a9ce9f4060f7a9e6ed244b3b51c8c69761251baf5e6394561c0
    Gameweek 3 state: a532e31e89c2e08156c1fd3ecfc3ce7f566c8d0cc41177939d1d566cf7532c97
    Gameweek 2 transition: a932d51c530dbfc8115263e7480c2e5dc20fa673cad4159b7062c328d45a97c1

A fully confirmed test copy of 2026/27 must transition into Gameweek 16 without changing the ordinary recurrence result, while 2025/26 must top up to five. Current source 2026/27 must be blocked before initial state creation. Chip windows and terminal state must change when their typed fixture values change, proving the engine is no longer relying on Python Gameweek literals. Invalid shapes, missing rules and unapproved inherited statuses must return named blockers and cause `RulesetActivationError` at engine entry.

## Idempotence and Recovery

Activation and semantic diff functions are pure. They do not rewrite YAML or state. Repeating the CLI is safe and yields identical JSON except for no generated timestamp, which is intentionally omitted. Failed activation creates no policy state. Existing public loader and transition signatures remain compatible; callers only see a domain error earlier when their catalogue is unsafe.

## Artifacts and Notes

Baseline hash capture before code edits:

    initial 437dacf98473a42a5743ab4398966877938d40626625c63cc4a8d7a8d6ef6780
    gw2_state 2c439118e69d6d730a8e76b9b978edd2bcb6388a15d3e81a3bb4709864083bed
    gw1_transition 61930485b2a83a9ce9f4060f7a9e6ed244b3b51c8c69761251baf5e6394561c0
    gw3_state a532e31e89c2e08156c1fd3ecfc3ce7f566c8d0cc41177939d1d566cf7532c97
    gw2_transition a932d51c530dbfc8115263e7480c2e5dc20fa673cad4159b7062c328d45a97c1

## Interfaces and Dependencies

No dependency is added. Use the standard library, existing PyYAML and existing `jsonschema`.

In `src/scoring/rules_loader.py` provide:

    class RulesetActivationError(ValueError): ...
    def build_ruleset_activation(rules, ruleset_sha256, *, mode="live", compatibility_policy=()) -> dict: ...
    def assert_ruleset_activatable(rules, ruleset_sha256, *, mode="live", compatibility_policy=()) -> dict: ...
    def ruleset_semantic_diff(left_rules, left_sha256, right_rules, right_sha256) -> dict: ...

`build_ruleset_activation` always returns a schema-valid report. `assert_ruleset_activatable` returns the compiled report or raises with every blocker. `ruleset_semantic_diff` is deterministic and compares decision-relevant normalized/raw rule values by canonical rule ID.

Revision note (2026-07-22): Initial plan created after Beads ownership checks, cross-season catalogue audit and baseline hash capture.

Revision note (2026-07-22): Completed implementation; recorded schema and import-cycle discoveries, exact CLI evidence and final focused/full test counts.
