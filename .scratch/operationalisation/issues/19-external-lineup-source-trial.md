# 19 — Implement and benchmark an approved external line-up source

Status: ready-for-agent
Type: task
Track: Phase 2 (expected-minutes evidence)
Blocked by: 13

Approved by ticket 13 / ADR-0025 (5 August 2026):

- **Source:** `rotowire-lineups` (RotoWire predicted/confirmed Premier League
  line-ups)
- **Collection method:** `manual_citation` only — no crawl, spider, scrape or
  unofficial API (terms: https://www.rotowire.com/termsandconditions.php)
- **Adjudication truth:** official team sheets (`official-lineups-minutes`)
- **Fallback:** byte-identical structured forecast; quarantine disagreements;
  never average feeds
- **Admission before live influence:** coverage, identity match, start
  calibration vs “started last GW” and `chance_of_playing`, confirmed-minutes
  accuracy vs FPL post-match oracle, latency of citation workflow, failure
  behaviour — thresholds to be set in the ticket-19 preregistration before the
  first scored trial window
- **Consolidator:** merge official citations + Rotowire citations + FPL
  availability flags only through the governed evidence-adjustment policy

## Scope after approval

- Implement only the registry-authorised collection method under the
  acquisition contract.
- Preserve publication, observation, effective and finalisation timestamps,
  source identity, content hash and correction history.
- Benchmark start probability against “started last Gameweek” and official
  `chance_of_playing`; benchmark confirmed minutes against the official FPL
  post-match oracle.
- Quarantine disagreements and retain the official team sheet as adjudication
  truth; never average feeds.
- Feed a source into expected minutes only through the governed evidence-
  adjustment policy and with a byte-identical baseline fallback.

## Done when

- Coverage, identity matching, start calibration, final-minutes accuracy,
  latency, quota headroom and failure behaviour meet the owner-approved
  thresholds over the preregistered fixture sample.
- A failed trial leaves the source disabled for live influence and records the
  negative result.

## Boundaries

No unregistered provider, HTML scraping, API secret in Git/model context, or
silent forecast override.
