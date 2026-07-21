# ADR-0013: Minimum evidence threshold for proposed adjustments

**Status:** Proposed
**Date:** 2026-07-21
**Decides:** Open Decision 10 (`docs/plan.md` Section 25)

## Context

Open Decision 10 asks what evidence threshold is required before an agent may propose an expected-minutes (or related) adjustment. Without a threshold, agents can emit low-quality noise that looks like evidence-backed change.

## Decision

Phase 1 uses the versioned policy file `control/policies/evidence-adjustments.yaml`:

- minimum claim confidence **0.55** and adjustment confidence **0.60**;
- absolute start-probability delta capped at **0.25** per proposal;
- citation (`provenance.source_ids`), `expires_at`, and at least one supporting `signal_id` are mandatory;
- text quarantined by injection checks cannot produce adjustments.

Orchestration may accept or reject proposals under this policy; agents never apply adjustments themselves.

## Consequences

- Thresholds are data, adjustable by ADR rather than code edits in prompts.
- Live season experience may tighten or loosen values via a superseding ADR.
