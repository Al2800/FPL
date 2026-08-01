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
└──────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────┐    ┌────────────────────────────────────────┐
│ PLANE A — HARD STATS       │    │ PLANE C — UNSTRUCTURED / CITATION      │
│ Official FPL, Vaastav,     │    │ Official club / lineups / news         │
│ football-data, odds, …     │    │ → live evidence ledger (registered)    │
└─────────────┬──────────────┘    └───────────────────┬────────────────────┘
              ▼                                       │
┌────────────────────────────┐                        │
│ PLANE B — STAT BASE        │                        │
│ 2025/26 player prior       │                        │
│ Six-GW live-faithful       │                        │
│ Frozen packet (read-only   │◄── retrieval packet ───┘
│  for all arms)             │
└─────────────┬──────────────┘
              │
              ├──────────────────────────────┐
              ▼                              ▼
┌──────────────────────────┐   ┌───────────────────────────────────────────┐
│ COMPARATOR ARMS          │   │ PLANE D — STRATEGY DECISION AGENT         │
│ deterministic / robust   │   │ Composer 2.5 + web search                 │
│ EP beams (not final)     │   │ PRIMARY ADVISORY DECISION                 │
└──────────────────────────┘   │ recommended 15 · chips · captains         │
              │                │ reasons · falsifiers · citations          │
              │                └─────────────────────┬─────────────────────┘
              │                                      │ declared 15
              ▼                                      ▼
              ┌──────────────────────────────────────────────────────────┐
              │ HOST: rules validate + rescore against frozen packet     │
              │ Challenger may stress-test rationale                     │
              │ Owner approval still required for FPL entry              │
              │ (LLMs never enforce or execute)                          │
              └──────────────────────────────────────────────────────────┘
```

**Same place rule**

- **Numbers the agent reasons over** live in the frozen Plane B packet (plus
  any host-applied ledger adjustments).  
- **The advisory choice of 15 / chips / captains** is produced by Plane D.  
- **Legality and objective scores** are always recomputed by the host on that
  same packet — the agent does not privately “win” by inventing totals.


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

**LLM contract for Plane B:** every arm — including the strategy decision
agent — binds to the **same** frozen packet hash. Deterministic/robust beams
are comparators. The strategy agent’s declared 15 is rescored on that packet.

## 5. Plane C — unstructured / citation agents

| Channel | Registry | How collected | Lands in | May move the squad? |
|---|---|---|---|---|
| Official club communications | `official-club-communications` | Manual citation (HTML scrape off) | Live evidence ledger if admitted | Only via claim → retrieval → adjustment |
| Official lineups / minutes | `official-lineups-minutes` | Manual citation (enabled citation path) | Ledger | Same |
| Official rules/news HTML | `fpl-official-rules-news` | Manual | Rules YAML / citations | Rules path, not EP blend |
| Unregistered X / blogs / “Review vs Solio” takes | **not registered** | Strategy agent web search | Informs Plane D decision (cited) | Via strategy agent’s declared 15 (host-rescored); not via silent EP blend |

Admission rules (`2026-27-evidence.json`):

- `manual_citation` for club/lineups/news;  
- `unregistered_analyst_or_blog_policy: reject_until_source_registry_and_owner_approval`;  
- append-only, content-addressed ledger;  
- claim confidence floor **0.55** (config); adjustment policy **0.60** (ADR-0013).

## 6. Plane D — web strategy decision agent (Composer 2.5)

Prompt: `prompts/daily-strategy-research/v1.md`  
Recipe: `config/automations/2026-27-daily-strategy-research.json`

**Role:** primary advisory decision arm (reason + strategise + recommend).

| Lane | Output | Join rule |
|---|---|---|
| A — official discovery | Metadata leads + discovery JSON (gitignored) | Human may create **Plane C** citations |
| B — strategy decision | `reports/strategy-research/YYYY-MM-DD.md` with recommended 15, chips, captains | Declared 15 handed to host for rules validation + rescoring on frozen packet |

Community debate does not rewrite prior rates. It informs the agent’s choice
of structure; the host still scores that choice on Plane B.

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

### 7.2 Evidence adjustments (optional numeric fork)

From ADR-0013 / `evidence-adjustments.yaml` — still available when a claim
should move a **rate** inside the packet before arms run:

- min adjustment confidence **0.60**;  
- start-probability delta cap **±0.25**;  
- citation + expiry + signal required;  
- challenger + host validation on a packet fork.

### 7.3 Strategy decision weight (final advisory choice)

The strategy agent does **not** blend community EV into `points_per_90`.
Its weight is applied at the **selection layer**:

```text
frozen packet (Plane B) + web reasoning (Plane D)
  → strategy agent declares 15 / chips / captains
  → host rules-validates + rescores on the same packet
  → deterministic/robust arms kept as published comparators
  → owner approval for any FPL entry
```

So community/strategy signal is decisive for *which legal squad we prefer*,
while hard-stat weights remain decisive for *how that squad is scored*.

## 8. Collection checklist (same place)

| Step | Collect into | Owner |
|---|---|---|
| 1. Official hard stats | Immutable preseason/live snapshot manifest | Scheduler / capture scripts |
| 2. Historical rebuild | Local prior envelope (one season) | `build_live_player_prior` / locked replay prior |
| 3. Optional odds/ratings | Slot artifacts referenced by checkpoint family state | Odds/ratings adapters |
| 4. Freeze packet | Feature state + six-GW horizon + solver input | Checkpoint runner |
| 5. Daily strategy decision | Recommended 15 + chips (+ discovery JSON gitignored) | Composer automation (Plane D) |
| 6. Promote official leads | Live evidence ledger claims | Human / citation protocol |
| 7. Host validate / rescore | Strategy 15 on frozen packet; publish comparators | Deterministic host |
| 8. Challenge (optional) | Stress-test rationale / adjustments | Challenger |
| 9. Owner gate | Approval approval / manual entry | Owner |

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
| Strategy decision automation not yet activated in Cursor UI | D | No primary advisory 15/chip decision each morning |
| (resolved) Live default prior is 2025/26 | B | Older 2024/25 replay prior kept for historical ablations only |

## 10. Design stance (do not erode)

1. **Registry gates collection.** Web search does not invent registry rights.  
2. **One statistical base per checkpoint** (content-addressed).  
3. **Strategy agent is the final advisory chooser; host validates and scores.**  
4. **Deterministic beams are comparators**, not the preferred decision.  
5. **LLMs never enforce rules or execute FPL actions.**  
6. **Degrade visibly** rather than invent neutral odds/ratings/xMins.  
7. **Ledger claims** remain the path for structured evidence rates; community
   text informs Plane D selection with citations.

## 11. Immediate wiring priorities

1. Activate the Composer strategy **decision** automation (Plane D).  
2. Keep official capture + 2025/26 prior packet builds on cadence (A/B).  
3. After each checkpoint, rescore the strategy agent’s declared 15 on that
   packet and publish diffs vs deterministic/robust comparators.  
4. Admit only high-impact official citations into the ledger (Plane C).
