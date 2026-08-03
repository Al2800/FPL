# 19 — Implement and benchmark an approved external line-up source

Status: needs-info
Type: task
Track: Phase 2 (expected-minutes evidence)
Blocked by: 13

Missing information: ticket 13 must name and enable a source, define its
permitted collection method and set trial admission thresholds. If the owner
selects “official manual path only”, close this ticket without a collector.

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

No unregistered provider, HTML scraping outside the approved method, API secret
in Git/model context, or silent forecast override.
