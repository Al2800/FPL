# 01 — Deepen EP: player Understat, event model, market team prior

**Blocked by:** None

**Status:** resolved

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Expected points already vary with **club and fixture** via team
multipliers, but player-finishing quality and market-implied team strength are
still missing. Wire player-level Understat into the live-faithful event path,
and consume Odds API h2h (when cutoff-safe) as the team-prior odds component —
without treating odds as player xG.

### Clarification already established

On `weekly-2026-08-02`:

- EP is **not** flat official `ep_next` anymore for the live path.
- Per Gameweek, each player's fixtures contribute components with
  `opponent_club_id`, `was_home`, `team_multiplier` derived from Understat
  team attack/defence xG + ClubElo.
- Example: Rogers EP `[5.43, 5.39, 3.13, 5.43, 5.36, 5.43]` — GW3 dip is fixture
  strength, not noise.
- **Caveat:** elite attacks can still look flat when
  `attack_multiplier` hits the configured ceiling (`1.45`). Arsenal’s GW1–GW6
  attack multipliers are all clipped at 1.45, so Saka’s EP is
  `[4.89 × 6]` despite FDR swinging 2→4. Fixture impact is real but partially
  censored by bounds; ticket 02’s audit trail must show raw expected xG /
  pre-clip signals or agents will misread “no fixture effect.”
- Production `event_model_weight = 0.0`, so only the rate×minutes×multiplier
  path scores. Event/xG player model exists but is not control.
- Understat capture already contains **537 player rows** (`xG`, `xA`, `npxG`,
  `time`, `team_title`, …) and is currently used **only** for match/team priors.

### Desired behaviour

1. **Identity-safe player Understat prior** from the admitted capture:
   - join Understat player → FPL identity with explicit mapping / quarantine;
   - no silent name-only matches for ambiguous transfers;
   - promoted / new players degrade to team/cold-start priors.
2. Feed player xG/xA (and minutes) into the live-faithful **event** rates used
   when `event_model_weight > 0`, or an equivalent documented blend.
3. Promote a calibrated non-zero `event_model_weight` only behind the existing
   challenger/calibration discipline (v2 events evaluation already records
   `0.25` as a challenger, not automatic production).
4. **Odds API** (`THE_ODDS_API_KEY` env only):
   - use for match `h2h` (and totals if present) in the team prior
     (`odds_weight` already configured at 0.1 but `team_prior_odds_absent`);
   - never invent player props; Odds API is not a player-level Understat
     substitute;
   - respect slot / cutoff policy; degrade without blocking.
5. Packet `forecast_quality.limitations` must distinguish:
   - team fixture adjustment present;
   - player Understat absent/partial;
   - odds absent/partial.

### Why Odds is related but separate

| Source | Feeds |
|---|---|
| Understat matches/teams | Team attack/defence multipliers (already on) |
| Understat players | Player event rates / finishing (this ticket) |
| The Odds API h2h/totals | Market-implied team strength / scorelines |
| ClubElo | Elo tilt on team multipliers (already on) |

### Acceptance criteria

- [x] Documented join report: matched / quarantined / promoted-fallback counts
      for the 2025 Understat player capture vs current bootstrap.
- [x] Live-faithful path can consume player Understat rates with
      `event_model_weight=0` still byte-stable vs control when weight stays 0.
- [x] Challenger config path can raise weight without editing prompts or
      hard-coding rules.
- [x] When a cutoff-safe odds snapshot is admitted, team prior limitation
      `team_prior_odds_absent` clears; missing odds still degrade cleanly.
- [x] No API key in git, logs, manifests or packet lineage URLs.
- [x] Focused tests cover identity quarantine, weight=0 invariance, and odds
      degradation.

### Out of scope

- In-packet fixture audit columns (ticket 02).
- Start-probability evidence blend (ticket 03).
- Set-piece effect promotion (ticket 04).
- Changing WC fatigue weight (ticket 05).

## Answer

Implemented and wired into the live initial-squad horizon path.

### Player Understat

- New `src/forecasting/understat_player_context.py`:
  - identity-safe join with quarantine for ambiguous names;
  - cross-club unique full-name remap for transfers (e.g. Rogers);
  - event-rate overlay updates only `expected_goals_per_90` /
    `expected_assists_per_90` (not points/start_p).
- Horizon builder enriches the player prior before `build_live_faithful_forecast`.
- Limitations: `understat_player_event_rates_{applied|partial|absent}`.
- Compact join report:
  `reports/forecasting/understat-player-join-2025-to-2026-27.json`
  (381 unique FPL matches, 6 quarantined, 143 unmatched; regenerable via
  `scripts/report_understat_player_join.py`).
- Production control remains `event_model_weight=0.0`;
  `control/models/live-faithful-v2.events.json` remains the challenger at 0.25.

### Odds → team prior

- New `src/forecasting/live_odds_team_prior.py` projects The Odds API captures
  into fixture-keyed `registered_predeadline` 1X2 snapshots.
- Admission requires observation before the packet decision cutoff **and** a
  valid slot window for that cutoff (diagnostic early wiring captures correctly
  degrade for the GW1 deadline).
- `build_understat_attack_defence_team_prior` now accepts `odds_snapshots` and
  uses `decision_cutoff` as team-prior as_of so T-24h odds can enter near
  deadline even when bootstrap `observed_at` is earlier.
- Checkpoint discovers local odds under `data/live-shadow/odds/`.

### Tests

Focused suites covering join/quarantine, weight=0 EP invariance, odds
accept/degrade, and existing Understat team-prior contracts: green.

## Comments

- 2026-08-01: live Odds API smoke from this environment returned 10 EPL events
  commencing 2026-08-21 … 2026-08-24 (quota remaining observed). Formal slot
  capture still follows `.scratch/evidence-gap-fill/issues/04-odds-slot-capture-runbook.md`.
- 2026-08-01: ticket implemented; production EP unchanged at weight 0 until an
  owner-approved challenger promotion.
