# FPL-bsw.38.14 broad live evidence and candidate-boundary retrieval

This ExecPlan is a living document. Keep `Progress`, `Discoveries`, `Decision
log`, and `Outcomes` current while implementation proceeds.

## Purpose

Operationalise a production-shaped live evidence funnel for 2026/27 without
weakening the deterministic engine or the frozen no-evidence shadow. The
system must accumulate more evidence than an agent can read directly, use the
shared engine to discover the players and decisions that matter, retrieve a
small reproducible cited packet, and measure omissions and decision impact.

## Existing foundation

`src/evidence/live_evidence_ledger.py` already provides registry-gated,
append-only claims; exact publication, observation, availability and expiry
timestamps; explicit supersession; conflict exclusion; quarantine; immutable
decision-time projections; and bounded packets.

`src/ingestion/live_evidence_collector.py` currently automates only the enabled
official FPL bootstrap source. `src/ingestion/acquisition.py` and
`control/sources/source-registry.yaml` enforce source rights and immutable raw
snapshots.

`src/orchestration/boundary_retrieval.py` ranks availability claims against
caller-supplied boundaries. `src/orchestration/live_evidence_arm.py` binds one
packet to the shared engine output and preserves the exact no-evidence
candidate on missing, invalid or rejected agent output.

The missing production layer is deterministic candidate discovery, entity
expansion, broad source/checkpoint coverage accounting, and retrieval/eval
metrics across raw acquisitions, active claims, retrieved claims and accepted
adjustments.

## Guardrails

- Do not enable or scrape a source whose registry rights and collection mode
  are unresolved.
- Disabled sources retain a manual linked-citation path and an explicit gap;
  they are never silently treated as covered.
- Missing evidence never means a player is fit.
- All inputs are point-in-time and outcome-blind. Known outcome fields fail
  closed.
- Structured screening chooses the attention set. Agents interpret bounded
  unstructured claims; they do not search the whole ledger.
- Every model arm receives the identical content-addressed packet.
- The frozen no-evidence candidate remains byte-stable and independently
  scored.
- Historical replay artifacts remain frozen; this work is prospective for
  live shadow operation.

## Progress

- [x] Claim `FPL-bsw.38.14` and verify file ownership does not overlap the
  active preseason-capture bead.
- [x] Audit the existing source registry, immutable acquisition layer, live
  evidence ledger, availability ledger, boundary ranker and frozen shadow.
- [x] Confirm no reusable prior-conversation implementation exists.
- [x] Define source/checkpoint coverage configuration and metrics.
- [x] Implement governed source orchestration with fail-closed degradation.
- [x] Implement deterministic owned-player and legal external-candidate
  discovery across position, price, club and planning horizon.
- [x] Implement entity-expanded, boundary-aware, freshness/authority-aware
  bounded retrieval with explicit omission records.
- [x] Implement coverage and golden retrieval evaluation.
- [x] Add the offline audit CLI and integration fixtures.
- [x] Run focused tests, performance guardrails and the full suite.

## Design

### 1. Coverage configuration

`config/data_sources/2026-27-evidence-coverage.json` defines source families,
their registry source IDs, collection modes, authority ranks, freshness
windows, checkpoint expectations, manual alternatives, packet limits and
candidate-search limits. It does not override the source registry.

### 2. Governed acquisition orchestration

`src/ingestion/evidence_source_orchestrator.py` converts configuration and the
source registry into an acquisition plan. Automated adapters execute only when
the registry and coverage policy both permit them. Manual-only and disabled
sources produce linked-citation requirements and coverage gaps. Adapter
failures are recorded as degraded observations while retaining the prior
ledger and frozen control.

### 3. Deterministic candidate-boundary retrieval

`src/evidence/candidate_boundary_retrieval.py` consumes the shared structured
engine input/output and current squad. It:

1. rejects post-deadline or outcome-bearing inputs;
2. scores the owned squad for availability risk and replacement opportunity;
3. constructs legal affordable external replacements by position, club limit,
   price and planning horizon;
4. emits reproducible transfer, lineup and captaincy boundaries plus expanded
   player, club and fixture entities;
5. joins active claims by explicit boundary or stable entity;
6. ranks by boundary-flip potential, decision margin, freshness, source
   authority, uncertainty and stable identifiers;
7. enforces claim and character caps and records every omission reason;
8. exposes only selected evidence and relevant conflicts to agents while
   retaining complete omission metadata for host audit; and
9. seals one packet bound to the engine output and evidence-view hashes.

### 4. Coverage and evaluation

`src/evaluation/evidence_coverage.py` separately reports:

