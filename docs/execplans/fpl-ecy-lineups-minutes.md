# FPL-ecy: production line-ups and minutes integration

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Build a provider-neutral capture/reconciliation path that replay and the live
season both call. Official Premier League/club team sheets are canonical primary
truth for published lineups and substitutions. Sportradar is the automated,
trusted challenger. No provider failure may alter the shared structured baseline:
it surfaces as a degraded feature family.

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
- [ ] Owner-approved team-sheet rights/capture rehearsal and measured
  ≥10-fixture / ≥3-matchday Sportradar challenger trial (`FPL-eah`).
- [ ] Enable exactly one automated provider only after admission gates pass.
- [ ] Historic fixture reconciliation and live preseason capture under the
  approved policy.

## Surprises & Discoveries

- Observation: no `SPORTRADAR_API_KEY` is present in this environment; no
  automated candidate credential is currently available. Values are never
  logged.
- Observation: `official-lineups-minutes` is the canonical citation source and
  `sportradar-soccer` is registered as a disabled automated challenger.
  API-Football and football-data.org remain fallback-only.
- Observation: official team sheets are the primary truth for published lineups;
  the capture path is manual/citation-only until rights and domain rehearsal are
  approved.

## Decision Log

- Decision: official Premier League/club team sheets are canonical primary truth;
  Sportradar is the automated challenger trial. Do not average disagreements:
  quarantine and adjudicate against the official sheet, with FPL event-live /
  element-summary as the post-match minutes oracle.
  Rationale: this preserves an authoritative published lineup while still
  measuring a trusted automation path without allowing vendor claims to rewrite
  truth.
  Date/Author: 2026-07-31 / Codex.
- Decision: do not select or enable a provider from marketing documentation.
  Rationale: admission gates require measured EPL coverage, identity, quota and
  owner-approved terms.
  Date/Author: 2026-07-31 / Codex.
- Decision: treat missing credentials as a hard access gate that records an
  empty trial matrix rather than inventing coverage.
  Rationale: bead acceptance permits documenting why a trial could not run.
  Date/Author: 2026-07-31 / Codex.
- Decision: keep `selected_provider=null` until the owner-approved trial passes.
  Rationale: a disabled challenger must not affect live or replay decisions.
  Date/Author: 2026-07-31 / Codex.
- Decision: model `observed_at` as the exact host capture time and reject a
  provider envelope that claims a different observation time; require
  `available_at <= observed_at`.
  Rationale: accepting advisory/mismatched timestamps would allow stale or
  future data to be sealed under a trusted checkpoint.
  Date/Author: 2026-07-29 / Codex.
- Decision: hash canonical captured source bytes as `source_sha256`, then include
  that digest when independently sealing the normalized envelope as
  `content_sha256`.
  Rationale: source provenance and envelope integrity are separate claims and
  must detect tampering independently.
  Date/Author: 2026-07-29 / Codex.

## Outcomes & Retrospective

Evaluation remains access-gated without provider activation. Official team-sheet
adjudication, Sportradar challenger selection, immutable writes, timestamp
admission, independent digest layers and degraded failure modes are specified
and tested. Integration remains blocked on `FPL-eah`; downstream `FPL-cm6` can
operationalise credentials only after a provider clears the measured gates.

## Validation

```bash
python -m pytest -q tests/data/test_lineups_minutes.py
```

## Non-goals

Scraping unapproved websites, embedding credentials, name-only identity
fallback, network retry storms, or treating vendor claims as measured coverage.