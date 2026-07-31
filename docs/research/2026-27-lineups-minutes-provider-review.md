# 2026/27 line-ups and minutes provider review

Access date for this evaluation note: **2026-07-31**.

The production contract is provider-neutral. Every pre-kickoff observation is
captured as an immutable, point-in-time snapshot and mapped only through explicit
fixture/player aliases. Official FPL `event-live` / `element-summary` remains the
post-match minutes oracle; it is not used to manufacture a pre-kickoff lineup.

## Decision: two complementary sources

| Track | Source | Role | Current state |
| --- | --- | --- | --- |
| 1 | Official Premier League / club team sheets | **Canonical primary truth** for the published starting XI, substitutions and cited publication time | Manual/citation capture; disabled for automated collection until domain rights and capture rehearsal are approved |
| 2 | [Sportradar Soccer Sport Event Lineups](https://developer.sportradar.com/soccer/reference/soccer-sport-event-lineups) | **Automated challenger trial** for starting players, formation and substitutions | Credentialed trial candidate; disabled until EPL coverage, timing, rights, identity and quota gates are measured |

The sources are not averaged. If the automated challenger disagrees with an
official team sheet, quarantine the affected fixture/player and adjudicate
against the official team sheet. If the official sheet is unavailable, retain a
degraded state rather than guessing. The post-match FPL oracle is used to measure
minutes agreement and to document corrections, not to rewrite the pre-kickoff
snapshot.

Sportradar is a suitable trusted challenger because its documented lineup
response includes starters and substitutions, but coverage is subscription- and
competition-dependent. Its documented trial is limited to 30 days and 1,000
requests per rolling 30 days with a default 1 QPS limit, so those limits must be
checked against the intended capture schedule before activation:
[lineup endpoint](https://developer.sportradar.com/soccer/reference/soccer-sport-event-lineups),
[trial/account limits](https://developer.sportradar.com/football/docs/football-ig-account-maintenance),
[authentication](https://developer.sportradar.com/getting-started/docs/authentication).

## Fallbacks (not primary truth)

- **API-Football** remains a fallback comparison feed. Its published line-up
  timing is a vendor claim and still needs a measured trial:
  [documentation](https://www.api-football.com/documentation).
- **football-data.org** remains a low-cost fallback comparison feed. Its v4
  policies document unfolded line-ups/substitutions, but pre-kickoff timing and
  final-minute fidelity remain unmeasured:
  [policies](https://docs.football-data.org/general/v4/policies.html).
- **TheSportsDB** remains non-authoritative fallback-only and is not a launch
  dependency.

## Trial and admission gates

Run at least **10 Premier League fixtures across at least three matchdays** and
record endpoint/tier, publication time relative to kickoff, full-XI coverage,
substitutions, final minutes versus the FPL oracle, correction timing, identity
coverage, rate limits, retention/redistribution rights, cost and failure
behaviour. Enable no provider unless all gates pass:

- owner-approved terms, retention and credential handling;
- full XI before kickoff for at least 95% of trial fixtures;
- at least 99% of identity-resolved final minute rows within ±1 minute of the FPL oracle;
- 100% stable identity mapping for admitted rows (unknowns quarantine);
- at least 20% quota headroom at the planned capture cadence.

The current matrix is intentionally empty: no credential is present, no source
has automated-collection approval, and `selected_provider` remains `null`. The
family therefore stays degraded and the shared structured baseline is unchanged.

## Credential handoff

Provision the challenger key only as a user/process environment variable. Never
send it in chat or commit it to a manifest, URL or log:

```powershell
[Environment]::SetEnvironmentVariable("SPORTRADAR_API_KEY", "<your-key>", "User")
```

After opening a new terminal, preflight may report only
`credential_present=true`; it must not print the value. The source registry entry
`sportradar-soccer` remains disabled until the owner approves terms, retention,
cost and the measured trial.

## Existing implementation boundary

- `config/data_sources/2026-27-lineups-minutes.json`
- `control/sources/source-registry.yaml`
- `control/identities/lineup-provider-aliases.yaml`
- `src/ingestion/lineups_minutes.py`
- `tests/data/test_lineups_minutes.py`

Bead **`FPL-eah`** tracks the owner-approved credential, registry review and the
10-fixture/3-matchday trial. Until those inputs arrive, no network collection or
provider enablement occurs.