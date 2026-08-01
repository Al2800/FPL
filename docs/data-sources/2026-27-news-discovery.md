# 2026/27 governed club and Premier League news discovery

`FPL-469` makes daily discovery reproducible without treating search text as
evidence.  `control/sources/club-news-catalogue.yaml` contains the Premier
League plus all 20 2026/27 clubs.  Each entry currently has the conservative
`official_domain_search_fallback` status: a deterministic domain-restricted
query identifies possible official originals. The model-run host may then
fetch a selected registered URL ephemerally for hashing and admit a derived
claim; it does not retain article bodies or run a bulk scraper.

## Boundary

- The operator/browser captures only result metadata immediately after the
  recorded `observed_at` time: URL, title, publication timestamp and rank.
- `scripts/discover_evidence_news.py` canonicalises an official HTTPS URL,
  rejects cross-domain/syndicated, stale, future and timestamp-less results,
  and writes an immutable, hashed discovery artifact.
- Search snippets and article bodies are deliberately discarded. The cited
  original packet contains bounded metadata only. The scheduled engine model
  may create a structured derived-claim candidate from a registered official
  URL; the host fetches that URL ephemerally for a hash, discards the body and
  appends only candidates that pass exact identity, rights, timestamp and
  confidence validation.
- An empty, successfully executed search means no current lead—not no news.
  A missing club search is visible degraded coverage.  It is never converted
  into an availability assertion.

## RSS/API upgrade path

When an exact club feed or supported API is verified, change only that
catalogue row to `verified_rss_or_api`, record its endpoint and validation
evidence, and retain the same timestamp/canonical-URL/immutable-artifact
rules. Registry `official-club-communications` remains a citation-only source
with a separate model-assisted ephemeral path; bulk scraping and article
retention remain disabled.

## Scheduled web search

Daily discovery is **Lane A** inside the Composer 2.5 strategy research
automation:

- Driver recipe: `config/automations/2026-27-daily-strategy-research.json`
- Driver prompt: `prompts/daily-strategy-research/v1.md`
- Nested discovery prompt: `prompts/daily-news-research/v1.md`
- Loop: `docs/evaluation/2026-27-daily-agent-strategy-loop.md`

Lane A captures search **metadata only**, runs this script, and feeds official
leads into the strategy briefing and model-evidence run. The model proposes;
`scripts/ingest_model_evidence_run.py` performs deterministic admission.
Strategy debate from X/blogs stays in Lane B (briefing only) and can never
enter the governed ledger.

## Run

```powershell
python scripts/discover_evidence_news.py --catalogue control/sources/club-news-catalogue.yaml --config config/data_sources/2026-27-news-discovery.json --search-results captured-search-metadata.json --observed-at 2026-08-20T12:00:00Z --output evidence/news-discovery.json --packet-output evidence/cited-originals.json
```

The input JSON is keyed by `club_id`; each result is `{url, title,
published_at, rank}`.  Do not include copied article content in that file.

The daily strategy automation then emits
`data/live-shadow/evidence/model-runs/YYYY-MM-DD/model-evidence-run.json` and
runs the host gate. The run searches every catalogue club and carries a broad
watchlist; it is not limited to the eventual selected 15. The committed
briefing exposes the resulting ledger/audit hashes and concise decision trace.
