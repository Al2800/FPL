# Freeze Live Forecast Inputs Before They Reach the Shadow Arms

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

This change makes the future 2026/27 input pipeline production-shaped without
turning on an unreviewed data feed. An operator can capture official FPL launch
state, classify promoted-team and transferred-player cold starts, and record
the status of fixed-time market snapshots. Every admitted value carries the
time it was observed, the time it became available, and the hash of its source.
If an odds source is absent or unapproved, the run remains usable but explicitly
degraded.

The observable result is an immutable `forecast-input-capture.json` beside the
existing raw FPL capture. Tests show that launch state cannot be frozen after
the GW1 deadline, late odds cannot enter a decision, unapproved sources cannot
be activated, and missing optional odds do not block official capture.

## Progress

- [x] (2026-07-27 08:49+01:00) Claimed `FPL-dnr`, checked Beads for conflicting
  work, searched prior conversations, and inspected the live capture, episode
  builder, source registry, temporal policy and historical forecast interface.
- [x] (2026-07-27 08:56+01:00) Added contract tests for launch freezing,
  cold-start classes, timestamped odds, approval gates and degraded operation.
- [x] (2026-07-27 09:03+01:00) Implemented the immutable forecast-input capture
  contract and CLI controls.
- [x] (2026-07-27 09:08+01:00) Updated the source and timing policies plus
  operator documentation.
- [x] (2026-07-27 09:27+01:00) Passed 23 focused, 92 forecasting/integration,
  8 registry and 505 full-suite tests, with clean diff hygiene.
- [ ] Record the implementation in Beads, close the bead, commit and push.

## Surprises & Discoveries

- Observation: the repository already has immutable official endpoint capture
  and a cutoff-safe live episode builder.
  Evidence: `scripts/capture_fpl_live_shadow.py` records bootstrap and fixtures,
  while `src/orchestration/episode_builder.py` verifies every byte and source
  manifest.
- Observation: the current episode builder deliberately requires the two
  official endpoints to succeed; optional market data should therefore be a
  separate degraded input rather than weakening that existing hard gate.
  Evidence: `_verify_capture` rejects any endpoint failure before materialising
  the feature view.
- Observation: an off-season or incomplete bootstrap may be worth retaining
  even though it cannot yet produce the launch forecast contract.
  Evidence: the broader integration suite includes a deliberately minimal
  bootstrap with no deadline or complete player catalogue.
- Observation: disabled-source policy tests require every registry note to
  state an alternative or accepted gap explicitly.
  Evidence: the first full run had 504 passes and one failure for the initial
  live-odds candidate note; the corrected run passed all 505 tests.

## Decision Log

- Decision: preserve capture version 1.0 and add a separately self-hashed
  forecast-input artifact referenced by the summary.
  Rationale: existing episode artifacts and tests remain compatible while the
  future forecast layer gains richer lineage.
  Date/Author: 2026-07-27 / Codex.
- Decision: accept market snapshots only as pre-staged local evidence whose
  source is enabled and explicitly approved for both terms and cost.
  Rationale: this bead must not select, purchase or fetch a commercial feed.
  Date/Author: 2026-07-27 / Codex.
- Decision: keep official FPL capture mandatory and odds optional.
  Rationale: launch prices, positions, clubs and availability are canonical
  inputs; missing odds should degrade the forecast rather than erase usable
  official evidence.
  Date/Author: 2026-07-27 / Codex.
- Decision: ordinary incomplete off-season capture records the forecast-input
  layer as degraded, but any explicit launch-freeze or market request fails.
  Rationale: raw official evidence should not be lost, while an operator must
  never believe an explicitly requested freeze succeeded on incomplete state.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

The implementation now produces a self-hashed forecast-input artifact from a
complete official snapshot, preserves the old episode-builder contract, and
makes all four optional market slots visible. It does not claim that an odds
provider exists: the sole candidate is disabled pending named terms and cost
approval. This provides the structured base required by the paired live-shadow
bead without adding credentials or account execution.

## Context and Orientation

