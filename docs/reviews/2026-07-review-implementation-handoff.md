# Implementation handoff for the July 2026 review

**Date:** 28 July 2026
**Companion to:** `docs/reviews/2026-07-evidence-and-engine-review.md`
**Status:** decomposition of review recommendations R1–R7 into bounded work
items. This is a handoff index, not an ExecPlan: an implementing agent claims
one work item, opens its own ExecPlan under `docs/execplans/` (and a beads
issue via `bd`), and stays inside that item's boundary per `AGENTS.md`.

## How to use this document

Read first, in order: `AGENTS.md`, `docs/plan.md` §§4–7, 15–17 and 24–25, the
review itself, and — for evidence items — `docs/evaluation/2026-27-evidence-acquisition-retrieval-design.md`
and `docs/evaluation/2026-27-live-evidence-policy.md`.

Non-negotiable constraints that apply to **every** item below:

1. Frozen 2025/26 trajectories are never re-run, re-tuned or amended. New
   behaviour is evaluated as a **named fork or registered challenger** with a
   fit/validate split no later than 2024/25, or prospectively on live 2026/27
   shadow weeks. 2025/26 sealed outcomes are test evidence only.
2. Anything that changes live decision behaviour ships as versioned data under
   `control/` (policy JSON/YAML, model config) plus an ADR when a trade-off is
   involved; promotion into the production path is an owner decision.
3. No new collection without a registry entry (`control/sources/source-registry.yaml`)
   with confirmed `licence_status` and `allowed_use`.
4. Preregistration before outcomes: any 2026/27 live policy (chips, hits,
   evidence caps) has its thresholds recorded in
   `docs/evaluation/2026-27-preregistration.md` before the Gameweek it first
   applies to.
5. **Validation boundary (pending `FPL-cfb`):** current CI still runs
   `python3 -m pytest` and is not fresh-clone green because some tests require
   gitignored historical episode/raw artifacts and some sealed hashes remain
   platform-dependent. `FPL-cfb` is the authoritative P0 bug for separating a
   tracked-safe portable suite from an explicitly artifact-backed integration
   suite. Until it closes, every work item must publish and pass its focused
   tracked-safe command, name any required local artifacts, and report the
   corresponding artifact-backed command separately. Do not describe the
   repository-wide suite or CI as green, silently skip an ordinary contract,
   or treat `python3 -m scripts.download_historical` as provisioning governed
   episode trees: that command restores registered raw history only.

**Data prerequisite for calibration items (W2, W7, W9, W11):** raw vaastav and
football-data files under `data/raw/` are gitignored and may be absent in a
fresh environment. Restore them via `python3 -m scripts.download_historical`
against the registered sources (vaastav pinned at commit
`f2090d378ebd1b0c3d14884770dde95f38c50a0d`) before running calibrations; do
not substitute unregistered data. Synthetic-fixture test work proceeds without
them.

## Status legend

- **agent-ready** — implementable now by an agent within existing governance.
- **owner-gated** — agent can draft/build, but activation needs an owner
  decision (ADR ratification, rights review, provider contract, promotion).
- **blocked-on-data** — design can be built and tested on fixtures, but the
  real evaluation waits for live 2026/27 captures to accumulate.

## Point-in-time notice — Beads are authoritative

> **This handoff was written on 28 July 2026.** Main has since advanced;
> several work items below were implemented and their Beads closed. Consult
> `.beads/issues.jsonl` for current status before claiming any item. The table
> below carries a **Bead** column that cross-references the authoritative
> issue; where a Bead is listed as **superseded**, the work is complete and
> must not be duplicated.

## Bead crosswalk (W1–W19 → current status)

