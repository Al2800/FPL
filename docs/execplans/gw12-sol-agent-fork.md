# Bridge the Sol evidence arms into an isolated GW12 fork

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

The repository already has two separate capabilities: a constrained subscription-hosted evidence/challenger arm, and a manually specified retrospective GW12 evidence fork. This change joins them safely. A user will be able to construct an observed-only GW12 host bundle, run the evidence and challenger roles, and pass only independently reviewed proposals through a deterministic adapter into one isolated replay. The canonical replay and its hidden outcome remain unavailable to the agents and unchanged on disk.

The result is deliberately one week only. It compares the canonical control, the earlier hand-authored evidence fork, and the new agent-proposed fork. It does not continue the altered state into GW13 until the user has inspected the first result.

## Progress

- [x] (2026-07-26 12:35+01:00) Create and claim Bead `FPL-6z6`; confirm no competing in-progress Bead or file overlap.
- [x] (2026-07-26 13:05+01:00) Trace the GW12 episode manifest, frozen solver input/output, reconstructed source bundle, agent validators, challenger gate, and isolated fork.
- [x] (2026-07-26 13:35+01:00) Add contracts for an observed-only immutable bundle, retrospective-but-honest temporal handling, independent proposal bindings, deterministic application, exact fallback, canonical immutability, and byte-identical reruns.
- [x] (2026-07-26 13:42+01:00) Implement the adapter and one-week runner.
- [x] (2026-07-26 13:49+01:00) Run the evidence and challenger roles through the approved GPT-5.6 Sol subagent surface using only the rendered observed bundle.
- [x] (2026-07-26 13:55+01:00) Materialise and inspect the isolated comparison, reproduce byte-identically, and pass 31 focused tests plus all 452 repository tests.

## Surprises & Discoveries

- Observation: the recovered sources were published before the GW12 deadline but first captured by this repository in July 2026.
  Evidence: `evidence-bundle.json` records 2025 publication times and `2026-07-25T10:50:00Z` capture times. Production validation correctly rejects those observation/availability times.

- Observation: the current hosted evidence validator cannot admit the retrospective experiment without either lying about capture time or adding an explicit mode.
  Evidence: `validate_evidence_result` calls `assess_claim_for_decision` and `propose_adjustment` with the historical cutoff. Both reject the truthful 2026 observation time.

- Observation: the manual experiment's targets do not match the agent contract.
  Evidence: the manual bundle uses `availability_flag` and `start_probability_delta`; the agent schema permits only absolute `expected_minutes` and `start_probability`.

- Observation: the canonical GW12 baselines materially overstate the two subsequently reconstructed availability cases.
  Evidence: Gabriel has 85.6 expected minutes and 0.9524 start probability; Semenyo has 87.7 and 0.9821.

- Observation: the independent Sol roles converged on the same governed transforms as the prior manual experiment.
  Evidence: the evidence role proposed Gabriel expected minutes `85.6 -> 0` and Semenyo start probability `0.9821 -> 0.7321`; the challenger reviewed both exact IDs and dismissed the challenge.

- Observation: equal transforms reproduced the manual decision and score despite passing through a different proposal/review path.
  Evidence: both forks selected Gabriel to Daniel Muñoz, captained Salah, took no hit, and scored 43 versus the canonical 29.

- Observation: the collaboration subagent surface does not expose trustworthy token, cost, or wall-clock metering.
  Evidence: the raw hosted response records `measurement_status: unavailable_from_collaboration_surface` and zeroes the unavailable numeric fields; subscription cost remains null. These values must not be interpreted as measured zero consumption.

## Decision Log

- Decision: preserve truthful 2026 capture/availability timestamps and add a narrow retrospective validation mode.
  Rationale: backdating would hide the central limitation. The mode may admit only claims published by the deadline whose production rejection is solely caused by retrospective capture; it remains exploratory and never becomes production eligible.
  Date/Author: 2026-07-26 / Codex.

