# Decision: 2026/27 official club communications evidence path

**Date:** 2026-07-31  
**Outcome:** **official citation path selected and enabled**

## Decision

Unstructured club injury, return-to-training and tactical comments for 2026/27
use official club public pages via the **manual citation** path. Automated HTML
scrape, bulk article retention and paid challengers remain off.

Because `official-club-communications` is registered with confirmed restricted
citation rights, the path is enabled:

- registry `official-club-communications`: `enabled: true`
- capture method: **manual citation only** (no automated HTML scrape, no API)
- live evidence admission: already `manual_citation` / `admitted: true` in
  `config/data_sources/2026-27-evidence.json`
- automated adapter status: `disabled_manual_citation_only`

## Rights / cost

- Source: `official-club-communications` (registry 0.6.3+)
- Licence: restricted; allowed use private analysis citation only
- Cost: zero (manual citation; no paid provider)
- Owner: Alastair, 2026-07-31
- Scope: manual citation capture; metadata and derived claims only; no
  redistribution; no HTML scrape

## What this does not unlock

- Automated claim extraction from club sites
- Verbatim full-article retention
- Treating news-discovery search snippets as evidence
- Closing an evidence gap when no valid citation exists
