# Make the deterministic optimiser season-aware and replay-scale

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a historical replay can pass the 2025/26 rules catalogue explicitly into the optimiser and evaluate the full declared one-, two-, or three-transfer candidate pool without repeatedly parsing YAML, rebuilding pandas data frames, or retaining every candidate in memory. The selected plan, strategy summaries, first 50 ranked candidates, and deterministic tie order must remain identical for the existing golden input. A reviewer can run scale tests and see all 120 one-transfer, 5,856 two-transfer, and 151,672 three-transfer combinations processed with bounded retained state before the genuine replay starts.

This work does not make the optimiser globally optimal. The declared pool still limits each position to the weakest owned sale candidates and strongest affordable available purchase candidates. Wildcard and Free Hit continue to make transfers free for hit accounting, but the optimiser does not claim to search every possible 15-player rebuild.

## Progress

- [x] (2026-07-23 21:01Z) Confirmed no other bead was in progress, claimed `FPL-kcc`, and recorded the starting note in Beads.
- [x] (2026-07-23 21:02Z) Read the governing project plan, optimiser, transfer enumeration, lineup selector, tests, prior performance audit, and profiling harness.
- [x] (2026-07-23 21:02Z) Reproduced the current golden baseline: 123 candidates, output fingerprint `a4605dc794cd45d6c2ea54071ba330d66bff88c52da7458e246df2592b412fec`, one cold solve in 9,910.128 ms.
- [x] (2026-07-23 21:16Z) Added contracts for explicit rules, pure/reference lineup equivalence, exact transfer widths, emitted-plan validation, full-search retention, and Wildcard/Free Hit capability claims.
- [x] (2026-07-23 21:16Z) Implemented a pure-data lineup selector with expected-points-descending/player-ID-ascending tie order and retained an independent pandas reference.
- [x] (2026-07-23 21:16Z) Converted transfer-set enumeration to a lazy iterator and precomputed selling prices, rule values, position counts, and club cap.
- [x] (2026-07-23 21:16Z) Made the solver require explicit rules/hash and retain only the top 50 plus best-per-strategy plans.
- [x] (2026-07-23 21:16Z) Updated the replay harness, walking skeleton, optimizer CLI, profiling harness, and tests to pass intentional rules.
- [x] (2026-07-23 21:24Z) Captured post-change p50/p95/p99, throughput, and peak Python heap at all three declared widths in `reports/performance/optimiser-scale.json`.
- [x] (2026-07-23 21:29Z) Ran 50 focused integration tests and all 298 repository tests; `git diff --check` passed and no optimizer module imports `load_rules`.
- [x] (2026-07-23 21:31Z) Added the detailed implementation evidence and closed `FPL-kcc`; commit, push, and CI confirmation remain the publication step.

## Surprises & Discoveries

- Observation: one 123-candidate golden solve currently takes roughly ten seconds, even though transfer enumeration itself is only a few milliseconds.
  Evidence: the stored CPU profile attributes 22.568 seconds of instrumented cumulative time to 122 calls of `choose_starting_xi`; 123 rules loads account for 10.273 seconds. The fresh uninstrumented solve took 9,910.128 ms.

- Observation: the rules mapping passed to `_evaluate_squad` is not passed onward to `choose_starting_xi`.
  Evidence: `src/optimisation/simple_plan.py::choose_starting_xi` calls `legal_formations()` with no argument, causing the default 2026/27 YAML to be loaded for every candidate even when the surrounding solver has another rules mapping.

- Observation: the solver materialises both all transfer tuples and every fully evaluated plan before sorting, although its public artefact retains only 50 candidates and one candidate per strategy.
  Evidence: `enumerate_transfer_sets` returns a list, `solve` appends all plans to `candidates`, then sorts the complete list and slices `ranked[:50]`.

