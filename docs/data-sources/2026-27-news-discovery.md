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
rules.  Registry `official-club-communications` is enabled for manual citation
only (see `2026-27-club-communications-citation-decision.md`). This catalogue
still does not automate article fetching or claim extraction.

## Scheduled web search

Daily discovery is **Lane A** inside the Composer 2.5 strategy research
automation:

- Driver recipe: `config/automations/2026-27-daily-strategy-research.json`
- Driver prompt: `prompts/daily-strategy-research/v1.md`
- Nested discovery prompt: `prompts/daily-news-research/v1.md`
- Loop: `docs/evaluation/2026-27-daily-agent-strategy-loop.md`

Lane A captures search **metadata only**, runs this script, and feeds official
leads into the strategy briefing. It does not admit claims. Strategy debate
from X/blogs stays in Lane B (briefing only).

## Run

```powershell
python scripts/discover_evidence_news.py --catalogue control/sources/club-news-catalogue.yaml --config config/data_sources/2026-27-news-discovery.json --search-results captured-search-metadata.json --observed-at 2026-08-20T12:00:00Z --output evidence/news-discovery.json --packet-output evidence/cited-originals.json
```

The input JSON is keyed by `club_id`; each result is `{url, title,
published_at, rank}`.  Do not include copied article content in that file.
