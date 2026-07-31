# 2026/27 line-ups and minutes provider review

Access date for this evaluation note: **2026-07-31**.

The production contract is provider-neutral. Every pre-kickoff observation is
captured as an immutable, point-in-time snapshot and mapped only through explicit
fixture/player aliases. Official FPL `event-live` / `element-summary` remains the
post-match minutes oracle; it is not used to manufacture a pre-kickoff lineup.

## Decision: two complementary sources

| Track | Source | Role | Current state |
| --- | --- | --- | --- |
| 1 | Official Premier League / club team sheets | **Canonical primary truth** for the published starting XI, substitutions and cited publication time | Manual/citation capture; not automated because domain rights and capture rehearsal remain outstanding |
| 2 | [Sportradar Soccer Sport Event Lineups](https://developer.sportradar.com/soccer/reference/soccer-sport-event-lineups) | **Automated challenger candidate** for starting players, formation and substitutions | **Disabled** after the owner decided ongoing provider cost was not justified |

The sources are not averaged. If an automated challenger is used in the future
and disagrees with an official team sheet, quarantine the affected fixture/player
and adjudicate against the official team sheet. If the official sheet is
unavailable, retain a degraded state rather than guessing.

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

This was endpoint reachability only, not the admission trial. No immutable
fixture snapshot, official-sheet comparison, identity mapping, final-minute
reconciliation or quota measurement was completed. `fixtures_measured` remains
0.

## Cost reversal

The Sportradar source is now disabled in both the source registry and lineup
config. `selected_provider` is `null`, the family is degraded safely, and no
network collection will occur. The API key has been removed from the Windows
user environment. The historical probe remains documented solely for audit
purposes; it does not justify ongoing spend or production use.

## Fallbacks (not primary truth)

- **API-Football** remains a fallback comparison feed; timing and final-minute
  fidelity would require a separate approved trial:
  [documentation](https://www.api-football.com/documentation).
- **football-data.org** remains a low-cost fallback comparison feed; its v4
  unfolded line-ups/substitutions are not yet measured for this use:
  [policies](https://docs.football-data.org/general/v4/policies.html).
- **TheSportsDB** remains non-authoritative fallback-only.

## If a future provider is reconsidered

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

Bead **`FPL-eah`** remains open as a deferred provider decision. Official
team-sheet capture and a lower-cost alternative can be reconsidered later.