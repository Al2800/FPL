# FPL-469 — Governed club and Premier League news discovery

## Intent

Discover current official club and Premier League news without treating search
content as evidence. The output is a replayable, time-stamped list of cited
official originals for manual derived-claim admission.

## Rules

- Maintain one 2026/27 catalogue entry for the Premier League and every 20
  club, with exact official domain and source status.
- Prefer a verified RSS/API endpoint when explicitly catalogued. Until then,
  use a fixed `site:` query against the official domain.
- Preserve query, source, rank, observed timestamp, URL, and publication time.
- Drop snippets, reject non-official domains, canonicalise URLs, and deduplicate
  syndicated/duplicate results.
- A lead is not a claim. The receiving agent follows the official URL and may
  create only a linked, rights-governed derived claim.
- Missing or stale discovery remains an explicit gap, interpreted as unknown.

## Verification

- Catalogue has exactly 20 clubs plus the Premier League source.
- Plans and outputs reproduce byte-for-byte from the same inputs.
- Query/rank/time provenance is retained.
- Cross-domain, stale, duplicate, and snippet-only input cannot enter the cited
  original packet.

