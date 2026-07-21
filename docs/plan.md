# FPL Agentic Decision Laboratory

**Status:** Initial project plan, revised 21 July 2026 (first review; replay scoping and multi-manager cohort; clarity and acceptance-criteria pass)  
**Plan date:** 21 July 2026  
**Target season:** Fantasy Premier League 2026/27  
**Primary purpose:** A reproducible test environment for data management, forecasting, optimisation, AI-agent orchestration, human oversight and controlled computer-use automation.

---

## How to read this plan

| Need | Where |
|---|---|
| Why the project exists and how success is defined | Sections 1–4 |
| Rules-as-data and source-governance constraints that bind all work | Sections 5–6 |
| Known data problems the design must solve | Section 7 |
| What is being built: architecture, data model, processing, models, optimiser, agents, evidence | Sections 8–14 |
| How the system operates in season and what it outputs | Sections 15–16 |
| How every component is evaluated, including the statistical design | Section 17 |
| Build order, with per-phase exit criteria | Section 18 |
| Deliberately deferred capabilities | Section 19 |
| Concrete work packages, each with acceptance criteria | Section 24 |
| Open decisions and immediate next steps | Sections 25–26 |

FPL and project-specific terms are defined in Appendix A.

---

## 1. Executive summary

This project will use official Fantasy Premier League (FPL) as a controlled environment for studying how AI agents make decisions under uncertainty.

The immediate aim is not simply to create another FPL transfer recommender. Existing projects already provide historical datasets, expected-points models, optimisation solvers, dashboards and chat assistants.

The differentiating proposition is:

> **An open, reproducible decision laboratory that compares deterministic analytics, optimisation, single-agent reasoning and multi-agent orchestration using point-in-time evidence and auditable outcomes.**

FPL is a useful test environment because it combines:

- structured and unstructured data;
- explicit rules and hard constraints;
- uncertain player availability and performance;
- changing prices and fixtures;
- short-term and long-term planning;
- fixed decision deadlines;
- measurable weekly outcomes;
- a real external action that can eventually be automated.

The first implementation will operate in **advisory mode**. It will generate a validated Gameweek proposal, with human entry of the resulting transfers and team selection. More advanced information retrieval, competitive analysis, cloud deployment and computer-use execution remain part of the overall plan but are deliberately scheduled after the initial build.

---

## 2. Core research questions

The principal research question is:

> **Does agentic orchestration add measurable value over a conventional data pipeline, forecasting model and mathematical optimiser?**

Supporting questions include:

1. Does a single tool-using agent improve decisions over a deterministic optimiser?
2. Does a specialised multi-agent review improve decisions over a single agent?
3. Which unstructured information materially improves expected-minutes or player-performance forecasts?
4. Can agent decisions remain grounded, reproducible and compliant with the FPL rules?
5. How should confidence, conflicting evidence and stale information be represented?
6. When does orchestration complexity cease to justify its cost and latency?
7. Can a computer-use agent execute an approved decision safely and verify the result?
8. Which findings transfer to enterprise decision systems outside fantasy football?

Each question has a designated home in the plan:

| Question | Addressed by | Primary evidence |
|---|---|---|
| 1, 2 | Phase 3 experiment; Sections 17.6–17.7 | Multi-season replay for structured-data strategies; live paired shadow evaluation and the multi-manager cohort for evidence-dependent strategies |
| 3 | Section 7.1 benchmarking; WP-05; Phase 3–4 ablations | Per-source accuracy against naive baselines |
| 4 | Sections 4.2, 13 and 21.4; success criterion 6 in Section 3.2 | Agent golden cases and deterministic validation |
| 5 | Sections 9.4 and 14; WP-08 | Evidence-lifecycle records and conflict handling |
| 6 | Sections 13.5 and 17.4; Phase 3 | Cost and latency reported per decision |
| 7 | Phases 7–8; Section 17.5 | Dry-run and execution audit metrics |
| 8 | Retrospectives and evaluation reports | Qualitative synthesis at season end |

---

## 3. Scope and success definition

### 3.1 Initial-build outcome

For each Gameweek, the initial system should produce a **Gameweek Decision Record** containing:

- the data cutoff and FPL deadline;
- current squad, bank, selling prices, transfers and chips;
- player projections and uncertainty;
- candidate transfer strategies;
- recommended starting XI;
- captain and vice-captain;
- ordered bench;
- optional chip recommendation;
- expected gain against doing nothing;
- alternative conservative and aggressive plans;
- supporting and conflicting evidence;
- deterministic rules-validation result;
- final human decision;
- eventual outcome and retrospective.

### 3.2 Initial success criteria

The initial build is successful when it can:

1. reconstruct what data was available before a historical or live deadline;
2. validate a squad, transfer plan and line-up against a versioned rule set;
3. generate baseline player projections without look-ahead leakage;
4. create legal candidate plans through deterministic optimisation;
5. ground qualitative adjustments in cited, expiring evidence;
6. reproduce any decision on demand: deterministic components must return identical results when rerun with identical inputs and versions, and agent components must be fully replayable from recorded prompts, tool calls and cached model outputs (bit-identical regeneration of freshly sampled LLM output is not claimed);
7. compare its recommendation with a do-nothing baseline;
8. record the decision and later evaluate its outcome.

Final FPL rank alone is not an adequate success measure because it contains substantial variance and luck.

---

## 4. Differentiation

### 4.1 Agent versus non-agent comparison

The same Gameweek should eventually be evaluated through parallel strategies:

1. simple statistical baseline;
2. forecast plus deterministic optimiser;
3. one LLM agent using tools;
4. specialised multi-agent review;
5. human decision.

The project will measure whether additional agents improve decision quality enough to justify their cost and complexity. The comparison design — its statistical-power constraints, what replay can and cannot fairly evaluate, and the multi-manager live cohort — is defined in Sections 17.6 and 17.7.

### 4.2 Point-in-time reproducibility

Every recommendation should preserve:

- what information was available;
- when it was published;
- when the system observed it;
- which data and model versions were used;
- which rules were active;
- which prompts and tools were used, with full recorded traces of agent tool calls and model responses sufficient to replay the run without re-sampling the model;
- where agents agreed or disagreed;
- what was finally approved and executed.

### 4.3 Separation of responsibilities

The project separates:

- data ingestion;
- data-quality validation;
- football-event forecasting;
- FPL scoring;
- mathematical optimisation;
- evidence interpretation;
- critical review;
- human approval;
- external execution.

An LLM must not be responsible for enforcing budget, formation or transfer rules.

### 4.4 Robust decisions rather than one answer

The system should expose decision sensitivity, for example:

- safest plan;
- highest expected-value plan;
- no-transfer plan;
- bank-transfer plan;
- aggressive differential plan;
- response to uncertain starting probability;
- response to fixture or injury scenarios.

---

## 5. FPL 2026/27 rules baseline

Rules are data and must be versioned. They must not be scattered through model prompts or optimiser code.

### 5.1 Confirmed for 2026/27

As of 21 July 2026, the Premier League has confirmed:

- two sets of four chips: Wildcard, Free Hit, Triple Captain and Bench Boost;
- one set is available in each half of the season;
- first-half chips expire at the Gameweek 19 deadline;
- up to five free transfers can be banked;
- no exceptional AFCON transfer top-up in 2026/27;
- defensive-contribution points remain;
- live ranks and league positions;
- projected bonus points from approximately 20 minutes into matches;
- Gameweek scores become final at 09:00 UK time on the morning after the final match;
- an official player-price predictor;
- player-position changes for the new season;
- revisions to the Bonus Points System.

Confirmed 2026/27 BPS changes include:

- removal of the BPS penalty for being tackled;
- one BPS for every three clearances, blocks and interceptions rather than every two;
- revised goalkeeper save calculations;
- additional BPS for saving a big chance;
- seven BPS rather than eight for a penalty save, alongside the big-chance-save component.

### 5.2 Existing rules pending launch verification

Current official guidance supports the following, but each item must be checked once 2026/27 FPL is fully live:

- £100.0m initial budget;
- 15-player squad;
- 2 goalkeepers, 5 defenders, 5 midfielders and 3 forwards;
- maximum three players from one Premier League club;
- starting XI containing one goalkeeper;
- at least three defenders, two midfielders and one forward;
- captain and vice-captain;
- formation-preserving automatic substitutions;
- one new free transfer per Gameweek;
- four-point cost for transfers beyond the free allowance;
- selling-price half-profit rule;
- Gameweek deadline 90 minutes before the opening fixture;
- one chip per Gameweek;
- banked transfers retained when using Wildcard or Free Hit;
- current restrictions concerning Wildcard and Free Hit use in Gameweek 1 and adjacent half-season Gameweeks.

