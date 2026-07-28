# Repository review: evidence gathering, replay engine and evidence weighting

**Date:** 28 July 2026
**Status:** advisory review — not an ADR; nothing here changes any frozen replay,
policy or registry entry. Recommendations that carry trade-offs should be
ratified through `docs/decisions/` before implementation.

This review answers four questions posed by the owner:

1. How does the engine work today, as demonstrated by the historic replays?
2. What gaps exist in how evidence is gathered — both for optimising the squad
   and throughout the live gameweek?
3. Is the current weighting of each evidence class right, and can it be
   optimised?
4. Where should the project go next?

---

## 1. How the engine works today (as replayed)

### 1.1 The decision core

The production stack, as exercised by the 2025/26 replays, is:

- **Forecast** — `live-faithful-v1`
  (`control/models/live-faithful-v1.feature-complete.json`,
  `src/forecasting/live_faithful.py`): a rate-based expected-points model.
  Prior-season points-per-90 by FPL `code` (position × price-band fallbacks for
  new players), empirical-Bayes updated in-season
  (`prior_equivalent_minutes: 1350`, `start_prior_equivalent_matches: 2`),
  multiplied by expected minutes and a coupled attack/defence Elo fixture
  multiplier (k=40, home advantage 80, `fixture_scale` 0.25, bounds
  [0.7, 1.3]). The event-decomposition path exists but is calibrated to
  **weight 0** — the production forecast is effectively
  `posterior_pp90 × minutes/90 × team_multiplier`.
- **Optimiser** — single-Gameweek transparent solver
  (`src/optimisation/solver.py`, ADR-0011/0012): maximise XI EP + captain EP
  − hits, plus a fixed banked-free-transfer option value of 1.80 points
  (ADR-0020). Captain is the max-EP starter; bench order is by EP and does not
  enter the objective outside Bench Boost.
- **Evidence** — a governed, append-only ledger
  (`src/evidence/live_evidence_ledger.py`) feeding a bounded packet (≤12
  claims, ≤12,000 chars) to a proposal-only hosted evidence agent, reviewed by
  an independent challenger, applied by the host as **reductions only** to
  `expected_minutes` / `start_probability`, capped at ±0.25 absolute start-prob
  delta (`control/policies/evidence-adjustments.yaml`, ADR-0013 / Open
  Decision 10). Everything else falls back to the frozen no-evidence plan.

### 1.2 What the replays demonstrate

The replay engineering is exceptional: sealed episodes, per-arm state chains,
freeze-before-reveal, factorial (2×2 seed × evidence) attribution, and paired
same-state controls that separate "evidence was accepted" from "evidence
changed the decision" from "the change scored points". The integrity story is
the repository's strongest asset. Headline results:

| Result | Value | Source |
|---|---|---|
| Canonical optimiser vs do-nothing baseline | 2010 vs 1990 (+20; 95% CI [−5.64, +6.69] weekly) | `reports/evaluation/2025-26-control-review.json` |
| Enhanced factorial, optimised seed effect | +45 (structured), +113 (evidence trajectory) | `docs/evaluation/2025-26-enhanced-season-review.md` |
| Longitudinal evidence effect | −15 (Scout seed), +53 (optimised seed) | same |
| **Same-state causal evidence effect** | **0 (Scout), +11 (optimised) across 38 weeks** | same |
| Agent-fork hybrid season (GW12 fork) | 2075 vs 2010 canonical (+65), of which **direct same-state +16** | `reports/benchmarks/2025-26-agent-forks/season-deep-review.md` |
| Chips used, any arm, any trajectory | **0** | all checkpoints |
| Forecast on selected XI | MAE 3.25, bias −0.93, correlation 0.21 | control review calibration |

Three readings matter for prioritisation:

1. **The optimiser barely beats doing nothing** on the canonical path (+20,
   not significant). The seed (initial squad) and inherited trajectory effects
   dominate everything the weekly engine adds.
2. **Evidence, as currently surfaced and gated, is nearly score-neutral.**
   Seventeen applied weeks per arm produced non-zero same-state deltas in only
   five Gameweeks (GW7 −8, GW12 −1/−1, GW17 +2/+3, GW18 −1/+9, GW22 +8/0).
   The season review correctly attributes the +53 longitudinal headline mostly
   to path interaction, not agent prose.
3. **The forecast is weakest exactly where decisions live.** Whole-market MAE
   (1.09) is respectable, but the selected XI — the only cohort that scores —
   shows heavy top-bin overprediction (predicted ~9.5 vs realised ~5.9 in the
   top bin) and near-noise correlation (0.21).

