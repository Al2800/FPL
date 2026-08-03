# Operationalisation: from decision laboratory to live decision engine

**Date:** 3 August 2026
**Origin:** repository review (functionality, structure, data usage) by a cloud agent; this spec converts that review into a handover plan.
**Read first:** `AGENTS.md`, `docs/plan.md` (§§11–19, 25–26), `docs/handover-brief.md`, `docs/optimisation/wp07-status.md`, ADRs 0011, 0012, 0016, 0020 and 0021.

## Review findings this plan responds to

### State of the repo

Governance, reproducibility and evaluation scaffolding are excellent: rules-as-data with golden cases, source registry, point-in-time enforcement (`src/orchestration/historical_feature_state.py` even forbids `ep_this`), ~784 tests, and ~190 historical decision records under `reports/benchmarks/2025-26/`. But as a decision engine it is a laboratory, not an operational system: `reports/gameweeks/` contains only the synthetic `skeleton-gw3` — zero live 2026/27 Gameweek Decision Records.

### Functional gaps

1. **No closed weekly loop.** Producing a recommendation is a human-orchestrated chain: capture dispatch → manual manager-state entry (`control/templates/manager-state-entry.json`, ADR-0005) → `scripts/build_live_episode.py` → optimiser/shadow scripts. The manager-state → `SolverInput` + GDR adapter is still listed as next work in `docs/handover-brief.md`. There is no single `run_gameweek` command.
2. **Forecasting is heuristic baselines.** Lagged-minutes blends, walk-forward Elo, per-90 rates × expected minutes, a three-state appearance distribution. No fitted models and **no Monte Carlo simulation** — plan §11.3 calls for point distributions, but downstream consumers see deterministic expected points plus a q80 shrinkage band.
3. **Optimiser is enumerative, not optimal.** `src/optimisation/solver.py` searches same-position transfer sets in a candidate pool; Wildcard/Free Hit full-squad rebuild is stubbed (hit accounting only, per `docs/optimisation/wp07-status.md`). Multi-week beam search exists, but the Phase-1 live horizon remains single-GW under ADR-0012 as amended by the ADR-0020 option-value bridge.
4. **The AI layer is manual-in-the-loop.** `src/orchestration/agent_arm.py` targets `gpt-5.6-sol` via the ChatGPT-subscription Codex host (no API key, per Open Decision 8); a human runs the model and materialises responses. Evidence/challenger arms cannot run unattended at T-48h/T-8h/T-2h.
5. **Missing decision surfaces:** price-change forecasting, effective ownership / rank-aware risk (Phase 5 by design), automatic post-GW outcome attachment on live records, any dashboard or notification surface.
6. **Operational fragility:** capture scheduling is a single Windows machine (`scripts/install_deadline_capture_scheduler.ps1`, 15-minute polling) with no freshness/failure alerting; §22.1 degraded-operation reporting exists as policy, not as notification.

### Structural assessment

The four-plane architecture is sound and respected in code. Two criticisms:

- `src/orchestration/` (~30 modules) and `scripts/` (~80 entries, including many one-off `run_gwNN_agent_fork*.py` runners) have sprawled; the replay/evaluation apparatus dwarfs the decision core and there is no legible snapshot-to-recommendation path.
- Evaluation-first has crowded out live-first — the repo is on the wrong side of its own §17.6 warning about over-investing in replay at the expense of day-one live capture.

### Data captured but unused (Tier 1, already licensed)

| Field / source | Current state |
|---|---|
| `transfers_in_event` / `transfers_out_event` | Captured; no consumer in `src/` — raw input for price-change modelling |
| `selected_by_percent` | Captured; episode metadata only — unused for EO/template/captaincy risk |
| ICT index (influence/creativity/threat) | Summed into historical lag aggregates; absent from all projection formulas |
| Official FDR / team strength ratings | Only used in initial-squad prior; never benchmarked as WP-05 requires |
| Set-piece roles | Full ledger built (`src/ingestion/set_piece_roles.py`) but `effect_weights: None`, shadow-only |
| `event/{gw}/live` | Captured post-match only (Phase 6 by design) |
| `element-summary` past-season histories | Captured; priors lean on the vaastav warehouse instead |

Source state as at 3 August 2026:

- `official-lineups-minutes` is registered and enabled for **manual citation capture only**; the owner selected this path on 31 July (`docs/data-sources/2026-27-lineups-citation-decision.md`);
- named predicted-line-up services such as Fantasy Football Scout and Rotowire are plan candidates but are not registered sources and therefore cannot be collected;
- paid or third-party confirmed-line-up challengers remain disabled;
- Understat/FBref (xG/xA and defensive actions) and ClubElo (promoted-team priors) remain disabled pending a source decision.

## The plan

The work is sequenced by activation gate, not just technical desirability.
Only tickets 01–03 are in the current Phase 0/1 implementation queue.

- **Current Phase 0/1 — close the live advisory loop:** tickets 01–03.
- **Phase 2 activation — operational hardening, distributions and reporting:** tickets 04–06, 09, 11, 14, 17 and 19.
- **Model feature ablations (activate only with cutoff-safe evaluation data):** tickets 15–16.
- **Owner/ADR gates:** tickets 08, 10 and 13.
- **Implementations blocked by owner gates:** tickets 18–19.
- **Phase 5 activation — price and competitive intelligence:** tickets 07 and 20.
- **Structural proposal:** ticket 12; an ADR must be accepted before package moves.

Tickets live in `issues/` per the local tracker conventions (`docs/agents/issue-tracker.md`). `Blocked by:` lines encode sequencing; owner-gated tickets carry `Status: ready-for-human`.

`needs-triage` means the capability belongs in the full operationalisation
roadmap but is **not authorised for implementation in the current phase**.
`needs-info` means an owner decision, source approval or evidence threshold must
be resolved and the ticket updated before an agent may claim it.

## Hard boundaries (unchanged)

Same as `AGENTS.md` and `docs/handover-brief.md`: rules-as-data; no collection without registration; point-in-time discipline; LLMs propose only — never enforce, approve or execute; no secrets in Git or model context; no deferred execution implementation (browser automation, autonomous chips) — those remain Phases 7–8.

## Owner-only items carried forward (do not invent)

- Ratify the remaining Proposed ADRs in 0011–0016; ADR-0012 is now amended by
  ADR-0020 and must not be described simply as Proposed.
- Recruit the ~5-manager cohort (ADR-0009).
- Decide whether to authorise an API-backed model provider arm for scheduled agent runs (ticket 10).
- Decide whether any named predicted-line-up or third-party event/strength
  provider should be registered and evaluated (ticket 13); the official manual
  citation path is already enabled.
