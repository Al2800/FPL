# Reconstruct Early-Season Evidence Without Rewriting History

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

This work extends the 2025/26 evidence experiment from its current GW12 start
back to the beginning of the season. A reviewer will be able to see exactly
which historical documents were recovered for each deadline, which were
excluded, where the reconstruction abstained, and why no retrospective item is
eligible to support a production claim. The accepted exploratory records can
then drive two auditable experiments: weekly GW2-GW11 evidence forks and a
separate GW1 initial-squad counterfactual.

The user-visible result is a sealed early-season evidence manifest, one
machine-readable record per Gameweek, a coverage report, and later replay
reports that keep the existing canonical season byte-identical.

## Progress

- [x] (2026-07-27 10:05Z) Froze the first live 2026/27 official launch
  checkpoint so current evidence is not lost while historical work proceeds.
- [x] (2026-07-27 10:06Z) Claimed `FPL-bsw.38.1` and audited the benchmark
  index, GW12 bundle, evidence lifecycle, availability ledger, weekly evidence
  programme, source registry and canonical GW1-GW11 decisions.
- [x] (2026-07-27 10:18Z) Implemented and tested the early-season manifest
  contract, immutable builder, benchmark binding and quality gates.
- [x] (2026-07-27 10:35Z) Recovered and classified 12 decision-relevant
  candidates across GW1-GW11 and sealed the complete inventory.
- [x] (2026-07-27 12:20Z) Ran the sealed GW2-GW11 isolated and longitudinal
  evidence replay with a frozen no-evidence shadow, independent Sol review,
  GW12 bridge and byte-identical canonical artifact proof.
- [x] (2026-07-27 14:35Z) Constructed and ran the separate historical GW1
  structured-prior seed branch through GW11, preserving the Scout control and
  proving byte-identical rerun behavior.
- [ ] Review forecasting, optimisation, state and evidence gaps before changing
  the prospective live initial-squad engine.

## Surprises & Discoveries

- Observation: GW1-GW11 already have sealed structured episodes and canonical
  replay artifacts, but no unstructured evidence bundles.
  Evidence: `evals/episodes/structured/benchmark-v0-index-v2.json` contains all
  eleven episode identities and deadlines, while
  `evals/evidence-forks/2025-26` begins at GW12.
- Observation: the existing evidence-bundle validator maps retrospective
  `captured_at` to both `observed_at` and `available_at`. That correctly makes
  the source production-ineligible, but it does not provide a season-wide
  inventory, exclusion or abstention record.
  Evidence: `src/orchestration/evidence_fork.py` and the committed GW12 bundle.
- Observation: GW1 is a controlled official Scout seed and the generic weekly
  evidence programme deliberately refuses GW1.
  Evidence: `control/seeds/2025-26/official-scout-gw1.json` and
  `run_weekly_evidence_programme`, which supports only GW2-GW38.
- Observation: the weakest calibrated period is the cold start, so absence of
  evidence is itself an important result rather than a reason to manufacture a
  bundle.
  Evidence: the existing preregistration reports the largest appearance error
  in GW1-GW6.
- Observation: the final GW1 export is not a complete pre-deadline eligibility
  snapshot even when only launch-like fields are admitted.
  Evidence: it retained Luis Diaz as a Liverpool candidate after his 30 July
  transfer to Bayern. The branch now excludes him using the dated club
  announcement and records the remaining eligibility uncertainty.
- Observation: changing only the initial seed created a material state-policy
  interaction after a weak start.
  Evidence: the branch scored 48 versus 56 in GW1 and trailed by 20 after GW2,
  but reached GW11 at 591 versus 553 after different transfers and retained
  players. The later +46 is not a pure seed effect.

## Decision Log

- Decision: preserve the canonical Scout-seeded replay and create additive
  branches only.
  Rationale: changing GW1 changes every later manager state and would erase the
  existing control.
  Date/Author: 2026-07-27 / Codex.
- Decision: distinguish `published_at` from retrospective `observed_at` and
  `available_at` in the manifest.
  Rationale: a page published before a deadline may support an exploratory
  reconstruction, but a page first recovered in July 2026 was not actually
  available to the historical agent.
  Date/Author: 2026-07-27 / Codex.
- Decision: permit explicit weekly abstention and report its rate.
  Rationale: forcing one evidence item per week would reward searchability and
  hindsight rather than realistic point-in-time evidence.
  Date/Author: 2026-07-27 / Codex.
