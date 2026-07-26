# Agent-run trace contract

**Status:** Phase 1 benchmark contract
**Schema version:** 1.0
**Applies to:** `evidence_agent` and `evidence_challenger` benchmark arms

## Purpose

An agent result is reproducible only when the recorded context is sufficient to
replay the run without contacting the model or live tools again. The canonical
record is `control/schemas/decisions/agent_runs.json`; a Gameweek-level index of
those records is `control/schemas/benchmark/run-manifest.json`.

Open Decision 8 was resolved by the owner on 26 July 2026:
`gpt-5.6-sol` runs through a ChatGPT-subscription-authenticated Codex host.
`src/orchestration/agent_arm.py` is the deterministic ingestion and validation
boundary. It does not use an API key, execute FPL changes, or grant the model
write authority.

## Replay boundary

Each run binds to one immutable `episode_id`, the common observed-episode hash
and the exact snapshot identifiers. It records:

- provider, subscription authentication mode, Codex host version, requested
  model, reported model when available, and reasoning effort;
- code, ruleset, prompt, policy and tool contract versions and hashes;
- hashes and immutable references for rendered context and structured output;
- every tool call in contiguous sequence, with argument hash, versioned tool,
  status, timing and cached result reference;
- every model call in contiguous sequence, with request/response hashes and a
  cached-response reference;
- token, tool-call and wall-clock limits plus actual use; subscription cost is
  explicitly unavailable rather than a fictional zero charge;
- completed, degraded or failed status and a structured failure category; and
- trace JSONL location, the decision cutoff, actual run time,
  retrospective/live mode and normal provenance.

A replay resolves the recorded artefact references, verifies every hash and
feeds the cached raw model result through the closed output schema and all
deterministic semantic checks. It does not resample the model or re-query a live
source. A missing, corrupt or version-stale cache selects the exact
deterministic fallback; it is never silently trusted or regenerated as the same
run.

The hosted input contains only immutable, hash-verified passages, known player
identities and their deterministic baselines. Source identity and source
timestamps are hydrated by the host. A citation must exactly match an approved
passage. Hidden-outcome references, credentials and authority-bearing output
fields are rejected.

## JSONL event order

The referenced trace uses monotonically increasing sequence numbers and may
contain planning, model-call, tool-call, validation, fallback and final-output
events. The summary schema retains the ordered calls required for fast contract
validation; the JSONL artefact retains the complete event history.

## Budgets and degraded operation

Limits and usage are recorded separately for wall-clock milliseconds, tool
calls and input/output/total tokens. One hosted attempt is allowed. A
postflight overrun rejects the result and records the triggering dimensions in
`budget.exhausted`. Subscription execution does not expose a monetary meter,
so the trace records `metering_status: unavailable`. A real currency cap would
require an API-backed provider selected later.

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
prompt and response bodies are excluded from the summary contract. The
returned run object materialises the hash-bound raw response and validated
output separately so a cache store can persist them outside Git.

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

`tests/agent-evals/test_agent_arm.py` additionally proves passage grounding,
host-owned timestamps, baseline/range validation, contradiction and injection
blocking, strict output schemas, challenger ablation, proposal binding, host
attestation, honest zero-call failure, deterministic fallback and hash-verified
cache replay.