| ID | Bead | Bead status | Note |
|---|---|---|---|
| W1 | `FPL-dah` | closed | Implemented; event-sourced fixture state live |
| W2 | — | not yet opened | Still agent-ready once W1 consumed |
| W3 | — | not yet opened | Owner-gated; W1 and W2 first |
| W4 | `FPL-uwu` | open | In progress; availability persistence |
| W5 | — | not yet opened | Owner-gated ADR; depends on W4 |
| W6 | `FPL-f55` | closed | Implemented; claim-value ledger live |
| W7 | — | not yet opened | Raw data prerequisite applies |
| W8 | `FPL-ejl` | closed | Implemented; decision-aligned metrics live |
| W9 | `FPL-y0e` | closed | Implemented; **gate rejected** — top-bin recalibration did not clear locked-validation bar; rejection report is the deliverable |
| W10 | `FPL-4r6` | closed | Implemented; autosub/bench evaluation complete |
| W11 | — | not yet opened | Agent-ready; W8 prerequisite now satisfied |
| W12 | — | — | Owner-only; no bead |
| W13 | — | not yet opened | Owner-gated registry step first |
| W14 | — | not yet opened | Owner-gated registry step first |
| W15 | — | blocked-on-data | Awaiting ≥4 live GW odds captures |
| W16 | — | not yet opened | Agent-ready; W8 prerequisite now satisfied |
| W17 | — | blocked-on-data | Awaiting live shadow weeks |
| W18 | `FPL-1co` | closed | Implemented; hosted-response linter live |
| W19 | `FPL-sw0` | closed | Implemented; governance doc drift corrected |

## Work item index

| ID | Item | From | Bead | Status | Depends on |
|---|---|---|---|---|---|
| W1 | Event-sourced fixture state and DGW/BGW detection | R1 | `FPL-dah` | **superseded** (closed) | — |
| W2 | Elo-based future-fixture EP for multiweek/chip projection | R1 | — | agent-ready (promotion owner-gated) | W1 helps, not required |
| W3 | Chip policy preregistration draft | R1 | — | owner-gated | W1, W2 |
| W4 | Persistent availability state in the production projection | R2 | `FPL-uwu` | agent-ready (open) | — |
| W5 | Bounded upward evidence adjustments (policy revision) | R2 | — | owner-gated (ADR) | W4 |
| W6 | Claim-value ledger (ex-post evidence accounting) | R3 | `FPL-f55` | **superseded** (closed) | — |
| W7 | Calibrate FPL availability flags to start probability | R3 | — | agent-ready | raw data |
| W8 | Decision-aligned metrics in challenger gates | R4 | `FPL-ejl` | **superseded** (closed) | — |
| W9 | Per-position top-bin forecast recalibration challenger | R4 | `FPL-y0e` | **superseded** (closed — gate rejected) | W8 |
| W10 | Default expected-autosub/bench objective | R4 | `FPL-4r6` | **superseded** (closed) | W8 |
| W11 | Captain haul-probability challenger | R4 | — | agent-ready (promotion owner-gated) | W8 |
| W12 | Club-domain rights review tranche | R5 | — | owner-only | — |
| W13 | Predicted-lineups provider trial | R5 | — | owner-gated (registry) | W12-style rights step |
| W14 | Competition-calendar source registration and congestion feature | R5 | — | owner-gated (registry) | — |
| W15 | Odds team-context ablation rerun on real captures | R6 | — | blocked-on-data | ≥4–6 live GWs of Odds API slots |
| W16 | xG-rate event challenger | R6 | — | agent-ready (data caveat) | W8 |
| W17 | Set-piece role effect ablation | R6 | — | blocked-on-data | live shadow weeks |
| W18 | Hosted-response linter (reject-and-reprompt) | §5 | `FPL-1co` | **superseded** (closed) | — |
| W19 | Governance doc drift fixes | §5 | `FPL-sw0` | **superseded** (closed) | — |

Suggested next items for a single agent (as of 29 July 2026): W4 is open
(`FPL-uwu`); once closed, W5 (ADR) and W11 and W16 are the natural follow-ons.
W2, W7 and W11 are agent-ready with no open gates beyond W8 (now closed).
W19, W6, W8 and W18 are complete — do not re-implement.

---

## W1 — Event-sourced fixture state and DGW/BGW detection

**Objective.** Track fixture revisions (postponements, reschedules, blanks,
doubles) as an event-sourced history so any Gameweek's fixture set can be
reconstructed as-known-at a cutoff, and expose per-team fixture counts per
future Gameweek. This is plan §7.5 and the prerequisite for meaningful chip
planning.

**Touch points.** New module under `src/data/` or `src/normalisation/`
consuming successive `data/raw/fpl/*/fixtures` snapshots (already captured by
`scripts/run_snapshot.py` / `scripts/capture_fpl_live_shadow.py`); a derived
fixture-revision artifact; consumers in `src/optimisation/multiweek.py` and
`src/optimisation/chips.py` (both currently assume one fixture per team per
GW via the FDR projection in `control/policies/transfer-horizon-v1.json` and
`control/policies/chip-v1.json` `future_projection`).

