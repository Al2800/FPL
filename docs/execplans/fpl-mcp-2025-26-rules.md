# Recover the executable 2025/26 FPL ruleset

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, Benchmark v0 can validate decisions and label episodes with the actual 2025/26 Fantasy Premier League rules instead of a placeholder or the later 2026/27 catalogue. A reviewer can inspect one source-backed YAML catalogue, execute deterministic historical golden cases, and verify that each episode manifest contains the SHA-256 of the exact catalogue bytes used to build it.

## Progress

- [x] (2026-07-22 15:45Z) Closed the accepted historical episode-builder bead and claimed `FPL-mcp` without ownership conflicts.
- [x] (2026-07-22 16:00Z) Located contemporaneous Premier League sources for squad, lineup, transfers, prices, chips, scoring, assists, defensive contributions, bonus changes, deadlines and the AFCON transfer event.
- [x] (2026-07-22 16:10Z) Captured a five-failure red baseline for the missing catalogue and golden cases, then added exact-hash and fail-closed tests.
- [x] (2026-07-22 16:25Z) Added `control/rules/2025-26.yaml`, ADR-0019 and historical golden cases from official evidence.
- [x] (2026-07-22 16:40Z) Replaced the episode rules limitation with validated rules injection and additive v2 output, preserving v1.
- [x] (2026-07-22 17:05Z) Built 38 v2 episodes twice, captured stable hashes, passed 20 focused tests and passed 162 repository tests.

## Surprises & Discoveries

- Observation: The reusable validation functions accept an explicit `rules` mapping, but several branches in `src/scoring/golden_runner.py` call the 2026/27 default loader internally.
  Evidence: `fixtures.blank_gameweek`, `corrections.provisional_then_final`, and `deadlines.ninety_minutes` call `load_rules()` with no path. Historical tests must inject the historical catalogue directly rather than claim that the existing default runner is season-aware.

- Observation: The 2026/27 announcement explicitly says that 2025/26 scores locked one hour after the final whistle, whereas 2026/27 moves locking to 09:00 the next day.
  Evidence: Premier League article `https://www.premierleague.com/en/news/4679873/all-you-need-to-know-about-changes-to-fpl-for-202627`.
- Observation: Directly running `python scripts/build_historical_episodes.py` cannot resolve the repository-root `src` package in this environment; module execution works.
  Evidence: direct invocation raised `ModuleNotFoundError: No module named 'src'`; `python -m scripts.build_historical_episodes` completed all 38 episodes.


## Decision Log

- Decision: Hash the exact UTF-8 rules file bytes and copy that exact file into each v2 episode directory.
  Rationale: A raw-file hash makes the manifest independently auditable and prevents YAML formatting or metadata changes from being hidden by parsed-object canonicalisation.
  Date/Author: 2026-07-22 / Codex.

- Decision: Preserve v1 episodes and create additive v2 outputs after rules recovery.
  Rationale: The repository and workspace prohibit destructive cleanup, and retaining the limitation-bearing v1 artefacts makes the provenance transition visible.
  Date/Author: 2026-07-22 / Codex.

- Decision: Represent rules that affect replay but are not yet computed by the scoring engine, such as the revised assist criteria and detailed BPS inputs, as sourced catalogue data with deterministic catalogue assertions.
  Rationale: Historical final FPL points are observed outcomes; the benchmark must know the operative definitions without pretending that incomplete event data can reconstruct every subjective decision.
  Date/Author: 2026-07-22 / Codex.

## Outcomes & Retrospective

Benchmark v0 now has a confirmed, official-source-backed 2025/26 catalogue and
38 additive v2 episodes that embed and hash its exact bytes. The historical
rules limitation is removed. Genuine replay remains correctly dependent on
longitudinal policy state, not on further rules recovery.

## Context and Orientation

`control/rules/2026-27.yaml` is the general default catalogue, while `control/rules/2025-26.yaml` is the validated historical catalogue. `src/scoring/rules_loader.py` loads either catalogue, and `src/scoring/validator.py` plus `src/scoring/engine.py` accept an explicit parsed mapping. `src/orchestration/historical_episode_builder.py` validates the historical catalogue, embeds its exact bytes as `ruleset.yaml`, and hashes them into each v2 manifest. The historical catalogue covers every category returned by `src.scoring.rules_loader.required_categories()`.

A ruleset content hash is the lower-case SHA-256 digest of the exact bytes in `control/rules/2025-26.yaml`. An observed episode is the information available before a Gameweek deadline. A hidden outcome contains that Gameweek's realised results and must remain inaccessible until a policy proposal is frozen.