The replay's own review sections identify most of this. The value this review
adds is ranking the gaps by expected points and proposing concrete mechanisms.

---

## 2. Is the evidence weighting right?

Short answer: **there is currently almost nothing that could be called a
weighting, so the question is really whether the gates and caps are right —
and they are uncalibrated, asymmetric and in two cases confounded.**

### 2.1 Findings

**F1 — No evidence class has a learned or even estimated production weight.**
Ratings and set-piece families carry `effect_weights: null`; odds enter only a
rejected challenger at a hand-set `odds_weight: 0.1`; unstructured evidence is
gated by fixed thresholds (claim confidence ≥0.55, adjustment confidence
≥0.60, start-prob delta cap 0.25) that ADR-0013 explicitly marks as proposed
defaults, never revisited against outcomes. The official-FPL news claim class
is minted at a hard-coded confidence of 0.98 and default impact of 6.0 points.
None of these numbers has an empirical basis yet. That was the right call for
Phase 1 (fail-closed beats fail-fitted), but the project now has a full season
of claim → outcome pairs sitting in sealed artifacts and no loop that consumes
them.

**F2 — Evidence application is reductions-only, which caps its value at
roughly half of what the class can offer.** The agent may only lower
`expected_minutes` / `start_probability`. "Confirmed starter in the press
conference", "penalty taker retained", "returned to full training" — the
positive half of the availability signal — cannot enter the projection at
all. The five non-zero evidence weeks in 2025/26 were all exclusion-shaped.
Asymmetry was a sound safety choice, but it should now be an explicit,
measured trade-off rather than a structural constant: a bounded upward
adjustment (e.g. capped at +0.15 start-prob, stricter confidence 0.75,
citation from a canonical source only) is a preregistrable counterfactual.

**F3 — Availability state does not persist; it is re-derived weekly.** The
Timber case (GW34–36 in the agent-fork review) shows the deterministic
baseline restoring high expected minutes each week until evidence was
re-applied. `src/evidence/availability_ledger.py` exists precisely for
stateful accepted/stale/superseded availability, but the production projection
path does not treat an accepted unavailability as standing until superseded.
This is the cheapest high-value evidence fix in the repository: it converts
one-shot adjustments into a persistent belief state and removes a whole class
of "evidence agent must repeat itself or the forecast forgets" failures.

**F4 — Two negative ablation results are confounded and should not be read as
"this evidence class has no value".**

- The team-context/odds challenger was rejected with odds **degraded in 37 of
  38 Gameweeks** — it was evaluated essentially without its input. Once The
  Odds API slots (T-24h/T-8h/T-2h/final) accumulate real timestamped
  captures, the ablation must be rerun before odds are written off.
- The event-decomposition challenger (weight 0.25, rejected out-of-sample)
  was built on **realised** goal/assist rates, the noisiest possible event
  signal. The 2026/27 bootstrap now carries FPL-native xG/xA/xGC; an
  xG-rate-based event path is a materially different hypothesis and deserves
  its own registered challenger rather than inheriting the rejection.

**F5 — The retrieval impact score is the right shape but only routes
attention.** `impact = max_boundary_swing × claim_confidence` ranks claims
into the packet, which is exactly the decision-boundary framing the
acquisition/retrieval design (`docs/evaluation/2026-27-evidence-acquisition-retrieval-design.md`)
formalises. But nothing downstream ever scores whether the routed claim
*deserved* its rank. The paired same-state deltas already recorded per week
are the missing training signal.

### 2.2 How to optimise the weighting (mechanism, not vibes)

The project's governance stance — deterministic core, LLM proposes only —
rules out "learn a soft weight per evidence type inside the forecast" as a
first move, and rightly so. The compatible optimisation path is:

1. **Build the claim-value ledger now (ex-post accounting).** For every
   admitted claim, join what is already recorded: claim class, source family,
   authority, confidence, age at deadline → did it enter a packet → did the
   agent cite it → did it change the plan → paired same-state delta → did the
   underlying assertion verify (player started / minutes played / role held)?
   All of these fields exist across ledger, packet, application and outcome
   artifacts; nothing new needs collecting. This is a deterministic reporting
   job, and it turns the deferred `source-reputation` capability from "needs
   labelled data someday" into "regenerate a table each Gameweek".