These rules should initially carry an `inherited` or `provisional` status.

### 5.3 Rule categories

The machine-readable rule set must cover:

| Category | Required coverage |
|---|---|
| Squad | Budget, size, positions and club limit |
| Line-up | Formation, captain, vice-captain and bench order |
| Transfers | Free allowance, banking, hits, same-position replacement and financial state |
| Prices | Purchase, current and selling prices |
| Chips | Availability, expiry, cancellation and interactions |
| Scoring | Minutes, goals, assists, clean sheets, saves, cards and negative events |
| Defensive contributions | Position-specific thresholds and caps |
| Bonus | Season-specific BPS and tie handling |
| Automatic substitutions | Goalkeeper and formation-preserving outfield replacement |
| Captain fallback | Vice-captain only when the captain records zero minutes |
| Fixtures | Blank, Double, postponed and rescheduled fixtures |
| Corrections | Provisional and final scores |
| Deadlines | Deadline derived from the opening fixture |
| Exceptional events | Season-specific transfer awards or rule changes |

### 5.4 Rule representation

Example:

```yaml
rule_id: transfer.max_banked
season: 2026-27
value: 5
status: confirmed
effective_from: 2026-07-20
source_url: https://www.premierleague.com/en/news/4679873/all-you-need-to-know-about-changes-to-fpl-for-202627
verified_at: 2026-07-21
```

Allowed status values should include:

- `confirmed`
- `inherited`
- `provisional`
- `disputed`
- `retired`

### 5.5 Scoring limitation

The system may not possess every Opta event required to reproduce exact BPS independently. Therefore:

- official final FPL points remain the outcome source of truth;
- rules validation must remain deterministic;
- future bonus points should be forecast probabilistically;
- exact historical BPS reconstruction should not be claimed without complete underlying data.

---

## 6. Data-source strategy

### 6.1 Source hierarchy

#### Tier 1: Canonical operational sources

| Source | Use | Key limitation |
|---|---|---|
| Official FPL rules and news | Rules and season changes | Pages can change and require snapshots |
| FPL JSON endpoints | Players, teams, fixtures, prices, points and status | Unofficial and unsupported as a developer API |
| Authenticated manager state | Squad, bank, chips, transfers and selling prices | Private authentication and automation risk |
| Official club communications | Injuries, returns, transfers and manager comments | Unstructured and sometimes ambiguous |
| Official competition schedules | PL, cups and European matches | Multiple identifiers and frequent revision |

The FPL public endpoints were unavailable during the pre-launch review. The ingestion design must tolerate off-season resets, 404 responses, schema changes and cache rebuilds.

#### Maximising official FPL endpoint data

The official FPL endpoints already carry substantially more decision-relevant signal than the basic player/price/points fields, and this data should be exploited fully before any third-party collection is enabled. Subject to launch verification of the 2026/27 schemas, the known coverage includes:

| Endpoint (indicative) | Decision-relevant content |
|---|---|
| `bootstrap-static` — players | Status flags, `news` text and `news_added` timestamp, `chance_of_playing_this_round`/`next_round`, `ep_this`/`ep_next`, form, points per game, ICT index components (influence, creativity, threat), `selected_by_percent`, per-Gameweek `transfers_in_event`/`transfers_out_event`, `cost_change_event`/`cost_change_start` |
| `bootstrap-static` — teams | Official team strength ratings (overall, attack, defence, home and away splits) |
| `bootstrap-static` — events | Deadlines, most-captained and most-transferred players, chip-play counts, average and highest scores |
| `fixtures` | Kickoff times, provisional/rescheduled flags, official Fixture Difficulty Rating (FDR), per-fixture stat breakdowns after matches |
| `element-summary/{player}` | Current-season Gameweek-by-Gameweek history, upcoming fixtures, and summarised past-season totals per player |
| `event/{gw}/live` | In-match player stats, live BPS and provisional bonus |
| `entry/{manager}` and related | Squad picks, transfer history, chip usage, bank and team-value history — the canonical manager-state source |
| `leagues-classic`/`leagues-h2h` | Mini-league standings and rival entries (Phase 5 input) |
| Official editorial | Set-piece takers notes, Scout selections, the new 2026/27 official price predictor |

Specific obligations:

- `chance_of_playing`, status flags and `news`/`news_added` are canonical Tier 1 availability evidence and must feed the expected-minutes model directly, timestamped like any other claim;
- `ep_this`/`ep_next` and FDR must be captured **before** the deadline to be usable; post-deadline capture is a leakage risk and must be labelled accordingly;
- `selected_by_percent` and per-Gameweek transfer counts provide free groundwork for price-change modelling (Phase 5) and effective-ownership approximations, and should be snapshotted from day one even though those features are deferred;
- official team strength ratings and FDR are coarse and must be benchmarked as baselines, not trusted as ground truth;
- `entry` transfer history preserves purchase prices, but manager-state capture should still begin at Gameweek 1 so selling prices are never reconstructed from incomplete data.

#### Tier 2: Historical and community sources

| Source | Potential value | Required review |
|---|---|---|
| `vaastav/Fantasy-Premier-League` | Historical Gameweek data through 2024/25 | NOASSERTION licence; weekly updates stopped; known `xP` leakage risk |
| `FPL-Core-Insights` | 2025/26 data, detailed actions, cups, Europe and Elo | Provenance and rights for “Opta-like” data |
| `open-fpl-solver` | Mature deterministic optimisation | Requires our own projections and current rules |
| football-data.co.uk | Results, match statistics and odds | Terms, attribution and schema stability |
| ClubElo | Team-strength baseline | Promoted-team priors and identity matching |
| Understat | xG and xA | No supported public API; collection and reuse terms |
| FBref (StatsBomb-derived) | Per-match defensive actions (tackles, interceptions, blocks, clearances), shooting and passing detail — directly relevant to defensive-contribution modelling | Terms and attribution; collection cadence; identity matching |
| Bookmaker odds (football-data.co.uk historical; live odds APIs such as The Odds API) | Market-implied match, clean-sheet and anytime-goalscorer probabilities as calibrated baselines | Cost and terms; odds must be captured pre-deadline |
| Predicted line-up services (Fantasy Football Scout, Rotowire) | Start-probability evidence for the expected-minutes model | Subscription terms; per-source accuracy must be benchmarked |
| Confirmed line-up feeds (Sofascore, Fotmob) | Confirmed XIs approximately one hour before kickoff; minutes and ratings history | Unofficial APIs; terms and collection-method review |
| 2026 World Cup data (FIFA/official) | Per-player tournament minutes, elimination dates and return-to-training reports as 2026/27 pre-season priors | One-off collection; identity matching to PL squads |

#### Tier 3: Editorial and benchmark sources

Potential sources include:

- FPL Review;
- Fantasy Football Scout editorial;
- BBC Sport;
- official club press conferences;
- injury-reporting services;
- reputable FPL blogs and podcasts.

These should initially be treated as linked evidence and benchmark outputs, not bulk republished datasets.

Predicted and confirmed line-up services are deliberately promoted to Tier 2 rather than left here: expected minutes is the identified weakest point (Section 7.1), so its principal sources require first-class registry entries and per-source accuracy benchmarking rather than ad-hoc editorial treatment.

### 6.2 Source registry

No collector should be enabled until its source has a registry entry.

Required fields:

| Field | Purpose |
|---|---|
| `source_id` | Stable internal identifier |
| `owner` | Rights holder or publisher |
| `source_type` | API, file, RSS, HTML, manual or commercial feed |
| `authority` | Canonical, secondary, commentary or benchmark |
| `terms_url` | Applicable terms |
| `licence_status` | Confirmed, restricted, unknown or prohibited |
| `allowed_use` | Private analysis, training, retention, display or redistribution |
| `authentication` | None, API key, browser session or manual |
| `collection_method` | API, download, permitted fetch or manual entry |
| `expected_cadence` | How often updates are expected |
| `max_staleness` | Acceptable age before a decision |
| `failure_policy` | Stop, use cache, degrade or require manual confirmation |
| `retention_policy` | What can be stored and for how long |
| `attribution` | Required citation |
| `enabled` | Whether the source may currently be collected |
| `review_date` | Next governance review |

### 6.3 Legal and operational caution

The Premier League Terms of Use restrict reproduction and re-utilisation of website/app material and explicitly mention creating databases from obtained material. Public endpoint availability must not be interpreted as permission to archive or redistribute the data.

Before persistent collection or authenticated automation:

