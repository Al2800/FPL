# Decision: Understat via collinb9/understatAPI

**Date:** 2026-08-01  
**Outcome:** **enabled for private local EPL capture**  
**Registry:** `understat` in `control/sources/source-registry.yaml` v0.6.6+

## Decision

Collect Understat EPL xG/xA (and related league/team/match tables) using the
MIT client [collinb9/understatAPI](https://github.com/collinb9/understatAPI)
(`pip install understatapi` / optional extra `.[understat]`).

Script: `scripts/capture_understat_epl.py`  
Retention: gitignored under `data/live-shadow/understat/`  
Attribution: Understat + understatAPI

## What this does **not** claim

- understatAPI’s MIT licence covers the **client**, not Understat’s data.
- Understat still has no official public API or explicit reuse grant; the site
  `robots.txt` disallows crawling. Owner accepts residual site-terms risk for
  **private local analysis only** (ADR-0001/0002; no redistribution).
- Data is **post-match** performance intel (xG, xA, shots, etc.), not real-time
  minutes, injuries, or pre-deadline start probabilities.
- Season `2026` may be empty until 2026/27 matches are played; use `2025` for
  completed 2025/26 rates.

## Wiring status

1. Bounded capture of season `2025` complete (local gitignored); `2026` empty until matches.
2. **Team prior wired** into `build_live_faithful_initial_squad_horizon` via
   `src/forecasting/understat_team_context.py` (match xG → separate attack/defence
   multipliers; FDR fallback if join fails). ClubElo expected-result scores optional.
3. Player-level xG/xA still deferred while `event_model_weight=0.0`.
4. Keep official FPL `expected_*` and odds as baselines/comparators.
