# FPL-ecy: production line-ups and minutes integration

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Build a provider-neutral capture/reconciliation path that replay and the live
season both call. Official Premier League/club team sheets are canonical primary
truth for published lineups and substitutions. Automated providers remain
optional, cost-gated challengers and may never alter the shared structured
baseline without measured admission evidence.

## Progress

- [x] (2026-07-28) Provider-neutral contract, aliases file, reconcile helper and
  focused tests landed.
- [x] (2026-07-29) Credential-presence probe, degraded family helpers (missing
  credential / timeout / rate-limit / outage), research access-gate matrix and
  blocker bead `FPL-eah`.
- [x] (2026-07-29) Review remediation: exact capture/provider timestamp
  equality, available-before-observed ordering, independent raw-source/envelope
  hashes, activation gating and negative tamper tests.
- [x] (2026-07-31) Official team sheets designated canonical truth; Sportradar
  was tested once with a redacted historical endpoint probe (HTTP 200, 22
  starter rows) but no fixture was admitted or reconciled.
- [x] (2026-07-31) Owner reversed Sportradar enablement because ongoing provider
  cost was not justified. Config and source registry are back to
  `selected_provider=null` and degraded/no-network mode; the credential was
  removed from the user environment.
- [ ] Select and approve a lower-cost alternative, or proceed with official
  team-sheet citation capture only.
- [ ] If a provider is reconsidered, capture at least 10 fixtures across three
  matchdays and apply the 95/99/100/20 promotion gates.

## Surprises & Discoveries

- Observation: Sportradar authentication and endpoint reachability worked, but
  a successful HTTP response was not enough to justify its ongoing cost or
  production use.
- Observation: official team sheets remain the adjudication truth; their capture
  path is manual/citation-only until domain rights and rehearsal are complete.
- Observation: no fixture has been sealed into the immutable provider-neutral
  snapshot contract, so `fixtures_measured` remains 0.

## Decision Log

- Decision: official Premier League/club team sheets are canonical primary truth;
  any future challenger disagreement is quarantined and adjudicated against
  them, with FPL event-live / element-summary as the post-match minutes oracle.
  Date/Author: 2026-07-31 / Codex.
- Decision: reverse Sportradar controlled-trial enablement and remove its user
  credential because ongoing cost is not justified.
  Rationale: the one-off probe proved reachability but did not establish value;
  no production decision depends on it.
  Date/Author: 2026-07-31 / Codex.
- Decision: keep `selected_provider=null` and degrade safely until a lower-cost
  source is explicitly approved and measured.
  Date/Author: 2026-07-31 / Codex.
- Decision: model `observed_at` as the exact host capture time, require
  `available_at <= observed_at`, and hash raw source and normalized envelope
  independently.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

Sportradar was tested once and then disabled by owner decision. The provider
adapter, immutable snapshot contract, timestamp admission, independent digest
layers and degraded failure modes remain available for a future lower-cost
source. Integration remains open on `FPL-eah`.

## Validation

```bash
python -m pytest -q tests/data/test_lineups_minutes.py
```

## Non-goals

Scraping unapproved websites, embedding credentials, name-only identity
fallback, network retry storms, raw-response redistribution, or treating an
HTTP 200/vendor claim as measured production coverage.