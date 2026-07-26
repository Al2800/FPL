# Make Agent Attempts Host-Owned and Fail Closed Before Scoring

This ExecPlan is a living document. The sections `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to
date as work proceeds. It is maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a model supplies only the football-specific structured
answer it was asked to reason about. Trusted repository code supplies the
provider identity, request and response hashes, completion time, execution
attestation and usage record. A malformed or rejected attempt remains
available as an immutable diagnostic artifact, but no shared agent-fork
entrypoint can solve or score a gameweek unless both the evidence and
challenger runs completed successfully.

This removes an ambiguity exposed during the 2025/26 replay. Previously a
degraded run could silently select the deterministic solver input and continue
through the agent-fork scorer. The resulting week looked scored even though
the agent gate had failed. The focused tests demonstrate the new behavior by
building the same host envelope twice with identical results and by proving
that degraded runs raise before any solver output is written.

## Progress

- [x] (2026-07-26 22:15+01:00) Inspected the agent arm, fork adapter, trace
  schema, committed replay artifacts and existing compatibility tests.
- [x] (2026-07-26 22:23+01:00) Added failing tests for deterministic
  host-owned envelopes, retry classification and hard completion-gate refusal.
- [x] (2026-07-26 22:28+01:00) Implemented the host-owned response builder and
  semantic-payload entrypoint.
- [x] (2026-07-26 22:32+01:00) Enforced the shared completion gate before
  adjustment, solving, file output or hidden-outcome scoring, including
  refusal of hash and proposal-binding tampering.
- [x] (2026-07-26 22:35+01:00) Recorded the gate in both the live-shadow
  candidate generator and checked-in policy, then verified its self-hash.
- [x] (2026-07-26 22:43+01:00) Passed 41 focused tests, 89 wider agent/trace
  tests, and the full repository suite of 494 tests; `git diff --check` passed.
- [x] (2026-07-26 22:47+01:00) Added the implementation record, closed
  `FPL-bsw.32`, and committed the implementation as `9c88e0b`.

## Surprises & Discoveries

- Observation: `apply_agent_adjustments` currently detects a non-completed run
  but returns the unchanged solver input instead of refusing the operation.
  Evidence: lines 565-568 of `src/orchestration/agent_fork_adapter.py` return
  fallback reasons `evidence_run_not_completed` and
  `challenger_run_not_completed`; both public fork runners then call the solver
  and outcome scorer.
- Observation: historical accepted response artifacts already contain the
  full legacy hosted envelope.
  Evidence: `run_agent_arm` validates these fields directly, so the new
  semantic-payload entrypoint must be additive and keep the legacy validation
  path readable.
- Observation: merely checking `status=completed` is insufficient if the run
  hash, validated output or proposal binding has been tampered with.
  Evidence: the shared boundary now rejects those cases as errors, while the
  existing completed blocked-challenger test still proves that a legitimate
  policy abstention returns the unchanged deterministic input.

## Decision Log

- Decision: Keep `run_agent_arm` as the compatibility validator for existing
  hosted response artifacts and add a new entrypoint that accepts only a
  semantic payload and constructs the envelope in trusted code.
  Rationale: this fixes future operation without invalidating immutable
  historical runs.
  Date/Author: 2026-07-26, Codex.
- Decision: Require callers to supply a whole-second UTC completion timestamp
  to the host builder.
  Rationale: using the current clock inside the builder would make identical
  inputs produce different envelopes, while allowing the model to supply the
  timestamp would make trusted metadata model-owned.
  Date/Author: 2026-07-26, Codex.
- Decision: Raise `EvidenceForkError` for any non-completed input at the common
  adjustment boundary.
  Rationale: every present shared scoring route crosses that boundary, and a
  raised error makes it impossible to confuse an agent failure with a scored
  deterministic fallback.
  Date/Author: 2026-07-26, Codex.
- Decision: Treat invalid hashes, missing validated outputs and inconsistent
  proposal bindings as hard refusal conditions even when a record claims
  `status=completed`.
  Rationale: status is a claim inside the artifact; integrity and binding must
  be proven independently before hidden outcomes are accessible.
  Date/Author: 2026-07-26, Codex.

## Outcomes & Retrospective

The executable work is complete. Models can now return semantic output without
constructing trusted metadata, and repeated host construction is deterministic
for the same completion observation and usage. Rejected attempts remain
hash-bound diagnostic artifacts with protocol, semantic or execution retry
dispositions. Both shared fork runners refuse degraded or tampered inputs
before writing or scoring, while existing completed replay artifacts still
reproduce.

The deterministic control fallback remains available outside the agent scoring
path, and a successfully completed challenger may still abstain through its
explicit approval gate. This distinction prevents a failed agent run from
being reported as an agent result without compromising deadline-safe control
operation.

## Context and Orientation

`src/orchestration/agent_arm.py` validates one evidence-agent or
evidence-challenger attempt. A “semantic payload” is the football-specific
JSON object produced by the model: claims and projection reductions for the
evidence arm, or review findings for the challenger. A “host-owned envelope”
is the trusted metadata wrapped around that payload by repository code.

`src/orchestration/agent_fork_adapter.py` is the bridge from completed agent
runs into the deterministic optimiser and the hidden-outcome scorer.
`apply_agent_adjustments`, `run_sequential_agent_fork_week`, and
`run_isolated_agent_fork` are shared public entrypoints. A “completion gate”
means that both supplied agent run records must have a valid immutable hash,
`status` equal to `completed`, and a validated semantic output before any
adjustment or scoring may proceed.

`control/policies/live-shadow-candidate.json` is the checked-in policy for the
future 2026/27 observation-only shadow. It must explicitly name the hard
completion gate so live orchestration cannot reinterpret a degraded attempt
as an evidence decision.

## Plan of Work

Create `src/orchestration/hosted_response.py`. Its pure
`build_hosted_response` function will accept a hash-bound request, semantic
structured output, whole-second UTC completion time and optional host-observed
usage. It will validate these inputs and deterministically construct provider
identity, hashes, read-only attestation, fixed allowed event types and
subscription cost semantics.

Add `run_hosted_semantic_payload` to
`src/orchestration/agent_arm.py`. It will call the builder and then the existing
validator. The existing `run_agent_arm` interface remains supported for
reading committed artifacts. For rejected attempts, add a hash-bound
`retry_disposition` to the result so callers can distinguish protocol
failures, semantic validation failures and external execution failures without
changing the already-versioned trace failure schema.

Change `apply_agent_adjustments` in
`src/orchestration/agent_fork_adapter.py` to validate hashes and reject
non-completed or missing validated runs by raising `EvidenceForkError`.
Policy-safe abstention by a successfully completed challenger remains a normal
unchanged-input result. Because both fork runners call this function before
the solver, this is the single shared refusal boundary.

Extend `tests/agent-evals/test_agent_arm.py` and
`tests/agent-evals/test_agent_fork_adapter.py`. The tests will prove
determinism, host ownership, timestamp rejection, legacy compatibility,
protocol-versus-semantic classification and no-output refusal. Update the live
shadow policy and its self-hash after the executable behavior is green.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`. Before each new bead, inspect Beads and claim
only open work. For this bead, run:

    .venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_arm.py tests/agent-evals/test_agent_fork_adapter.py -q