- Observation: current tie behavior is deterministic on the committed input but implicit in pandas' default sort implementation.
  Evidence: `choose_starting_xi` sorts only by expected points, without a documented secondary key. Equal expected points therefore lack a domain-level ordering contract.

- Observation: the first implementation of bounded retention sorted a 51-item list for every valid candidate.
  Evidence: replacing repeated full sorting with ordered insertion reduced the direct 157,650-candidate solve to 17.790 seconds.

- Observation: the pure-data path preserves the exact committed decision while removing nearly all golden-fixture latency.
  Evidence: seven post-change golden solves took 13.161–19.911 ms and retained output fingerprint `a4605dc794cd45d6c2ea54071ba330d66bff88c52da7458e246df2592b412fec`, compared with the 9,910.128 ms starting run.

## Decision Log

- Decision: `solve` will require `rules` and `ruleset_sha256` as keyword-only arguments; it will never load a default catalogue.
  Rationale: replay correctness requires the episode's season catalogue, while live callers must make their active catalogue equally explicit. A required argument prevents a 2025/26 replay from silently using 2026/27 rules.
  Date/Author: 2026-07-23 / Codex.

- Decision: player ID ascending will be the explicit secondary ordering for equal expected points, and both the pandas reference selector and pure selector will use it.
  Rationale: this converts an implementation accident into a stable contract. The committed golden output has no affected tie and must remain byte-equivalent.
  Date/Author: 2026-07-23 / Codex.

- Decision: transfer enumeration will yield each unique tuple lazily in the existing deterministic structural order; output ranking will use one shared total-order key and bounded top-50 retention.
  Rationale: all transfer sets still receive exactly one evaluation, while memory no longer grows with 151,672 full plan dictionaries. Since ranking has a total deterministic key, enumeration order cannot affect the selected plan or displayed top 50.
  Date/Author: 2026-07-23 / Codex.

- Decision: ordinary one-to-three transfer search remains separate from full squad rebuild search.
  Rationale: setting hit cost to zero for Wildcard or Free Hit does not make a limited same-position transfer pool a complete rebuild optimiser. Capability metadata and tests must state this limitation.
  Date/Author: 2026-07-23 / Codex.

## Outcomes & Retrospective

The optimiser is now ready for genuine replay. It accepts only an explicit rules mapping and rules hash, preserves the exact committed golden decision and fingerprint, and evaluates a full 157,650-candidate cumulative declared pool in about 18.6 seconds p50 while retaining 50 candidates. The pure/reference differential cases cover ties and shuffled squad order; the streamed transfer tests prove the exact 120, 5,856 and 151,672 layer sizes; emitted candidates pass the deterministic validators and the selected scale plan crosses the canonical validated-plan boundary.

The largest measured search uses roughly 147 KB peak Python heap under `tracemalloc`, so candidate state is bounded rather than proportional to 151,672 plan dictionaries. The full repository suite passes 298 tests. Full Wildcard and Free Hit rebuild remains deliberately unimplemented and is reported as false in search capability metadata.

## Context and Orientation

`src/optimisation/types.py` defines `SolverInput`, the structured market, squad, bank, free-transfer, chip, horizon, and candidate-pool inputs. `src/optimisation/transfers.py` selects weak owned players and strong affordable available replacements, enumerates same-position transfer tuples, and applies each tuple to a squad. A “declared candidate pool” is this bounded set, not the full FPL market.

`src/optimisation/simple_plan.py::choose_starting_xi` currently converts each 15-player candidate squad into pandas structures, enumerates legal formations, chooses the highest expected-points XI, picks captain and vice-captain, and orders the bench. `src/optimisation/solver.py::_evaluate_squad` validates that result and calculates the one-Gameweek objective. `solve` currently stores all plans, sorts them, and emits the selected plan, strategy representatives, and the first 50 candidates.

