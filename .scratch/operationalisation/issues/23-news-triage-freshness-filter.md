# 23 — News triage freshness filter

**Blocked by:** None

**Status:** resolved

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

## Answer

**Implemented in `src/ingestion/news_triage.py` + policy v1.1
(2026-08-12).**

- Publication date derived per candidate from `published_at` or URL-path
  dates (`/YYYY/MM/DD/`, `/YYYY/monthname/DD/`; month-only dates resolve
  to month end so exclusion stays conservative).
- Hard exclusions when the policy `freshness` block is present: derivable
  date older than `max_age_days` (14), prior-year stamps in title/URL,
  and non-first-team sections (women/WSL/academy/U21/classic) by URL
  marker or word-bounded title marker. Undatable candidates are kept —
  living pages (e.g. injury lists) carry no date and verification remains
  their arbiter.
- Triage output now records `excluded_candidate_count`,
  `freshness_excluded_count`, `section_excluded_count`, per-candidate
  exclusion reasons, and a `shortlist_freshness` rate for automation to
  flag stale days.
- Acceptance runs: 2026-08-11 capture — 160/398 excluded (121 stale-dated,
  28 prior-year, 11 section). 2026-08-12 capture — 27/47 excluded,
  shortlist 24 → 20 with all three verifiable leads retained.
- Isolated end-to-end test (per the new AGENTS.md convention): filtered
  shortlist → verification gate (3 verified) → discovery (3 admitted) →
  host ingest with a test ledger root seeded from the genesis ledger —
  4/4 claims accepted, chain intact.
- Tests: `tests/ingestion/test_news_triage.py` (exclusion matrix,
  policy-absent back-compat).