`scripts/capture_fpl_live_shadow.py` performs unauthenticated read-only capture
of the official bootstrap and fixtures endpoints. The raw bodies and manifests
are stored under `data/live-shadow/fpl`, which is ignored by Git.
`control/sources/source-registry.yaml` is the authority for whether a source may
be collected. `control/policies/source-availability.yaml` defines when fields
become admissible. `src/forecasting/live_faithful.py` consumes self-hashed
player and team priors during replay; the new artifact records enough launch
identity and cold-start classification to construct those same shapes later.

A capture slot is a named interval relative to an FPL deadline: T-24h, T-8h,
T-2h, or the final pre-deadline observation. A degraded feature is an optional
input that is absent or unusable but is recorded with a machine-readable reason.
It is not silently imputed.

## Plan of Work

Create `src/forecasting/live_capture.py` as a pure validation and artifact
builder. It will extract immutable launch players and teams from the official
bootstrap payload; validate an optional operator-supplied launch context;
classify promoted-team, transferred-player and ordinary cold starts; validate
pre-staged market snapshots against the registry, deadline and capture slot; and
seal the complete artifact with a content hash.

Extend `scripts/capture_fpl_live_shadow.py` with optional launch-context,
market-snapshot, decision-cutoff and launch-freeze arguments. The script will
not fetch those optional inputs. It will copy their bytes immutably into the
same run directory only after validation and will expose a reference in the
capture summary.

Extend the registry with a disabled live-market candidate whose terms, cost,
credentials and retention decisions remain explicitly pending. Extend the
availability policy with launch and market timestamp rules. Update the cadence
and capture documentation so an operator knows what to run and what remains
blocked.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the focused contract:

    .venv/Scripts/python.exe -m pytest tests/integration/test_live_episode_builder.py -q

Then run the complete suite:

    .venv/Scripts/python.exe -m pytest -q

No live network capture is required for verification. The tests use HTTPX mock
transport and local temporary files.

## Validation and Acceptance

The focused tests must demonstrate five behaviors. A pre-GW1 capture with
`freeze_launch=True` produces a self-hashed catalogue of launch prices,
positions, clubs and availability. Promoted and transferred entities receive
explicit cold-start classes. The same request at or after the GW1 deadline
fails closed. An odds snapshot is admitted only when its observed and available
times are strictly before the decision cutoff and it belongs to an approved,
enabled source. Missing odds produce a degraded record with all required slots
listed. The existing live episode builder continues to accept the extended
official capture summary unchanged.

## Idempotence and Recovery

All writes use immutable comparison: an identical rerun reuses bytes and a
conflicting rerun refuses replacement. The implementation does not delete
files, install dependencies, fetch market data, authenticate, or write to an
FPL account. If optional evidence is invalid, its rejection is recorded and
official capture remains available.

## Artifacts and Notes

The artifact will expose `official_launch`, `cold_start_priors`,
`market_evidence`, `degraded_features`, `feature_contract`, and
`content_sha256`. Final proof transcripts:

    23 passed in 5.46s
    92 passed in 11.76s
    8 passed in 0.15s
    505 passed in 379.29s (0:06:19)
    git diff --check: clean

## Interfaces and Dependencies

`src/forecasting/live_capture.py` will expose:

    def build_live_forecast_capture(
        *,
        bootstrap: Mapping[str, Any],
        bootstrap_manifest: Mapping[str, Any],
        observed_at: str,
        decision_cutoff: str,
        launch_context: Mapping[str, Any] | None,
        market_snapshots: Sequence[Mapping[str, Any]],
        source_registry: Mapping[str, Any],
        freeze_launch: bool,
    ) -> dict[str, Any]: ...

It uses only the standard library and existing PyYAML-backed registry loader.
No new dependency is required.

Revision note (2026-07-27): created after repository inspection to preserve the
existing official hard gate and place optional market data behind an explicit
degraded boundary.

Revision note (2026-07-27): updated after implementation to record the
off-season degraded-mode decision, policy-test discovery and complete
validation evidence.