- Decision: make the deterministic adapter the sole application authority.
  Rationale: both model roles are proposal/review only. The adapter applies only adjustment IDs listed as unopposed by a completed challenger; any degradation, downgrade, rerun, escalation, mismatch, or unsupported transform returns the exact canonical input.
  Date/Author: 2026-07-26 / Codex.

- Decision: support one absolute adjustment per player in version 1 and permit reductions only.
  Rationale: this experiment concerns negative availability evidence. One adjustment avoids ambiguous compounding, and reductions cannot opportunistically inflate the forecast.
  Date/Author: 2026-07-26 / Codex.

- Decision: scale expected minutes, start probability, and expected points together by the accepted absolute-value ratio.
  Rationale: the optimiser consumes a coherent player row. Changing only one availability field would leave contradictory planning inputs.
  Date/Author: 2026-07-26 / Codex.

- Decision: do not run a longitudinal branch.
  Rationale: the user asked to pause after the first interesting fork result and inspect how the agent evidence changed the decision.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The one-week bridge is complete. The evidence role proposed two grounded reductions: Gabriel expected minutes `85.6 -> 0` at 0.99 confidence and Semenyo start probability `0.9821 -> 0.7321` at 0.74 confidence. The independent challenger reviewed both exact IDs and returned `dismissed`, which exposed them to—not applied them around—the deterministic adapter.

The adapter coherently scaled each affected forecast row, the optimiser selected Gabriel to Daniel Muñoz, Salah captain, and no hit. The frozen plan scored 43 versus 29 for the canonical control, a +14 delta, and exactly matched the earlier manual fork. The canonical GW12 tree hash remained `64d06384c005c69c4e37a0b85682f0bb0234eeebe861b021aa0fe241fe1279fe` before and after. A second complete run produced the same comparison file SHA-256 `4154677bb52ed4a0eb6ac4e84aff79706518e90ac8dc141831b8b62e71dd0707`.

This is successful process evidence, not an unbiased performance estimate. The sources were recovered later, the case was selected after the season, and the subscription collaboration surface does not provide measured token/cost telemetry. The repository passes 31 focused contracts and 452 total tests. No GW13 agent fork was created.

## Context and Orientation

`src/orchestration/agent_arm.py` builds hash-bound host requests and validates hosted evidence and challenger responses. It already forbids hidden-outcome references, tools, rule mutation, direct forecast application, FPL execution, and unverified citations. `src/agents/evidence_agent.py` normalises grounded claims and proposals. `src/agents/challenger_agent.py` independently reviews every proposal and exposes an unopposed ID set only for a dismissed challenge.

`src/orchestration/evidence_fork.py` runs the existing manual retrospective fork. It copies the canonical GW12 reviewed solver input, applies adjustments, solves and freezes the plan, and only then reads `hidden-outcome.json`. The canonical control lives under `reports/benchmarks/2025-26`; the manual fork lives under `reports/benchmarks/2025-26-forks`.

The new `agent_fork_adapter.py` is the bridge. “Observed-only” means the object contains episode identity, deadline, observed snapshot hashes, ruleset identity, canonical player baselines, immutable reconstructed passages, and the deterministic candidate hash, but no hidden-outcome reference, realised score, post-deadline player outcome, or canonical result.

## Plan of Work

First add a host-bundle builder that reads the existing reconstructed evidence, episode manifest, and frozen solver artifacts. Convert each source into a content-hashed immutable document with its truthful publication, observation, and availability timestamps. Select only the named evidence players and the two allowed baseline fields. Bind the exact canonical candidate by hash.

Extend the evidence validator with an explicit `retrospective_published_before_deadline` mode. Keep the normal live path unchanged. In retrospective mode, record production ineligibility and allow proposal construction only if publication is not after the cutoff, the claim is not expired, confidence and citation gates pass, and the only production-time failure is the known post-cutoff capture/availability condition.

