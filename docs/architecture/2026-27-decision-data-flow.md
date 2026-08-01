# 2026/27 decision data-flow map

**Status:** Active working architecture (Phase 0/1)  
**Audience:** owner + agents designing daily collection and LLM use  
**Related:** `docs/architecture/point-in-time-contract.md`,  
`docs/evaluation/2026-27-evidence-acquisition-retrieval-design.md`,  
`docs/evaluation/2026-27-daily-agent-strategy-loop.md`,  
`control/sources/source-registry.yaml`,  
`control/policies/evidence-adjustments.yaml`,  
`control/policies/feature-source-precedence.yaml`

## 1. What this map answers

1. Which **hard stats** we collect, from where, and what is still missing.  
2. How those stats become the **statistical base** every LLM may see.  
3. How **unstructured** and **web-search** agents add information.  
4. The **single join path** into a decision (so nothing “floats” unweighted).  
5. How **weighting** works — and what is deliberately *not* blended.

## 2. End-to-end picture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ PLANE 0 — GOVERNANCE                                                     │
│ source-registry.yaml · rules YAML · evidence / capture configs           │
│ (nothing collects or admits without this)                                │
└──────────────────────────────────────────────────────────────────────────┘
                 │ enables / blocks
                 ▼
┌────────────────────────────┐    ┌────────────────────────────────────────┐
│ PLANE A — HARD STATS       │    │ PLANE C — UNSTRUCTURED / CITATION      │
│ Official FPL API           │    │ Club / PL / lineups (manual citation)  │
│ Vaastav history            │    │ Official FPL news (manual citation)    │
│ football-data.co.uk        │    │                                        │
│ Odds API (slots)           │    │ PLANE D — WEB STRATEGY SEARCH          │
│ StatsBomb Open (local)     │    │ Composer daily research (X/blogs/etc.) │
│ Launch context / WC priors │    │ → briefing ONLY unless promoted        │
└─────────────┬──────────────┘    └───────────────────┬────────────────────┘
              │                                         │
              ▼                                         ▼
┌────────────────────────────┐    ┌────────────────────────────────────────┐
│ PLANE B — STAT BASE        │    │ LIVE EVIDENCE LEDGER                   │
│ Player prior (one season)  │    │ append-only claims + rights snapshot   │
│ Team/FDR prior             │    │ (official / registered citations only) │
│ Feature state              │    └───────────────────┬────────────────────┘
│ Six-GW live-faithful       │                        │
│   forecast packet          │                        ▼
│ Initial-squad / solver     │    ┌────────────────────────────────────────┐
│   input (frozen)           │───▶│ CANDIDATE-BOUNDARY RETRIEVAL PACKET    │
└────────────────────────────┘    │ small, budgeted claims for LLM arms    │
                                  └───────────────────┬────────────────────┘
                                                      │
              ┌───────────────────────────────────────┼──────────────────┐
              ▼                                       ▼                  ▼
     Deterministic / robust                  Evidence-agent arm    Challenger
     optimiser (no LLM)                      proposes bounded      accept/reject
                                             EP / minutes deltas
                                                      │
                                                      ▼
                                  ┌────────────────────────────────────────┐
                                  │ HOST VALIDATION + SCORED PROPOSAL      │
                                  │ rules · hashes · approval gate         │
                                  │ (LLMs never enforce or execute)        │
                                  └────────────────────────────────────────┘