**Deliverables.** Revision-log builder + point-in-time fixture view keyed by
`available_at <= cutoff`; per-team GW fixture-count table; tests covering a
postponement (GW blank appears), a reschedule into an existing GW (double
appears), and reconstruction at two different cutoffs giving different views.

**Acceptance.** Given two fixture snapshots where a match moves, the
point-in-time view at the earlier cutoff shows the original schedule and at
the later cutoff shows the revision; multiweek/chip projections consume
fixture counts (0, 1, 2) rather than assuming 1. No network access in tests.

## W2 — Elo-based future-fixture EP for multiweek/chip projection

**Objective.** Replace the flat FDR difficulty multipliers (1.2/1.1/1.0/0.9/0.8
in `transfer-horizon-v1.json` and `chip-v1.json`) with future-fixture
multipliers from the already-calibrated Elo team prior
(`src/forecasting/team_prior.py`, parameters in
`control/models/live-faithful-v1.feature-complete.json`), applied per player
per future Gameweek within the existing 4–6 GW horizons.

**Touch points.** `src/optimisation/multiweek.py`, `src/optimisation/chips.py`,
`src/optimisation/trajectory.py`; new versioned policy files
(`transfer-horizon-v2.json`, `chip-v2.json`) — do not mutate v1, which sealed
replay artifacts reference. Evaluation via `scripts/run_multiweek_challenger.py`
and the counterfactual harnesses (`src/evaluation/transfer_counterfactual.py`,
`chip_counterfactual.py`).

**Method constraint.** Future-GW multipliers use ratings strictly as of the
decision cutoff (no walk-forward through unplayed fixtures). Fit any new
scaling on ≤2023/24, validate once on 2024/25; 2025/26 forks are descriptive.

**Acceptance.** Paired evaluation report under `reports/` comparing v1 (FDR)
vs v2 (Elo) horizon projections on locked seasons with decision-level metrics
(transfer choice agreement, horizon EP error at 1–4 GWs ahead); v2 promoted to
challenger only if the locked validation improves or documents a trade-off.
Promotion to production is owner-gated.

## W3 — Chip policy preregistration draft (owner-gated)

**Objective.** Draft the 2026/27 chip deployment section of
`docs/evaluation/2026-27-preregistration.md`: per-chip deployment conditions
using W1 fixture counts and W2 projections, revised reserve/decay values with
their derivation, and the human-confirmation step (chips stay advisory in
Phase 1). The agent drafts and evidences; the owner ratifies before GW1 or
before first sanctioned use.

**Acceptance.** A preregistration diff the owner can ratify unchanged:
explicit numeric thresholds per chip, DGW/BGW conditions, abstention defaults,
and the evaluation that justified each number (from W2 runs and the existing
`reports/benchmarks/2025-26-chip/` counterfactuals). Open questions recorded,
not resolved silently.

## W4 — Persistent availability state in the production projection

**Objective.** Make accepted availability evidence a standing belief: once an
unavailability/reduction is accepted, it persists across checkpoints and
Gameweeks until superseded by newer evidence or expiry — eliminating the
"forecast forgets each week" failure (Timber, GW34–36).

**Touch points.** `src/evidence/availability_ledger.py` (state machine already
exists), `src/orchestration/live_evidence_arm.py` and
`src/orchestration/agent_fork_adapter.py` (application currently one-shot per
week), the projection assembly in `src/forecasting/live_capture.py` /
`replay_adapter.py`. Policy: extend `control/policies/evidence-adjustments.yaml`
with persistence semantics (carry-forward until `expires_at` or supersession;
re-confirmation cadence).

**Boundary.** Reductions-only, existing caps unchanged (upward adjustments are
W5). Frozen 2025/26 paths untouched; demonstrate on a named 2025/26 fork
(GW33–36 window) plus live-shadow wiring for 2026/27.

**Acceptance.** Test: an accepted unavailability at GW N still suppresses
minutes at GW N+1 without re-proposal, and a superseding claim restores the
baseline; the no-evidence control remains genuinely evidence-free. A named
fork artifact shows the Timber-class case no longer regresses. All lifecycle
gates (challenger, citation, expiry) still enforced.

## W5 — Bounded upward evidence adjustments (owner-gated ADR)

**Objective.** Allow the evidence arm to propose bounded *increases* to
`start_probability`/`expected_minutes` for canonical-source confirmations,
under stricter gates than reductions.