2. **Calibrate the gate constants against that ledger.** The 0.55/0.60/0.25
   trio and the 0.98/6.0 official-news constants become empirical questions:
   at what observed verification rate does a claim class earn a larger cap?
   Fit on 2025/26 (acknowledging its retrospective-evidence caveats) plus
   live 2026/27 shadow weeks; validate only on later live weeks; change the
   policy YAML via ADR, never mid-trajectory.
3. **Calibrate FPL's own flags as an evidence class.** `status` and
   `chance_of_playing_next_round` (25/50/75%) are the one availability signal
   with ten seasons of history in the vaastav archive. Estimating
   P(start | flag, position, days-to-deadline) is leak-free, deterministic,
   and would give the projection a principled availability prior that the
   evidence agent then only perturbs. Today the flags are consumed naively
   (hard override in the baseline; claim-minting in live capture) without any
   measured mapping.
4. **Replace the fixed ±0.25 cap with class-conditional caps** once (1)–(3)
   exist: canonical-source availability claims verified at ≥95% can earn a
   hard-zero or near-hard-zero application; weaker classes keep tight caps.
   The cap schedule lives in `control/policies/` as data, satisfying the
   rules-as-data ground rule.

This sequence never lets a model set a weight; it lets **measured claim
verification rates** set the weights, with the LLM still only proposing.

---

## 3. Gap analysis

### 3.1 Decision-layer gaps (largest expected points, zero licensing risk)

**G1 — Chips are the single largest hole.** No arm, in any trajectory, used a
chip across 38 weeks; the chip policy (`control/policies/chip-v1.json`) is an
experimental shadow challenger whose reserve values (WC 16, FH 12, BB 8, TC 8)
and 2.0-point deployment hurdle kept every chip in reserve all season. A
competent human's chip suite is conservatively worth 60–120+ points a season;
the replay's own GW31 counterfactual showed a Free Hit restore branch worth
+28 over GW31–38 even in a season it declined to play. The engine as replayed
is therefore structurally unable to match good managers regardless of forecast
quality. The GW26–GW30 review already flags this ("a material limitation");
it should now be treated as the top production work item, with preregistered
deployment thresholds and a DGW/BGW-aware horizon before the 2026/27 chips
matter (fixture-revision awareness, plan §7.5, is a prerequisite — chip value
concentrates almost entirely in blanks and doubles).

**G2 — The single-GW horizon starves the transfer decision.** ADR-0012 fixed
a one-week horizon with a flat 1.80 banked-FT bridge. Transfers are the one
decision where the future dominates: fixture swings, price-locked squad
structure and hit amortisation are all multi-week phenomena. The multiweek
challenger (4-GW beam, discount 0.9) exists but projects future fixtures with
crude FDR multipliers (1.2…0.8) even though the calibrated Elo pipeline
already produces per-fixture multipliers for the current week. Promoting
Elo-based future-fixture EP into the transfer objective (lineup/captain can
stay single-week) is an internal change with a ready-made evaluation harness.

**G3 — Captaincy is max-EP with no upside term.** Captaincy is ~20% of season
points and is a ceiling decision, not a mean decision. The rejected captain
challenger failed because its position-residual model was unstable — not
because upside doesn't matter. The calibrated appearance-distribution model
(`control/models/appearance-distribution-v1.json`) plus per-90 haul
probabilities from ten seasons of vaastav data supports a cleaner formulation:
maximise E[captain points] with a P(≥10) tie-break, validated on locked
seasons.

**G4 — Bench/autosub value is opt-in, not default.** The canonical arm banked
+85 autosub points passively; the probabilistic contingency objective exists
(`squad-contingency.md`) but is not the production default. Given the
appearance model is already calibrated (Brier 0.362 vs 0.372 uncalibrated),
defaulting expected-autosub into the objective is low-risk.

### 3.2 Forecast-layer gaps

**G5 — Top-bin overprediction where it costs points.** Selected-XI bias −0.93
and 0.21 correlation mean the solver systematically buys inflated EP. The
robust-selection challenger shrinks the tail but worsened top-15 regret —
evidence that uniform shrinkage is the wrong tool. A per-position isotonic (or
binned) recalibration layer fitted on locked seasons, applied after
composition, targets the bias without flattening genuine premium separation.
Equally important: promote **decision-aligned metrics** (XI regret vs
best-possible XI, captain regret, top-price-band rank correlation) to
first-class gates alongside MAE, which is dominated by the irrelevant long
tail of non-players. The current gate structure rejected two challengers on
all-player MAE while both improved the owned/selected cohorts.

