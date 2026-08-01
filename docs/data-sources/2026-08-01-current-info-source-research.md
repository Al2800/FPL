# Research: current-info sources for the live-faithful optimiser

**Date:** 2026-08-01  
**Status:** research / owner decisions pending  
**Trigger:** strategy dry-runs showed the host still scores on a thin packet —
club + FDR fixtures yes; live minutes / market strength / event xG mostly no.  
**Governance:** plan §6.2, `AGENTS.md` (no collection without registry),
ADR-0001/0002, ADR-0022 (LLM must not invent start probs).

This note maps **what the optimiser needs**, **which serious sources can
supply it**, **registry/licence state**, and **what to do next** without
turning web-search narrative into fake xMins.

---

## 1. What “current info” means for Plane B

| Signal | Decision job | Present on `weekly-2026-07-31`? |
|---|---|---|
| Club identity | Who the player plays for | **Yes** — bootstrap `team` / packet `club_id` |
| Opponent + home/away | Who they play this GW | **Yes** — official fixtures bound into feature state |
| Fixture strength | Scale EP by difficulty | **Partial** — official FDR only (`official_fdr_team_prior_baseline`) |
| Expected minutes / start | Will they play ~60–90? | **Weak** — flat 6-GW `start_probability` from prior + `status=a`; no news adjustment; WC fatigue **0** |
| Expected goals / attack rates | Goal involvement intensity | **Historical prior only** — live `event_model_weight = 0.0`; bootstrap season `expected_*` present but not wired as live GW features |
| Market team strength | Replace/supplement FDR | **No** — The Odds API enabled in registry but freeze reason `optional_licensed_odds_not_configured` |
| Role / injury / return | Minutes overrides | **No ledger binding** — citation paths exist; availability family degraded |
| WC return fatigue | GW1–5 minutes prior | **CSV exists, not admitted** — registry source `world-cup-2026` still `enabled: false`; freeze gap `optional_world_cup_priors_not_supplied` |

Haaland example on that freeze: EP varies by FDR
`[5.74, 5.74, 6.6, 4.88, 6.6, 4.88]`, but `start_probability` is flat `0.815`
and `world_cup_fatigue = 0.0` even though
`control/identities/world-cup-2026-priors.csv` labels him `extreme`
(Norway QF, 465 WC minutes).

---

## 2. Open-source / commercial practice (why these sources)

| Practice | Minutes | Attack / xG | Team strength | Lesson for us |
|---|---|---|---|---|
| **FPL Review** (commercial) | Proprietary simulated **xMins**, human+auto news | Own model | Own model | Best fidelity; **not registrable as free scrape**; never invent equivalent in an LLM |
| **Sertalp open-fpl-solver** | Bring-your-own projections | BYO | BYO | Keep forecasting separate from LP legality |
| **OpenFPL** (arxiv 2508.09992, MIT) | FPL **availability tags**, no proprietary xMins | **Understat** xG/xA/team metrics | Fixtures + Understat team context | Honest open baseline; Understat rights still **unresolved** in our registry |
| **This lab (target)** | Official chance/status + cited lineups/news + WC priors → capped adjustments | Prior rates; optional event model; official/bootstrap `expected_*` with care | FDR baseline → odds / Elo challengers | Degrade visibly; no silent fabrication |

---

## 3. Source shortlist by signal

### 3.1 Expected minutes / start probability

| Source | Registry | Licence / allowed use | Cadence | Fit | Verdict |
|---|---|---|---|---|---|
| **FPL bootstrap** `status`, `chance_of_playing_*`, `news`, `news_added` | `fpl-official-endpoints` **enabled** | restricted; private local | Snapshot cadence | Canonical Tier-0 availability (plan §7) | **Use now** — calibrate to P(start) (handoff **W7**) |
| **FPL element-summary** history | same | same | Bounded IDs | Post-GW minutes oracle / calibration | **Use** for calibration, not pre-deadline invention |
| **Official club / PL lineups & minutes** | `official-lineups-minutes` **enabled** citation | restricted citation | Matchday | Confirmed XI → ledger → capped start delta | **Use** via citation protocol (already decided 2026-07-31) |
| **Official club communications** | `official-club-communications` **enabled** citation | restricted citation | Daily | Injury/return/role claims | **Use** for high-impact citations only |
| **World Cup 2026 priors CSV** | `world-cup-2026` **disabled** auto; derived CSV committed | unknown / private one-off priors | One-off | GW1–5 fatigue tiers (`none`…`extreme`) | **Wire derived artifact** after owner enablement path; do not scrape FIFA bulk |
| **Predicted lineup services** (FFS, Rotowire, etc.) | **not registered** | subscription; accuracy unknown | Pre-deadline | plan §6 Tier-2 candidates | **Do not collect** until registry + rights + accuracy benchmark |
| **FPL Review xMins** | **not registered** | proprietary paid | Hourly | Gold standard commercial | **Out of scope** as automated source; may inform strategy debate with citation only (Plane D), never silent EP blend |
| **Sportradar** | `sportradar-soccer` disabled | unknown / paid | Matchday | Lineup challenger | **Remain off** (lineups decision) |

