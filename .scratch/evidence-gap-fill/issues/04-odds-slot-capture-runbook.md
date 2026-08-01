# 04 — Odds slot capture operationalisation

**Blocked by:** None

**Status:** ready-for-human

**Type:** research

## Summary

Document and verify the T-24h/T-8h/T-2h/final Odds API capture path for 2026/27
fixtures. Family is capture_ready and registry-enabled; blocked on credential +
live markets. No fabricated odds. Feeds W15 ablation once ≥4 GWs exist.

## Answer

**Capture path operationally verified; live smoke remains human-gated.**

- The Odds API is registered and owner-approved for private local analysis.
- `scripts/capture_live_odds.py` and
  `src/ingestion/live_odds_provider.py` implement T-24h, T-8h, T-2h and
  final checkpoints from the versioned provider configuration.
- Capture rejects late or out-of-window observations before network access,
  reads only `THE_ODDS_API_KEY` from the environment, strips the key from
  stored request metadata, writes immutable local raw/derived artefacts and
  records quota and degradation metadata.
- `h2h` is required; `totals` is optional. Missing or malformed markets
  degrade to the shared structured forecast and never create odds by
  imputation.
- Fixture coverage verifies all four slot contracts, cutoff safety, missing
  credentials without a network call, rate-limit degradation, required-market
  gaps, secret-free output and immutable reruns.
- A live smoke capture is not claimed: this environment has no
  `THE_ODDS_API_KEY`, and the 2026/27 markets are not yet available. The owner
  must run one valid capture per slot before W15 ablation can open; at least
  four Gameweeks of slot-complete captures are required.
