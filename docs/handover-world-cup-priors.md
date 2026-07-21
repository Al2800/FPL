# Agent brief: assemble 2026 World Cup priors (Section 7.7)

**Goal:** Fill `control/identities/world-cup-2026-priors.csv` so the expected-minutes model can apply named GW1–5 fatigue / late-return priors for Premier League players who played at the 2026 World Cup.

**Context:** Tournament window was **11 June – 19 July 2026** (final 19 July). As of this brief the tournament has concluded or is concluding — assemble immediately; these priors are most valuable before GW1.

**Governance:** `world-cup-2026` in `control/sources/source-registry.yaml` is **`enabled: false`** for automated bulk collection. Prefer **manual / citation-based assembly** into the CSV. If you need a scripted fetch, first add/complete a registry entry for that specific source with `licence_status` + `allowed_use`, keep redistribution off, and leave raw dumps under gitignored `data/raw/`. Do **not** commit FIFA/Transfermarkt raw HTML dumps to Git.

---

## What “good” looks like

One row per **Premier League–relevant** player who was in a World Cup squad (including those who travelled but barely played).

| Field | Required? | Meaning |
|---|---|---|
| `player_uid` | Ideal | Stable internal id once identity map exists; else leave blank and set `fpl_code` / names for later join |
| `fpl_code` | Strongly preferred | FPL `code` from bootstrap / vaastav `players_raw` — best join key |
| `display_name` | Yes | Common name as published |
| `club_short_name` | Yes | PL club at season start (ARS, LIV, …) |
| `national_team` | Yes | FIFA nation name |
| `reached_round` | Yes | `group` / `r32` / `r16` / `qf` / `sf` / `final` / `champions` / `third` |
| `elimination_date` | Yes | Date national team’s tournament ended (`YYYY-MM-DD`); champions use final date |
| `wc_appearances` | Preferred | Matches played at the tournament |
| `wc_minutes` | Preferred | Total minutes; `0` if unused squad member |
| `return_to_training_date` | Optional | First credible club return-to-training report; often missing — leave blank rather than invent |
| `fatigue_prior` | Derived OK | Coarse label: `none` / `moderate` / `high` / `extreme` (see rules below) |
| `notes` | Optional | Ambiguities, dual nationality, late call-ups |
| `source` | Yes | Short citation list (URLs or “FIFA match centre + FPL bootstrap 2026-07-XX”) |
| `observed_at` | Yes | ISO UTC when you captured the values |

**Done when:**

1. Every PL club’s WC-involved players are present or explicitly listed as “none known” in the run notes.
2. `elimination_date` + `reached_round` filled for all rows.
3. `wc_minutes` filled for ≥90% of rows (squad members with unknown minutes marked `wc_minutes=` blank and `notes=minutes_unconfirmed`).
4. Join check: ≥95% of rows with `fpl_code` resolve to a current FPL `elements[]` entry (or documented misses).
5. Output written to `control/identities/world-cup-2026-priors.csv` (committed) and a short provenance note in `docs/data-sources/world-cup-2026-priors.md`.

---

## Recommended staged approach (do not skip stages)

### Stage 0 — Freeze the PL universe (1 short step)

1. Run / reuse a fresh FPL snapshot: `python3 -m scripts.run_snapshot` (or read latest `data/raw/fpl/*/api_bootstrap-static.json`).
2. Extract the 2026/27 PL player list: `id`, `code`, `web_name`, `first_name`, `second_name`, `team` / club short name, `element_type`.
3. Save a working table under `data/raw/world-cup/` (gitignored), e.g. `pl_universe.csv`. This is the only population that needs priors for FPL.

### Stage 1 — Team-level elimination map (highest leverage, do first)

Build `nation → elimination_date / reached_round` from **match results**, not player pages.

**Preferred sources (citation / open schedule data):**

- FIFA tournament site (canonical results): https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026
- Open schedule/results JSON (verify against FIFA before trusting): https://github.com/openfootball/worldcup.json (`2026/worldcup.json`)

