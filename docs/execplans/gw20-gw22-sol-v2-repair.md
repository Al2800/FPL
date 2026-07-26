# Repair the challenger contract and rerun GW20-GW22 as sol-v3

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

The historical evidence fork must distinguish a genuine agent decision from a safe deterministic fallback. GW20, GW21, and GW22 were recorded under `sol-v1`, but their challenger responses used the wrong JSON types and therefore degraded to the forecast optimiser. An initial `sol-v2` repair correctly completed GW20 but exposed a second hash-encoding failure at GW21. After this repair, a reviewer can inspect a separate `sol-v3` trajectory whose evidence and challenger stages completed successfully, while both earlier degraded versions remain immutable evidence of the failures.

## Progress

- [x] (2026-07-26 17:15+01:00) Diagnose the challenger schema mismatch and create Bead `FPL-xym`.
- [x] (2026-07-26 17:16+01:00) Confirm that no other Bead owns the affected files and claim the repair.
- [x] (2026-07-26 17:18+01:00) Add version-aware orchestration without changing any `sol-v1` artifact.
- [x] (2026-07-26 17:19+01:00) Add initially failing regression contracts that distinguish completed agent runs from fail-closed fallback runs.
- [x] (2026-07-26 17:22+01:00) Preserve the partial `sol-v2` diagnostic after its GW21 response-hash failure.
- [x] (2026-07-26 17:31+01:00) Run fresh GPT-5.6 Sol evidence and challenger stages for the clean `sol-v3` GW20-GW22 trajectory.
- [x] (2026-07-26 17:33+01:00) Complete and compare the legal `sol-v3` state chain.
- [x] (2026-07-26 17:38+01:00) Prove immutability, repeatability, terminal behavior, and pass 469 repository tests.
- [x] (2026-07-26 17:39+01:00) Close Bead `FPL-xym` and prepare the verified repair for commit and push to `main`.

## Surprises & Discoveries

- Observation: the model judgments were semantically suitable, but their transport objects violated the repository contract.
  Evidence: `prompts/challenger/output.schema.json` requires `notes` to be a non-empty string and permits only `dismissed`, `confidence_downgrade`, `forced_re_run`, or `escalation`. The GW20-GW22 wrappers used arrays for `notes`.

- Observation: the existing tests correctly allowed fail-closed execution but did not require these named experimental runs to complete.
  Evidence: the full suite passed while `challenger-run.json` reported `status: degraded` for GW20-GW22.

- Observation: manually hashing a structured response with Python's default JSON settings is unsafe when the response contains non-ASCII punctuation.
  Evidence: the GW21 `sol-v2` response contained curly quotation marks. Its default `ensure_ascii=True` hash differed from the repository's `artifact_hash`, which uses UTF-8 with `ensure_ascii=False`; the host therefore recorded `model_response_hash_mismatch`.

## Decision Log

- Decision: preserve `sol-v1` and write the repair under `sol-v2`.
  Rationale: sealed experimental failures are useful audit evidence and must not be rewritten after the outcome is known.
  Date/Author: 2026-07-26 / Codex.

- Decision: start `sol-v2` from the exact GW20 starting state used by `sol-v1`, then chain its own GW21 and GW22 successors.
  Rationale: this isolates the contract repair from all earlier trajectory differences.
  Date/Author: 2026-07-26 / Codex.

- Decision: require completed evidence and challenger statuses in the version-specific benchmark contract.
  Rationale: generic production orchestration should retain safe fallback, but an experiment labelled as an evidence-agent run must make degradation explicit rather than silently count it as successful agent evidence.
  Date/Author: 2026-07-26 / Codex.

- Decision: preserve the successful GW20 and failed GW21 `sol-v2` artifacts and promote the clean full rerun to `sol-v3`.
  Rationale: write-once audit artifacts must not be edited or deleted after a failure. A complete version must also use one consistent namespace from GW20 through GW22.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The clean `sol-v3` trajectory completed every evidence and challenger gate and applied all three proposed reductions. GW20 reduced Rodon to zero expected minutes but left the plan unchanged because he was benched; it scored 49 versus 65 canonical. GW21 reduced unowned Gvardiol to zero and left the Woltemade-to-Igor transfer unchanged; it scored 57 versus 55. GW22 reduced owned Guéhi to zero, which added a free Guéhi-to-Gabriel transfer alongside Cunha-to-Bruno Guimarães. That plan scored 49 versus 44 for its same-state control and 47 canonical.

The repaired GW20-GW22 slice scored 155 versus 167 canonical, improving the degraded `sol-v1` slice by five points. Keeping the valid GW18-GW19 results, the experimental trajectory through GW22 now stands at 562 versus 566 canonical, a four-point deficit rather than nine.

Every `sol-v3` comparison hash remained identical across an aggregate rerun. Tests preserve the exact `sol-v1` and partial `sol-v2` trees, require completed agent gates and applied adjustments for `sol-v3`, bind GW20 to the original frozen state, prove the GW20-GW22 successor chain, and prove the terminal GW22 boundary. Focused contracts passed 8/8; the full repository suite passed 469/469 in 213.48 seconds.