- review current terms;
- document the private, non-commercial research purpose;
- seek clarification where necessary;
- do not bypass technical controls;
- do not redistribute third-party raw data;
- keep credentials outside prompts and model context.

---

## 7. Principal data gaps

### 7.1 Expected minutes

Expected minutes are likely to be the most important weak point. Required factors include:

- starting probability;
- likely substitution time;
- injury recovery;
- competition for position;
- tactical role;
- new manager or formation;
- cup and European minutes;
- international travel;
- fixture congestion;
- press-conference evidence;
- official FPL availability flags, `news` text and chance-of-playing percentages;
- predicted and confirmed line-up sources.

The MVP should implement a transparent baseline expected-minutes model and support cited manual or agent-proposed adjustments.

Each start-probability source (official flags, predicted line-ups, press conferences) must be benchmarked against a naive "started last Gameweek" baseline so that its marginal value is known before it is trusted in live decisions.

### 7.2 Point-in-time history

Every temporal record should distinguish:

- `published_at`: when the source published it;
- `observed_at`: when the system collected it;
- `effective_at`: when the underlying state became true;
- `finalised_at`: when FPL locked or confirmed it.

Historical replay must use only observations available before the relevant deadline.

### 7.3 Defensive-contribution data

Defensive-contribution scoring began in 2025/26, leaving limited directly comparable history. Modelling requires clearances, blocks, interceptions, tackles and, for midfielders and forwards, ball recoveries.

Because these actions now score FPL points, the official endpoints have exposed the relevant per-player counts since 2025/26 (`defensive_contribution`, `clearances_blocks_interceptions`, `tackles`, `recoveries`). Subject to launch verification, Tier 1 therefore covers the scoring-relevant defensive counts, and third-party sources such as FBref are enrichment and cross-checks, not launch prerequisites.

Detailed third-party defensive data must not be used until its provenance and permitted use are understood.

### 7.4 Personal financial state

The optimiser requires manager-specific:

- purchase price;
- current price;
- actual selling price;
- bank;
- squad value;
- free transfers;
- chip state.

This state should be captured immediately before each live decision.

### 7.5 Fixture revisions

Fixtures must be event-sourced or revisioned rather than overwritten. Blanks and Doubles can result from:

- FA Cup;
- EFL Cup;
- European competitions;
- postponements;
- weather or policing;
- broadcast changes;
- delayed rescheduling decisions.

### 7.6 New players and distribution shift

Uncertainty should be increased for:

- promoted clubs;
- players arriving from other leagues;
- players changing clubs;
- position reclassifications;
- new managers;
- major tactical changes;
- players with little recent playing time.

### 7.7 2026 World Cup carry-over

The 2026 World Cup final falls approximately four weeks before the 2026/27 season begins. This is the dominant expected-minutes consideration for Gameweeks 1–5 and is specific to this season:

- players at the tournament will have truncated pre-seasons;
- players reaching the later rounds may return late or be rested early;
- accumulated fatigue raises early-season rotation and injury risk;
- some transfers complete late because of the tournament window.

Required data: per-player World Cup minutes, each national team's elimination date, and reported return-to-training dates. These must be captured once, matched to Premier League squads, and used as named pre-season priors in the expected-minutes model.

### 7.8 Disciplinary suspensions

Yellow-card accumulation (five, ten and fifteen cards, with competition-specific cutoff Gameweeks) makes some absences deterministic and forecastable weeks in advance. Red-card bans and their competition scope must also be tracked. The availability model must therefore include accumulated cards and threshold proximity as structured inputs, not treat all absences as injury-shaped uncertainty.

---

## 8. System architecture

The system is divided into four planes.

### 8.1 Control plane

The control plane defines how the system is allowed to behave.

```text
control/
├── rules/
│   ├── 2024-25.yaml
│   ├── 2025-26.yaml
│   └── 2026-27.yaml
├── sources/
│   └── source-registry.yaml
├── schemas/
├── identities/
├── calendars/
└── policies/
    ├── data-retention.yaml
    ├── agent-permissions.yaml
    └── execution-policy.yaml
```

### 8.2 Data plane

```text
data/
├── raw/
│   ├── fpl/
│   ├── fixtures/
│   ├── results/
│   ├── manager-state/
│   └── documents/
├── normalised/
├── features/
├── snapshots/
└── quarantine/
```

Recommended initial technologies:

- Parquet for immutable analytical snapshots;
- DuckDB for local analytical queries;
- SQLite or PostgreSQL for operational state;
- Git for code, rules, schemas, prompts and evaluation cases;
- no credentials, browser sessions or unrestricted raw datasets in Git.

### 8.3 Decision plane

```text
decision/
├── models/
│   ├── team-strength/
│   ├── expected-minutes/
│   ├── player-events/
│   └── calibration/
├── simulations/
├── optimizer/
├── agents/
├── evaluations/
└── reports/
```

### 8.4 Action plane

```text
action/
├── approvals/
├── dry-runs/
├── execution/
├── verification/
└── audit/
```

The action plane must accept an immutable, validated proposal. It may not independently alter the transfer or line-up plan.

---

## 9. Core data model

### 9.1 Identity and football entities

- `players`
- `player_identities`
- `player_team_history`
- `player_position_history`
- `teams`
- `team_identities`
- `club_managers` (head-coach tenure history, so managerial changes and press-conference evidence attach to a real entity)
- `competitions`
- `seasons`
- `gameweeks`
- `fixtures`
- `fixture_revisions`

Internal surrogate IDs should link changing source-specific IDs across seasons.

### 9.2 Performance and price data

- `player_match_events`
- `player_match_stats`
- `player_gameweek_stats`
- `team_match_stats`
- `player_prices`
- `player_availability`
- `player_discipline` (card accumulation, suspension thresholds and served bans)
- `set_piece_roles`

### 9.3 Manager state

- `manager_snapshots`
- `manager_squads`
- `manager_finance`
- `manager_chips`
- `manager_transfers`
- `manager_gameweek_picks`

### 9.4 Documents and evidence

- `source_documents`
- `document_passages`
- `extracted_claims`
- `claim_entities`
- `claim_conflicts`
- `decision_signals`

The schema should support later full-text and vector retrieval even if vector search is not part of the first build.

### 9.5 Models and decisions

- `forecast_runs`
- `player_projections`
- `simulation_runs`
- `optimizer_runs`
- `candidate_plans`
- `agent_runs`
- `agent_reviews`
- `rule_validations`
- `final_proposals`
- `approvals`
- `executions`
- `decision_outcomes`
- `retrospectives`

Every derived record should retain source references and the transformation, rules, model and prompt versions used.

---

## 10. Data processing layers

### 10.1 Raw/bronze

Immutable source responses and files, including:

- response body;
- request URL or file origin;
- HTTP status;
- collection time;
- content hash;
- source-registry version;
- schema-detection result.

Failed and unexpected responses should also be retained as operational evidence where permitted.

### 10.2 Normalised/silver

- canonical identities;
- consistent types and units;
- fixture revisions;
- season-aware positions;
- deduplicated records;
- explicit missing values;
- data-quality flags;
- temporal validity.

### 10.3 Decision/gold

- expected minutes;
- goal and assist rates;
- clean-sheet probabilities;
- defensive-contribution probabilities;
- forecast points distributions;
- rotation and injury risk;
- fixture-strength features;
- price and transfer signals;
- candidate transfer plans.

---

## 11. Modelling strategy

### 11.1 Predict events rather than historical FPL points

Directly training on historical `total_points` mixes different rule systems. Instead, where data permits, forecast:

- minutes;
- goals;
- assists;
- clean-sheet probability;
- saves;
- goals conceded;
- cards;
- defensive actions;
- bonus probability.

The season-specific scoring engine then converts forecast events into FPL points.

This supports:

- historical replay under the original rules;
- estimates of old performances under new rules;
- clearer separation of model error and rule changes;
- easier adaptation to future scoring changes.

### 11.2 Baselines before complex ML

Initial baselines should include:

- rolling points and minutes;
- per-90 event rates;
- simple fixture adjustments;
- official FPL expected-points field (`ep_next`) and Fixture Difficulty Rating where safely captured before the deadline;
- odds-implied projections built from pre-deadline match, clean-sheet and anytime-goalscorer odds — the market's own calibrated forecast and likely the strongest cheap baseline (player-prop odds have thin historical coverage, so historical clean-sheet probabilities are derived from match and totals odds where props are unavailable);
- Poisson or Elo-based team-strength model;
- simple expected-minutes heuristics.