**Touch points.** `control/policies/evidence-adjustments.yaml` (new
`upward_adjustments` block — proposed defaults: cap +0.125 start-prob, min
adjustment confidence 0.75, canonical/primary source authority only),
`src/orchestration/evidence_fork.py` and `agent_fork_adapter.py` scaling logic
(currently reduction-shaped), prompts (`prompts/evidence-agent/v1.md` →
version bump with schema change), challenger schema.

**Gate.** This revises Open Decision 10 / ADR-0013 — requires a new ADR in
`docs/decisions/` and owner ratification, plus preregistration before live
use. The agent implements behind policy data defaulting to disabled.

**Acceptance.** With the policy block disabled, behaviour is byte-identical to
today (regression suite proves it). Enabled in a fork: upward proposals above
cap are clamped, below-confidence proposals rejected, non-canonical sources
refused; golden cases added under `evals/golden-cases/evidence/`.

## W6 — Claim-value ledger (ex-post evidence accounting)

**Objective.** A deterministic weekly report that joins, for every admitted
claim: claim class, source family, registry authority, confidence, age at
deadline → retrieved into packet? → cited by agent? → plan changed? → paired
same-state delta → underlying assertion verified against post-match minutes.
This is the measurement substrate for recalibrating every evidence constant,
and it operationalises the deferred `source-reputation` capability as pure
reporting (no ML, no behaviour change).

**Touch points.** New `src/evaluation/claim_value_ledger.py` +
`scripts/build_claim_value_ledger.py`. Inputs all exist:
`data/live-shadow/evidence/ledgers/`, packet artifacts and application records
from `src/orchestration/live_evidence_arm.py` outputs, paired deltas from
`src/evaluation/paired_metrics.py` / `shadow_attribution.py`, verification
from FPL `event/{gw}/live` post-match captures. Output: content-addressed JSON
per GW under `reports/evaluation/claim-value/` plus a cumulative roll-up by
(claim class × source family).

**Boundary.** Read-only over existing artifacts. Changes no policy, no
threshold, no prompt. 2025/26 rows carry the retrospective-evidence caveat as
a field.

**Acceptance.** Running against the existing 2025/26 agent-fork artifacts
reproduces the season review's published totals (17 applied weeks per arm;
non-zero paired weeks exactly GW7/12/17/18/22; same-state sums 0 Scout / +11
optimised) — the check that the join is correct. Idempotent: identical inputs
give identical bytes. Report renders even when a GW has zero claims.

## W7 — Calibrate FPL availability flags to start probability

**Objective.** Estimate P(start | `chance_of_playing_next_round` ∈ {25, 50,
75, null}, `status`, position, days-since-flag) from the vaastav archive, and
publish it as a versioned calibration table under `control/models/` for use as
the projection's availability prior.

**Touch points.** New `scripts/calibrate_availability_flags.py` following the
split discipline of `src/forecasting/calibrate_live_faithful.py` (fit
≤2023/24, locked validation 2024/25, never fit on 2025/26); consumers later in
`src/forecasting/live_faithful.py` minutes path (consumption itself is a
follow-up challenger, not this item).

**Data caveat.** Verify flag fields actually exist per season in the vaastav
exports before promising coverage; if pre-deadline flag snapshots are
unavailable historically, restrict claims to what the export's timing
supports and record the limitation in the calibration report.

**Acceptance.** Calibration report under `reports/forecasting/` with per-flag
empirical start rates, sample sizes, confidence intervals and locked-season
Brier improvement over the current hard-override treatment
(`src/forecasting/naive.py` behaviour as baseline). Table published with
`content_sha256`; no 2025/26 fitting.

## W8 — Decision-aligned metrics in challenger gates

**Objective.** Add XI-regret (selected XI EP-realised gap vs best-possible XI
from the same market), captain regret, and top-price-band rank correlation as
first-class metrics computed by every forecast evaluation, alongside MAE/RMSE
— so future challengers are judged on the cohorts that score points.

**Touch points.** `src/forecasting/evaluate.py`, `src/evaluation/calibration.py`,
the promotion-gate definitions referenced by
`docs/evaluation/live-faithful-forecast-policy.md` (gate *changes* are
documented, not silently applied: this item computes and reports the metrics;
re-weighting promotion criteria is a policy edit for owner sign-off).