**Research conclusion (minutes):** serious current minutes intel is
**official FPL flags + official citations + WC priors**, not an unregistered
xMins feed. The gap is **wiring and calibration**, not “find a magic scrape.”

### 3.2 Expected goals / attacking rates

| Source | Registry | Licence | Fit | Verdict |
|---|---|---|---|---|
| **2025/26 player prior** (vaastav-backed envelope) | `vaastav-fpl` enabled local | restricted; no redistribution | `points_per_90`, historical `expected_goals_per_90` in prior build | **Already in live prior** |
| **FPL bootstrap `expected_goals*` / `expected_assists*`** | `fpl-official-endpoints` | restricted | Season-level Opta-derived fields on elements (e.g. Haaland `expected_goals=25.50` on 31 Jul freeze with `form=0.0` — treat as **carried official season rates**, not live GW xG) | **Research then wire carefully**; do not treat as next-match xG |
| **Understat** | `understat` **disabled** | **unknown / unresolved** | Player/team xG, xA, PPDA — OpenFPL’s open attack feed | **Rights review required** before any fetch; gap accepted until then |
| **StatsBomb open data** | `statsbomb-open` enabled local files only | restricted; attribution; no network downloader | Method prototyping; **not** assumed to cover live 2026/27 EPL | Shadow ratings only; not live xG spine |
| **Commercial EPL event data** | `commercial-epl-event-data` disabled placeholder | unresolved | Production event xG | Buy only after Tier 0–2 ablation proves bottleneck (registry note) |
| **Live `event_model_weight`** | model config | n/a | Currently **0.0** in live-faithful | Keep off until odds/Understat-class inputs are admissible |

**Research conclusion (xG):** do **not** scrape Understat yet. Prefer (1)
historical prior rates already in use, (2) documented use of official FPL
`expected_*` fields with temporal caveats, (3) odds-implied team attack as a
challenger once slots exist, (4) Understat only after `licence_status` +
`allowed_use` are resolved.

### 3.3 Team strength / who they play (beyond FDR)

| Source | Registry | Licence | Fit | Verdict |
|---|---|---|---|---|
| **Official fixtures + FDR** | `fpl-official-endpoints` | restricted | Opponent, H/A, difficulty 1–5 | **In use** (baseline limitation acknowledged) |
| **The Odds API** (h2h, totals) | `the-odds-api` **enabled** | restricted; private local; key in env | Pre-deadline market team strength / CS proxies | **Highest leverage registered gap** — capture T-24h…final slots (docs already exist) |
| **football-data.co.uk** | enabled historical | restricted + attribution | Historical closing/pre-closing odds; Elo fits | **Historical / comparator**; not a substitute for live timestamped odds |
| **ClubElo** | disabled | About page (fetched 2026-08-01): author permits reuse of calculations/rankings **for any further use with citation** | External Elo team strength | **Rights look favourable** — owner should set `licence_status: restricted`, `allowed_use: private_analysis_with_attribution`, then enable bounded PIT capture |
| **Bootstrap team strength ratings** | official | restricted | Coarse attack/defence ratings on `teams[]` | Benchmark as baseline (plan); not ground truth |

**Research conclusion (strength):** opponents are already known; **replace FDR
monoculture** with registered **odds** first, then **ClubElo** as a
point-in-time comparator once licence fields are updated.

### 3.4 Explicit non-sources for Plane B

- Unregistered blogs / X / FPL Review screenshots → Plane D citations only.
- LLM-invented start_prob / xMins tables → forbidden (ADR-0022).
- Sportradar / paid lineup APIs → off unless owner reopens.
- Bulk HTML scrape of club sites → off; citation metadata only.

---

## 4. Wiring gaps (data we already have but do not apply)

These are **research findings**, not collector asks:

1. **WC priors CSV committed but freeze degraded**  
   - Artifact: `control/identities/world-cup-2026-priors.csv` (176 rows; Haaland `extreme`).  
   - Freeze: `world_cup_return_fatigue` → `optional_world_cup_priors_not_supplied` because registry `world-cup-2026.enabled: false` and snapshot did not supply the optional path.  
   - Action: owner decision to admit the **derived CSV** into launch_context / WC family without enabling FIFA bulk scrape.

