# 23 — News triage freshness filter

**Blocked by:** None

**Status:** needs-triage

**Type:** bug

## Summary

The 2026-08-11 one-off Lane A verification run rejected all 24 triage
shortlist rows: every shortlisted official-domain page was prior-season,
an end-of-2025-26 retrospective, women/WSL, a 404 or an empty
bot-challenged body. Zero leads reached discovery and zero claims were
admitted (ledger `96533cd1…`, review
`reports/evidence-review/2026-08-11-adhoc-verification-run.md`).

The triage scorer (`src/ingestion/news_triage.py`) demotes stale years
and historical managers, but with 398 candidates dominated by archive
links the top-24 shortlist was still 100% stale. Verification did its
job, but the shortlist wasted the whole verification budget on pages
that could have been screened out deterministically.

## Proposed work

- Extract or estimate a publication date per candidate at capture or
  triage time (URL path dates, `<time>`/meta tags already present in the
  capture payload) and hard-exclude candidates older than a configurable
  freshness window (e.g. 14 days) rather than merely demoting them.
- Demote or exclude clearly non-first-team sections (women/WSL, academy,
  classic-match retrospectives) via URL-path patterns in the triage
  policy.
- Consider boosting known news-index URLs fetched at capture time so the
  shortlist favours listing pages that link to genuinely new articles.
- Add a triage report metric: shortlist freshness rate, so automation
  can flag a day where the shortlist is predominantly stale.

## Acceptance

A rerun of triage against the 2026-08-11 capture yields a shortlist in
which stale prior-season articles are excluded (not just demoted), and
the triage JSON records how many candidates were excluded on freshness
grounds.