Add the deterministic adapter. It accepts completed, hash-valid evidence and challenger run artifacts. It verifies that the challenger is bound to the evidence proposal and that every proposed ID is unopposed. It rejects multiple adjustments per player, increases, baseline mismatches, excessive start-probability changes, and unsupported targets. On any rejection it returns an unchanged deep copy plus an explicit fallback reason. On acceptance it updates a copied solver input and emits before/after audit records and the policy hash.

Add a CLI runner that can build the bundle and, after supplied hosted responses are present, run both arm validators and the isolated fork. The runner writes only below `reports/benchmarks/2025-26-agent-forks/gw-12`. It freezes before reveal and publishes a three-way comparison with the canonical and existing manual fork. It refuses to overwrite a differing sealed artifact.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run focused tests during development:

    .\.venv\Scripts\python.exe -m pytest tests/agent-evals/test_agent_fork_adapter.py tests/agent-evals/test_agent_arm.py tests/historical-replay/test_evidence_fork.py -q

Build the observed-only host bundle:

    .\.venv\Scripts\python.exe -m scripts.run_gw12_agent_fork --mode prepare

After the two approved subscription subagent responses have been captured, run:

    .\.venv\Scripts\python.exe -m scripts.run_gw12_agent_fork --mode complete

Then run:

    .\.venv\Scripts\python.exe -m pytest -q
    git diff --check

## Validation and Acceptance

The persisted host bundle must recursively contain no forbidden hidden/realised outcome key or string marker. Every document, request, response, validated output, policy, solver input, plan, and comparison must be content-hash bound.

A valid dismissed challenger review may allow the deterministic adapter to apply supported reductions. A missing provider, invalid response, unsupported target, increased projection, multiple proposals for one player, challenger downgrade, forced rerun, escalation, proposal hash mismatch, or incomplete reviewed-ID set must preserve the exact canonical solver input.

The plan must be frozen and hash-valid before the runner reads the hidden outcome. Hashes of every file in canonical GW12 must match before and after. Running the complete command twice must produce byte-identical output. No GW13 agent-fork directory may be created.

## Idempotence and Recovery

All repository artifacts use canonical JSON and fail-on-difference writes. Preparation is safe to repeat. A changed model response or policy requires a new run/experiment ID rather than replacing a sealed result. If either hosted role fails, the run persists its degradation trace and exact deterministic fallback; it does not partially apply proposals.

## Artifacts and Notes

The first experiment uses:

    episode: benchmark-v0:2025-26:gw12:manager-neutral
    cutoff: 2025-11-22T11:00:00Z
    Gabriel baseline: expected_minutes 85.6, start_probability 0.9524
    Semenyo baseline: expected_minutes 87.7, start_probability 0.9821
    model: gpt-5.6-sol
    surface: Codex ChatGPT-subscription subagent

The previous manual fork is a comparison arm, not training data for the evidence or challenger role. Its adjustments and realised +14 result must not enter either hosted request.

## Interfaces and Dependencies

No new package is required.

`src/orchestration/agent_fork_adapter.py` will expose:

    def build_gw12_agent_host_bundle(...) -> dict[str, Any]

    def apply_agent_adjustments(
        solver_input: Mapping[str, Any],
        evidence_run: Mapping[str, Any],
        challenger_run: Mapping[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]

    def run_isolated_agent_fork(...) -> dict[str, Any]

`src/agents/evidence_agent.validate_evidence_result` and `src/orchestration/agent_arm.build_hosted_request` gain an explicit evidence mode whose default preserves the current production behaviour.

Revision note (2026-07-26): Initial plan written after tracing both existing halves of the system and identifying the truthful retrospective-time seam, target mismatch, deterministic application boundary, and one-week stopping point.

Revision note (2026-07-26): Completed the isolated Sol evidence/challenger run, deterministic application, sealed comparison, idempotence check, canonical immutability check, and regression suite. Recorded the exact +14 result and telemetry limitation.
