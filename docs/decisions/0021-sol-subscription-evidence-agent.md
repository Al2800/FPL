# ADR-0021: GPT-5.6 Sol on the subscription-hosted Codex surface

**Status:** Accepted
**Date:** 2026-07-26
**Ratified:** 2026-07-26
**Owners:** Project owner
**Decides:** Open Decision 8
**Related:** ADR-0010, ADR-0013, ADR-0016, ADR-0017

## Context

The benchmark kernel defines evidence and challenger arms but deliberately
deferred provider-specific work until the owner selected a model and access
surface. ChatGPT subscription access and OpenAI API billing are separate. The
project needs a first measurable model arm without introducing an API secret,
giving an agent account access, or weakening deterministic replay.

## Decision

Use `gpt-5.6-sol` through the ChatGPT-subscription-authenticated Codex subagent
surface for the first constrained evidence and challenger arms.

The model receives only a hash-bound, observed-only bundle of approved evidence
passages, player identities and deterministic baseline values. It has no live
tools, network, browser, account credentials, hidden outcomes or write
authority. It may propose evidence adjustments or independently review them.
It may not apply, approve or execute anything.

The repository validates the returned structured object against a closed
schema, grounds citations against host-owned passages and timestamps, enforces
resource limits, caches the raw response by full run identity and falls back to
the exact deterministic candidate on any failure. Subscription cost is recorded
as unavailable because this surface has no reliable per-run monetary meter.

## Consequences

The project can now measure the value added by Sol's unstructured-evidence
reasoning while preserving the deterministic engine as the safety boundary.
Single-agent and challenger configurations remain separate ablations.

This decision does not add an API key, permit unattended account execution or
authorise the model to select a final FPL plan. A future API-backed arm would
need a separate provider decision, secret handling and hard monetary budget.

Historical runs must stage only observed evidence. They must never launch the
agent from a directory containing the hidden-outcome partition.

## Alternatives considered

1. Use an OpenAI API key immediately. Rejected because the owner selected the
   existing subscription surface and subscription/API billing are separate.
2. Give the model live web or browser tools. Rejected for the first arm because
   unequal retrieval and session leakage would confound the model comparison.
3. Treat model output as an approved forecast change. Rejected because proposal,
   review, deterministic application and execution are distinct authorities.

Ratified by the project owner on 26 July 2026.
