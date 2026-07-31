# 2026/27 line-ups and minutes provider review

Access date for this evaluation note: **2026-07-31**.

The production contract is deliberately provider-neutral. A captured provider
snapshot is mapped only through explicit fixture/player aliases and reconciled
against official FPL post-match minutes (`event-live` / `element-summary` as the
reconciliation oracle, never as a pre-kickoff lineup source). Any mismatch
quarantines that player; missing data degrades the feature family and never
becomes a zero-minute claim.

## Candidates

| Provider | Registry / rights | Credential env | Current decision | Reason |
| --- | --- | --- | --- | --- |
| API-Football | Not registered/enabled for automated collection | `API_FOOTBALL_KEY` | **recommended primary trial**, access-gated | Official docs say line-ups are available 20–40 minutes pre-kickoff where competition coverage supports it; endpoint and timing still need measurement. |
| football-data.org | `football-data-org` registered but `enabled: false`; terms pending | `FOOTBALL_DATA_ORG_TOKEN` | secondary trial candidate, **access-gated** | v4 supports unfolded line-ups/substitutions; pre-kickoff availability and minutes quality remain unmeasured. |
| TheSportsDB | Not registered/enabled | `THESPORTSDB_API_KEY` | fallback trial candidate, **access-gated** | Free limits and timing make it unsuitable as an assumed authoritative feed. |

## Trial matrix (access gate)

Required trial: at least **10 Premier League fixtures across at least three
matchdays**, recording endpoint/tier, lineup publication time relative to
kickoff, full-XI coverage, substitutions, final minutes vs FPL oracle,
correction timing, identity coverage, rate limits, retention/redistribution
rights, cost and failure behaviour.

| Gate | Result on 2026-07-29 |
| --- | --- |
| Owner-approved terms, retention and credential handling | **Fail** — no candidate has automated-collection approval; `official-lineups-minutes` remains citation-only. |
| Credential present in environment (values never logged) | **Fail** — `API_FOOTBALL_KEY`, `FOOTBALL_DATA_ORG_TOKEN` and `THESPORTSDB_API_KEY` are all absent. |
| Fixtures measured | **0** (trial not started) |
| Matchdays measured | **0** |
| ≥95% full XI before kickoff | Not measured |
| ≥99% minute agreement ±1 vs FPL oracle | Not measured |
| 100% admitted identity mapping | Not measured |
| ≥20% quota headroom | Not measured |

**Conclusion:** an access/rights gate prevented the representative trial. No
provider is selected. `selected_provider` remains `null` and the family stays
**degraded**. Marketing documentation is not treated as measured coverage.

## Provider-neutral contract already in repo

- `config/data_sources/2026-27-lineups-minutes.json`
- `control/identities/lineup-provider-aliases.yaml` (explicit aliases only)
- `src/ingestion/lineups_minutes.py` (reconcile + degraded capture helpers)
- `tests/data/test_lineups_minutes.py`

Missing credential, timeout, rate-limit and outage paths return a degraded
family with `retry_scheduled=false` and `baseline_unchanged=true`.

## Blocking follow-up

Bead **`FPL-eah`** tracks owner-approved credential provisioning, registry
enablement where lawful, and the ≥10-fixture / ≥3-matchday measured trial before
any provider may be enabled.
## Decision and credential handoff (2026-07-31)

API-Football is the recommended first trial because its published line-up
contract is the closest match to the live decision boundary: it documents a
20–40 minute pre-kickoff window when the competition coverage flag is enabled,
with an update cadence of 15 minutes (see https://www.api-football.com/documentation). This is a vendor claim, not an admission
result; the EPL coverage flag, timing, identity mapping, quota and final-minute
agreement must be measured on the required matrix before enablement.

The trial needs one owner-provisioned key. Store it only as a user or process
environment variable; never commit it, put it in a manifest, or include it in a
URL. PowerShell setup (replace the placeholder locally, not in chat):

```powershell
[Environment]::SetEnvironmentVariable("API_FOOTBALL_KEY", "<your-key>", "User")
```

After opening a new terminal, the preflight must report only
`credential_present=true`; it must not print the value. Until the key and the
rights/retention decision are present, `selected_provider` remains `null` and
lineups/minutes stay degraded.

The football-data.org API is retained as the fallback trial: its v4 policies
support `X-Unfold-Lineups` and `X-Unfold-Subs` (see https://docs.football-data.org/general/v4/policies.html), but we have not yet measured
pre-kickoff publication or minutes fidelity. TheSportsDB remains a low-cost
fallback only, not an assumed authoritative source.
