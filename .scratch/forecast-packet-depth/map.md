# Forecast packet depth — map

## Notes

Owner review of the frozen statistical packet (2026-08-02) after Understat team
prior wiring. Direction: log detailed tickets for each material gap, then
continue analysis before implementation bursts.

## Decisions so far

- Team + fixture **do** already affect EP through live-faithful team multipliers
  (Understat attack/defence + ClubElo). Player-level Understat is the missing
  layer, not the existence of fixture adjustment.
- The Odds API key is for **match markets** (h2h/totals) into the team prior /
  licensed-odds family — not a substitute for player Understat xG/xA.
- In-packet opponent / home-away / FDR / multiplier audit trail is **required**
  for agent and human reasoning.
- GW-specific start probability informed by unstructured evidence (press,
  availability ledger, later match ratings) is key.
- Set-piece roles should be included in the packet story now that the family is
  admitted; effect weights stay gated by ablation policy.
- World Cup fatigue: keep cautious / under-weighted until calibration says
  otherwise; under-use is acceptable.
- Related optional families (odds, ratings, transfers, availability blend) are
  required work, not nice-to-haves.

## Fog

- Exact identity join from Understat player rows → FPL `player_id` / `fpl_code`
  for 2025→2026 transfers and promoted clubs.
- Whether first Odds consumption is slot-gated only (T-24h…) or also allows a
  preseason shadow market prior once markets exist (markets observed open for
  early 2026/27 fixtures on 2026-08-01 with key present).
- How strongly availability “doubtful” should depress start_p before W4
  persistence is owner-enabled.
- Fatigue weight: keep 0.25 shrinkage vs lower; horizon fade vs scalar.

## Analysis notes (2026-08-01)

### EP / team+fixture impact — confirmed happening

Live-faithful already applies per-fixture team multipliers from Understat
match xG attack/defence + ClubElo. Player EP varies across GW1–GW6 for most
of the universe; that variation is fixture-driven. What is missing is
**player-level** Understat (capture has 537 player rows; production
`event_model_weight=0.0`) and market odds in the team prior.

### Player Understat join (naive probe)

With team aliases + web_name/full-name overlap: ~326/537 unique matches,
~4 ambiguous (Murphy/Fletcher collisions), ~207 missing (transfers, dual-club
rows, name/token mismatches, promoted-only FPL players). Ticket 01 must ship
a real identity report with quarantine — not this probe.

### Odds API

`THE_ODDS_API_KEY` present in this environment; `/v4/sports/soccer_epl/odds`
returned 10 events covering the GW1 slate window (commence 2026-08-21 …
2026-08-24). Use for team prior / licensed-odds family only — not player xG.
Formal slot capture still follows evidence-gap ticket 04.

### Set pieces

195 active roles already admitted (penalties, DFK, corners/indirect). Safe to
surface for reasoning now; scoring effects stay shadow until ablation.

### Start_p / unstructured

Availability ledger claims exist but do not move start_p. Model-run admission
can grow press/club clues; host blend is ticket 03.

## Cross-links

- Prior gap programme: `.scratch/evidence-gap-fill/` (tickets 01–06 largely
  resolved; odds slot runbook still human-gated).
- Model-run evidence admission: ADR-0023 /
  `docs/decisions/0023-model-run-evidence-admission-and-rationale.md`.
