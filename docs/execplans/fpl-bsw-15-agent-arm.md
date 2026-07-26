# Implement the First Constrained Evidence-Agent Arm

This ExecPlan is a living document. It must be maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. It is self-contained for a reader
who knows only this repository.

## Purpose / Big Picture

Add independently runnable `evidence_agent` and `evidence_challenger` arms
without giving either model permission to change projections, approve a plan,
read hidden outcomes, or execute FPL actions. The owner selected
`gpt-5.6-sol` through the subscription-backed Codex hosted/subagent surface on
26 July 2026. ChatGPT subscription and API billing remain separate, so this
slice must not introduce an API key or unattended API call.

The repository owns the deterministic boundary. It renders and hashes a
bounded request, accepts a structured hosted result, verifies model, prompt,
tool, evidence, identity, temporal, budget and privacy contracts, then either
exposes proposals to controlled orchestration or falls back to the frozen
`forecast_optimizer` candidate. Cached structured results make evaluation
replayable without resampling the model.

## Progress

- [x] (2026-07-26) Owner selected `gpt-5.6-sol` on the subscription-backed
  Codex hosted surface; API-backed automation was explicitly excluded.
- [x] (2026-07-26) Traced the evidence lifecycle, agent-run trace schema,
  historical replay fallback, approval gate and existing injection cases.
- [x] (2026-07-26) Used a separate `gpt-5.6-sol` review agent to challenge the
  draft against the actual evidence, trace and replay seams.
- [x] (2026-07-26) Added versioned prompts, closed raw-output schemas and a
  hash-bound hosted request/result contract.
- [x] (2026-07-26) Implemented host-grounded citations, baseline-bound
  proposals, independent challenger review, resource checks, host attestation,
  exact deterministic fallback and raw-response caching.
- [x] (2026-07-26) Focused agent and trace suite passes: 42 tests.
- [x] (2026-07-26) Resolved the obsolete WP-10 no-agent guard, passed the
  repository-wide suite (447 tests) and reran the latest agent/contracts slice
  (81 tests).
- [x] (2026-07-26) Added the detailed implementation record and closed
  `FPL-bsw.15`.
- [x] (2026-07-26) Committed as `caba6b3` and pushed `main` to
  `origin/main`.

## Surprises & Discoveries

- Observation: a self-consistent model-generated citation hash proves only
  that the model hashed its own text.
  Evidence: the original golden case passed without any source passage in the
  request. The revised validator requires an exact match to a hash-bound
  passage and hydrates source timestamps from the host.
- Observation: ChatGPT subscription execution does not expose a reliable
  per-run currency meter or model revision.
  Evidence: the trace now records subscription cost as unavailable, requested
  model separately from any reported model, and Codex host version.
- Observation: the legacy trace schema required a fictional tool and model
  call even before provider invocation.
  Evidence: the revised contract accepts zero tools and zero-call degraded
  runs; the focused trace suite remains green.
- Observation: `confidence_downgrade` had no deterministic downgrade formula
  but was treated as accepted.
  Evidence: it now requires human/deterministic resolution and never grants
  the challenger approval authority.

## Decision Log

- Decision: Treat the Codex model invocation as an external hosted step and the
  checked-in Python as its deterministic policy boundary.
  Rationale: the subscription supports GPT-5.6 Sol in Codex, while an arbitrary
  Python process cannot consume ChatGPT subscription credits as API credits.
  Date/Author: 2026-07-26, Codex with owner approval.
- Decision: Use one model call per arm in v1 and no live tools inside the model
  call.
  Rationale: evidence documents are collected and source-gated before the
  agent runs. This makes tool access auditable, avoids browser/session leakage,
  and leaves model capability—not unequal retrieval—as the measured variable.
  Date/Author: 2026-07-26, Codex.
- Decision: A missing, late, over-budget, malformed or unsafe hosted result
  selects the exact deterministic candidate supplied by the caller.
  Rationale: an agent may never delay the deadline or weaken validation.
  Date/Author: 2026-07-26, Codex.
- Decision: Validate citations against host-owned immutable passages and bind
  every proposal to host-owned baseline values.
  Rationale: model-owned text, source metadata or before-values are not
  trustworthy evidence.
  Date/Author: 2026-07-26, Codex after Sol review.
- Decision: The challenger can identify unopposed proposals but cannot approve
  or apply them. Confidence downgrade blocks pending deterministic handling.
  Rationale: approval and transformation are orchestration responsibilities.
  Date/Author: 2026-07-26, Codex after Sol review.

## Outcomes & Retrospective