**Acceptance.** Re-running the existing challenger evaluations (events,
team-context, robust) reproduces their published MAE numbers unchanged and
additionally reports the new metrics; the review's claim that rejected
challengers improved owned/selected cohorts is now visible in one table.
Deterministic and covered by fixture tests.

## W9 — Per-position top-bin forecast recalibration challenger

**Objective.** A post-composition recalibration layer (per-position isotonic
or binned mean-matching) targeting the documented top-bin overprediction
(selected-XI bias −0.93; top bin ~9.5 predicted vs ~5.9 realised), registered
as `live-faithful-v2.recalibrated` — fit ≤2023/24, locked 2024/25, judged on
W8 metrics.

**Touch points.** New module `src/forecasting/recalibration.py` + config
`control/models/live-faithful-v2.recalibrated.json`; calibration script
mirroring `calibrate_live_faithful.py`; evaluation via
`scripts/run_challenger_matrix.py`.

**Acceptance.** Locked-validation report showing top-bin bias reduction
without degrading top-15 precision or XI-regret (the failure mode that sank
uniform robust shrinkage). If the gate fails, the rejection report is itself
the deliverable — do not promote a plausible-sounding layer.

## W10 — Default expected-autosub/bench objective (owner-gated promotion)

**Objective.** Promote the existing `probabilistic_v1` contingency objective
(`src/optimisation/squad_contingency.py`, appearance model
`control/models/appearance-distribution-v1.json`) from opt-in to production
default, on the strength of a paired evaluation.

**Deliverable.** Paired locked-season + 2025/26-fork evaluation (default-off
vs default-on) with lineup/bench-order decision diffs and realised autosub
deltas; a one-page promotion note; promotion itself is an owner decision
recorded in the live-faithful policy doc.

**Acceptance.** Evaluation shows non-negative locked-season decision value and
no rule violations (bench order legality via `run_rules_golden`); the flag
flip is a single policy-data change, reversible.

## W11 — Captain haul-probability challenger

**Objective.** Re-attempt captaincy as max E[captain points] with a calibrated
P(points ≥ 10) tie-break derived from per-90 haul distributions (vaastav,
≤2023/24) and the appearance model — replacing the rejected position-residual
design (`control/policies/captain-v1.json`).

