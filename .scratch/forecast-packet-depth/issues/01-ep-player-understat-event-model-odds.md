# 01 — Deepen EP: player Understat, event model, market team prior

**Blocked by:** None

**Status:** open

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

- [ ] Documented join report: matched / quarantined / promoted-fallback counts
      for the 2025 Understat player capture vs current bootstrap.
- [ ] Live-faithful path can consume player Understat rates with
      `event_model_weight=0` still byte-stable vs control when weight stays 0.
- [ ] Challenger config path can raise weight without editing prompts or
      hard-coding rules.
- [ ] When a cutoff-safe odds snapshot is admitted, team prior limitation
      `team_prior_odds_absent` clears; missing odds still degrade cleanly.
- [ ] No API key in git, logs, manifests or packet lineage URLs.
- [ ] Focused tests cover identity quarantine, weight=0 invariance, and odds
      degradation.

### Out of scope

- In-packet fixture audit columns (ticket 02).
- Start-probability evidence blend (ticket 03).
- Set-piece effect promotion (ticket 04).
- Changing WC fatigue weight (ticket 05).

## Comments

- 2026-08-01: live Odds API smoke from this environment returned 10 EPL events
  commencing 2026-08-21 … 2026-08-24 (quota remaining observed). Formal slot
  capture still follows `.scratch/evidence-gap-fill/issues/04-odds-slot-capture-runbook.md`.
