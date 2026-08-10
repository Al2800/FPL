# Decision: 2026/27 official club communications evidence path

**Date:** 2026-08-01 (model-run follow-up)
**Outcome:** **official citation path selected and enabled; hands-off model admission added**

## Decision

Unstructured club injury, return-to-training and tactical comments for 2026/27
use official club public pages via the **manual citation** path or the bounded
**model-assisted ephemeral citation** path. Bulk HTML scrape, article
retention and paid challengers remain off.

Because `official-club-communications` is registered with confirmed restricted
citation rights, the path is enabled:

- registry `official-club-communications`: `enabled: true`
- capture method: manual citation plus one-URL-at-a-time model-run citation
  (no bulk HTML scrape, no API)
- live evidence admission: already `manual_citation` / `admitted: true` in
  `config/data_sources/2026-27-evidence.json`
- model-run admission: `model_assisted_citation` / `admitted: true` in
  `config/data_sources/2026-27-model-evidence-run.json`

## Rights / cost

- Source: `official-club-communications` (registry 0.6.3+)
- Licence: restricted; allowed use private analysis citation only
- Cost: zero (manual or engine-model citation; no paid provider)
- Owner: Alastair, 2026-07-31
- Scope: metadata and derived claims only; ephemeral source hash then discard;
  no redistribution; no bulk HTML scrape

## Hands-off model-run controls

The Composer strategy run (and any Grok run using the same schema) searches the
whole official club catalogue and a broad player watchlist before selecting a
15. It emits candidates plus a concise decision trace. The deterministic host
then:

1. checks prompt and catalogue hashes;
2. requires exact current player identity and registered official domains;
3. fetches each cited URL ephemerally for a content hash;
4. discards the page body;
5. appends only valid claims to a content-addressed ledger; and
6. writes an audit containing accepted/rejected candidates, coverage gaps and
   the model's rationale trace.

The owner does not append claims. Model prose and community sources remain
briefing material and cannot bypass the host gate.

## What this does not unlock

- Bulk automated claim extraction from club sites
- Verbatim full-article retention
- Treating news-discovery search snippets as evidence
- Closing an evidence gap when no valid citation exists