```

**Same place rule:** anything that can change a squad must either

- already sit inside the **frozen forecast / solver packet** (Plane B), or  
- enter as a **ledger claim** → **retrieval packet** → **bounded adjustment**  
  that the host reapplies onto that same packet.

Strategy briefings (Plane D) are *inputs to human attention*, not a second
scoring path.

## 3. Plane A — hard stats inventory

| Family | Source id | Where from | Local landing | Collector status | Used in stat base? | Gap today |
|---|---|---|---|---|---|---|
| Player market, prices, status, `ep_next`, FDR, ownership | `fpl-official-endpoints` | FPL public API (`bootstrap-static`, `fixtures`, bounded `element-summary`, post-lock `event-live`) | `data/snapshots/2026-27/preseason/<checkpoint>/` | **Enabled** automated | Yes — universe + cold-start fields | Only sparse preseason cadence so far; need T-48h…final chain |
| Historical player-gameweek events | `vaastav-fpl` | Community mirror of FPL-derived CSVs | gitignored historical root / warehouse | **Enabled** download | Yes — builds **player prior** | Private local only; not redistributable |
| Historical match results (+ legacy odds files) | `football-data-co-uk` | football-data.co.uk E0 files | gitignored historical root | **Enabled** download | Team/Elo calibration; diagnostic odds | Upload timing ≠ exact pre-deadline odds |
| Live licensed odds | `the-odds-api` | The Odds API | `data/live-shadow/` odds slots | **Enabled** adapter; slots empty until key + market window | Optional live-faithful component | **Zero 2026/27 slots** yet |
| Event / shot open data | `statsbomb-open` | Pre-acquired local files | local transform only | **Enabled** prototyping | Shadow / ablation; EP event weight = 0 | No 2026/27 PL coverage claim |
| Launch context (promoted / new / WC fatigue flags) | derived + `world-cup-2026` inputs | Bootstrap + prior roster + WC CSV | `data/snapshots/2026-27/launch-context/<hash>/` | WC source still registry-disabled; context builder used | Yes — post-forecast packet flags | Return-to-training dates mostly missing |
| Manager bank / squad / chips / FTs | `fpl-authenticated-manager-state` | Manual entry (ADR-0005) | GDR / manual state | **Disabled** automation | Required for live transfer weeks; initial-squad uses full £100m market | Must be typed by owner before weekly decisions |
| Overall ranks | FPL standings endpoint (bounded) | Official classic league 314 | post-finalisation only | Capture allowed post-lock only | Calibration only | Never a pre-deadline feature |
| ClubElo / Understat / FBref / commercial event / Sportradar | various | — | — | **Disabled** | No | Rights / cost / phase gates |

### Hard-stat collection cadence (intended)

From `config/data_sources/2026-27-evidence.json` + capture scheduler:

- **Daily preseason** official bootstrap/fixtures (and scheduler 07:00 / 10:00 London).  
- **Deadline-relative:** T-48h, T-24h, T-8h, T-2h, final, post-match.  
- **Odds:** T-24h / T-8h / T-2h / final when markets + key exist.  
- Missed window → **recorded gap**, never silent backfill.

## 4. Plane B — statistical base for LLMs

This is the structured spine. Agents may **read** it; they do not rewrite it
in place.

| Artifact | Built from | Weighting inside the artifact | Path / owner |
|---|---|---|---|
| **Player prior** (one completed season) | Vaastav completed 2025/26 | Single envelope per run — **not** blended with older seasons | Default: `reports/forecasting/2026-27-shared-player-prior-2025-26.json` (season `2025-26`) |
| **Team / FDR prior** | Official fixtures FDR (live initial-squad) | Explicit baseline limitation when Elo/odds absent | Built inside `live_initial_squad` |
| **Feature state** | Official bootstrap + fixtures + optional odds/ratings | Precedence in `feature-source-precedence.yaml`; missing optional → degrade | Checkpoint-bound |
| **Six-GW live-faithful horizon** | Prior + feature state + model config | See §6 | `live-faithful-v1.feature-complete` |
| **Frozen solver / initial-squad packet** | Horizon vectors + launch-context flags + rules hash | Discount factors 1.0…0.59 over 6 GWs; shrinkage weights in policy | `build_initial_squad_packet` |

**LLM contract for Plane B:** the evidence-agent and challenger receive the
**same** frozen packet hash as the deterministic arm. They may propose
adjustments or a full 15; the host rescoring path is identical.

## 5. Plane C — unstructured / citation agents

| Channel | Registry | How collected | Lands in | May move the squad? |
|---|---|---|---|---|
| Official club communications | `official-club-communications` | Manual citation (HTML scrape off) | Live evidence ledger if admitted | Only via claim → retrieval → adjustment |
| Official lineups / minutes | `official-lineups-minutes` | Manual citation (enabled citation path) | Ledger | Same |
| Official rules/news HTML | `fpl-official-rules-news` | Manual | Rules YAML / citations | Rules path, not EP blend |
| Unregistered X / blogs / “Review vs Solio” takes | **not registered** | Strategy agent search only | Strategy briefing | **No** — unless a future registry entry + owner approval exists |

Admission rules (`2026-27-evidence.json`):

- `manual_citation` for club/lineups/news;  
- `unregistered_analyst_or_blog_policy: reject_until_source_registry_and_owner_approval`;  
- append-only, content-addressed ledger;  
- claim confidence floor **0.55** (config); adjustment policy **0.60** (ADR-0013).

## 6. Plane D — web strategy search (Composer 2.5)

Prompt: `prompts/daily-strategy-research/v1.md`  
Recipe: `config/automations/2026-27-daily-strategy-research.json`

| Lane | Output | Join rule |
|---|---|---|
| A — official discovery | Metadata leads + discovery JSON (gitignored) | Human may create **Plane C** citations |
| B — strategy intelligence | `reports/strategy-research/YYYY-MM-DD.md` | **Does not** enter ledger or prior weights |

This is how chip paths, DEFCON shortlists and model-disagreement narratives
are rebuilt daily without contaminating the statistical base.

## 7. Weighting — what mixes, what must not

### 7.1 Inside the hard-stat forecaster (automatic)

From `live-faithful-v1.feature-complete`:

| Mechanism | Parameter | Effect |
|---|---|---|
| Player prior vs position/price cohort | `player_prior_reliability_minutes = 900` | `w = sample_min / (sample_min + 900)` |
| Prior vs current-season form | `prior_equivalent_minutes = 1350` | At GW1 cold start, current minutes = 0 → **100% prior** (after cohort shrink) |
| Start probability | `start_prior_equivalent_matches = 2` | Pseudo-count blend with observed starts |
| Recent minutes trajectory | `recent_minutes_weight = 0.5` | Only once last-3 history exists |
| Fixture strength | FDR/Elo scale `0.25`, bounds `[0.7, 1.3]` | Multiplies expected points per fixture |
| Event decomposition | `event_model_weight = 0.0` | **Off** — retained as rejected ablation |
| Odds / unstructured | optional | **Absent → degrade**, never fabricate 0.5 / “neutral” |

**Priors:** exactly **one** prior envelope per run. The live default is the
completed **2025/26** envelope. Older replay priors remain available for
historical ablations only — they are never averaged together with the live
default.

### 7.2 Evidence adjustments (LLM path — bounded, not free blend)

From ADR-0013 / `evidence-adjustments.yaml`:

- min adjustment confidence **0.60**;  
- start-probability delta cap **±0.25**;  
- citation + expiry + signal required;  
- challenger must accept; host validates;  
- applied only onto a **copy** of the frozen solver input (fork), never by
  silently editing Plane B hashes.

This is the only sanctioned way unstructured/web-promoted evidence changes
numbers the optimiser sees.

### 7.3 Strategy briefing (explicit zero forecast weight)

Lane B community content has **weight 0** in EP, starts, and prior math.
It influences the human (and optionally which boundaries to inspect). To
affect the squad it must be promoted:

```text
briefing watchlist
  → (optional) official URL citation in ledger
  → retrieval packet
  → evidence-agent bounded delta
  → challenger + host
  → rescored proposal