**Method:**

1. For each of the 48 nations, find the last match they played.
2. Set `elimination_date` to that match date; set `reached_round` from the round name.
3. Hosts / early exits still get dates — early exit ⇒ lower fatigue prior, but still useful as “available for pre-season”.

Deliverable: `nation_elimination.csv` (gitignored working file). This alone supports a usable GW1 prior even before minutes exist.

### Stage 2 — Squad membership ∩ PL universe

For each nation that has ≥1 PL player:

1. Obtain the **final 26-man** (or published) World Cup squad.
2. Match squad names to `pl_universe` using, in order:
   - exact `code` if a crosswalk exists;
   - normalised `first_name|second_name`;
   - `web_name` + club;
   - manual resolve for ambiguous cases (common surnames) — log them.
3. Emit one prior row per match with `wc_minutes` blank for now, but `national_team` / `elimination_date` / `reached_round` copied from Stage 1.

**Squad sources:** FIFA team pages, national FA announcements, reputable wire lists. Prefer one primary per nation and cite it.

### Stage 3 — Per-player minutes / appearances

Only after Stages 1–2.

**Practical options (pick the least-rights-sensitive that works):**

1. **Manual for shortlist first:** players who reached QF+ *or* played 270+ minutes — highest GW1 impact.
2. **Semi-structured:** if a rights-cleared stats page or open dataset exposes player tournament minutes, register it, then join on name+nation.
3. **Do not** enable Transfermarkt/FBref bulk scrapers without a registry terms review.

If minutes cannot be obtained quickly: ship Stage 2 file with `fatigue_prior` derived from `reached_round` only (see rules), and note `minutes_pending` in `docs/data-sources/world-cup-2026-priors.md`.

### Stage 4 — Return-to-training (sparse, optional)

Scan official club sites / trusted reports for “returned to training” / “back in pre-season”. Fill `return_to_training_date` only with citations. Missing is normal — the minutes + elimination date already drive the prior.

### Stage 5 — Derive `fatigue_prior` and write outputs

Suggested deterministic rules (encode in the fill script or docs; adjust only with an ADR if changed later):

| Condition | `fatigue_prior` |
|---|---|
| Not in WC squad | omit row (no prior) |
| In squad, `wc_minutes` = 0 | `none` |
| Eliminated in group or R32, minutes &lt; 180 | `none`–`moderate` |
| Reached R16/QF, or minutes ≥ 270 | `moderate`–`high` |
| SF/final, or minutes ≥ 450 | `high`–`extreme` |
| `return_to_training_date` after PL GW1 likely start | bump one tier |

Write:

- `control/identities/world-cup-2026-priors.csv` (commit)
- `docs/data-sources/world-cup-2026-priors.md` — counts by prior tier, join miss list, sources used, `observed_at`

---

## How this plugs into the model (for the implementing agent)

Expected-minutes baseline (WP-05) should accept an optional join on `fpl_code` / `player_uid`:

- Multiply early-GW start probability by a factor, or add a minutes penalty, keyed by `fatigue_prior` and fading by GW (e.g. full effect GW1–2, half GW3–4, none by GW6).
- Keep the adjustment **named and logged** in the Gameweek Decision Record (Section 7.7: “named pre-season priors”), not silently baked into form.

Until the CSV exists, WP-05 may ship with the join interface and identity stub only.

---

## Explicit non-goals

- Scraping FIFA behind logins or bypassing technical controls.
- Committing raw third-party HTML/JSON dumps.
- Perfect Opta-level event data — minutes + elimination date are enough for v1.
- Blocking WP-05 on return-to-training completeness.

---

## Suggested owner checkpoints

Bring back to the owner only if:

1. A new automated source must be **enabled** in the registry (terms unclear).
2. Dual-nationality / club-vs-country identity conflicts need a policy call.
3. You propose different `fatigue_prior` thresholds than the table above.

Otherwise execute Stages 0–5 and open a PR with the CSV + provenance note.
