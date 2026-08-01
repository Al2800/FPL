# Enablement log — current-info sources (2026-08-01)

Follow-up to `2026-08-01-current-info-source-research.md`.

## Registry (v0.6.5)

| Source | Change |
|---|---|
| `clubelo` | **enabled**; `licence_status=restricted`; reuse-with-citation (About page) |
| `world-cup-2026` | **enabled** for admitting derived CSV only; no FIFA HTML scrape |
| `the-odds-api` | already enabled — capture still blocked without `THE_ODDS_API_KEY` |
| `understat` | **left disabled** — rights still unresolved |

## Highest-leverage execution

| Item | Result |
|---|---|
| Promote launch context bound to weekly bootstrap `e3b41b91…` | `control/identities/2026-27-launch-context.json` updated |
| Admit WC priors + launch_context | Checkpoint `weekly-2026-08-02` — both **admitted** |
| Availability citation ledger | 4 doubtful claims (Rogers, Guéhi, Senesi, Anderson); Haaland omitted on purpose |
| W7 availability-flag calibration | `control/models/availability-flags-v1.provisional.json` + report; **provisional / non-PIT** (vaastav limitation) |
| ClubElo PIT capture | Local `data/live-shadow/clubelo/2026-08-01/…` (gitignored) |
| Odds slots | **Not captured** — env missing `THE_ODDS_API_KEY` |

## Packet effect (`weekly-2026-08-02`)

- `launch_context_enrichment`: **applied**
- Example `world_cup_fatigue`: Haaland/Guéhi/Anderson **1.0** (was 0.0); Semenyo/Bruno **0.35**; Rogers **0.7**
- EP vectors unchanged by design (`launch_context_flags_applied_after_forecast`); fatigue enters optimiser objective weights
- Remaining gaps: licensed_odds, player_ratings, promoted_team_priors, transfers_and_signings

## Owner follow-ups

1. Set `THE_ODDS_API_KEY` in the capture environment and run `scripts/capture_live_odds.py` for GW1 slots.
2. Decide when provisional W7 table may replace live hard-override (needs PIT bootstrap archive).
3. Optional: ClubElo → team-prior challenger wiring (capture exists; forecaster integration separate).
4. Understat rights review remains open before any fetch.
