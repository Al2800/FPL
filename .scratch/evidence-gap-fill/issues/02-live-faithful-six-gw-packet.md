# 02 — Materialise six-GW live-faithful packet for checkpoints

**Blocked by:** 01 (resolved)

**Status:** ready-for-agent

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Replace the flat official `ep_next` repeated across six Gameweeks in
the initial-squad checkpoint with a hash-bound `live-faithful` horizon built
from the sealed preseason manifest, so approval can be gated on a real forecast
contract rather than an operational rehearsal baseline.

### Current behaviour

`build_initial_squad_packet` still uses
`official-ep-next-flat-horizon-baseline-v1`: one official `ep_next` value
repeated for GW1–GW6. Launch-context enrichment (ticket 01) can set
`promoted_team` / `new_signing` / `world_cup_fatigue`, but expected points are
not multi-GW. `forecast_quality.status` is `operational_baseline_only` and
`manual_entry_eligible` is false. Live readiness rehearsal deliberately keeps
approval blocked on that basis.

Existing building blocks (not yet wired into this checkpoint path):

- `src/forecasting/live_faithful.py` — `build_live_faithful_forecast` for one
  episode/view (content-addressed).
- `src/forecasting/live_capture.py` — immutable launch + market evidence contract.
- `src/forecasting/launch_context.py` — cold-start + WC priors (now consumed).
- Locked/calibrated model configs under `control/models/live-faithful-v1.*.json`
  and v2 challengers.
- Policy: `docs/evaluation/live-faithful-forecast-policy.md`.

### Desired behaviour

From one verified preseason manifest:

1. Build cutoff-safe feature / prior inputs (official bootstrap + fixtures +
   admitted launch context; odds/set-pieces/ratings degrade visibly if absent).
2. Materialise a six-GW player surface: per Gameweek expected points, start
   probability and uncertainty for every eligible player.
3. Adapt that surface into the existing initial-squad packet schema
   (`expected_points` / `start_probability` / `uncertainty` length = policy
   horizon).
4. Set `forecast_model_version` to the bound live-faithful model id and
   `forecast_quality` to a non-baseline status that still sets
   `manual_entry_eligible: false` until owner acceptance of remaining
   degradations (odds, ratings, availability citations, etc.).
5. Keep the flat `ep_next` path available as an explicit ablation / fallback
   only when live-faithful inputs cannot be built — never silently.

### Approach (agreed shape)

| Step | What | Notes |
| --- | --- | --- |
| A | Adapter, not rewrite | Keep `validate_initial_squad_packet` / optimiser / approval gate; only change how the horizon vectors are produced |
| B | Prefer existing live-faithful + live_capture | Do not invent a third forecast stack |
| C | Preseason / GW1 cold-start first | Early season uses priors + launch context + fixture adjustments; missing odds degrade |
| D | Explicit degradation | Absent optional families → limitations list; no fabricated neutral odds/ratings |
| E | Approval stays blocked | Ticket 06 policy ratified; proposal approval still needs owner sign-off on a decision-grade packet |
| F | Tests without network | Synthetic manifest + priors; hash stability; baseline fallback when inputs missing |

Open design points to resolve inside this ticket (record in Answer):

1. Which model config is the first live bind — e.g.
   `live-faithful-v1.feature-complete` / reliability-calibrated / structured —
   and how its status maps to `forecast_quality`.
2. How multi-GW fixture adjustments are projected from the sealed fixtures
   list (GW1–GW6) without walking through unplayed results.
3. Whether `ep_next` remains a diagnostic comparator field on the universe
   rows after the switch.

### Key interfaces

- `build_initial_squad_packet` / `run_initial_squad_checkpoint`
- `build_live_forecast_capture` / `build_live_faithful_forecast`
- `control/models/live-faithful-*.json`
- `control/policies/initial-squad-2026-27.json` horizon + discounts
- Packet `forecast_quality` + approval blockers
- Related gap tickets (do **not** block this ticket’s first slice):
  - 03 set-pieces (optional enrich)
  - 04 odds slots (optional enrich; env key not in this cloud agent)
  - 05 availability / W4
  - 06 ratings gap discipline

### Acceptance criteria

- [ ] Checkpoint packet horizon vectors come from a hash-bound live-faithful
      build when required inputs are present; not from repeating `ep_next`.
- [ ] `forecast_quality` no longer claims only the flat baseline when
      live-faithful succeeds; `manual_entry_eligible` remains false until
      remaining degradations are owner-accepted.
- [ ] Missing optional families degrade with named limitations; no invented
      odds/ratings.
- [ ] Launch-context cold-start / WC fields from ticket 01 still apply.
- [ ] Focused tests: happy path materialisation, hash seal, missing-prior
      fallback/degrade, existing checkpoint/readiness suites stay green.
- [ ] Canonical 2025/26 replay artifacts unchanged.
- [ ] No network; no account writes.

### Out of scope

- Owner approval of a specific starting 15.
- Enabling Sportradar or club HTML scrape.
- Completing odds ablation (W15) or set-piece EP weights (W17).
- Rival / EO strategy.
- Expanding ticket 07 Benchmark Kernel residual (separate frontier).
