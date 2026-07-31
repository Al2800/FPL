# FPL-ecy: production line-ups and minutes integration

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Build a provider-neutral capture/reconciliation path that replay and the live
season both call. Official Premier League/club team sheets are canonical primary
truth for published lineups and substitutions. Sportradar is the automated,
trusted challenger. Trial enablement is allowed only inside the explicit local
trial boundary; production promotion remains gated on measured evidence.

## Progress

- [x] (2026-07-28) Provider-neutral contract, aliases file, reconcile helper and
  focused tests landed.
- [x] (2026-07-29) Credential-presence probe, degraded family helpers (missing
  credential / timeout / rate-limit / outage), research access-gate matrix and
  blocker bead `FPL-eah`.
- [x] (2026-07-29) Review remediation: exact capture/provider timestamp
  equality, available-before-observed ordering, independent raw-source/envelope
  hashes, activation gating and negative tamper tests.
- [x] (2026-07-31) Two-track policy: official team sheets are canonical primary
  truth; `sportradar-soccer` is the automated challenger; API-Football and
  football-data.org remain fallback-only.
- [x] (2026-07-31) Owner-authorized controlled trial enabled with
  `SPORTRADAR_API_KEY`. Redacted probes reached the competition, seasons,
  schedule and lineup endpoints; one coverage-shaped historical payload
  returned HTTP 200 with two competitors and 22 starter rows. No raw response
  or credential was retained.
- [ ] Capture at least 10 Premier League fixtures across at least three
  matchdays through the immutable provider-neutral snapshot contract and compare
  each against official team sheets and the FPL post-match oracle.
- [ ] Promote the challenger to production only after the 95/99/100/20 gates
  pass and the owner signs off the measured matrix.

## Surprises & Discoveries

- Observation: Sportradar trial authentication and endpoint reachability work
  with the owner-provided key. Trial season metadata exposes 2025/26 and
  2026/27; the 2025/26 schedule advertised pre-match lineups for 395 events.
- Observation: official team sheets remain the adjudication truth; their capture
  path is manual/citation-only until domain rights and rehearsal are complete.
- Observation: the historical lineup endpoint can return a valid payload while
  substitutions/minutes still require explicit mapping and post-match
  reconciliation; HTTP 200 is not an admission result.

## Decision Log

- Decision: official Premier League/club team sheets are canonical primary truth;
  Sportradar is the automated challenger trial. Do not average disagreements:
  quarantine and adjudicate against the official sheet, with FPL event-live /
  element-summary as the post-match minutes oracle.
  Date/Author: 2026-07-31 / Codex.
- Decision: enable Sportradar only in `controlled_trial` mode for local,
  non-redistributed captures; keep production promotion blocked until the
  measured matrix passes.
  Rationale: the owner explicitly requested a credential test, while the
  provider-neutral admission gates must still prevent an unmeasured vendor from
  changing live decisions.
  Date/Author: 2026-07-31 / Codex.
- Decision: do not select or promote a provider from marketing documentation.
  Rationale: admission gates require measured EPL coverage, identity, quota and
  owner-approved terms.
  Date/Author: 2026-07-31 / Codex.
- Decision: model `observed_at` as the exact host capture time and reject a
  provider envelope that claims a different observation time; require
  `available_at <= observed_at`.
  Date/Author: 2026-07-29 / Codex.
- Decision: hash canonical captured source bytes as `source_sha256`, then include
  that digest when independently sealing the normalized envelope as
  `content_sha256`.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

Controlled trial enablement and a first redacted endpoint probe succeeded.
Provider activation is still not production admission: no fixture has yet been
sealed and reconciled against an official sheet and the FPL minutes oracle.
Integration remains open on `FPL-eah`; downstream `FPL-cm6` can operationalise
production credentials only after the measured gates clear.

## Validation

```bash
python -m pytest -q tests/data/test_lineups_minutes.py
```

## Non-goals

Scraping unapproved websites, embedding credentials, name-only identity
fallback, network retry storms, raw-response redistribution, or treating an
HTTP 200/vendor claim as measured production coverage.