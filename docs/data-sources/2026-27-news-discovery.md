# 2026/27 governed club and Premier League news discovery

`FPL-469` makes daily discovery reproducible without treating search text as
evidence.  `control/sources/club-news-catalogue.yaml` contains the Premier
League plus all 20 2026/27 clubs.  Each entry currently has the conservative
`official_domain_search_fallback` status: a deterministic domain-restricted
query identifies possible official originals, but it does not automate article
fetching or admit a claim.

## Boundary

- The operator/browser captures only result metadata immediately after the
  recorded `observed_at` time: URL, title, publication timestamp and rank.
- `scripts/discover_evidence_news.py` canonicalises an official HTTPS URL,
  rejects cross-domain/syndicated, stale, future and timestamp-less results,
  and writes an immutable, hashed discovery artifact.
- Search snippets and article bodies are deliberately discarded.  The cited
  original packet contains bounded metadata only.  A human/agent can then read
  and cite the original page and create a linked, derived claim through the
  existing evidence protocol.
- An empty, successfully executed search means no current lead—not no news.
  A missing club search is visible degraded coverage.  It is never converted
  into an availability assertion.

## RSS/API upgrade path

When an exact club feed or supported API is verified, change only that
catalogue row to `verified_rss_or_api`, record its endpoint and validation
evidence, and retain the same timestamp/canonical-URL/immutable-artifact
rules.  This catalogue does not turn `official-club-communications` in the
source registry on: automated claim extraction remains disabled until the
separate source-rights and evidence-admission gate approves it.

## Run

```powershell
python scripts/discover_evidence_news.py --catalogue control/sources/club-news-catalogue.yaml --config config/data_sources/2026-27-news-discovery.json --search-results captured-search-metadata.json --observed-at 2026-08-20T12:00:00Z --output evidence/news-discovery.json --packet-output evidence/cited-originals.json
```

The input JSON is keyed by `club_id`; each result is `{url, title,
published_at, rank}`.  Do not include copied article content in that file.