- Decision: target research at declared deterministic decision boundaries,
  while recording retrospective case-selection bias.
  Rationale: evidence that cannot affect a transfer, lineup, captain or seed
  choice adds prompt volume without causal value.
- Decision: call the alternative seed a retrospective structured-prior
  reconstruction, not an admissible historical agent decision.
  Rationale: completed 2024/25 data are temporally valid priors and only
  launch price, position, team, name and element fields are whitelisted from
  GW1, but the bytes were not captured immutably before the deadline.
  Date/Author: 2026-07-27 / Codex.
- Decision: decompose GW1 realised seed delta from GW2 onward carried-state
  policy interaction.
  Rationale: attributing the complete trajectory to seed selection would hide
  endogenous transfers, captaincy, bank and free-transfer differences.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

The initial live checkpoint is complete and local. The first historical
milestone is also complete: all eleven early Gameweeks bind to their sealed
episodes, 12 candidates are admitted for exploratory use, no week silently
lacks a research result, and every item remains production-ineligible because
it was observed retrospectively. Eleven sources have date-level or inferred
publication precision and one has an exact timestamp; that asymmetry is
preserved as a limitation rather than normalised away. Replay and seed
counterfactual milestones remain.

The second historical milestone is complete. Five weeks produced bounded
availability proposals, five correctly abstained, and independent challengers
blocked three ambiguous Palmer adjustments through confidence downgrades. Only
GW7 and GW9 reached deterministic application. GW7's Gabriel fitness discount
changed the transfer route and lost eight realised points from the same state;
GW9 changed projections without changing points. Later carried-state decisions
recovered one point, so the evidence trajectory reached GW12 seven points
behind the frozen no-evidence control, with a different squad and 0.7 less
bank. This is exploratory regret, not evidence that the pre-deadline doubt was
false. It exposes a need for transfer hysteresis, explicit uncertainty
distributions and separate minutes/start/conditional-points calibration.

A second identical full replay succeeded. The canonical 3,063-file tree hash
remained `d1407dc2602d927dab23fed609b5467bbf114f59a24d4d17e42dc396e2602932`.

The third historical milestone is complete. A deterministic six-Gameweek
structured prior selected a legal £100.0m squad from completed 2024/25
performance, availability shrinkage, reconstructed launch fields and GW1-GW6
fixture difficulty. It selected Salah captain, scored 48 in GW1 versus the
official Scout control's 56, and fell 20 behind after GW2. The same locked
weekly engine then made a different sequence of transfers and the branch
reached GW11 at 591 versus 553. The report therefore records `-8` as the
realised GW1 seed delta and `+46` as the later seed-by-policy/state interaction,
for `+38` overall. This is a useful mechanism result, not a skill claim.

The branch reran byte-identically, 29 affected historical/evidence tests pass,
and the canonical 3,063-file hash remains
`d1407dc2602d927dab23fed609b5467bbf114f59a24d4d17e42dc396e2602932`.

## Context and Orientation

`evals/episodes/structured/benchmark-v0-index-v2.json` is the committed index
of 38 sealed historical episodes. An episode is all structured information
allowed at one deadline plus hashes of the hidden outcome. The canonical
manager trajectories live under `reports/benchmarks/2025-26/gw-NN`.

An evidence item is a short, attributed historical claim relevant to a player
or team. `published_at` is when the source says it was published. `observed_at`
is when this project actually recovered it. `available_at` is when the bytes
were available to this project. For this reconstruction, observed and
available times occur after the historical deadline; therefore every item is
exploratory and production-ineligible even when its publication time precedes
the deadline.

`src/orchestration/evidence_fork.py` validates and applies the existing
single-week bundles. `src/orchestration/weekly_evidence_programme.py` performs
isolated and longitudinal GW2-GW38 replay. The new manifest sits before those
modules. It records the research universe and admits only a subset into a
bundle, preventing a missing or rejected page from disappearing from the
audit.

## Plan of Work

First, add `src/evaluation/early_season_evidence_manifest.py`. It will validate
the benchmark binding, temporal fields, excerpt hashes, stable identities,
duplicate detection, inclusion/exclusion reasons, GW1 decision type and
production-ineligible classification. It will calculate coverage and
abstention metrics and seal the result with the repository's standard artifact
hash.

Add `scripts/build_early_season_evidence_manifest.py` to combine the benchmark
index with operator-authored research records under
`evals/evidence-forks/2025-26/gw-NN/research-record.json`. The script writes one
sealed `manifest-entry.json` per week plus
`evals/evidence-forks/2025-26/early-season-manifest.json`. Writes are immutable:
an identical rerun succeeds and a conflicting rerun refuses replacement.