```

## 8. Collection checklist (same place)

| Step | Collect into | Owner |
|---|---|---|
| 1. Official hard stats | Immutable preseason/live snapshot manifest | Scheduler / capture scripts |
| 2. Historical rebuild | Local prior envelope (one season) | `build_live_player_prior` / locked replay prior |
| 3. Optional odds/ratings | Slot artifacts referenced by checkpoint family state | Odds/ratings adapters |
| 4. Daily strategy + discovery | Briefing + gitignored discovery JSON | Composer automation |
| 5. Promote official leads | Live evidence ledger claims | Human / citation protocol |
| 6. Freeze packet | Feature state + six-GW horizon + solver input | Checkpoint runner |
| 7. Retrieve for LLMs | Candidate-boundary packet from **that** freeze | Retrieval layer |
| 8. Propose / challenge | Adjustments bound to packet hash | Evidence agent + challenger |
| 9. Score & gate | Recommendation + approval blockers | Deterministic host |

If a datum cannot be pointed to a row in this table, it is not yet in the
system — do not pretend the optimiser “knows” it.

## 9. Gap board (decision-grade blockers)

| Gap | Plane | Effect if ignored |
|---|---|---|
| Sparse preseason snapshots; T-48h…final not yet run | A | Weak point-in-time chain |
| Live odds slots empty | A/B | Degraded forecast; no market signal |
| Player ratings unavailable for 2026/27 PL | A/B | Shadow-only / zero effect |
| Club/press citations not yet admitted for candidates | C | Minutes/availability stay official-status only |
| Manager state manual | A | Cannot run true owned-squad transfer weeks |
| WC return dates thin | B | Fatigue flags incomplete |
| Strategy briefings not yet activated in Cursor UI | D | Human lacks daily chip/DEFCON depth |
| (resolved) Live default prior is 2025/26 | B | Older 2024/25 replay prior kept for historical ablations only |

## 10. Design stance (do not erode)

1. **Registry gates collection.** Web search does not bypass it.  
2. **One statistical base per checkpoint** (content-addressed).  
3. **LLMs propose; code validates and scores.**  
4. **Degrade visibly** rather than invent neutral odds/ratings/xMins.  
5. **Strategy intelligence and evidence claims are different products** that
   meet only through the ledger → retrieval → adjustment funnel.

## 11. Immediate wiring priorities

1. Activate the Composer daily strategy automation (Plane D) so briefings
   exist every morning.  
2. Keep official capture on the scheduler cadence (Plane A).  
3. Admit only high-impact **official** citations into the ledger (Plane C).  
4. Run initial-squad checkpoints against each new manifest and diff them —
   always from the same frozen packet the agents see.