Then run the wider agent and contract tests:

    .venv\Scripts\python.exe -m pytest tests/agent-evals tests/contracts/test_agent_run_trace.py -q

Finally run:

    .venv\Scripts\python.exe -m pytest -q
    git diff --check

Record exact passing counts here when known. Add a detailed implementation
comment to `FPL-bsw.32` before closing it.

## Validation and Acceptance

Calling `build_hosted_response` twice with the same request, semantic output,
completion time and usage must return equal dictionaries and equal hashes.
The response hash must equal the canonical hash of the semantic output, and
the request hash and attestation must equal the host-rendered request hash.
A fractional or offset completion timestamp must raise before an agent run is
created.

Calling `run_hosted_semantic_payload` with a valid evidence payload must return
`status=completed`. A malformed semantic payload must retain an immutable
response artifact, return `status=degraded`, and expose a semantic retry
classification. Tampered legacy wrapper metadata must expose a protocol retry
classification.

Calling `apply_agent_adjustments`, `run_isolated_agent_fork`, or
`run_sequential_agent_fork_week` with either run degraded must raise
`EvidenceForkError`. In the runner test the intended output directory must
remain absent, proving refusal occurred before file output or scoring.
Completed, valid historical artifacts must continue to reproduce their
existing result.

## Idempotence and Recovery

The builder and validators are pure and safe to rerun. Tests use temporary
directories and do not mutate canonical replay artifacts. The implementation
does not delete data, download packages, access an FPL account or call a model.
If validation fails, fix the smallest boundary and rerun the focused tests;
do not rewrite committed historical response files.

## Artifacts and Notes

The final validation transcripts were:

    41 passed in 8.50s
    89 passed in 29.45s
    494 passed in 236.68s (0:03:56)
    live-shadow policy hash verified

`test_shared_fork_runners_refuse_degraded_run_without_writing` covers both
public fork runners and asserts that neither output directory exists after
refusal.

## Interfaces and Dependencies

In `src/orchestration/hosted_response.py`, provide:

    class HostedResponseError(ValueError): ...

    def build_hosted_response(
        *,
        request: Mapping[str, Any],
        structured_output: Mapping[str, Any],
        completed_at: str,
        usage: Mapping[str, Any] | None = None,
        model_version: str = "gpt-5.6-sol",
        cli_version: str = "host-owned-envelope-v1",
        cache_hit: bool = False,
    ) -> dict[str, Any]: ...

In `src/orchestration/agent_arm.py`, provide:

    def run_hosted_semantic_payload(
        *,
        request: Mapping[str, Any],
        semantic_output: Mapping[str, Any],
        completed_at: str,
        deterministic_candidate: Mapping[str, Any],
        code_commit: str,
        evidence_proposal: Mapping[str, Any] | None = None,
        usage: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]: ...

Use only the standard library and existing repository hashing and validation
functions. No dependency installation is needed.

Revision note (2026-07-26): created after inspecting the live agent and fork
boundaries; records the additive compatibility design and the hard refusal
decision.

Revision note (2026-07-26): updated after implementation to record strict
integrity refusal, final interfaces, policy generation, and all validation
evidence.

Revision note (2026-07-26): recorded bead closure and implementation commit
after the final repository-wide validation.
