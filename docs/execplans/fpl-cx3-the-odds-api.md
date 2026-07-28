# FPL-cx3 The Odds API integration

This is a living implementation plan for the selected live odds provider.

## Purpose

Capture exact pre-deadline EPL odds at T-24h, T-8h, T-2h and the final safe
checkpoint. Raw provider responses remain private and local. Derived snapshots
are immutable, hash-bound and usable only by the isolated odds shadow until
the preregistered promotion gate passes.

## Guardrails

- Read the API key only from `THE_ODDS_API_KEY`.
- Never persist, print, log or include the key in an exception or URL artifact.
- Use `soccer_epl`, UK bookmakers, decimal odds and the featured `h2h,totals`
  markets.
- Treat 1X2 as required and totals as optional because soccer totals coverage
  can vary by bookmaker.
- Record provider `last_update`, exact local observation time and quota
  headers.
- Reject observations at or after the decision cutoff or outside the named
  slot.
- Retain raw data locally and do not redistribute it as a data product.
- Missing, malformed, stale or quota-exhausted data degrades to the shared
  structured forecast without imputation.

## Progress

- [x] Select provider and record owner approval.
- [x] Verify official API contract, quota accounting, terms and update cadence.
- [x] Define provider configuration and slot budgets.
- [x] Add failing fixture-driven tests.
- [x] Implement secret-safe acquisition and normalization.
- [x] Add immutable CLI and source-registry approval.
- [x] Run focused and repository regression tests.
- [ ] Perform a live smoke test after the local secret is available.

## Design

`src/ingestion/live_odds_provider.py` validates the slot before making a network
request, calls the V4 EPL odds endpoint, retains the raw response through the
governed acquisition boundary and normalizes valid bookmaker markets into the
existing live forecast market-snapshot contract.

The capture records request scope, response status, content hash, bookmaker and
market update times, quota usage and rejection reasons. It stores only a
sanitized request URL without the `apiKey` query parameter.

## Validation

    .venv\Scripts\python.exe -m pytest tests/data/test_live_odds_provider.py -q
    .venv\Scripts\python.exe -m pytest tests/data/test_odds_snapshot.py tests/integration/test_live_episode_builder.py -q
    .venv\Scripts\python.exe -m pytest

All 660 collected repository tests passed in bounded batches after the monolithic
run exceeded the five-minute command window. The CLI no-secret smoke path also
refused before network access and named only the environment variable.

## Discoveries

- The free plan currently provides 500 credits per month.
- Cost is one credit per returned market per requested region. The proposed
  request costs no more than two credits.
- Featured markets update at roughly 60-second intervals before kickoff.
- EPL 1X2 is directly documented. Totals are available but may vary by
  bookmaker, so they are optional rather than a completion requirement.

## Outcomes

The provider is configured, registry-approved and implemented behind a
secret-safe CLI. Fixture tests prove cutoff safety, immutable reruns, quota and
retry metadata, required-market degradation, absence of secret material and
compatibility with the live forecast contract. All 660 repository tests pass.

The only pending item is the real-provider smoke capture. It requires
`THE_ODDS_API_KEY` to be set locally during a valid checkpoint window.