The prior audit in `docs/evaluation/core-performance-audit.md` established the optimization target with p50/p95/p99, CPU, allocation, and I/O evidence. `reports/performance/core-baseline.json` is the baseline artefact. It found rules parsing and pandas lineup reconstruction, not episode I/O, to be the measured bottlenecks.

The scale counts arise from the existing default realistic pool widths: all 15 owned players may be sold, and each of the four positions has eight purchase candidates. Matching positions yields 120 distinct one-transfer sets, 5,856 distinct two-transfer sets, and 151,672 distinct three-transfer sets. These are candidates inside the declared pool; they are not all possible market transfers.

## Plan of Work

First create reference and differential tests. Preserve the existing pandas selector as a clearly named reference path with explicit expected-points-descending/player-ID-ascending ordering. Add a pure list-and-dictionary selector and compare complete lineup outputs across generated legal squads, legal formations, equal-point ties, and input permutations. Add transfer iterator tests that compare its complete sequence or set and counts with a small materialised reference.

Then introduce a compiled search context in `src/optimisation/solver.py` or `src/optimisation/simple_plan.py`. It will extract legal formations, club cap, position counts, captain multiplier, and chip rules once. The pure selector will partition 15 player records by position, sort each partition once, evaluate the small fixed set of legal formations, and build the same ordered XI, captain, vice, and bench without pandas.

Change `enumerate_transfer_sets` into an iterator. Precompute each owned player's sale price and each market player's normalized identity, position, club, price, expected points, and availability before entering the nested search. `apply_transfers` will use those normalized values and direct counts instead of calling broad validators for every candidate; emitted plans will still pass the existing deterministic squad, lineup, and chip validators.

Change `solve` to require explicit `rules` and `ruleset_sha256`. Verify the input rules ID against the supplied mapping under the existing fail-closed or explicit-allow policy. Count valid candidates as they stream. Maintain a bounded sorted list of the best 50 candidates and the best candidate for each strategy using the same ranking key currently used after materialisation. Preserve the separate no-transfer and bank-transfer candidates and the current output fingerprint fields.

Update `src/orchestration/replay_harness.py`, `scripts/run_optimiser.py`, and `scripts/profile_core_performance.py` to load an intentional catalogue once and pass it into `solve`. Tests will pass either `control/rules/2026-27.yaml` for the committed future-season golden fixture or `control/rules/2025-26.yaml` for historical replay fixtures.

Finally run scale measurements. The performance test itself will avoid brittle CI time thresholds but will assert candidate counts, deterministic output, bounded retained candidates, and capability metadata. A local report will record p50/p95/p99, candidates per second, tracemalloc peak, and process RSS for each declared width. Review selected plans through the canonical validated-plan boundary where the fixture supplies a complete legal state and market.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the existing baseline and retain its output fingerprint:

    .\.venv\Scripts\python.exe -m pytest tests/test_optimiser.py tests/performance/test_core_performance_oracles.py -q

Add red contracts, then run:

    .\.venv\Scripts\python.exe -m pytest tests/test_optimiser.py tests/performance/test_optimiser_scale.py -q

After implementation, run:

    .\.venv\Scripts\python.exe -m pytest tests/test_optimiser.py tests/performance/test_optimiser_scale.py tests/performance/test_core_performance_oracles.py -q

Capture the scale report with a dedicated script or test helper using at least five unprofiled samples for smaller widths and enough samples for a meaningful three-transfer p95/p99 without making the measurement impractical. Store the report under `reports/performance/`.

At completion run:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

The existing golden input must still select transfer `12` to `16`, objective `60.4`, and output fingerprint `a4605dc794cd45d6c2ea54071ba330d66bff88c52da7458e246df2592b412fec`. Calling `solve` without rules must fail at the Python interface rather than loading the default catalogue. Passing 2025/26 rules to a historical input must report `2025-26-v1.0`; no code under `src/optimisation/` may call `load_rules`.

