# Evidence gap fill — map

## Notes

User direction 2026-07-31: aim to fill evidence-family gaps for research and
competition. Stay inside Phase 0/1; no rival modelling or account execution.

## Decisions so far

- Sportradar stays off; official lineups are manual citation.
- Highest-leverage unblocked work: consume admitted `launch_context` (promoted /
  new / transferred / WC fatigue) in the initial-squad packet, then materialise
  a six-GW live-faithful packet, then bind set-pieces from bootstrap.
- Odds need live slot captures + env credential; ratings stay degraded until
  rights-cleared 2026/27 PL coverage exists.
- The registered historical datasets were restored locally; the latest
  2025/26 player-prior build records and removes only exact duplicate
  player-fixture rows.
- Official FPL availability capture now has 55 complete claims with no
  collection gaps; club, press and role claims remain manual-citation-only
  until model-run / citation paths admit them.
- Ticket 04 progressed: the four-slot Odds API path is fixture-verified and
  registry-enabled; live smoke and W15 remain owner-gated on the credential,
  market availability and four Gameweeks of captures.
- Ticket 01 resolved: launch-context cold-start/WC fields now enrich the
  initial-squad packet when admitted; EP horizon still baseline-only at the
  time of resolution (later superseded by ticket 02 live-faithful bind).
- Ticket 02 resolved: `live-faithful-v1.feature-complete` now supplies a
  hash-bound six-GW horizon; live default prior is the completed 2025/26
  envelope; checkpoint remains degraded while optional live evidence is absent.
- Ticket 03 resolved: set-piece ledger is derived from admitted official
  bootstrap bytes; effect weights remain shadow-only.
- Ticket 05 resolved: official FPL availability remains automated; W4
  persistence is a named, default-disabled challenger; club and high-impact
  role claims remain manual-citation-only until the W12 rights decision
  (model-run ephemeral citation path added later under ADR-0023).
- Ticket 06 resolved: the registered StatsBomb Open local-transform path is
  ready but has no verified 2026/27 Premier League envelope; ratings remain
  degraded and shadow-only with no effect weights.
- 2026-08-01 follow-on packet-depth work tracked under
  `.scratch/forecast-packet-depth/` (player Understat, fixture audit trail,
  GW start_p blend, set-piece visibility, fatigue weight caution, optional
  family integration).

## Fog

- Club-domain rights tranche (W12) still blocks automated club HTML scrape.
- Owner-supplied Odds API credential is present in some agent environments;
  formal T-24h/T-8h/T-2h/final slot captures and ≥4 GW ablation corpus still
  required before W15.
- When markets open for Odds API T-24h slots relative to each deadline
  (early 2026/27 h2h markets observed forming ahead of GW1).
- Whether live-faithful promotion clears owner acceptance with remaining
  degradations.
- The complete structured/unstructured audit is
  `docs/evaluation/2026-07-31-evidence-coverage-audit.md`.
