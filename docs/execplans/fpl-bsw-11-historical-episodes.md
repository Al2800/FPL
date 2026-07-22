# Build genuine historical Benchmark v0 episodes

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be updated as work proceeds. It follows the workspace guidance in `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, the frozen 2025/26 Benchmark v0 dataset can be transformed into one deterministic historical episode per Gameweek. An episode is the information available for one decision deadline, split into an observed partition that policies may read and a hidden-outcome partition that is sealed until their proposals are frozen. A reviewer can run one command, inspect several genuinely different Gameweeks, and verify that rerunning the command produces identical content hashes.

The builder must not pretend that end-of-season player catalogue fields, same-Gameweek results, historical news, or a historical manager squad were available before a deadline. It uses lagged completed Gameweek rows and a stripped current fixture schedule as structured observed evidence, keeps current-Gameweek results and points hidden, and records unavailable historical evidence explicitly. The later policy-state bead, `FPL-bsw.12`, will provide each policy arm's evolving squad and financial state before genuine chronological replay in `FPL-bsw.13`.

## Progress

- [x] (2026-07-22 15:10Z) Claimed `FPL-bsw.11` and confirmed that no other bead owns overlapping files.
- [x] (2026-07-22 15:20Z) Inspected the frozen seed, feature-view boundary, episode schema, replay skeleton, identity resolver and local 2025/26 source columns.
- [x] (2026-07-22 15:35Z) Added the historical episode tests and confirmed the expected red state: import fails because the builder module does not exist yet.
- [x] (2026-07-22 15:50Z) Implemented the immutable, schema-valid historical episode builder.
- [x] (2026-07-22 15:55Z) Implemented the user-facing historical episode CLI.
- [x] (2026-07-22 16:05Z) Built all 38 real episodes, wrote the safe index and proved its byte-for-byte deterministic rerun hash.
- [x] (2026-07-22 16:35Z) Passed 18 focused/contract/seed tests and 155 broader tests excluding only the known local Parquet-engine-dependent walking-skeleton file.
- [x] (2026-07-22 16:40Z) Updated Beads and prepared representative GW1/GW2/GW20/GW38 evidence for owner review.

## Surprises & Discoveries

- Observation: The frozen `merged_gw.csv` has 29,757 physical rows but ten are exact duplicate extras; the seed's canonical partition has 29,747 rows.
  Evidence: `validate_seed_files` records ten exact duplicates and zero conflicting natural keys.
- Observation: Every 2025/26 fixture has a kickoff timestamp, but the export is an end-of-season snapshot rather than an archived pre-deadline fixture revision.
  Evidence: all 380 fixture rows have `kickoff_time`, while the seed manifest was observed on 2026-07-22.
- Observation: The repository has only a 2026/27 executable rules file and no historical 2025/26 manager-state archive.
  Evidence: `control/rules/` contains only `2026-27.yaml`; Benchmark v0 documentation explicitly excludes reconstructed historical evidence.
- Observation: The frozen CSV files are UTF-8, while a permissive Latin-1 read silently corrupts accented player names.
  Evidence: the builder now tries UTF-8 with BOM handling before a legacy Latin-1 fallback.
- Observation: Two football-data team names differ from the FPL catalogue: `Man United`/`Man Utd` and `Tottenham`/`Spurs`.
  Evidence: comparison of the two frozen source catalogues; the builder must make these season-specific mappings explicit and fail on any other unresolved name.
- Observation: The initial historical episode suite reaches collection and fails only because the new module is absent.
  Evidence: `python -m pytest tests/historical-replay/test_historical_episode_builder.py -q` reports `ModuleNotFoundError: src.orchestration.historical_episode_builder`.

## Decision Log

- Decision: Keep detailed observed and hidden partitions under the gitignored local Benchmark v0 data root; commit only code, tests, an episode index containing hashes and counts, and explanatory documentation.
  Rationale: Source payloads and derived row-level data are private-research artefacts and must not be redistributed through Git.
  Date/Author: 2026-07-22 / Codex
- Decision: Derive each deadline as 90 minutes before the earliest current-Gameweek kickoff and record that derivation plus the final-export fixture-revision limitation.
  Rationale: All fixture kickoff times are present, while a separate archived deadline field is not. The result is deterministic and honest about its evidence limitation.
  Date/Author: 2026-07-22 / Codex
- Decision: The observed player feature partition contains only the immediately preceding Gameweek's completed rows, filtered to kickoff before cutoff, and excludes `xP`. Gameweek 1 records a cold-start gap rather than using end-of-season player aggregates.
  Rationale: This is the smallest useful leakage-safe v0 feature set and avoids cumulative file growth or final-season catalogue leakage.
  Date/Author: 2026-07-22 / Codex
- Decision: Current-Gameweek fixture rows expose schedule and team identity only. Scores, stats, started/finished state and minutes remain hidden.
  Rationale: Policies need the fixture slate, but final outcomes cannot cross the isolation boundary.
  Date/Author: 2026-07-22 / Codex
- Decision: Historical manager state and news are explicit unavailable-evidence artefacts, not invented fixtures. The episode still carries content-addressed references required by schema v1.0.
  Rationale: A structurally valid limitation is preferable to a plausible but false reconstruction. `FPL-bsw.12` owns policy state.
  Date/Author: 2026-07-22 / Codex
- Decision: The observed episode pairing hash excludes the hidden outcome reference and generated timestamps, following accepted ADR-0017.
  Rationale: Outcomes and build time must not change the information-parity key.
  Date/Author: 2026-07-22 / Codex
- Decision: Generated episode output is versioned below `data/benchmark-v0/episodes/v1/2025-26`.
  Rationale: Immutable outputs must not be overwritten when the builder's content contract changes.
  Date/Author: 2026-07-22 / Codex

## Outcomes & Retrospective

At the requested review checkpoint, all 38 Gameweeks build into distinct, schema-valid observed and hidden partitions. A repeated full run preserves safe-index SHA-256 `F7C3A61F9B3166C400A25C22E590A32BD3BA814E89A774FCCE4524232A315485`. GW1 is an explicit cold start; GW2 observes 690 prior player rows and ten prior results; GW20 observes 780 prior player rows and 190 prior results; GW38 observes 840 prior player rows and 370 prior results. Same-Gameweek points, minutes, fixture scores and stats stay hidden. Manager state and historical news remain explicitly unavailable. The absence of a validated 2025/26 executable ruleset was recorded as new blocker `FPL-mcp` before season-accurate replay.

## Context and Orientation

`control/manifests/datasets/benchmark-v0.json` is the committed frozen dataset manifest. It identifies five local source artefacts below `data/benchmark-v0/2025-26/`: merged FPL Gameweek player rows, FPL fixtures, the final player catalogue, the team catalogue and football-data.co.uk match results. The local files are gitignored.

`control/schemas/benchmark/episode-manifest.json` defines the public episode manifest. It requires season, Gameweek, cutoff, deadline, code and ruleset references, observed source and feature references, allowed tools, budgets, five fixed policy arms and an opaque hidden-outcome reference. The hidden payload itself is not part of this manifest.

`docs/evaluation/benchmark-protocol.md` and accepted `docs/decisions/0017-benchmark-kernel.md` define the observed episode hash. It is SHA-256 over canonical JSON for the observed decision state, excluding hidden outcomes, policy results, evaluation records and run-generated timestamps.

`src/features/deadline_view.py` is the generic governed feature-view boundary. Benchmark v0 predates per-deadline source snapshots, so this builder cannot falsely manufacture quality reports or publication timestamps for the final season export. Instead it creates a specialised historical structured partition that applies the seed's documented field allow-list and records the reconstruction limitation. Future live episodes should continue using the generic deadline view.

An observed partition is a JSON artefact policies may read. It contains the stripped current fixture slate, prior-Gameweek player outcomes, prior match results, identity mappings and limitations. A hidden-outcome partition is a JSON artefact the evaluator may read only after proposal freeze. It contains current-Gameweek player outcomes and final fixture results. A content-addressed artefact has a SHA-256 hash calculated from canonical JSON, so identical content always has the same identity.

## Plan of Work

First add `tests/historical-replay/test_historical_episode_builder.py`. The tests will construct a small two-Gameweek dataset in a temporary directory and a matching frozen manifest. They will prove that Gameweek 2 observes Gameweek 1 data but not Gameweek 2 points or minutes; that current fixture scores and stats are hidden; that `xP` and untimestamped odds never enter observed data; that post-cutoff rows are filtered; that unknown football-data team identities fail closed; that reruns and reordered source rows produce identical hashes; and that an existing different artefact is never overwritten.

Then add `src/orchestration/historical_episode_builder.py`. Define `HistoricalEpisodeError`, canonical JSON and hashing helpers, dataset path resolution, exact-duplicate collapse with conflicting-key failure, season-specific team identity construction, cutoff derivation, observed and hidden partition construction, immutable JSON writing, episode-manifest validation and an index builder. Provide a public function:

    build_historical_episodes(
        *,
        dataset_manifest_path: Path,
        out_dir: Path,
        data_root: Path | None = None,
        gameweeks: Iterable[int] | None = None,
        code_commit: str | None = None,
    ) -> dict[str, Any]

The returned dictionary is the safe episode index. Each index row records episode ID, Gameweek, cutoff, deadline, observed episode hash, observed and hidden artefact hashes, row counts, identity-map hash, rules limitation hash and evidence limitations. It contains no player-level outcome rows.

Add `scripts/build_historical_episodes.py` as the user-facing command. It accepts `--manifest`, `--data-root`, `--out`, and comma-separated Gameweek selection. By default it builds all 38 episodes below `data/benchmark-v0/episodes/v1/2025-26/` and writes the safe index to `evals/episodes/structured/benchmark-v0-index.json`. It prints a concise count and representative hashes.

Finally run the command against the real local seed, inspect Gameweeks 1, 2, 20 and 38, validate all episode manifests, rerun to prove immutability and determinism, and update this plan and the Beads completion record.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the focused red test after adding it:

    python -m pytest tests/historical-replay/test_historical_episode_builder.py -q

Before implementation, expect import or assertion failures. After implementation, expect all tests in that file to pass.

Build representative episodes during development:

    python -m scripts.build_historical_episodes --gameweeks 1,2,20,38

The command should report four episodes with four distinct observed hashes. Inspect `evals/episodes/structured/benchmark-v0-index.json`; it should contain counts and hashes but no `total_points`, `minutes`, scores or player rows.

Build the complete season and rerun it:

    python -m scripts.build_historical_episodes
    python -m scripts.build_historical_episodes

Both runs should report 38 episodes and identical index content. Then run:

    python -m pytest tests/historical-replay/test_historical_episode_builder.py tests/contracts/test_benchmark_schemas.py tests/integration/test_benchmark_v0_seed.py -q
    git diff --check

## Validation and Acceptance

The implementation is accepted when all 38 Gameweeks build from the registered local paths, have distinct observed episode hashes, and validate against schema v1.0. Gameweek 2's observed partition must contain only Gameweek 1 player outcomes plus the stripped Gameweek 2 fixture slate; its hidden partition must contain Gameweek 2 points and minutes. Gameweek 1 must record the lack of lagged player history rather than loading final player aggregates. No observed partition may contain `xP`, current-Gameweek outcomes, fixture scores, fixture stats, untimestamped odds or reconstructed news.

Every episode must record a season-specific team identity mapping with zero unresolved names, a rules limitation reference, the source content hashes from the frozen dataset, and explicit fixture-revision, manager-state and news limitations. Rebuilding from identical data must reproduce every content and observed episode hash. An existing file with different content must cause a clear error rather than be overwritten.

## Idempotence and Recovery

The builder writes canonical JSON immutably. If a target file already contains identical content, it is reused. If it contains different content, the command fails and identifies the conflicting path. Re-running after an interrupted build is safe because completed identical artefacts are reused. Generated detailed partitions remain under the gitignored data root. No command downloads data, mutates the frozen seed, or deletes files.

## Artifacts and Notes

The frozen dataset hash is `fac1f0711ffd403e0cd68b7e7a75ef4cce0540ff0d42da970212efd2da54c6b0`. It contains 38 distinct Gameweek partitions, 29,747 de-duplicated player/Gameweek/fixture rows, 841 player catalogue entries, 20 teams and 380 fixtures/results.

## Interfaces and Dependencies

Use only the existing Python standard library, pandas, PyYAML and jsonschema dependencies. Do not add or install packages. Avoid Parquet output in this bead because JSON is directly inspectable and the current local Python environment lacks its optional Parquet engine despite `pyarrow` being declared in project metadata.

`src/orchestration/historical_episode_builder.py` owns historical partition construction and stable hashing. `scripts/build_historical_episodes.py` owns argument parsing and reporting only. `tests/historical-replay/test_historical_episode_builder.py` owns behavioural proof. `evals/episodes/structured/benchmark-v0-index.json` is the only generated real-data summary intended for Git; detailed episode artefacts stay under `data/benchmark-v0/episodes/`.

Plan revision note (2026-07-22): Initial plan created after inspecting the complete frozen seed and accepting ADR-0017. It deliberately separates truthful structured reconstruction from unavailable historical manager/news evidence.

Plan revision note (2026-07-22): Recorded the test-first red milestone and its exact failure before implementation.


Plan revision note (2026-07-22): Recorded the complete 38-episode build, deterministic rerun, verification evidence and the new historical-rules blocker at the owner review checkpoint.
Plan revision note (2026-07-22): Recorded the UTF-8 source discovery and versioned generated-output decision so immutable development artefacts are never overwritten.