More complex models — and later, agent adjustments — must demonstrate improvement over these baselines. If a model cannot beat the odds-implied baseline, that finding is itself a result worth recording.

### 11.3 Model components

1. **Team-strength model** — expected goals for and against, including home advantage.
2. **Expected-minutes model** — start probability and minutes distribution.
3. **Player-event model** — scoring, assisting, saving, conceding and defensive actions.
4. **Monte Carlo simulation** — distributions rather than single-value forecasts.
5. **FPL scoring engine** — season-specific conversion to expected FPL points.
6. **Calibration layer** — P10, P50, P90 and relevant event probabilities.

### 11.4 Look-ahead controls

- train/test splits must follow time;
- features must carry an `available_at` timestamp;
- deadline replay must filter by `available_at <= deadline`;
- post-match `ep_this` or equivalent values must be excluded or shifted;
- later fixture corrections must not appear in earlier decision snapshots;
- outcome data must remain isolated from the decision context.

---

## 12. Optimisation strategy

FPL squad management is a constrained multi-period optimisation problem.

### 12.1 Hard constraints

- valid squad size and positions;
- budget and actual selling prices;
- maximum players per club;
- legal starting XI;
- captain and vice-captain;
- ordered bench;
- free-transfer balance;
- point-hit costs;
- chip availability and interactions;
- Blank and Double Gameweeks.

### 12.2 Objective

A representative objective is:

```text
Maximise:
  expected points over the selected horizon
  - transfer-hit costs
  - injury and rotation risk penalty
  - excessive uncertainty penalty
  + retained transfer and squad optionality
```

### 12.3 Candidate plans

The planning horizon is an explicit design decision (Section 25, item 14), not an implementation detail: single-Gameweek optimisation systematically undervalues banked transfers and chip timing, while long horizons multiply forecast error. Chips in particular are season-scale assets — two sets of four with a Gameweek 19 expiry — so even the initial build should evaluate chip use against at least a coarse multi-Gameweek plan (for example, expected value of Bench Boost now versus the best remaining Double Gameweek) rather than greedily.

The optimiser should eventually expose:

- highest expected-value plan;
- no-transfer plan;
- bank-transfer plan;
- no-hit plan;
- conservative plan;
- aggressive/differential plan;
- chip and no-chip alternatives;
- plans under alternative expected-minutes scenarios.

The initial build may implement a smaller subset but should preserve this interface.

---

## 13. Agent design

Agents must use tools and structured records rather than receiving the full database in a prompt.

### 13.1 Initial agents

#### Evidence agent

- searches approved sources;
- extracts player availability, tactical and set-piece claims;
- provides citations and publication times;
- identifies ambiguity and conflicts;
- assigns confidence and expiry;
- proposes, but cannot apply, a model adjustment.

#### Challenger agent

- checks for stale or missing information;
- challenges expected-minutes assumptions;
- identifies reliance on one weak source;
- checks whether alternatives were considered;
- flags rules or financial inconsistencies;
- cannot bypass deterministic validation.

#### Orchestrator

- invokes data, model, optimiser and agent tools;
- assembles the decision context;
- records failures and degraded operation;
- produces the Gameweek Decision Record.

In the initial build the orchestrator is **deterministic workflow code, not an LLM**. An LLM-driven orchestrator is one of the experimental conditions in Phase 3 and must remain clearly distinguishable from the deterministic pipeline, otherwise the agent-versus-non-agent comparison is contaminated.

### 13.2 Later agents

The longer-term plan includes:

- data-steward agent;
- source-rights/governance assistant;
- fixture and competition-monitoring agent;
- expected-minutes specialist;
- strategy and chip-planning agent;
- mini-league/rival analyst;
- price-change analyst;
- live-match review agent;
- execution agent.

These are not part of the first implementation unless required to test a specific hypothesis.

### 13.3 Agent permissions

| Capability | Evidence agent | Challenger | Orchestrator | Executor |
|---|---:|---:|---:|---:|
| Read approved data | Yes | Yes | Yes | Minimum required |
| Query models | Yes | Yes | Yes | No |
| Propose adjustments | Yes | Yes | Yes | No |
| Modify projections | No | No | Controlled service only | No |
| Validate rules | Request only | Request only | Request only | Must verify passed result |
| Approve proposal | No | No | No | No |
| Execute FPL changes | No | No | No | Later phase only |

### 13.4 Disagreement and escalation

A challenger flag must always resolve to one of a small set of policy-defined outcomes, recorded in the decision record:

1. **Dismissed** — with a stated reason;
2. **Confidence downgrade** — the recommendation stands but its confidence rating is reduced;
3. **Forced re-run** — projections or plans are regenerated under amended assumptions;
4. **Escalation** — the decision requires explicit human review before approval.

An unresolved challenge blocks any automatic approval path. Without this policy, multi-agent review is decorative text in a report and ablation will correctly find it worthless.

### 13.5 Agent runtime and cost budgets

Every agent stage carries an explicit token/cost cap and wall-clock timeout. Budgets are set per Gameweek run and recorded alongside the decision. Near-deadline behaviour is defined in Section 15.3: agents that overrun degrade to the deterministic output rather than delaying the decision.

---

## 14. Evidence lifecycle

The system must distinguish four stages:

1. **Document** — article, transcript, post or structured source.
2. **Claim** — a statement extracted from that document.
3. **Signal** — a decision-relevant interpretation of one or more claims.
4. **Adjustment** — a controlled change proposed to a forecast assumption.

Example:

```text
Document:
  Manager press conference transcript

Claim:
  "Player X trained today and will be assessed"

Signal:
  Availability remains uncertain; no confirmation of a start

Proposed adjustment:
  Starting probability 72% -> 61%

Decision impact:
  Player X falls from candidate plan 1 to candidate plan 3
```

Adjustments should be:

- cited;
- confidence-scored;
- time-limited;
- recorded separately from the original model output;
- accepted or rejected by policy-controlled orchestration.

---

## 15. Gameweek operating cycle

### 15.1 Pre-season

- confirm rule and position changes;
- review source terms;
- initialise identities;
- capture launch prices and squad lists;
- establish promoted-team and new-player priors;
- capture 2026 World Cup minutes, elimination dates and return-to-training reports as fatigue and late-start priors (Section 7.7);
- monitor pre-season minutes and tactical roles;
- create Gameweek 1 projections and scenarios.

### 15.2 Daily in-season collection

- current player and fixture state;
- prices and availability;
- fixture revisions;
- cup and European participation;
- approved news/document metadata;
- manager state where authenticated collection is permitted.

### 15.3 Before each deadline

- **T-48h:** initial projections and candidate plans;
- **T-8h:** press-conference and availability refresh;
- **T-2h:** final forecast, simulation and optimisation run;
- **T-30m:** optional approved execution in a later phase;
- **deadline:** immutable decision snapshot.

Times are relative to the official FPL deadline, not the first kickoff.

Agent stages within this schedule run under the budgets defined in Section 13.5. If the evidence or challenger agents have not completed by **T-90m**, the system falls back to the deterministic forecast-plus-optimiser plan and marks the Gameweek Decision Record as degraded. A late agent must never delay or block the decision.

### 15.4 After matches

- ingest provisional match results and points;
- preserve revisions rather than overwrite them;
- ingest final state after the 09:00 Gameweek lock;
- evaluate model calibration and decisions;
- produce the retrospective;
- update, but do not silently rewrite, model assumptions.

---

## 16. Gameweek Decision Record

A representative output should contain:

```text
Gameweek: 4
Decision cutoff: 2026-09-12 11:30 UTC
Deadline: 2026-09-12 12:30 UTC
Ruleset: 2026-27-v1.2
Data quality: Passed with one stale secondary source

Recommendation:
  Roll transfer
  Captain Player X
  Vice-captain Player Y
  Start Player Z over Player Q

Expected advantage over current setup:
  +2.3 points

Confidence:
  Moderate

Principal uncertainty:
  Player X starting probability

Evidence:
  Four supporting sources
  One conflicting predicted line-up

Alternative:
  Transfer Player A to Player B if Player X is ruled out

Validation:
  Squad rules passed
  Financial rules passed
  Chip rules passed

Approval:
  Human approved

Execution:
  Manual in initial phase

Outcome:
  Added after Gameweek finalisation

Retrospective:
  Decision process sound; expected-minutes assumption incorrect
```

---

## 17. Evaluation framework

### 17.1 Data evaluation

- collection success rate;
- source freshness;
- schema failures;
- missing records;
- identity-matching errors;
- source conflicts;
- successful backfills;
- lineage completeness.

### 17.2 Forecast evaluation