**G6 — The minutes model is the weakest input and has no context features.**
Expected-minutes MAE sits around 17–19; the model is
`start_p × minutes_per_start + (1−start_p) × 10` blended with a 3-GW recent
window. It knows nothing about European/cup congestion (the
`official-competition-schedules` source is disabled, so midweek UCL/UEL/cup
load is invisible), manager changes, or role changes. Plan §7.1 already names
expected minutes as the weakest point of the entire pipeline; the replay
confirms it (the Timber case, the GW7 Gabriel case, and the fact that every
consequential evidence week was minutes-shaped). Minutes is where both new
data and new evidence classes should be pointed first.

### 3.3 Live-week evidence-surface gaps

The checkpoint cadence (daily preseason, T-48h, T-24h, T-8h, T-2h, T-5m,
post-match) is well designed. The problem is what flows through it:

**G7 — Only one automated claim source exists.** `fpl-official-endpoints` is
the sole automated evidence producer; club news, press conferences, training
reports and lineup evidence are all required families in the coverage config
but `manual_citation` in practice — so every pre-deadline checkpoint starts
with known coverage gaps that only manual effort fills. Press conferences
(typically T-48h to T-24h) are precisely where the highest-value minutes
evidence appears, and they are currently the weakest-covered family. The
news-discovery catalogue (21 official domains) finds leads but cannot extract
claims. Concretely: the pipeline is production-grade from ledger to packet,
and starved at the mouth.

**G8 — Odds are captured without player markets and not yet consumed.** The
Odds API capture is h2h + totals, shadow-only. Team-level odds are largely
redundant with the calibrated Elo (that is partly why the odds challenger
looked worthless); the market signal the forecast cannot replicate is
**player props** — anytime goalscorer and clean-sheet prices are the best
public per-player forecast of attacking/defensive returns. No registered
provider currently offers them; that evaluation belongs on the roadmap ahead
of another team-odds iteration.

**G9 — Mid-week signal decays between checkpoints.** Post-match capture reads
`event/{gw}/live`, but injuries from midweek cup/European fixtures (not in the
FPL fixture feed) surface only if a human notices. A persistent availability
ledger (F3) plus the competition-calendar gap (G6) compound here: the system
can go from Saturday to the following Friday with no machine-visible reason
to doubt a player who was hurt on Wednesday.

### 3.4 Data gaps, ranked by expected decision value

| Rank | Gap | Status today | Route |
|---|---|---|---|
| 1 | Press-conference / training availability evidence, automated | Manual citation; registry disabled pending rights | Rights review for club official domains (already catalogued); even 3–5 clubs automated would cover most owned players |
| 2 | Predicted / confirmed lineups | `official-lineups-minutes` disabled; provider `null`, trial required | Run the provider trial; post-match minutes already flow via FPL event-live |
| 3 | Competition calendars (UCL/UEL/domestic cups) | Disabled | Needed for congestion features in the minutes model and DGW/BGW chip planning |
| 4 | Player-market odds (goalscorer, CS) with pre-deadline timestamps | Not offered by registered provider | Provider evaluation; The Odds API team markets are already captured but low-incremental over Elo |
| 5 | FPL-native xG/xA as event rates | Available in 2026/27 bootstrap; unused by forecast | Internal work only — registered xG-event challenger (see F4) |
| 6 | Set-piece / penalty roles as an effect | Captured (64 pen / 60 DFK / 71 corner candidates), `effect_weights: null` | Live ablation; penalty status is a large, cheap EP adjustment |
| 7 | Betfair/exchange timestamped prices | Blocked pending account/terms | Keep pending; player props (rank 4) likely dominate for effort |
| 8 | Ratings (FotMob/Sofascore blocked; StatsBomb no live coverage) | Degraded family | Accept the gap; do not spend effort here in 2026/27 |

Historical replays cannot be improved much further: WP-04 established that
pre-deadline news is unrecoverable at scale (`news-recoverability.md`), so the
2025/26 evidence surface stays sparse. **The scarce asset is live 2026/27
capture — every week not captured is unrecoverable**, which is why acquisition
(G7) outranks any modelling change that could be done later on stored data.

---

## 4. Recommendations, prioritised

Ordered by expected points per unit of invasiveness, with dependencies noted.
R1–R4 are internal (no licensing exposure); R5–R6 need rights work.

