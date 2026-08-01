# ADR-0023: Engine-model evidence admission and visible decision rationale

**Status:** Accepted
**Date:** 2026-08-01
**Decides:** how scheduled Composer/Grok research contributes to the evidence
ledger without requiring owner-side claim entry

## Context

The owner wants the evidence ledger to grow consistently before the final
starting 15 is chosen, while retaining access to why a model selected or
rejected a player. Manual citation entry is not a sustainable operating model.
The model layer can search broadly, but model prose, snippets and community
opinions are not automatically trustworthy evidence.

## Decision

Use a two-stage engine-model run:

1. The model searches every registered official club/competition domain and
   builds a broad watchlist containing comparator candidates, strategy
   alternatives, high expected-point players and official FPL-flagged players.
2. It emits a versioned `model-evidence-run-v1` JSON object containing:
   official claim candidates, source URLs/titles, publication and expiry
   times, exact player IDs, confidence, relevance and a concise decision trace.
3. The deterministic host runs
   `scripts/ingest_model_evidence_run.py`. It checks source rights and policy,
   prompt/catalogue hashes, catalogue coverage, exact identities, official
   domains, timestamps, confidence, injection-like text and ephemeral source
   hashes.
4. The host discards fetched page bodies and appends only valid derived claims
   to a content-addressed availability ledger. Rejections, conflicts,
   duplicates and coverage gaps remain in an audit artifact.
5. The host renders a committed review under `reports/evidence-review/`,
   while the model-authored briefing remains under
   `reports/strategy-research/` or `reports/news-discovery/`. Both are retained:
   the briefing explains the research and the review checks signal capture.
6. Composer is the scheduled production model. Grok or another model may be
   compared by emitting the same contract; its model ID and prompt hash remain
   bound in the audit.

The decision trace records choice, alternatives rejected, opportunity-cost
notes, supporting/conflicting claim IDs, confidence and falsifiers. It is a
concise rationale record, not hidden chain-of-thought.

## Consequences

Positive:

- ledger growth is hands-off and repeatable;
- coverage is broader than the eventual selected 15;
- every admitted claim has source, time, identity and model-run lineage;
- readers can inspect the model's rationale and the host's admission reasons;
- pre-season review can identify weak coverage or a high rejection rate before
  the selected 15 is treated as reliable;
- community research remains useful to the advisory briefing without becoming
  a governed fact.

Trade-offs:

- ephemeral URL fetching still depends on official sites being reachable;
- incomplete catalogue coverage degrades the run rather than blocking valid
  claims;
- the host may reject a model claim even when its prose sounds persuasive;
- raw article text is intentionally unavailable after hashing;
- player-level strategy rationale remains an advisory artefact and is never
  allowed to enforce FPL rules or clear owner approval.