- points MAE and RMSE;
- expected-minutes error;
- start-probability calibration;
- clean-sheet probability calibration;
- goal/assist event calibration;
- performance by position;
- performance by forecast horizon;
- performance against simple baselines.

### 17.3 Decision evaluation

- realised transfer gain against doing nothing;
- point-hit recovery;
- captaincy gain or loss;
- bench-order effectiveness;
- chip value;
- transfer optionality retained;
- decision regret against the best feasible hindsight action;
- robustness across forecast scenarios.

### 17.4 Agent evaluation

- unsupported factual claims;
- citation completeness;
- stale evidence use;
- unknown-player fabrication;
- attempted rule violations;
- unnecessary tool calls;
- cost and latency;
- run-to-run consistency;
- recovery from unavailable tools or sources;
- value added over deterministic output.

### 17.5 Automation evaluation

For later execution phases:

- dry-run success;
- precondition-validation success;
- write success;
- read-back verification success;
- ambiguous-write frequency;
- missed deadlines;
- duplicate-action prevention;
- screenshot and audit completeness.

### 17.6 Statistical power and comparison design

A single live season is too noisy to distinguish five strategies: one captaincy differential can swing more points than a season of marginal model improvements. The comparison design must confront this directly:

- **historical replay across multiple seasons is the primary evidence** for comparing structured-data strategies, with the live season as validation; for evidence-dependent agent strategies this relationship inverts (see the asymmetry below);
- comparisons are **paired per decision** — same Gameweek, same information set, different strategy — never unpaired season totals;
- decisions are **decomposed into sub-decisions** (captaincy, individual transfers, bench order, chip timing) to multiply the effective sample count;
- before any difference is claimed, a **detectable-effect-size estimate** derived from simulated point distributions must state how many decisions are needed to distinguish a 0.5-point-per-Gameweek advantage (accepted minimum meaningful difference — ADR-0004);
- **the project operates one live FPL entry**: FPL terms permit one account per person, so the project's own parallel strategies are evaluated in shadow against the same live data snapshots. A recruited cohort of consenting managers, each a real person with their own single account, is the compliant route to parallel live entries (Section 17.7).

Replay is the measurement instrument, not a source of decision value: it generates statistical confidence about strategies, while the decision value itself comes from the data and models of Sections 6 and 11. Two consequences bound how much to invest in it:

- **Replay has an evidence asymmetry.** Historical datasets preserve structured statistics, not the pre-deadline news environment — press conferences, injury reports and predicted line-ups as they looked at the time. Multi-season replay can therefore fairly compare the structured-data strategies (statistical baseline, forecast plus optimiser, horizon and chip-timing policies) but will structurally understate evidence-dependent agent strategies, which draw precisely on the material history does not preserve. Evidence-dependent comparisons lean instead on live-season paired shadow evaluation and the multi-manager cohort, accepting that confidence accrues more slowly there.
- **Do not over-invest in historical evidence reconstruction.** The time-critical, irreplaceable investment is day-one live capture (Section 6.1): this season's pre-deadline snapshots become the first replay corpus that is complete for evidence-dependent strategies. The replay harness itself must be cheap per run, since hundreds of replayed Gameweeks are expected, but reconstructing historical news environments (archived pages, Wayback captures) is limited to a feasibility assessment in WP-04, not a build commitment.

### 17.7 Multi-manager live cohort

FPL terms permit one account per person; they do not prevent several people from each running their own account under an agreed protocol. A recruited cohort of consenting managers, each assigned one strategy, provides live evidence that shadow evaluation structurally cannot:

- real execution effects — actual price changes, selling prices and rank movements, which shadow strategies never pay;
- adherence behaviour — whether humans actually follow recommendations is itself a research question (strategy 5 in Section 4.1) and is only observable in live accounts;
- paired live comparisons — same Gameweek, same information snapshots, different strategies, matching the design above.

Protocol requirements:

- each participant is a real person operating exactly one account, consistent with FPL terms;
- informed participation: managers know which strategy they follow and what is recorded about their decisions;
- one strategy per manager, assigned before Gameweek 1;
- standardised starting squads, or the initial divergence recorded so later comparisons can condition on it;
- adherence logged per decision — followed, partially followed or overridden — with overrides retained as human-behaviour data rather than discarded;
- cohort results are supporting evidence: the sample is small, so they complement, and never replace, replay and shadow evaluation.

No participant credentials or personal data enter the repository or model context (Section 22.3).

---

## 18. Delivery roadmap

Deferred features remain part of the plan. Their schemas and interfaces should be anticipated now, but they must not expand the initial build uncontrollably.

### Phase 0 — Governance and design

**Purpose:** Establish a safe and testable foundation before building collectors.

Deliverables:

- source registry;
- data-rights and permitted-use review;
- 2024/25, 2025/26 and draft 2026/27 rulesets;
- rule verification checklist for launch;
- canonical data model;
- point-in-time contract;
- identity-resolution strategy;
- architecture decision records, including the orchestration-substrate decision (Section 25, item 12);
- initial evaluation definitions, including the statistical-power design (Section 17.6);
- weekly operating-effort budget: an explicit estimate of hours per Gameweek the human loop is allowed to cost. **Set — two hours per Gameweek at season start, reducing to one, with further reduction as automation earns trust (ADR-0003).**

Exit criteria:

- every proposed source is registered;
- prohibited or unresolved collectors are disabled;
- rules carry a source and confidence status;
- decision-time filtering is specified;
- Open Decisions 1 and 2 (private use and permitted retention) are answered and act as a hard gate on raw-data collection. **Answered 21 July 2026 (ADR-0001, ADR-0002) — the gate is cleared.**

Phase 0 governance must not consume the pre-season: the Phase 1 walking skeleton may begin in parallel once the source registry covers the sources it needs.

### Phase 1 — Initial MVP: reproducible advisory pipeline

**Purpose:** Produce valid, auditable recommendations without external execution.

Deliverables:

- immutable raw snapshots;
- normalised player, team, fixture and Gameweek tables;
- fixture-revision ledger;
- manager-state import or permitted capture;
- baseline expected-minutes model;
- event/points projection baseline;
- season-aware scoring engine;
- deterministic squad and transfer validator;
- deterministic optimiser;
- evidence agent;
- challenger agent;
- Gameweek Decision Record;
- defined human approval interface (a rendered decision record plus a signed approval entry in the journal is sufficient; a dashboard is not required in Phase 1);
- manual decision and outcome journal;
- historical replay for selected Gameweeks;
- **walking-skeleton milestone:** one historical Gameweek end-to-end with crude models, delivered early rather than after all other Phase 1 items;
- **historical orchestration pilot:** as soon as replay works, run agent and non-agent strategies on replayed Gameweeks — the core research question must not wait for Phase 3. Agent-condition results from this pilot validate the harness plumbing; because historical data lacks the pre-deadline news environment (Section 17.6), they are smoke tests, not evidence of agent value.

Exit criteria:

- the eight initial success criteria (Section 3.2) are each demonstrated on replayed Gameweeks;
- one complete Gameweek Decision Record is produced end-to-end — raw snapshot to rendered record — for a replayed or live deadline, and reproduced from its recorded inputs and versions by rerun;
- the deterministic validator rejects every invalid rule golden case (Section 21.1);
- the historical orchestration pilot has produced at least one paired agent-versus-non-agent comparison, reported as smoke-test evidence;
- no deliverable requires undocumented manual intervention to run.

Explicitly not activated in Phase 1:

- unrestricted full-article collection;
- vector database;
- live-match agents;
- mini-league rival modelling;
- effective-ownership strategy;
- computer-use submission;
- unattended account access;
- cloud-scale deployment.

### Phase 2 — Live advisory operation

**Purpose:** Operate reliably over consecutive live Gameweeks.

Deliverables:

- scheduled daily and deadline-relative workflows;
- pre-deadline manager-state snapshot;
- press-conference and injury evidence workflow;
- Monte Carlo projections;
- multiple candidate plans;
- conservative/aggressive scenarios;
- final-lock result reconciliation;
- weekly retrospective;
- freshness and failure alerts;
- dashboard or static report view.

Exit criteria:

- several consecutive Gameweeks completed without unreconstructable decisions;
- no rules-invalid proposals;
- data and agent failures visibly degrade rather than silently pass.

### Phase 3 — Orchestration experiment

**Purpose:** Measure whether agents improve the deterministic system.

Parallel shadow strategies:

1. statistical baseline;
2. forecast plus optimiser;
3. single tool-using agent;
4. specialised multi-agent workflow;
5. human selection.