**R1 — Make chip + multiweek transfer planning a production layer (G1, G2).**
Promote the chip and multiweek challengers from shadow to a preregistered
production policy for 2026/27: DGW/BGW-aware horizon fed by event-sourced
fixtures (plan §7.5), Elo-based future-fixture EP replacing FDR multipliers in
`transfer-horizon-v1`/`chip-v1`, deployment thresholds registered in
`docs/evaluation/2026-27-preregistration.md` before first use. This is the
only change plausibly worth >50 points on its own.

**R2 — Persistent availability state + bidirectional bounded evidence (F2,
F3, G9).** Wire `availability_ledger.py` into the production projection so
accepted unavailability stands until superseded; add a preregistered, capped
upward-adjustment class for canonical-source fitness confirmations. Both are
policy-YAML + orchestration changes with existing tests to extend.

**R3 — Claim-value ledger and gate recalibration (F1, §2.2).** Deterministic
ex-post accounting per claim (routed → cited → plan-changed → paired delta →
verified), regenerated each Gameweek; use it to recalibrate ADR-0013
constants and the official-news 0.98/6.0 defaults at season checkpoints. This
also operationalises the deferred `source-reputation` capability a phase
early, without any of its ML risk.

**R4 — Decision-aligned forecast calibration (G5, G3, G4).** Per-position
top-bin recalibration fitted on locked seasons; XI-regret / captain-regret /
top-band rank metrics added to every challenger gate; appearance-based
expected-autosub objective made default; captain policy re-attempted as
mean + calibrated haul-probability tie-break.

**R5 — Attack the minutes evidence surface (G6, G7, data ranks 1–3).**
Sequence: (a) owner rights review to move a first tranche of club official
domains from `manual_citation` to automated collection; (b) run the
predicted-lineups provider trial already stubbed in config; (c) register a
competition-calendar source so congestion enters the minutes model. Every
consequential evidence week in 2025/26 was minutes-shaped; this is where
acquisition effort converts to points.

**R6 — Rerun the confounded ablations on real data (F4, G8).** Once 4–6 weeks
of timestamped Odds API slots exist, rerun the team-context ablation as
registered; build the xG-rate event challenger from FPL-native fields; run the
set-piece effect ablation. Separately evaluate a player-props provider —
that, not team odds, is the market signal worth paying for.

**R7 — Keep the acquisition/retrieval design's four-plane metrics as the
evidence KPI** (endorsing `FPL-bsw.38.14` as specified): boundary coverage,
candidate recall, decision-change rate and paired delta — never document or
claim volume. R3's ledger is the natural fifth plane (ex-post claim value).

**Sequencing note.** Before 2026/27 GW1: R2 and the preregistration halves of
R1/R4 (thresholds must be registered before outcomes exist), plus R5(a)
because rights review has external latency. During the season: R3, R6 and R7
run as weekly accounting; R1's chip policy activates at the first sanctioned
DGW/BGW window. Post-season: gate recalibration (R3) and any cap-schedule
ADRs for 2027/28.

---

## 5. Minor findings

- **Documentation drift:** `docs/data-sources/wp02-status.md` (claims only FPL
  enabled, registry 0.1.0), `docs/data-sources/profiles/statsbomb-open.md`
  (says disabled; registry v0.6.0 enables local transform), and
  `docs/data-sources/live-forecast-capture.md` / `snapshot-cadence.md` (say no
  approved live odds provider; The Odds API is enabled) all lag the registry.
  Cheap fixes that prevent a future agent acting on stale governance state.
- **Hosted-protocol fragility:** 16 degraded hosted namespaces in GW20–38
  were schema/serialisation failures, not judgement failures. A stricter
  host-side response linter (reject-and-reprompt within budget) would recover
  most of these before they cost a fallback week.
- **The GW7 Gabriel case deserves a permanent place in the golden set:** a
  correct-in-expectation evidence cut that cost 8 realised points is exactly
  the example that keeps "evidence value" honest — expected-value policy
  quality and realised outcomes must continue to be reported separately.

## 6. Open questions for the owner

1. Chip activation is the largest points lever but also the largest new risk
   surface — should chip deployment remain human-confirmed (advisory) for all
   of 2026/27 even after preregistration? (Consistent with Phase 1 advisory
   posture; recommended.)
2. Which club domains should enter the first automated-collection rights
   review tranche (R5a)? Suggest starting from ownership-weighted coverage of
   the current squad plus the top transfer candidates.
3. Should bounded upward evidence adjustments (R2) wait for one season of
   claim-verification data (R3), or launch with conservative caps at GW1?
   Recommend launching at GW1 with caps half the downward equivalents,
   preregistered.
