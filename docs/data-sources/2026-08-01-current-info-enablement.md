# Enablement log — current-info sources (2026-08-01)

Follow-up to `2026-08-01-current-info-source-research.md`.

## Registry (v0.6.6)

| Source | Change |
|---|---|
| `clubelo` | **enabled**; `licence_status=restricted`; reuse-with-citation (About page) |
| `world-cup-2026` | **enabled** for admitting derived CSV only; no FIFA HTML scrape |
| `the-odds-api` | enabled; free-tier wiring smoke complete |
| `understat` | **enabled** via understatAPI (private local; residual site risk accepted) |

## Highest-leverage execution

| Item | Result |
|---|---|
| Promote launch context bound to weekly bootstrap `e3b41b91…` | `control/identities/2026-27-launch-context.json` updated |
| Admit WC priors + launch_context | Checkpoint `weekly-2026-08-02` — both **admitted** |
| Availability citation ledger | 4 doubtful claims (Rogers, Guéhi, Senesi, Anderson); Haaland omitted on purpose |
| W7 availability-flag calibration | `control/models/availability-flags-v1.provisional.json` + report; **provisional / non-PIT** (vaastav limitation) |
| ClubElo PIT capture | Local `data/live-shadow/clubelo/2026-08-01/…` (gitignored) |
| Odds slots | **Wiring smoke complete** (free tier); formal GW1 slots still pending window |

## Packet effect (`weekly-2026-08-02`)

- `launch_context_enrichment`: **applied**
- Example `world_cup_fatigue`: Haaland/Guéhi/Anderson **1.0** (was 0.0); Semenyo/Bruno **0.35**; Rogers **0.7**
- EP vectors unchanged by design (`launch_context_flags_applied_after_forecast`); fatigue enters optimiser objective weights
- Remaining gaps: licensed_odds, player_ratings, promoted_team_priors, transfers_and_signings

## Odds free-tier wiring (2026-08-01)

- Key supplied for session use only via `THE_ODDS_API_KEY` (never committed).
- Free-tier smoke: `/v4/sports` OK; remaining credits **500 → 498** after one
  governed `h2h+totals` capture (2 credits).
- Diagnostic artifact (gitignored):  
  `data/live-shadow/odds/captures/diagnostic-2026-08-01-wiring-t24h.json`  
  Uses a **synthetic** ~24h cutoff to satisfy the T-24h window — **not** GW1
  market evidence for deadline `2026-08-21T17:30:00Z`.
- Formal GW1 slots (`T-24h` / `T-8h` / `T-2h` / `final`) open only inside the
  configured lead-time windows before that deadline (~20 Aug onward for T-24h).

## Owner follow-ups

1. Keep `THE_ODDS_API_KEY` in the capture environment (free tier). Re-run
   `scripts/capture_live_odds.py` for real GW1 slots when windows open.
2. Decide when provisional W7 table may replace live hard-override (needs PIT bootstrap archive).
3. Optional: ClubElo → team-prior challenger wiring (capture exists; forecaster integration separate).
4. Understat: use `scripts/capture_understat_epl.py` (season `2025` now;
   `2026` when matches exist); optional event-model wiring is separate.