Primary statistical evidence for the structured-data strategies comes from the multi-season historical replay corpus (Section 17.6). For evidence-dependent agent strategies, replay is structurally incomplete, so the live season — paired shadow evaluation plus the multi-manager cohort where recruited (Section 17.7) — provides the primary evidence, with the project's own live entry serving as validation.

Deliverables:

- fixed historical and live evaluation cases;
- reproducible tool and prompt versions;
- deterministic hard checks;
- model-graded qualitative checks where appropriate;
- cost, latency and decision-quality comparison;
- ablation tests removing individual agents or data sources.

Exit criteria:

- the detectable-effect-size estimate (Section 17.6) was recorded before any comparative results were examined;
- every strategy has run on the full fixed evaluation set with paired, sub-decision-level metrics;
- cost and latency per strategy are reported alongside decision quality;
- ablations attribute observed differences to specific agents or data sources;
- a written conclusion states whether orchestration justified its cost — a null result is an acceptable finding and must be reported with the same rigour.

### Phase 4 — Extended data and retrieval

**Purpose:** Add the deferred information-management capabilities without altering the trusted decision core.

Deliverables may include:

- larger approved document corpus;
- rights-aware full-text retrieval;
- vector retrieval where it demonstrates value;
- podcast or transcript claim extraction;
- expanded official club and competition monitoring;
- cross-competition player minutes;
- tactical-role history;
- source reputation and historical accuracy scores;
- contradiction detection across sources;
- richer promoted-player and transfer priors.

Conditions:

- source rights and retention must be documented;
- retrieval must return citations and timestamps;
- vector retrieval must be compared against SQL/full-text baselines;
- raw third-party content must not be redistributed without permission.

### Phase 5 — Competitive and price intelligence

**Purpose:** Add strategically useful but non-essential FPL dimensions.

Deliverables may include:

- mini-league rival snapshots;
- template and differential analysis;
- effective-ownership approximations;
- captaincy-risk analysis;
- rank-aware conservative/aggressive modes;
- official price-predictor integration if access and use are permitted;
- price-rise/fall scenarios;
- team-value optimisation;
- rival-aware but rules-valid candidate plans.

These features must remain optional. The core expected-points system should work without them.

### Phase 6 — Live-match monitoring

**Purpose:** Study real-time data orchestration, not influence a locked Gameweek decision.

Deliverables may include:

- live score and provisional bonus monitoring;
- provisional defensive-contribution tracking;
- league-rank movement;
- post-match correction detection;
- live agent-generated incident summaries;
- comparison of provisional and final points;
- automatic retrospective evidence collection.

The live agent cannot change a team after the deadline and should remain separate from the next-Gameweek decision context until data is finalised or explicitly marked provisional.

### Phase 7 — Controlled computer-use execution

**Purpose:** Execute a human-approved immutable proposal safely.

Prerequisites:

- current terms and automation permissions reviewed;
- stable advisory operation;
- validated browser flow;
- secret-management design;
- proposal-specific human approval;
- incident and recovery procedures.

Delivery sequence:

1. browser navigation only;
2. read-only manager-state verification;
3. dry-run form filling without confirmation;
4. screenshot-based human review;
5. approved line-up changes;
6. separately approved transfers;
7. separately approved irreversible chip actions;
8. read-back verification and audit.

Safety requirements:

- credentials never enter the LLM context;
- no action without a valid unexpired proposal ID;
- no automatic substitution of rejected players;
- no ambiguous write retry;
- pre- and post-action screenshots;
- immediate stop on changed prices, squad state or deadline;
- chips and point hits require heightened confirmation.

### Phase 8 — Experimental autonomous operation

**Purpose:** Test constrained autonomy only after the system has demonstrated reliability.

Possible scope:

- limited automatic line-up and captain updates;
- pre-authorised low-risk actions;
- strict limits on transfers and point hits;
- no autonomous chip use initially;
- kill switch and manual override;
- separate experimental FPL entry only if explicitly permitted — FPL terms allow one account per person, so additional entries operated by the same person are assumed prohibited; shadow evaluation remains the default and the recruited multi-manager cohort (Section 17.7) is the compliant route to parallel live entries.

This phase is optional and should not be treated as the expected destination of the initial project.

### Phase 9 — Cloud and scale-out architecture

**Purpose:** Explore production infrastructure only when local operation becomes limiting.

Potential additions:

- object storage for snapshots;
- managed PostgreSQL;
- data-asset orchestration;
- event queues;
- model registry;
- distributed agent runs;
- hosted dashboard;
- monitoring, tracing and cost controls;
- infrastructure as code;
- disaster recovery and environment separation.

Cloud migration must be justified by reliability, collaboration or experimental needs rather than introduced for its own sake.

---

## 19. Deferred-feature register

The following capabilities are deliberately deferred from the initial build but included in the target architecture.

| Feature | Planned phase | Interface/schema anticipated in MVP? | Activation condition |
|---|---:|---:|---|
| Full approved article corpus | 4 | Yes | Rights and retention confirmed |
| Vector database/RAG | 4 | Yes | Demonstrates benefit over SQL/full-text |
| Podcast/transcript ingestion | 4 | Yes | Permitted source and reliable transcription |
| Source reputation scoring | 4 | Yes | Sufficient historical claims/outcomes |
| Mini-league rival analysis | 5 | Partly | Stable manager/league data access |
| Effective ownership | 5 | Partly | Reliable and permitted population data |
| Price-change strategy | 5 | Yes | Official predictor/data access understood |
| Rank-aware strategy | 5 | Yes | Decision objective and risk policy defined |
| Live-match agents | 6 | Yes | Stable live data and provisional labels |
| Real-time ranks/bonus | 6 | Yes | Supported source and operational value |
| Browser dry-run | 7 | Yes | Terms review and stable selectors |
| Automatic line-up submission | 7/8 | Yes | Verified approval and read-back controls |
| Automatic transfers | 7/8 | Yes | Stronger controls and explicit approval |
| Autonomous chip use | 8 or later | Yes | Exceptional reliability; separate policy |
| Cloud warehouse | 9 | No immediate implementation | Local approach becomes limiting |
| Distributed orchestration | 9 | No immediate implementation | Clear scale or reliability requirement |

“Anticipated” means the core data model should avoid blocking the future feature. It does not mean implementing the feature during Phase 1.

---

## 20. Suggested repository structure

```text
fpl-agentic-decision-lab/
├── README.md
├── AGENTS.md
├── docs/
│   ├── plan.md
│   ├── architecture/
│   ├── decisions/
│   ├── rules/
│   ├── data-sources/
│   └── evaluations/
├── control/
│   ├── rules/
│   ├── sources/
│   ├── schemas/
│   ├── identities/
│   └── policies/
├── src/
│   ├── ingestion/
│   ├── normalisation/
│   ├── quality/
│   ├── features/
│   ├── forecasting/
│   ├── scoring/
│   ├── optimisation/
│   ├── evidence/
│   ├── agents/
│   ├── orchestration/
│   ├── reporting/
│   └── execution/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contracts/
│   ├── rules/
│   ├── historical-replay/
│   └── agent-evals/
├── prompts/
├── evals/
│   ├── golden-cases/
│   └── baselines/
├── reports/
│   └── gameweeks/
├── scripts/
└── data/
    ├── raw/
    ├── normalised/
    ├── features/
    ├── snapshots/
    └── quarantine/
```

Raw data, credentials, browser state and generated secrets must be excluded from version control.

---

## 21. Testing strategy

### 21.1 Rule tests

Golden cases should cover:

- valid and invalid squad composition;
- club-limit violations;
- all legal formations;
- captain and vice-captain fallback;
- automatic substitution edge cases;
- transfer banking and hits;
- selling-price calculations;
- Wildcard, Free Hit, Bench Boost and Triple Captain;
- Blank and Double Gameweeks;
- first-half chip expiry;
- season-specific scoring differences;
- bonus-point ties;
- late score corrections.

### 21.2 Data contract tests

- required fields;
- type and range checks;
- duplicate source identifiers;
- fixture identity consistency;
- player-team-position validity by date;
- cumulative-stat reversal detection;
- unexpected schema changes;
- stale manager-state detection.

### 21.3 Historical replay

A replay must:

1. select a historical Gameweek;
2. set the historical deadline;
3. expose only information available before that deadline;
4. run the complete decision pipeline;
5. preserve the generated proposal;
6. reveal outcomes only after the proposal is final;
7. compare against baselines.

### 21.4 Agent tests

Golden cases should include:

