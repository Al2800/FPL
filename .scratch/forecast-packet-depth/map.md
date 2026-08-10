# Forecast packet depth — map

## Notes

Owner review of the frozen statistical packet (2026-08-02) after Understat team
prior wiring. Direction: log detailed tickets for each material gap, then
continue analysis before implementation bursts.

## Decisions so far

- Team + fixture **do** already affect EP through live-faithful team multipliers
  (Understat attack/defence + ClubElo). Player-level Understat is the missing
  layer, not the existence of fixture adjustment.
- Ticket 01 resolved: player Understat event rates are joined with quarantine
  and overlaid into the live-faithful prior; production `event_model_weight`
  stays 0.0 (challenger config can raise it). Cutoff-safe Odds API h2h
  snapshots feed the team prior when the slot window matches the decision
  cutoff; otherwise odds degrade cleanly.
- Tickets 02–06 resolved: fixture-audit companion; availability→start_p host
  blend; set-piece role surface (shadow effects); gap panel for strategy;
  fatigue weight kept at 0.25 with optional horizon-fade follow-on only.
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

### EP / team+fixture impact — confirmed happening (with clipping)

Live-faithful already applies per-fixture team multipliers from Understat
match xG attack/defence + ClubElo. Player EP varies across GW1–GW6 for much
of the universe; that variation is fixture-driven (Chelsea mean EP moves
with the Arsenal away week). Missing pieces remain **player-level** Understat
(capture has 537 player rows; production `event_model_weight=0.0`) and market
odds in the team prior.

Clipping nuance: Arsenal attack multipliers are **1.45 for all six GW1–GW6
fixtures**, so Saka EP is flat even though FDR/xG opponents differ. Audit
trails should expose pre-clip expected xG / Elo, not only the bounded
multiplier, or agents will conclude fixtures do nothing for elite sides.

### Player Understat join (naive probe)

With team aliases + web_name/full-name overlap: ~354/537 unique matches,
~4 ambiguous (Murphy/Fletcher collisions), ~179 missing. Many misses are
**expected**, not bugs:

- Understat 2025 still includes relegated-club players (West Ham, Burnley,
  Wolves, etc.) absent from the 2026/27 FPL bootstrap.
- Club changes break team-scoped joins (e.g. Rogers now Chelsea in bootstrap,
  still Villa-tagged in the 2025 Understat row until remapped).
- Some stars are simply not in the current bootstrap universe (e.g. no Salah
  row in this checkpoint’s elements).

Ticket 01 must ship a real identity report with quarantine and
cross-club remaps — not this probe.

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

### Set-piece volume ready for visibility

Admitted roles on this checkpoint: 64 penalty / 60 DFK / 71 corner-or-indirect
(195 active). Rank-1 pens include Saka, Palmer, Isak, Haaland, Mateta, etc.
Ticket 04 is visibility-first.

### Suggested implementation order

1. Ticket 01 — resolved
2. Ticket 02 — resolved (fixture audit companion)
3. Ticket 03 — resolved (availability → start_p blend)
4. Ticket 04 — resolved (set-piece surface)
5. Ticket 06 — resolved (gap panel)
6. Ticket 05 — resolved (keep fatigue weight 0.25)

### Rebuild proof (2026-08-02)

Sealed `reports/live/.../weekly-2026-08-02/` is immutable (pre-ticket lineage).
Packet-depth rebuild for the same manifest materialised companions at:

`reports/live/2026-27/initial-squad/weekly-2026-08-02-packet-depth/`
(gitignored; recreate via `scripts/run_initial_squad_checkpoint.py` with a
distinct `--output-root` or by replacing that parallel directory).

Observed on rebuild:
- `fixture-audit.json` — 509 players, schema `initial-squad-fixture-audit-v1`
- `availability-blend.json` — status `applied`; 4 doubtful claims (Guehi,
  Rogers, Anderson, Senesi) depress start_p / EP across GW1–6
- `gap-panel.json` — odds/ratings/promoted/transfers still unavailable;
  availability blended; set-pieces surfaced shadow-only
- Set-piece roles attached (e.g. Saka pens rank 1; `effect_weights: null`)

Next weekly capture can seal companions on the canonical checkpoint id.

Next frontier: real T-24h odds slot (~20 Aug), optional horizon-aware fatigue
vector without raising weight, event-weight challenger promotion only after
calibration.

## Cross-links

- Prior gap programme: `.scratch/evidence-gap-fill/` (tickets 01–06 largely
  resolved; odds slot runbook still human-gated).
- Model-run evidence admission: ADR-0023 /
  `docs/decisions/0023-model-run-evidence-admission-and-rationale.md`.