Recover historical sources manually through normal research. Each candidate
must name the boundary it could affect and retain the exact publication
precision, retrieval time, URL, excerpt hash, player bindings, rights status
and exclusion reasons. A week without defensible evidence is sealed as an
abstention. No automated HTML collector is enabled because the relevant source
registry entries remain disabled for bulk collection.

Once the manifest is frozen, transform only admitted GW2-GW11 claims into the
existing evidence-bundle contract. Run the generic weekly programme first in
same-state isolation and then as an independent longitudinal branch. Compare
its GW12 opening state to the canonical GW12 state rather than splicing it into
the accepted GW12-GW38 trajectory.

Finally, build GW1 as a separate initial-squad experiment. It may reuse the
same research inventory, but it must use a dedicated seed optimiser and create
its own downstream state. Report seed effect separately from later evidence
and policy effects.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the manifest contract tests:

    .venv/Scripts/python.exe -m pytest tests/evaluation/test_early_season_evidence_manifest.py -q

Build and verify the manifest:

    .venv/Scripts/python.exe -m scripts.build_early_season_evidence_manifest

Run the complete test suite after each bead:

    .venv/Scripts/python.exe -m pytest -q

The manifest command must report eleven bound weeks, admitted, excluded and
abstained counts, zero production-eligible weeks, and an unchanged content
hash on an identical rerun.

## Validation and Acceptance

The validator must reject a deadline or episode-hash mismatch, a publication
after the decision cutoff, an excerpt-hash mismatch, duplicate evidence,
missing exclusion reasons, a supposedly production-eligible retrospective
item, and a GW1 record labelled as ordinary weekly management. It must accept
an explicit abstention.

The committed manifest must cover GW1-GW11 exactly once and bind every record
to `benchmark-v0-index-v2.json`. Every admitted item must be publication-safe
for its exploratory deadline and remain labelled retrospective. Coverage,
exclusion and abstention rates must be visible without reading prose.

Later replay acceptance requires byte-identical canonical hashes before and
after execution, isolated attribution for each evidence week, an independently
carried manager state, and a GW12 bridge-state comparison. The GW1 seed branch
must never overwrite the official Scout seed.

## Idempotence and Recovery

All generated committed JSON uses write-once comparison. Research records are
operator-authored inputs; generated manifest entries never edit them. A failed
validation writes no generated output. Raw web pages are not bulk-downloaded or
committed. Existing canonical reports and sealed evidence runs are never
deleted or rewritten.

The live launch checkpoint under `data/live-shadow/fpl` is gitignored,
immutable and independent of this historical work.

## Artifacts and Notes

Initial live preservation proof:

    29 passed in 6.06s
    capture_id=e2499ad7ab46d7147bba829d21eb6a8418b3d5f05fe7ff09708fdb458d802460
    players=558 teams=20 fixtures=380
    decision_cutoff=2026-08-21T17:30:00Z

The official capture is structurally complete. Optional odds at T-24h, T-8h,
T-2h and final, unstructured documents, promoted-team context and transferred
player context are currently explicit gaps.

## Interfaces and Dependencies

`src/evaluation/early_season_evidence_manifest.py` will expose:

    def build_manifest_entry(*, episode, research_record) -> dict[str, Any]: ...
    def build_early_season_manifest(*, index, research_records) -> dict[str, Any]: ...
    def validate_early_season_manifest(manifest, *, index) -> None: ...
    def write_immutable_json(path, value) -> None: ...

The implementation uses the standard library and
`src.forecasting.live_faithful.artifact_hash`. It adds no dependency and no
network collector.

Revision note (2026-07-27): created after the live checkpoint and historical
architecture audit. It separates retrospective publication evidence from
point-in-time availability and treats abstention as a first-class result.

Revision note (2026-07-27): updated after completing `FPL-bsw.38.1` to record
the sealed 11-week inventory, quality profile and 27-test focused regression
result.

Revision note (2026-07-27): updated after completing `FPL-bsw.38.2` with the
paired evidence/no-evidence result, protocol-wrapper correction, idempotence
proof and engine implications.

Revision note (2026-07-27): updated after completing `FPL-bsw.38.3` with the
field-whitelisted structured-prior seed, stale-eligibility discovery,
independent GW1-GW11 trajectory, seed-versus-policy decomposition, canonical
hash proof and reproducibility result.