For randomized legal squads, the pure selector and reference selector must return the same formation, XI order, bench order, captain, vice-captain, and expected points. Equal expected points must resolve by ascending player ID. The transfer iterator must produce the reference transfer tuples without duplicates.

The realistic pool must evaluate exactly 120 one-transfer, 5,856 two-transfer, and 151,672 three-transfer sets. The public result must retain at most 50 ranked candidates, deterministic strategy representatives, and a bounded amount of search state. Repeated runs must produce the same fingerprints.

Every plan present in `selected`, `plans`, and `all_candidates` must pass the existing squad, lineup, chip, transfer-finance, and canonical validated-plan checks appropriate to its input. Wildcard and Free Hit metadata must explicitly report that hit accounting is supported but full rebuild optimality is not.

## Idempotence and Recovery

All search functions are pure and safe to rerun. Tests and profiling write only designated reports or temporary pytest paths. If the pure selector differs from the reference, keep both implementations, reduce the failing generated case, and correct the pure selector before changing the solver path. Do not update the committed golden output to conceal a difference.

No dependency or download is required. If a scale run is interrupted, rerun that width; no persistent state is mutated.

## Artifacts and Notes

Starting evidence:

    golden candidates: 123
    golden output fingerprint: a4605dc794cd45d6c2ea54071ba330d66bff88c52da7458e246df2592b412fec
    fresh cold wall time: 9,910.128 ms
    stored warm wall p50/p95/p99: 9,000.979 / 10,619.170 / 10,899.074 ms
    stored Python heap peak: 811,942 bytes

The stored CPU profile identifies `choose_starting_xi`, repeated rules loading, and pandas reconstruction as the top measured cost. Transfer enumeration was only 2.538 ms in the 123-candidate fixture.

Post-change scale evidence:

    one-transfer layer 120; cumulative 122:
      p50/p95/p99 11.068 / 14.082 / 14.629 ms
      throughput 10,595.612 candidates/s; peak Python heap 97,952 bytes
    two-transfer layer 5,856; cumulative 5,978:
      p50/p95/p99 447.177 / 615.135 / 646.649 ms
      throughput 12,277.835 candidates/s; peak Python heap 128,184 bytes
    three-transfer layer 151,672; cumulative 157,650:
      p50/p95/p99 18,609.752 / 18,738.890 / 18,759.852 ms
      throughput 8,460.935 candidates/s; peak Python heap 146,968 bytes

All widths retained exactly 50 ranked candidates and reproduced one fingerprint across five unprofiled samples.

## Interfaces and Dependencies

No new third-party package is needed.

In `src/optimisation/simple_plan.py`, retain:

    def choose_starting_xi(squad: pandas.DataFrame, *, rules: Mapping[str, Any]) -> dict[str, Any]

and add a pure selector:

    def choose_starting_xi_rows(
        squad: Sequence[Mapping[str, Any]],
        *,
        formations: Sequence[Mapping[str, int]],
    ) -> dict[str, Any]

The reference wrapper and pure selector must share the explicit tie-order contract.

In `src/optimisation/transfers.py`, change:

    def enumerate_transfer_sets(...) -> Iterator[list[tuple[str, str]]]

and keep `apply_transfers` compatible with the yielded tuple lists while avoiding default rules.

In `src/optimisation/solver.py`, define:

    def solve(
        solver_input: SolverInput,
        *,
        rules: Mapping[str, Any],
        ruleset_sha256: str,
    ) -> dict[str, Any]

The result retains the existing keys and adds the supplied rules hash plus explicit search capability and retention metadata.

Revision note (2026-07-23): Initial ExecPlan created after baseline reproduction and source/profile mapping. It records the decision to require explicit rules, define tie ordering, stream candidates, retain bounded ranked state, and keep full rebuild capability separate.

Revision note (2026-07-23): Updated after implementation and realistic-width measurement with the pure selector, streamed search, bounded retention, exact candidate counts, and recorded p50/p95/p99/throughput/heap evidence.
