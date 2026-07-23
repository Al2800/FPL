# Agent-run trace contract

**Status:** Phase 1 benchmark contract  
**Schema version:** 1.0  
**Applies to:** `evidence_agent` and `evidence_challenger` benchmark arms

## Purpose

An agent result is reproducible only when the recorded context is sufficient to
replay the run without contacting the model or live tools again. The canonical
record is `control/schemas/decisions/agent_runs.json`; a Gameweek-level index of
those records is `control/schemas/benchmark/run-manifest.json`.

This is a trace contract, not an agent implementation and not permission to
select a provider. Open Decision 8 still gates provider-specific runtime code.

## Replay boundary

Each run binds to one immutable `episode_id`, the common observed-episode hash
and the exact snapshot identifiers. It records:

- provider, model identifier, model version and sampling settings;
- code, ruleset, prompt, policy and tool contract versions and hashes;
- hashes and immutable references for rendered context and structured output;
- every tool call in contiguous sequence, with argument hash, versioned tool,
  status, timing and cached result reference;
- every model call in contiguous sequence, with request/response hashes and a
  cached-response reference;
- token, tool-call, wall-clock and currency limits plus actual use;
- completed, degraded or failed status and a structured failure category; and
- trace JSONL location, temporal fields and normal provenance.

A replay resolves the recorded artefact references, verifies every hash and
feeds cached tool/model results back in sequence. It does not resample the model
or re-query a live source. A missing cache artefact or hash mismatch makes the
run non-replayable; it must not be silently regenerated.

## JSONL event order

The referenced trace uses monotonically increasing sequence numbers and may
contain planning, model-call, tool-call, validation, fallback and final-output
events. The summary schema retains the ordered calls required for fast contract
validation; the JSONL artefact retains the complete event history.

## Budgets and degraded operation

Limits and usage are recorded separately for wall-clock milliseconds, tool
calls, input/output/total tokens and currency cost. Runtime enforcement must
stop before a new action would exceed a limit. `budget.exhausted` records the
triggering dimensions.

The structured failure taxonomy is:

- `timeout`;
- `tool_failure`;
- `source_failure`;
- `budget_exhaustion`;
- `provider_failure`;
- `invalid_output`; and
- `policy_denial`.

A degraded evidence run requires a failure record and an explicit
`forecast_optimizer` fallback. A completed run cannot contain a failure. No
failure permits an unregistered source, larger budget or delayed deadline.

## Privacy and secrets

Agent traces must never contain credentials, authorisation headers, cookies,
session state, API tokens, manager personal data, or raw browser material. Raw
prompt and response bodies are also excluded from the summary contract: only
content hashes and access-controlled local artefact references are retained.

Before persistence, runtime code must redact and scan the trace. The record is
valid only with `privacy.redaction_status = passed` and
`prohibited_data_detected = false`. `additionalProperties: false` rejects
uncontracted secret-bearing fields at every structured layer. Cached artefact
storage remains outside Git and inherits the repository retention policy.

## Verification

`tests/contracts/test_agent_run_trace.py` proves that:

- identity, model, prompt, policy, tool, budget and hash fields are mandatory;
- ordered tool calls and cached model responses provide the replay inputs;
- timeout, tool/source failure and budget exhaustion are structured;
- completed/degraded conditional rules hold;
- uncontracted credentials, cookies and personal-data fields are rejected; and
- semantic checks detect non-contiguous sequences and budget overruns.