**Touch points.** `src/optimisation/captaincy.py`, new `captain-v2.json`
policy, evaluation via `scripts/run_captain_counterfactual.py` and
`src/evaluation/captain_counterfactual.py` against the same locked 2024/25
gate that rejected v1 (v1's −9 on 2024/25 is the bar to beat).

**Acceptance.** Locked 2024/25 validation ≥ control (non-negative), then
descriptive 2025/26 counterfactual; promotion remains owner-gated. The
distribution calibration ships with its own report and `content_sha256`.

## W12 — Club-domain rights review tranche (owner-only)

Not agent work. Owner reviews terms for a first tranche of official club
domains (suggest: ownership-weighted coverage of the current squad plus top
transfer candidates, from the catalogue in
`control/sources/club-news-catalogue.yaml`) and updates
`control/sources/source-registry.yaml` entries with confirmed
`licence_status`/`allowed_use`. Agents must not enable collection ahead of
this. An agent may prepare the per-domain terms dossier (URLs of terms pages,
robots.txt status) as input — without collecting content.

## W13 — Predicted-lineups provider trial (owner-gated)

**Objective.** Execute the trial already stubbed in
`config/data_sources/` lineups config (`selected_provider: null`,
`trial_required_before_activation`): evaluate one candidate provider for
predicted/confirmed lineups on rights, timestamp precision and accuracy.

**Sequencing.** Owner selects/contracts the provider and registers it
(disabled → shadow); the agent then builds the shadow capture adapter
following the `capture_live_odds.py` pattern (env-var key, raw snapshots,
checkpoint binding, no claim minting) and a lineup-accuracy scorer against
post-match FPL minutes.

**Acceptance.** After ≥4 live GWs: a trial report with per-slot availability,
prediction accuracy vs realised XIs, and a promote/reject recommendation.
Capture is shadow-only throughout.

## W14 — Competition-calendar source and congestion feature (owner-gated)

**Objective.** Register a rights-cleared source for UCL/UEL/domestic-cup
fixtures (registry entry `official-competition-schedules` is currently
disabled), then add per-player midweek-load features (days since last match,
matches in trailing 14 days incl. non-PL) to the minutes model as a registered
challenger. Agent can build the schema, adapter skeleton and the
feature/challenger code against fixture data; enabling collection waits on the
registry.

**Acceptance.** Feature computation is cutoff-safe (test: adding a post-cutoff
match does not change the feature); minutes-model challenger evaluated under
the standard locked-season protocol with expected-minutes MAE and start Brier
as gates.

## W15 — Odds ablation rerun (blocked-on-data)

**Objective.** Rerun the team-context/odds challenger
(`src/forecasting/team_context_challenger.py`) with genuinely timestamped
pre-deadline odds once ≥4–6 Gameweeks of The Odds API slot captures
(T-24h/T-8h/T-2h/final) exist — the 2025/26 rejection was evaluated with odds
degraded in 37/38 GWs and must not be cited as a negative result.

**Acceptance.** Prospective evaluation on live shadow weeks with per-slot
odds coverage reported; decision recorded either way. Separately deliver a
short provider survey for **player-market** odds (anytime scorer, clean
sheet) with rights notes, as input to an owner sourcing decision.

## W16 — xG-rate event challenger

**Objective.** Rebuild the event-decomposition path using expected rather than
realised event rates: xG/xA/xGC per 90 as the goals/assists/CS inputs to the
existing event composition in `src/forecasting/live_faithful.py` (which is
retained at weight 0). Register as `live-faithful-v2.xg-events`.

**Data caveat.** Confirm which historical seasons carry usable xG in the
registered local estate (vaastav understat mirrors are local-analysis-only per
the registry; FPL-native xG fields begin in recent bootstraps). The
calibration report must state exactly which seasons trained the rates; if
insufficient history exists, this becomes a 2026/27 live-shadow challenger
using FPL-native fields prospectively.

**Acceptance.** Standard challenger protocol (fit ≤2023/24 where data allows,
locked 2024/25, W8 metrics). The prior event-model rejection (realised rates,
weight 0.25, OOS MAE +0.118) is the documented baseline it must beat.

## W17 — Set-piece role effect ablation (blocked-on-data)

**Objective.** Turn the captured set-piece/penalty roles
(`src/ingestion/set_piece_roles.py`, currently `effect_weights: null`) into a
measured EP effect: penalty-taker status → additional expected goals from
historical penalty award rates; evaluated prospectively on 2026/27 shadow
weeks (historical role snapshots don't exist point-in-time).

**Acceptance.** Preregistered effect design before the season; ≥6 shadow weeks
of paired projection comparison; promote/reject recorded with the same
discipline as other families. Until then `effect_weights` stays null.

## W18 — Hosted-response linter

**Objective.** Recover the ~16 GW20–38 hosted namespaces lost to
schema/serialisation faults: a deterministic host-side linter that validates
agent/challenger responses (schema, key names, nesting, hash bindings) and
re-prompts once with the specific violation within the existing runtime
budget (ADR-0016), before falling back.

**Touch points.** `src/orchestration/hosted_response.py`,
`src/orchestration/agent_arm.py`; golden cases from the actual failed
namespaces preserved under `reports/benchmarks/2025-26-agent-forks/` (they are
immutable diagnostics — copy patterns into `evals/golden-cases/evidence/`,
do not modify sources).

**Acceptance.** Each archived failure class (nested claims, wrong keys, hash
mismatch) is detected with an actionable message; a compliant response passes
untouched; at most one re-prompt; fallback behaviour unchanged when the
re-prompt also fails. No change to what agents are allowed to propose.

## W19 — Governance doc drift fixes

**Objective.** Bring stale docs in line with registry v0.6.0:
`docs/data-sources/wp02-status.md` (claims only FPL enabled),
`docs/data-sources/profiles/statsbomb-open.md` (says disabled),
`docs/data-sources/live-forecast-capture.md` and
`docs/data-sources/snapshot-cadence.md` (say no approved live odds provider).
Each gets a dated correction note pointing at the registry as authoritative —
do not rewrite history, append a status update.

**Acceptance.** No doc contradicts `control/sources/source-registry.yaml`;
grep for the stale claims returns only the corrected passages. Docs-only
change.

---

## What this handoff deliberately does not decide

- Promotion of any challenger into the production path (owner, per policy).
- Rights outcomes for W12–W14 sources (owner).
- Whether upward evidence adjustments launch at GW1 or wait for W6 data
  (owner — review §6, question 3).
- Revised chip reserve numbers (W3 drafts them with evidence; owner ratifies).
