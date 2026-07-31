## Parent / origin

Migrated from Bead `FPL-eah` (was **in_progress**, priority 1).
Blocking follow-up from closed bead `FPL-ecy`.

## Status at migration

In progress. Sportradar controlled-trial enablement was **reversed** at owner
request (ongoing provider cost not justified). `selected_provider=null`,
degraded/no-network config restored, registry entry disabled. One-off redacted
endpoint probe retained in docs for audit only. `fixtures_measured=0`.

## What

Rehearse official EPL/club team-sheet citation capture **or** approve a
lower-cost challenger. Official Premier League/club sheets remain canonical
primary truth for published XIs/subs; official FPL event-live / element-summary
remain the post-match minutes oracle.

No paid provider is selected or enabled until explicitly approved.

If a future challenger is reconsidered: ≥10 PL fixtures across ≥3 matchdays via
immutable provider-neutral snapshots; record timing, XI coverage, subs, minutes
vs FPL oracle (±1), identity mapping, rate limits, retention rights, cost and
failure behaviour. Promote only if 95/99/100/20 admission gates pass.
Disagreements quarantine against the official sheet — never average.

## Files

- `docs/research/2026-27-lineups-minutes-provider-review.md`
- `config/data_sources/2026-27-lineups-minutes.json`
- `control/sources/source-registry.yaml`
- `control/identities/lineup-provider-aliases.yaml`
- `src/ingestion/lineups_minutes.py`
- `tests/data/test_lineups_minutes.py`

## Acceptance criteria

- [ ] Either: documented official citation-capture rehearsal path ready for live matchdays, **or** owner-approved lower-cost challenger registered with confirmed `licence_status` / `allowed_use`.
- [ ] `selected_provider` remains null and collection disabled until that decision.
- [ ] Focused tests continue to cover null-provider safety and disabled registry state.
- [ ] No API keys or raw provider payloads committed.

## Blocked by

Owner decision: official citation rehearsal vs lower-cost challenger (not Sportradar at current cost).

## Non-goals

Re-enabling Sportradar; paid collection without approval; averaging disagreeing feeds.