## Plan of Work

First add `tests/rules/test_2025_26_rules.py`. The test loads the historical YAML explicitly, checks all required families and source metadata, verifies season-specific changes including AFCON and score finalisation, executes validator and scoring functions with the historical mapping, and checks historical episode manifests against the exact file digest. Run it before implementation to preserve the red-test evidence.

Then create `control/rules/2025-26.yaml` from dated official Premier League evidence. Add `evals/golden-cases/rules-2025-26.yaml` for representative deterministic decisions and `docs/decisions/0019-historical-ruleset.md` for provenance, differences and the boundary between executable rules and observed official outcomes.

Finally update `src/orchestration/historical_episode_builder.py` to accept an explicit `rules_path`, reject the wrong season or unresolved catalogue, remove `historical_rules_not_yet_executable` from observed limitations, write an immutable `ruleset.yaml` copy, and place the exact byte hash in the episode manifest and safe index. Update the CLI to default to additive v2 paths, rebuild all 38 episodes, and verify reproducibility.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the new test before implementation:

    python -m pytest tests/rules/test_2025_26_rules.py -q

Expect failures because `control/rules/2025-26.yaml` does not yet exist and the builder still emits a limitation ruleset.

After implementation, run:

    python -m pytest tests/rules/test_2025_26_rules.py tests/historical-replay/test_historical_episode_builder.py tests/contracts/test_benchmark_schemas.py -q
    python -m scripts.build_historical_episodes
    python -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py

The focused tests must all pass. The build must report 38 episodes and 38 distinct observed hashes. The repository suite may exclude only the already documented local parquet-engine test when neither `pyarrow` nor `fastparquet` is installed.

## Validation and Acceptance

Acceptance requires a catalogue with season `2025-26`, no unresolved replay-blocking status, official dated source URLs, and every required rule family. The golden tests must prove a legal squad and formation, a four-point extra transfer, five-transfer banking, half-profit sale, first-half chip expiry, defensive-contribution thresholds, the 2025/26 AFCON top-up, and the one-hour score lock. A generated episode's `ruleset.content_sha256` must equal `sha256(control/rules/2025-26.yaml bytes)`, and its local `ruleset.yaml` must have the same digest. No observed episode may retain `historical_rules_not_yet_executable`.

## Idempotence and Recovery

Rules and documentation edits are additive. Episode v2 writes use the existing immutable writer: rerunning identical inputs succeeds, while altered content at an existing path fails rather than overwriting evidence. V1 artefacts remain untouched. If a source-backed rule remains unresolved, retain an explicit unresolved status and keep replay blocked instead of guessing.

## Artifacts and Notes

Primary evidence currently selected:

    https://www.premierleague.com/en/news/2174419
    https://www.premierleague.com/en/news/2174899/1000
    https://www.premierleague.com/en/news/2174907
    https://www.premierleague.com/en/news/2174900
    https://www.premierleague.com/en/news/2174909
    https://www.premierleague.com/en/news/4361991/whats-new-in-202526-fantasy-defensive-contributions
    https://www.premierleague.com/en/news/4362027
    https://www.premierleague.com/en/news/4362102/whats-new-in-202526-fantasy-extra-transfers-for-afcon
    https://www.premierleague.com/en/news/4362127/whats-new-in-202526-fantasy-changes-to-bonus-points-system
    https://www.premierleague.com/en/news/4362187
    https://www.premierleague.com/en/news/4362211/all-you-need-to-know-about-changes-to-fantasy-for-202526

Final evidence:

    focused: 20 passed in 1.07s
    repository: 162 passed in 74.72s
    v2 index: 726a0a4183d13bec7036016af65dbf8d400e66033dc03e4d08e90772482ce9fb
    ruleset: 376e6a7982b54bce8562a73cfd749f30c2d869c50bfa036a531b96c90bb5a809
    episodes: 38; distinct observed hashes: 38

## Interfaces and Dependencies

Keep the existing Python and PyYAML stack; add no dependency. Extend `build_historical_episodes` with `rules_path: Path = DEFAULT_RULES` and validate it via `load_rules`. The safe index episode row should expose `ruleset_sha256`, replacing `ruleset_limitation_sha256`. Tests must always pass the loaded historical mapping into `validator` and `engine` functions so the later default catalogue cannot leak into historical assertions.

Revision note (2026-07-22): Initial plan created after primary-source research and inspection of the existing season-default leakage risk.
Revision note (2026-07-22): Updated after implementation with the red/green evidence, module-invocation discovery, immutable v2 build hashes and final regression results.