2. **Launch context hash mismatch**  
   - `launch_context` degraded: `official_bootstrap_hash_mismatch`.  
   - Rebuild launch_context against current bootstrap before next checkpoint.

3. **Odds adapter enabled, slots empty**  
   - `the-odds-api` ok in registry; freeze `optional_licensed_odds_not_configured`.  
   - Action: configure key locally, run slot capture runbook (`docs/data-sources/2026-27-live-odds-provider.md`).

4. **Availability citation path enabled, ledger unbound**  
   - `availability_role_evidence` degraded on freeze.  
   - Action: cite high-impact official news into ledger; keep ±0.25 start-prob cap (ADR-0013).

5. **W7 calibration not done**  
   - Map `chance_of_playing_next_round` ∈ {25,50,75,100,null+status} → empirical P(start).  
   - Agent-ready in `docs/reviews/2026-07-review-implementation-handoff.md`.

---

## 5. Recommended sequence (serious, governed)

| Priority | Work | Unlocks | Blocker |
|---|---|---|---|
| **P0** | Bind WC priors CSV + rebuild launch_context for next checkpoint | Non-zero `world_cup_fatigue` on deep runners | Owner: treat derived CSV as admissible input while auto source stays disabled |
| **P0** | Implement **W7** availability-flag → start_prob calibration | Bootstrap news becomes numeric minutes signal | Raw vaastav/history prerequisite (handoff) |
| **P0** | Capture **The Odds API** pre-deadline slots | Team strength beyond FDR | Local `THE_ODDS_API_KEY`; runbook |
| **P1** | Cite official minutes/availability for XI risk names (Rogers, Guéhi, Senesi, …) | Ledger-capped start deltas | Human citation time |
| **P1** | ClubElo licence field update + PIT adapter enablement | Elo challenger vs FDR | Owner approve registry text (reuse+cite looks OK) |
| **P2** | Documented bootstrap `expected_*` feature policy | Official attack rates without Understat | Temporal semantics review (season totals vs GW) |
| **P2** | Understat rights review | OpenFPL-class xG features | Must resolve `licence_status` / ToS before fetch |
| **P3** | Predicted-lineup vendor survey (FFS/Rotowire/…) | Optional Tier-2 minutes | New registry entries + cost + accuracy eval |
| **Never automatic** | FPL Review xMins scrape / LLM xMins | — | Proprietary / ungoverned |

---

## 6. How strategy agents should use this (until wired)

Plane D may **search and cite** team news, but must:

- tag evidence (`bootstrap` / `official` / `community` / `packet` / `unknown`);
- keep minutes **qualitative** unless packet/ledger supplies numbers;
- treat “missed tour / late return” as **output/sharpness risk** for nailed
  premiums (Haaland), not automatic non-start, unless official status says so.

That keeps research pressure on **sources + wiring**, not on smarter
hallucinated xMins.

---

## 7. Owner decisions requested

1. Admit `control/identities/world-cup-2026-priors.csv` into the next
   preseason checkpoint’s WC / launch_context path without enabling
   `world-cup-2026` automated collection?  
2. Prioritise odds slot capture this week (key already approved in registry)?  
3. Approve ClubElo registry upgrade to restricted + attribution and enable
   bounded PIT download?  
4. Commission Understat ToS/rights review, or keep gap and lean on official
   `expected_*` + odds?  
5. Open W7 calibration ticket now that raw-data prerequisites are in view?

---

## 8. References

- Plan §6–7 (source tiers; expected-minutes weakness; WC priors; odds baseline)
- `control/sources/source-registry.yaml` v0.6.3
- `docs/architecture/2026-27-decision-data-flow.md`
- `docs/data-sources/dataset-roadmap.md`
- `docs/data-sources/profiles/expected-minutes-evidence.md`
- `docs/data-sources/world-cup-2026-priors.md` + CSV
- `docs/data-sources/2026-27-odds.md` / `2026-27-live-odds-provider.md`
- `docs/data-sources/2026-27-lineups-citation-decision.md`
- `docs/decisions/0022-strategy-prompt-evidence-stance.md`
- OpenFPL: https://arxiv.org/abs/2508.09992 ; https://github.com/daniegr/OpenFPL
- FPL Review xMins (commercial, reference only): https://docs.fplreview.com/the-model/projections/xmins/
- ClubElo re-utilisation (About, 2026-08-01 fetch): cite author; reuse permitted
- Sertalp: https://github.com/solioanalytics/open-fpl-solver
