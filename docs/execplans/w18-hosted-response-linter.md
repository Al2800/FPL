# Live Hosted-Response Linting and Bounded Repair

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Move protocol conformance to the trusted host boundary. Before a hosted
evidence or challenger payload can enter semantic validation, deterministically
lint its serialization, schema shape, key names, nesting, identity and episode
bindings. If the default-on policy permits it, expose one actionable repair
request and accept at most one additional hosted response inside the original
ADR-0016 wall-clock and token budgets. A second failure must use the unchanged
forecast-optimizer fallback.

## Progress

- [x] (2026-07-28 20:05Z) Created and claimed `FPL-1co` after checking active
  Beads and file ownership.
- [x] (2026-07-28 20:21Z) Audited the host-owned envelope, agent-arm validation,
  output schemas, ADR-0016, and immutable GW30/GW31/GW33 failure artifacts.
- [x] (2026-07-28 20:25Z) Added the default-on versioned policy, deterministic
  diagnostics and repair request contract.
- [x] (2026-07-28 20:31Z) Added one-retry orchestration with cumulative usage,
  latency and fallback traces.
- [x] (2026-07-28 20:35Z) Added archived failure patterns as golden cases and
  regression tests.
- [x] (2026-07-28 20:44Z) Passed focused, affected and full repository tests.

## Discoveries

- `build_hosted_response` already makes timestamps, attestation, usage and
  hashes host-owned when the model returns a semantic mapping.
- `run_agent_arm` already distinguishes protocol and semantic failures in
  `retry_disposition`, but it does not perform a retry.
- The immutable replay demonstrates repeatable protocol failures: nested claim
  fields, `adjustments` instead of `proposed_adjustments`, an incorrect role
  literal, fractional host timestamps, a response-hash mismatch, and a
  challenger that reviewed the wrong adjustment ID.
- The evidence and challenger JSON Schemas are already the authoritative
  structural contracts. Reusing them avoids a second hand-maintained schema.
- ADR-0016 specifies one-attempt limits today. W18 may add one repair attempt
  only by treating the original limits as cumulative across both calls, never
  as a fresh budget.

## Decisions

- Keep the linter diagnostic-only: it may explain a violation but must never
  silently rename, flatten, fill, delete or otherwise repair semantic content.
- Express diagnostics as stable objects with a code, JSON path, message and
  expected value. Sort them deterministically.
- Bind repair instructions to the original rendered request hash, observed
  episode hash and failed payload hash. The retry cannot receive new evidence
  or wider authority.
- Default the versioned host policy on for live use. A caller may explicitly
  select the rollback switch, which preserves the pre-W18 zero-retry behavior.
- Retry only protocol-repairable failures. Policy denials, grounding failures,
  stale evidence, budget exhaustion and other semantic failures remain
  immediate deterministic fallbacks.
- Record both calls, cumulative resource use, retry reason and elapsed time in
  the result without changing proposal permissions or automatic application.

## Implementation

Extend `src/orchestration/hosted_response.py` with:

- versioned default-on policy resolution and rollback validation;
- schema-backed semantic linting for evidence and challenger outputs;
- envelope/hash/episode-binding linting for externally built envelopes;
- a canonical, hash-bound repair request.

Extend `src/orchestration/agent_arm.py` with one high-level host invocation
entrypoint. It will invoke once, lint and validate, issue one repair request
only when eligible and budget remains, aggregate both call usages, and finally
delegate to the unchanged `run_agent_arm` admission/fallback boundary. Existing
direct `run_agent_arm` callers remain supported for sealed replay artifacts.

## Validation

Focused:

    .\.venv\Scripts\python.exe -m pytest tests/orchestration/test_hosted_response.py tests/agent-evals/test_agent_arm.py -q

Affected orchestration and agent contracts:

    .\.venv\Scripts\python.exe -m pytest tests/orchestration tests/agent-evals -q

Full:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

The live entrypoint now defaults to `hosted-response-lint-v1`, while an
explicit rollback flag restores zero retries. Schema, key, nesting, host
timestamp, request/episode binding, response hash and serialization violations
produce ordered, actionable diagnostics. The repair request is hash-bound to
the original rendered input, observed episode and failed payload and explicitly
forbids new evidence or wider authority.

Only a structurally repairable response may trigger the second call. Grounding,
eligibility, policy and other semantic failures still fall back immediately.
The repair receives the exact remaining budget; trace model calls, cumulative
usage, violation lists and time to accepted decision are preserved. A second
failure and any cumulative budget breach retain the pre-W18 deterministic
candidate without applied adjustments.

Validation completed on 2026-07-28:

- focused hosted-response and agent-arm contracts: 41 passed;
- affected orchestration and agent-evaluation suites: 90 passed in 157.51s;
- complete repository suite: 721 passed in 462.56s.
