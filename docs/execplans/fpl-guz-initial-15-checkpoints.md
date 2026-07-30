# FPL-guz: prospective initial-15 optimiser at immutable preseason checkpoints

This is the living ExecPlan for `FPL-guz`. It follows the repository planning
convention: its progress, decisions, validation and recovery instructions are
kept in the same document as the implementation context.

## Purpose

Run the existing deterministic and robust initial-squad optimiser repeatedly
against a *specific immutable 2026/27 preseason checkpoint*. Each output must
prove which official bytes, rules, policy and forecast packet it used, so a
changed squad can be explained as a changed admitted input rather than a
mutable "latest" view. It is advisory only: no module or script in this plan
has an authenticated FPL, browser, or account-write path.

The first live exercise is intentionally an operational baseline. The current
official bootstrap exposes FPL's published `ep_next`, but the separately
validated six-Gameweek `live-faithful` forecast packet is not yet materialised
from the immutable preseason capture. The runner may repeat `ep_next` across
the preregistered six-week horizon **only** as
`official_ep_next_flat_horizon_baseline-v1`; it is visibly degraded, never
approval-ready, and is not a replacement for the richer forecast work.

## Repository context

- `src/orchestration/preseason_snapshot.py` owns immutable point-in-time
  official capture manifests and verifies their source-family hashes.
- `src/optimisation/initial_squad.py` owns legal squad search, XI, captain,
  vice-captain and bench validation. It fetches no data.
- `src/orchestration/live_seed_selection.py` runs equal-input deterministic
  and robust arms and applies the owner/rules approval gate.
- `control/policies/initial-squad-2026-27.json` fixes the six-GW objective and
  bounded beam configuration. `control/rules/2026-27.yaml` fixes legality.
- `reports/live/2026-27/initial-squad/` is a local immutable output root; raw
  captures and operational reports are intentionally ignored by Git.

## Interfaces and output contract

The runner is invoked from the repository root:

```powershell
python scripts/run_initial_squad_checkpoint.py `
  --manifest data/snapshots/2026-27/preseason/<checkpoint-id>/manifest.json `
  --output-root reports/live/2026-27/initial-squad
```

It rejects a malformed or non-self-hashed manifest, changed/missing bound
official bytes, an observation after the checkpoint deadline, an unknown
ruleset, an illegal output, or a different request attempting to reuse the
same checkpoint output directory.

For an accepted checkpoint it writes only create-or-identical artifacts:

- `input-packet.json`: the whole candidate universe, exclusions, declared
  forecast strategy, source-family states/hashes, and all fallbacks;
- `recommendation.json`: deterministic/robust arm results, selected 15, legal
  XI, captain, vice-captain, bench, bank, horizons, risks and alternatives;
- `diff.json` and `diff.md`: machine- and human-readable comparison with the
  latest earlier output; and
- `checkpoint.json`: a sealed index binding every artifact, configuration,
  predecessor recommendation and report hashes.

Missing optional source families remain named `unavailable` with their
manifest reason. They are not reported as observed zero-valued signals. The
schema-level no-adjustment fallback is separately labelled and makes the
approval gate block the result.

## Progress

- [x] 2026-07-30: Claimed `FPL-guz`, audited the existing capture,
  initial-squad and live-seed contracts, and captured
  `weekly-2026-07-30` from the public official endpoints.
- [x] 2026-07-30: Confirmed the capture is hash-bound and degraded only for
  optional families; the mandatory official bootstrap and fixtures are
  present.
- [ ] Implement manifest verification, candidate packet construction,
  checkpoint sealing and predecessor diffing.
- [ ] Add synthetic integration coverage for valid/degraded runs, all refusal
  paths, identical reruns and two-checkpoint diffs.
- [ ] Run the real current checkpoint, inspect its blocked advisory result,
  and record its operational gaps without changing the forecast policy.

## Design decisions

- The checkpoint runner consumes a manifest path, never a mutable current
  directory or an endpoint. It rereads every bound mandatory artifact and
  recomputes each digest before use.
- FPL `ep_next` is a labelled official one-week baseline, not an inferred
  six-week model. Repeating it for the fixed horizon is a transparent testing
  adapter that permits the full operational path to be exercised now. It must
  not be selected for manual entry.
- Availability is read only from the official FPL state at this stage.
  Non-available players are excluded; missing club/news/odds/ratings/set-piece
  families remain coverage gaps.
- The runner uses the existing `run_live_seed_selection` gate. A missing
  active rules activation, missing owner approval, or baseline-only forecast
  leaves the result blocked even when a legal exploratory squad is produced.
- Predecessors are selected by earlier `observed_at`, never by a hard-coded
  checkpoint label order. A first checkpoint records an explicit
  `no_predecessor` diff.

## Validation and recovery

Run focused coverage:

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m pytest -q `
  tests/integration/test_initial_squad_checkpoint.py `
  tests/optimisation tests/test_optimiser.py
```

Then exercise the same fixture twice and confirm all files compare byte for
byte. Exercise a later fixture checkpoint and confirm its `diff.json` names
the prior recommendation hash. Finally run the real public checkpoint and
inspect `checkpoint.json`; the expected current state is an advisory,
baseline-only, approval-blocked output with named missing families.

If a run fails, retain existing immutable artifacts. Fix the input or code and
retry at a new checkpoint only when the source capture itself changed. Never
rewrite a sealed checkpoint to make it pass, and never backfill an earlier
checkpoint from later observations.

## Completion criteria

The Bead closes only after the synthetic refusal/determinism/legality suite is
green, a real current checkpoint has produced a sealed advisory artifact, and
the report makes all current forecast/evidence gaps inspectable. Promotion of
the baseline or a proposal to manual entry remains an owner decision outside
this Bead.
