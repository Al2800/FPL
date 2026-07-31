# 2026/27 line-ups and minutes provider review

Access date for this evaluation note: **2026-07-31**.

The production contract is provider-neutral. Every pre-kickoff observation is
captured as an immutable, point-in-time snapshot and mapped only through explicit
fixture/player aliases. Official FPL `event-live` / `element-summary` remains the
post-match minutes oracle; it is not used to manufacture a pre-kickoff lineup.

## Decision: official citation path (2026-07-31)

| Track | Source | Role | Current state |
| --- | --- | --- | --- |
| 1 | Official Premier League / club team sheets | **Canonical primary truth** for the published starting XI, substitutions and cited publication time | **Enabled** for manual citation capture (`selected_provider=official-team-sheets`) |
| 2 | [Sportradar Soccer Sport Event Lineups](https://developer.sportradar.com/soccer/reference/soccer-sport-event-lineups) | Automated challenger candidate | **Disabled** — ongoing provider cost not justified; stays off |

Owner decision (ticket 05): complete the official citation branch. Do not
average disagreeing feeds; quarantine and adjudicate against the official sheet.

## One-off Sportradar probe (2026-07-31)

Before the cost decision, an owner-authorized redacted probe confirmed that the
credential and endpoint were reachable. The key and raw responses were not logged
or retained.

| Probe | Result |
| --- | --- |
| Trial competition catalog | HTTP 200; 1,275 competitions; Premier League `sr:competition:17` present |
| Premier League seasons | HTTP 200; 2025/26 `sr:season:130281` and 2026/27 `sr:season:140756` returned |
| 2025/26 schedule | HTTP 200; 395 events; pre-match lineup coverage advertised |
| Lineup endpoint for `sr:sport_event:61300505` | HTTP 200; one payload, two competitors, 22 starter rows |
| Raw retention | **False** |

This was endpoint reachability only, not an admission trial. It does not justify
ongoing spend or production use.

## Official citation rehearsal

Committed artifact:
`evals/golden-cases/evidence/official-team-sheet-citation-rehearsal.json`

The rehearsal seals a synthetic official XI/substitution citation with
publication and observation times, a correction history entry, explicit identity
aliases and reconciliation to the FPL minutes oracle. Production now selects
`official-team-sheets` with registry `official-lineups-minutes` enabled for
**manual citation only** (no HTML scrape, no Sportradar).

## Fallbacks (not primary truth)

- **API-Football**, **football-data.org** and **TheSportsDB** remain non-selected
  fallback candidates only. None may be enabled without a fresh owner and
  registry decision plus the 10-fixture / three-matchday admission trial.

## If a future paid provider is reconsidered

Any replacement must run at least **10 Premier League fixtures across at least
three matchdays** and record publication timing, full-XI coverage,
substitutions, final minutes versus the FPL oracle, correction timing, identity
coverage, rate limits, retention/redistribution rights, cost and failure
behaviour. Production promotion requires the 95% lineup, 99% minutes, 100%
identity and 20% quota-headroom gates.

## Existing implementation boundary

- `config/data_sources/2026-27-lineups-minutes.json`
- `control/sources/source-registry.yaml`
- `control/identities/lineup-provider-aliases.yaml`
- `src/ingestion/lineups_minutes.py`
- `tests/data/test_lineups_minutes.py`
- `docs/data-sources/2026-27-lineups-citation-decision.md`