- player unavailable;
- ambiguous injury report;
- two conflicting predicted line-ups;
- unknown or misspelled player;
- stale article presented as current;
- transfer that breaches the club limit;
- unaffordable replacement;
- request for an unjustified point hit;
- temptation to use a chip without sufficient evidence;
- source unavailable near deadline;
- prompt-injection-like text in a retrieved article.

---

## 22. Operational and safety policies

### 22.1 Degraded operation

If a source fails, the system must report:

- which source failed;
- last successful observation;
- staleness;
- affected features or players;
- whether a recommendation remains valid;
- whether human review is required.

It must not silently treat missing news as confirmation that a player is available.

### 22.2 Decision freeze

Once a final proposal is approved:

- its data snapshot is immutable;
- model and rule versions are fixed;
- subsequent evidence creates a new proposal version;
- execution requires approval of the new version;
- an expired proposal cannot be executed.

### 22.3 Secrets

- browser credentials and session data remain outside Git;
- agents receive opaque tool access, not raw credentials;
- logs redact cookies, tokens and personal information;
- local and cloud environments use separate secrets;
- screenshots are treated as potentially sensitive.

---

## 23. Principal risks

| Risk | Mitigation |
|---|---|
| FPL/API changes | Raw snapshots, schema detection, adapters and contract tests |
| Data-use restrictions | Source registry and disabled-by-default collectors |
| Look-ahead leakage | Point-in-time snapshots and `available_at` filtering |
| Weak expected-minutes data | Dedicated model, uncertainty and evidence review |
| Incomplete BPS events | Probabilistic bonus model; official outcome as truth |
| New-player cold starts | Priors and wider uncertainty |
| Over-engineered agents | Baselines, ablations and limited initial roles |
| Agent hallucination | Tool grounding, citations and deterministic validation |
| Missed deadline | Relative scheduling, alerts and manual fallback |
| Ambiguous browser write | No retry, verification and human intervention |
| Excessive cloud complexity | Local-first implementation |
| Outcome overfitting | Multiple seasons, shadow strategies and process metrics |
| Weekly operating burden causes mid-season abandonment | Explicit effort budget, walking skeleton, automation of the routine loop |
| Underpowered strategy comparisons | Replay-scale evaluation, paired sub-decision metrics and effect-size estimates (Section 17.6) |
| Governance overhead consumes the pre-season | Walking skeleton runs in parallel with Phase 0; legal gate limited to Open Decisions 1–2 |
| Over-investment in historical replay at the expense of live capture | Replay scoped to structured-data strategies; historical news reconstruction limited to a WP-04 feasibility assessment; day-one live snapshotting prioritised (Section 17.6) |
| Cohort managers deviate from assigned strategies | Adherence logging per decision; overrides retained as human-behaviour data; cohort treated as supporting evidence only (Section 17.7) |

---

## 24. Initial work packages for other agents

Agents contributing to the project should work against explicit, non-overlapping packages.

### WP-01: Rules audit

- produce the complete draft 2026/27 rule catalogue;
- link every rule to an official source;
- identify inherited and unresolved rules;
- create rule golden cases;
- update after FPL launch.

**Done when:** every category in Section 5.3 has versioned 2026/27 entries with status, source and verification date; golden cases cover each rule family; unresolved rules are explicitly listed as `inherited` or `provisional` rather than omitted.

### WP-02: Source governance

- populate the source registry;
- review terms, licences and attribution;
- recommend permitted collection methods;
- document disabled sources and alternatives.

**Done when:** every source named in Section 6.1 has a registry entry completing all Section 6.2 fields; each collector's enabled state follows its `licence_status`; each disabled source has a documented alternative or an accepted gap.

### WP-03: Canonical data model

- define identities and temporal semantics;
- define fixture revisions;
- define manager state;
- define evidence and decision records;
- publish schemas and examples.

**Done when:** every entity in Section 9 has a published schema; temporal entities carry the four point-in-time timestamps (Section 7.2); identity resolution is demonstrated on worked cross-season examples; each schema ships with a valid example record.

### WP-04: Historical-data assessment

- profile candidate datasets;
- identify missing seasons and columns;
- profile FBref defensive-action coverage against defensive-contribution requirements;
- assemble 2026 World Cup minutes and elimination data as pre-season priors;
- test player/team identity matching;
- quantify look-ahead and snapshot limitations;
- assess which historical Gameweeks have recoverable point-in-time news (archived bootstrap snapshots with `news` fields, Wayback captures) and report where evidence-dependent replay is honestly feasible (Section 17.6);
- recommend usable training targets.

**Done when:** each candidate dataset has a written profile covering coverage, gaps, licence and leakage risk; identity-match rates are measured and reported; the point-in-time news assessment states which Gameweeks support evidence-dependent replay; training targets are recommended per model component.

### WP-05: Baseline forecasting

- implement expected-minutes baseline;
- implement team-strength baseline;
- implement player-event baseline;
- implement the odds-implied baseline and benchmark official `ep_next` and FDR against it;
- benchmark each start-probability source against the naive "started last Gameweek" baseline;
- establish time-based evaluation;
- document calibration.

**Done when:** every baseline in Section 11.2 runs under time-based evaluation with reported error and calibration; each start-probability source is benchmarked against the naive baseline; results reproduce from committed code and versioned data references.

### WP-06: Rules and scoring engine

- validate squads and transfers;
- calculate season-aware scoring where data allows;
- implement chip and automatic-substitution rules;
- provide deterministic tests.

**Done when:** the validator passes all rule golden cases (Section 21.1); the scoring engine reproduces official points on sampled finalised Gameweeks within a documented tolerance (Section 5.5); every discrepancy is explained or filed as a defect.

### WP-07: Optimisation

- assess adaptation of `open-fpl-solver` versus a smaller internal model;
- implement current-squad, financial and transfer constraints;
- generate baseline candidate plans;
- retain reproducible solver inputs and outputs.

**Done when:** the solver choice (Open Decision 7) is recorded as an architecture decision record; generated plans satisfy every hard constraint in Section 12.1 across golden cases; a saved solver input reproduces its output exactly.

### WP-08: Evidence pipeline

- define document, claim, signal and adjustment interfaces;
- implement source citations and expiry;
- represent conflicting claims;
- define challenger escalation outcomes and their effect on approval (Section 13.4);
- create injection-resistant extraction tests.

**Done when:** document, claim, signal and adjustment records round-trip with citations and expiry; conflicting claims are represented and surfaced rather than merged; injection golden cases (Section 21.4) pass; challenger escalation outcomes are enforced in the approval path.

### WP-09: Decision record and evaluation

- define Gameweek Decision Record schema;
- implement baseline comparison;
- implement retrospective metrics;
- create historical replay harness.

**Done when:** the Gameweek Decision Record schema captures every element in Section 3.1; the harness replays a full historical Gameweek cheaply enough to run the volumes implied by Section 17.6; baseline comparison and retrospective metrics compute from recorded data alone.

### WP-10: Deferred-feature designs

- produce interface-only designs for vector retrieval, rival analysis, price strategy, live monitoring and execution;
- avoid implementing them during Phase 1;
- identify prerequisites and activation criteria.

**Done when:** every feature in Section 19 marked as anticipated has an interface-only design note stating prerequisites and activation criteria, with no implementation code.

---

## 25. Open decisions

The following require explicit decisions before or during Phase 0. Decisions taken are annotated below and recorded in `docs/decisions/`.

1. Is the project entirely private and non-commercial? **Decided — yes (ADR-0001).**
2. Which FPL and Premier League data may be retained locally, and for how long? **Decided — raw FPL and fixture/odds snapshots retained locally, indefinitely, for private research; no redistribution; kept out of Git (ADR-0002).**
3. Will historical raw datasets be downloaded or referenced through local user-provided paths? **Decided — downloaded locally into version-control-ignored paths, respecting each source's licence (ADR-0007).**
4. Is DuckDB plus Parquet sufficient for the first season? **Decided — yes (ADR-0008).**
5. Is manager state entered manually initially or read through an authenticated session? **Decided — manual entry initially; automated capture reviewed in later phases (ADR-0005).**
6. Which historical seasons have sufficiently reliable event-level data? **Proposed — 2022-23…2024-25 primary; see ADR-0014.**
7. Should the initial optimiser be adapted from `open-fpl-solver` or built as a smaller transparent model? **Proposed — smaller transparent internal model (ADR-0011).**
8. Which model providers, including local models, will be compared? **Open — must be decided, with keys added as environment secrets, before any evidence or challenger agent work begins (Section 26); nothing earlier needs them.**
9. What is the human risk preference: conservative, balanced or experimental? **Decided — balanced by default, with the aggressive/differential alternative selectable each Gameweek (ADR-0006).**
10. What evidence threshold is required before an agent may propose an expected-minutes adjustment? **Proposed — policy thresholds in `control/policies/evidence-adjustments.yaml` (ADR-0013).**
11. What number of live Gameweeks constitutes sufficient stability before browser dry-run work begins?
12. Which orchestration substrate (plain Python, a workflow engine, an agent framework) will run the pipeline, and how are agent traces captured, versioned and replayed? **Decided — plain Python modules and scripts for Phase 0/1; agent traces as JSONL by run ID (ADR-0010).**
13. What are the per-Gameweek cost and latency budgets for agent runs (Section 13.5)?
14. What planning horizon does the optimiser target (single Gameweek versus a rolling multi-Gameweek horizon), and how are future Gameweeks discounted? **Proposed — single-Gameweek for Phase 1 (ADR-0012).**
15. Will a multi-manager live cohort (Section 17.7) be recruited for 2026/27, and under what protocol — strategy assignment, starting-squad standardisation and adherence logging? **Decided — yes, approximately five managers, one strategy each, protocol agreed before Gameweek 1; recruitment owned by the project owner (ADR-0009).**