The implementation is demonstrably working: valid evidence and challenger
outputs produce proposal/review artefacts while leaving the deterministic FPL
candidate byte-for-byte unchanged; unsafe, stale, contradictory, ungrounded,
over-budget or unavailable runs degrade to that exact candidate. The remaining
work is final bead/commit hygiene.
No claim is made that the replay itself launches a model from its historical
episode directory. Hosted invocation must occur in an observed-only execution
surface and return the attested contract implemented here.

## Context and Orientation

`src/evidence/lifecycle.py` owns evidence eligibility, proposed adjustment and
challenger gate rules. `src/agents/evidence_agent.py` and
`src/agents/challenger_agent.py` convert untrusted structured model output into
validated proposal-only records. `src/orchestration/agent_arm.py` binds the
episode, model, prompt, passages, baseline, budget and deterministic fallback,
then creates a replayable run trace. The term “arm” means one independently
measurable benchmark policy configuration. An “observed episode” contains only
information available at the historical decision cutoff; hidden realised
points are excluded.

The raw model result is not trusted. A “host attestation” is a structured claim
from the subscription-backed controller that names its authentication mode,
read-only sandbox, disabled network, exact rendered-input hash and event types.
Unexpected command, file, MCP or web events invalidate the result.

## Plan of Work

Create `src/agents/evidence_agent.py` to render a stable hosted request and
validate cited claims, signals and proposed expected-minutes/start-probability
adjustments against the existing lifecycle. Create
`src/agents/challenger_agent.py` to validate the separately sampled review and
map its declared outcome through `evaluate_challenger_outcomes`.

Create `src/orchestration/agent_arm.py` to enforce the common request identity,
model pin, prompt hash, allowed tools, token/tool/time budgets, unavailable
subscription cost meter, forbidden
fields and output hash. It emits a schema-valid agent-run summary and either
proposal-only output, an independent non-approving challenger review, or an
exact caller-supplied deterministic fallback. It never calls the optimiser,
scorer, browser or FPL website.

Version prompts under `prompts/evidence-agent/` and `prompts/challenger/`.
Golden cases under `evals/golden-cases/agents/` cover valid evidence, stale and
conflicting evidence, unknown players, rule mutation, tool failure, injection
and budget exhaustion. Tests under `tests/agent-evals/` prove each arm can run
alone, the challenger is ablatable, caches replay exactly, and every failure
falls back without modifying the deterministic candidate.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`. Inspect ready/in-progress Beads work before
each milestone. Make edits with small patches. Run the focused agent and trace
tests, then the full repository suite. Record implementation detail on
`FPL-bsw.15` before closing it. Commit only the intended files after
`git diff --check` passes.

## Validation and Acceptance

Run:

    .venv\Scripts\python.exe -m pytest tests/agent-evals -q
    .venv\Scripts\python.exe -m pytest tests/contracts/test_agent_run_trace.py -q
    .venv\Scripts\python.exe -m pytest -q

No package installation, API key, source download or browser execution is
required.

The focused command must report 42 passing tests. A successful valid case must
have `status=completed`, a proposal/review-only authority marker, no applied
adjustments and the unchanged deterministic candidate. Every golden failure
must have `status=degraded`, a schema-valid failure trace and the same candidate.
The full suite must complete without regressions.

## Idempotence and Recovery

All validators and hashes are pure and may be rerun. Cache hits are revalidated
instead of trusted. A corrupt cache entry raises a deterministic cache error;
the controller must select the normal no-agent fallback rather than overwrite
the corrupt entry. No test or implementation step deletes repository data,
downloads dependencies, calls the FPL account or modifies a historical
episode.

## Artifacts and Notes

The key proof transcript at the focused milestone is:

    ..........................................  [100%]
    42 passed

The repository-wide compatibility transcript is:

    ...............                                                          [100%]
    447 passed in 205.93s

The Sol review found the citation-grounding, baseline, trace-honesty and
challenger-authority defects that shaped the final boundary.

## Interfaces and Dependencies

`build_hosted_request(...)` creates the immutable hosted envelope.
`render_hosted_input(request)` produces the exact bytes whose hash is traced.
`cached_or_invoke(...)` caches raw responses by episode/model/CLI/prompt/policy
identity and returns a cache-hit marker without new token usage.
`run_agent_arm(...)` validates the raw response, emits materialised artefacts
and a schema-valid trace, and always leaves `adjustments_applied` empty.
`validate_evidence_result(...)` requires approved evidence and player baseline
maps. `validate_challenger_result(...)` requires exact proposal binding.

These functions use only existing dependencies: Python standard library,
PyYAML and jsonschema. They do not install a provider SDK or require an API key.

Revision note (2026-07-26): expanded the initial plan after the Sol review to
record grounded evidence, truthful subscription trace semantics, cache
revalidation, host attestation, focused test evidence and the remaining
repository-wide validation.