- raw source attempts and successes;
- immutable documents and deduplicated claims;
- active, expired, superseded, conflicted and quarantined claims;
- expected club/player/source coverage and freshness;
- retrieved claims and budget omissions;
- accepted adjustments and plan changes; and
- golden-case recall, precision, latency and downstream decision impact.

Silence is represented as unknown/unobserved coverage, never as player
availability.

## Test strategy

Write tests before implementation:

- legal external replacement discovery and club/price/position rejection;
- current owned underperformer and availability-risk discovery;
- deterministic ordering and hash stability;
- look-ahead/outcome-field refusal;
- entity expansion and boundary-flip ranking;
- count/character budgets with explicit omissions;
- identical packets for agent arms;
- source registry and rights fail-closed behavior;
- manual citation fallback for disabled sources;
- source, club, player, freshness, conflict, deduplication and gap metrics;
- golden recall/precision and a bounded latency guardrail; and
- integration with the existing ledger and frozen no-evidence arm.

## Validation commands

    .venv\Scripts\python.exe -m pytest tests/evidence/test_candidate_boundary_retrieval.py -q
    .venv\Scripts\python.exe -m pytest tests/evaluation/test_evidence_coverage.py -q
    .venv\Scripts\python.exe -m pytest tests/integration/test_broad_live_evidence_funnel.py -q
    .venv\Scripts\python.exe -m pytest

## Discoveries

- Two existing boundary packet implementations cover different claim models:
  the availability-specific ranker and the general live evidence packet. The
  new module must compose with the general ledger and retain the older module
  for compatibility.
- Current claims often contain a synthetic availability boundary ID, but broad
  retrieval needs stable entity joins so claims can be discovered for newly
  generated transfer, lineup and captaincy boundaries.
- Official FPL endpoints are the only automated live evidence source currently
  enabled. Club communications and official lineup/minutes evidence are
  manual-citation only; analyst sources remain blocked until exact registry
  approval.
- The completed enhanced replay measured only +11 direct same-state evidence
  points on the optimized path despite a +53 longitudinal difference. Retrieval
  coverage and boundary targeting therefore matter more than raw context size.

- Focused TDD now covers 15 cases; the broader existing evidence, source and
  live-shadow regression set covers 49 cases after context-contract hardening.
- On the small deterministic fixture, discovery plus retrieval measured p50
  0.802 ms, p95 1.459 ms and p99 1.827 ms, 236.75 iterations/second and
  61,986 bytes peak traced memory over 1,000 profiled iterations.
- With 2,000 active claims, retrieval selected ten claims (270 claim-text
  characters), recorded 1,990 irrelevant omissions, and measured p50 180.564
  ms, p95 198.944 ms, p99 215.847 ms, 5.67 packets/second and 1,434,472 bytes
  peak traced memory. This remains inside the 250 ms local guardrail but leaves
  limited p99 headroom as the ledger grows.
- Source observations without an exact timestamp now degrade; a nominal
  successful adapter response cannot be counted as fresh by default.
- Agent-visible packet context is explicitly separated from complete host-audit
  omission and exclusion metadata.

## Decision log

- 2026-07-28: Extend the existing ledger rather than replace it.
- 2026-07-28: Keep candidate discovery deterministic and outcome-blind.
- 2026-07-28: Use explicit stable-entity expansion in addition to boundary IDs.
- 2026-07-28: Treat source silence as a coverage gap, never as fitness.
- 2026-07-28: Keep broad retrospective evidence experiments separate from the
  prospective 2026/27 live policy.

## Outcomes

The production-shaped evidence funnel is implemented without changing the
structured optimizer or historical replay artifacts. Registered-source rights
are checked before adapter execution, absent or stale observations degrade
visibly, and disabled families retain explicit manual-citation requirements.

Deterministic discovery now derives the attention set from the optimizer's own
evaluated legal candidates, expands stable player/club/fixture identities, and
binds the result to the solver input/output hashes. Retrieval joins the active
ledger to those boundaries, ranks reproducibly, caps selected claim count and
characters, exposes only relevant conflicts to agents, and retains every
omission identifier as host-only audit metadata.

Validation completed on 2026-07-28:

- 15 focused acquisition/retrieval/coverage tests passed;
- 49 broader evidence, source-acquisition and live-shadow tests passed;
- all 650 repository tests passed in 404.94 seconds with empty stderr;
- `git diff --check` and Python bytecode compilation passed; and
- the 2,000-active-claim scale fixture remained inside the configured 250 ms
  local packet-construction guardrail (p95 198.944 ms, p99 215.847 ms).

This is ready for prospective live shadow use, not automatic production
reliance. The next empirical work is to increase governed evidence capture,
run golden retrieval/coverage audits at real checkpoints, and measure accepted
adjustments against the continuously frozen no-evidence counterfactual.