Open Decisions 11 and 13 remain technical: the implementing agent proposes an answer as an architecture decision record for owner ratification rather than waiting on it. Decisions 6, 7, 10 and 14 have Proposed ADRs awaiting ratification.

---

## 26. Immediate next steps

Already complete: the repository exists, this plan lives at `docs/plan.md`, `AGENTS.md` defines permissions and boundaries, and the Phase 0 human gates are answered and recorded in `docs/decisions/` — private non-commercial use (ADR-0001), retention (ADR-0002), the effort budget (ADR-0003), manager-state entry (ADR-0005), risk preference (ADR-0006), historical-data handling (ADR-0007), storage (ADR-0008) and the multi-manager cohort (ADR-0009). Raw-data collection is no longer gated on governance answers.

1. ~~Complete WP-01 and WP-02 before enabling any automated collectors.~~ Done for Tier 1 / FPL endpoints.
2. ~~Start the Phase 1 walking skeleton.~~ Done (synthetic GW).
3. Re-check official 2026/27 rules and API schemas when FPL launches — **in progress:** live bootstrap schema notes captured in `docs/data-sources/fpl-endpoint-schema-notes.md`; inherited rules still need promotion after full launch verification.
4. ~~Create the canonical schemas and point-in-time contract.~~ Done (WP-03).
5. ~~Profile historical datasets for usable event-level and pre-deadline features (WP-04).~~ Done — see `docs/data-sources/wp04/`.
6. ~~Build a rules validator before building an LLM recommendation workflow.~~ Core validator/scoring in place (WP-06); expand golden-case runner and finalised-GW sample checks next.
7. Select a small set of historical Gameweeks for end-to-end replay — **candidates listed in** `docs/data-sources/wp04/news-recoverability.md` (structured-only).
8. ~~Establish deterministic baselines before measuring agent value (WP-05).~~ Done — see `docs/data-sources/wp05/` (official `ep_next`/FDR deferred to pre-deadline snapshots).
9. ~~Implement the deterministic optimiser and record Open Decisions 7 and 14 (WP-07).~~ Done — see `docs/optimisation/wp07-status.md`; ADRs 0011/0012 Proposed for ratification.
10. ~~Define the evidence lifecycle interfaces and escalation/injection tests (WP-08).~~ Done — see `docs/evidence/wp08-status.md`; live LLM agents still wait on Open Decision 8.
11. ~~Gameweek Decision Record, baseline comparison and replay harness (WP-09).~~ Done — see `docs/evaluation/wp09-status.md`.
12. Operate in manual-entry advisory mode until the later execution prerequisites are satisfied.
13. World Cup 2026 priors CSV assembled — see `control/identities/world-cup-2026-priors.csv` (brief: `docs/handover-world-cup-priors.md`).
14. ~~WP-10 deferred-feature interface notes~~ — next package after WP-09.

Human tasks that cannot be delegated, with their triggers:

- **(human, before Gameweek 1)** Recruit the approximately five cohort managers and agree the Section 17.7 protocol (ADR-0009).
- **(human, before any evidence or challenger agent work begins)** Select LLM provider(s) and add keys as environment secrets (Open Decision 8). Collectors, the snapshotter and the walking skeleton do not need them.

The standing brief for the next implementation agent is `docs/handover-brief.md`.

---

## 27. Reference sources

### Official

- [All you need to know about changes to FPL for 2026/27](https://www.premierleague.com/en/news/4679873/all-you-need-to-know-about-changes-to-fpl-for-202627)
- [2026/27 Bonus Points System changes](https://www.premierleague.com/en/news/4679946/whats-new-in-202627-fantasy-changes-to-bonus-points-system)
- [FPL transfer guidance](https://www.premierleague.com/en/news/2174907)
- [FPL scoring guidance](https://www.premierleague.com/en/news/2174909/fpl-basics-scoring)
- [FPL team-management guidance](https://www.premierleague.com/en/news/2174899/fpl-basics-managing-your-team)
- [FPL chip guidance](https://www.premierleague.com/en/news/2174900/fpl-basics-explained-how-to-use-your-chips)
- [Premier League Terms of Use](https://www.premierleague.com/terms-and-conditions)

### Historical data and optimisation

- [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League)
- [olbauday/FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights)
- [solioanalytics/open-fpl-solver](https://github.com/solioanalytics/open-fpl-solver)

### Existing analytics and agentic examples

- [FPL Review](https://fplreview.com/)
- [Fantasy Football Scout](https://www.fantasyfootballscout.co.uk/)
- [ikuzuki/fpl-platform](https://github.com/ikuzuki/fpl-platform)
- [fplkit](https://pypi.org/project/fplkit/)
- [lewis-king/fpl-mcp-server](https://github.com/lewis-king/fpl-mcp-server)

---

## 28. Final project principle

> **Build the trusted decision core first. Design for the larger vision now, but activate advanced retrieval, competitive intelligence, live agents, cloud infrastructure and computer-use automation only when their prerequisites are satisfied.**

The intended progression is:

```text
Governed data
    -> versioned rules
    -> point-in-time forecasting
    -> deterministic optimisation
    -> evidence-grounded review
    -> comparative agent evaluation
    -> controlled human approval
    -> verified computer-use execution
```

This preserves the wider ambition while keeping the initial build focused, measurable and safe.

---

## Appendix A. Glossary

FPL terms:

- **Gameweek (GW)** — one FPL scoring round, locked at a deadline before its opening fixture.
- **Chips** — once-per-half-season powers: Wildcard (unlimited free transfers for one Gameweek), Free Hit (temporary one-Gameweek squad), Bench Boost (bench players score), Triple Captain (captain scores treble).
- **BPS** — Bonus Points System, the per-match index that awards the 3, 2 and 1 bonus points.
- **FDR** — the official Fixture Difficulty Rating published through the FPL endpoints.
- **Blank / Double Gameweek** — a Gameweek in which a club has no fixture, or two.
- **Point hit** — the four-point cost of each transfer beyond the free allowance.
- **Selling price** — the amount recovered when selling a player under the half-profit rule; differs from current price.
- **Effective ownership (EO)** — the proportion of rival managers owning (and captaining) a player; deferred to Phase 5.
- **`ep_this` / `ep_next`** — official expected-points fields on the player endpoints, usable only if captured pre-deadline.
- **xG / xA** — expected goals and expected assists, chance-quality measures from shot models.

Project terms:

- **Point-in-time contract** — the four timestamps of Section 7.2 plus the rule that decisions may only use records with `available_at <= deadline`.
- **Replay** — re-running the whole decision pipeline against a historical deadline using only information available at that time (Section 21.3).
- **Shadow evaluation** — running a strategy against live data snapshots and scoring it without operating a live FPL entry for it.
- **Structured-data strategy** — a strategy whose inputs survive in historical datasets (statistical baseline, forecast plus optimiser); fairly evaluable by replay (Section 17.6).
- **Evidence-dependent strategy** — a strategy that also consumes the pre-deadline news environment (agent conditions); historical replay structurally understates it (Section 17.6).
- **Walking skeleton** — the earliest end-to-end pipeline: one historical Gameweek through crude versions of every component (Phase 1).
- **Gameweek Decision Record** — the auditable per-Gameweek output defined in Sections 3.1 and 16.
- **Multi-manager cohort** — recruited managers, each running their own single account under an assigned strategy (Section 17.7).
- **ADR** — architecture decision record, stored in `docs/decisions/`.
