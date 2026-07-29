# FPL-ecy: production line-ups and minutes integration

This ExecPlan is a living document. Keep Progress, Surprises, Decision Log and
Outcomes current.

## Purpose / Big Picture

Build a provider-neutral capture/reconciliation path that replay and the live
season both call. First approve exactly one provider after a documented EPL
trial; then add its HTTP collector without changing the snapshot schema. No
provider failure may alter the shared structured baseline: it surfaces as a
degraded feature family.

## Progress

- [x] (2026-07-28) Provider-neutral contract, aliases file, reconcile helper and
  focused tests landed.
- [x] (2026-07-29) Credential-presence probe, degraded family helpers (missing
  credential / timeout / rate-limit / outage), research access-gate matrix and
  blocker bead `FPL-lpm`.
- [ ] Owner-approved credentials and measured ≥10-fixture / ≥3-matchday trial
  (`FPL-lpm`).
- [ ] Enable exactly one provider only after admission gates pass.
- [ ] Historic fixture reconciliation and live preseason capture under the
  selected provider.

## Surprises & Discoveries

- Observation: no candidate credential is present in this environment.
  Evidence: `API_FOOTBALL_KEY`, `FOOTBALL_DATA_ORG_TOKEN` and
  `THESPORTSDB_API_KEY` all absent on 2026-07-29.
- Observation: `football-data-org` is registered but disabled; API-Football and
  TheSportsDB are not enabled sources for automated collection.
  Evidence: `control/sources/source-registry.yaml`.
- Observation: `official-lineups-minutes` remains citation-only with unknown
  licence status; it is not an automated pre-kickoff feed.

## Decision Log

- Decision: do not select or enable a provider from marketing documentation.
  Rationale: admission gates require measured EPL coverage, identity, quota and
  owner-approved terms.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: treat missing credentials as a hard access gate that records an
  empty trial matrix rather than inventing coverage.
  Rationale: bead AC permits documenting why a trial could not run.
  Date/Author: 2026-07-29 / Cursor agent.
- Decision: create blocker bead `FPL-lpm` and keep `selected_provider=null`.
  Rationale: AC requires a blocker when no provider passes; this bead must not
  be closed as integrated.
  Date/Author: 2026-07-29 / Cursor agent.

## Outcomes & Retrospective

Evaluation complete without provider activation. The reconcile path, immutable
writes and degraded failure modes are tested. Integration remains blocked on
`FPL-lpm`. Downstream `FPL-cm6` can operationalise credentials only after a
provider clears the measured gates.

## Validation

```bash
python -m pytest -q tests/data/test_lineups_minutes.py
```

## Non-goals

Scraping unapproved websites, embedding credentials, name-only identity
fallback, network retry storms, or treating vendor claims as measured coverage.