The two failed versions demonstrated that fail-closed orchestration worked correctly, but also exposed a benchmark-observability gap: safe degradation could previously pass the suite without a named experiment asserting completion. That gap is now closed. The broader performance diagnosis remains unchanged for GW20: the 16-point loss is an inherited Woltemade-versus-Igor state difference, not an evidence failure.

## Context and Orientation

The runner `scripts/run_gw18_gw22_agent_forks.py` currently writes only `reports/benchmarks/2025-26-agent-forks/gw-NN/sol-v1`. It creates a frozen evidence request, validates a hosted evidence response, creates an independent challenger request, validates the hosted challenger response, adjusts player projections only when the challenger leaves every proposal unopposed, solves the squad decision, reveals the hidden result, and transitions the manager state.

The phrase “fail closed” means an invalid or unavailable model response cannot change the deterministic projections. The orchestration deliberately substitutes its deterministic forecast candidate and records `status: degraded`. That behavior is correct for availability, but it is not equivalent to a completed evidence experiment.

The canonical challenger schema is `prompts/challenger/output.schema.json`. In particular, `notes` is one string rather than a list, and `dismissed` means the challenger found no reason to oppose the proposed adjustment.

## Plan of Work

Make the existing runner accept an artifact version. Retain the current `sol-v1` defaults for compatibility. For repaired versions, support only GW20-GW22, bind the GW20 start to the already frozen `sol-v1` GW20 starting state, and read later successors from the preceding directory of the same version. Rebuild hosted request identities with versioned run IDs and write the prepared host bundle to a version-specific evaluation filename.

Extend `tests/agent-evals/test_agent_fork_gw18_gw22.py` with contracts that snapshot every `sol-v1` file hash before the repair, require `sol-v2` evidence and challenger runs to be completed, require every proposed adjustment to appear in the adapter audit, require a continuous state chain, and require no GW23 successor.

Use fresh GPT-5.6 Sol subscription subagents for each evidence and challenger response. Provide the canonical schema vocabulary directly in each prompt. Compute response hashes through the repository's `artifact_hash` implementation rather than an adjacent JSON encoder. Complete GW20 before preparing GW21, and complete GW21 before preparing GW22, because each manager state depends on the preceding validated plan and outcome.

Finally rerun the versioned command and compare artifact hashes before and after. Run the focused contracts and complete repository suite. Record both point totals and the exact reason for any difference from `sol-v1`.

## Concrete Steps

From `C:/Users/Alastair/FPL`:

    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --artifact-version sol-v3 --mode prepare --gameweek 20
    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --artifact-version sol-v3 --mode validate-evidence --gameweek 20
    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --artifact-version sol-v3 --mode complete-week --gameweek 20

Repeat those stages sequentially for GW21 and GW22. Then run:

    .\.venv\Scripts\python.exe -m scripts.run_gw18_gw22_agent_forks --artifact-version sol-v3 --mode complete
    .\.venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_gw18_gw22.py -q
    .\.venv\Scripts\python.exe -m pytest -q

## Validation and Acceptance

All existing `sol-v1` file hashes must remain identical to commit `fa509e4`, and the partial `sol-v2` diagnostic hashes must remain frozen. Each `sol-v3/evidence-run.json` and `sol-v3/challenger-run.json` must report `status: completed`. The adapter audit must report `applied: true` whenever the evidence run proposed an adjustment and the challenger dismissed it. The GW21 starting-state hash must equal the GW20 successor, and the GW22 starting-state hash must equal the GW21 successor. GW22 must not write a next-policy-state file.

The exact repeat command must preserve every `sol-v3/comparison.json` hash. Every canonical gameweek tree hash must be identical before and after. The focused test and complete repository suite must pass.

## Idempotence and Recovery

All artifact writes are write-once. A rerun with identical inputs is safe; changed bytes fail rather than overwrite prior evidence. If a hosted response fails validation, retain the degraded artifact and diagnose it before continuing the state chain. Never delete or alter `sol-v1` or the partial `sol-v2` diagnostic.

## Artifacts and Notes

The repaired results live under `reports/benchmarks/2025-26-agent-forks/gw-20/sol-v3` through `gw-22/sol-v3`. Prepared bundles use `evals/evidence-forks/2025-26/gw-NN/agent-host-bundle-sol-v3.json`. The partial `sol-v2` tree remains as a diagnostic record.

## Interfaces and Dependencies

No package is added. `scripts.run_gw18_gw22_agent_forks` gains `--artifact-version` with `sol-v1` as the compatibility default and additive repaired versions for audit-safe retries. Existing orchestration functions in `src/orchestration/agent_arm.py` and `src/orchestration/agent_fork_adapter.py` remain the authority for schema validation, fallback, scoring, and state transition.

Revision note (2026-07-26): Initial plan written after the degraded challenger diagnosis and before implementation. Revised after the partial `sol-v2` run exposed a non-ASCII canonical-hash mismatch; the clean complete rerun is now `sol-v3`.
