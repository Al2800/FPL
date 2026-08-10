# Graded AI-overlay improvement loop — review (ticket 21)

**Date:** 6 August 2026  
**Status:** Recommendation — **defer** hosted training / provider binding  
**Authorises:** Written review only (no live `run_gameweek` changes)  
**Related:** ADR-0010, ADR-0016, ADR-0021, ADR-0024; tickets 10, 11

## Verdict

Fit is real for the **proposal-only** evidence/challenger overlay, but the lab
is not ready to bind a cloud training provider or install a Verifiers stack.
The scarce asset is already local: sealed rubrics, golden cases, forced-timeout
degrade contracts, and JSONL traces. **Defer** Prime Intellect Lab (and any
metered training/inference host) until early 2026/27 live Gameweeks produce a
stable graded corpus. The smallest future experiment, if re-opened, is a
**local offline graded harness** over existing artefacts — no new secrets, no
RL that can enforce transfers or chips, and a fresh ADR amending ADR-0021/0024
before any provider.

## Architecture fit

| Constraint | Overlay loop implication |
| --- | --- |
| LLMs propose only (plan §4.3 / §13.3) | Rewards may score schema validity, citation grounding, unopposed adjustments, and sealed outcome deltas — never optimiser replacement |
| Deterministic core + GDR degrade (ADR-0016, ticket 11) | Timeout / T-90m must remain a graded “correct degrade”, not a training failure to override |
| No API arm (ADR-0024); sol subscription (ADR-0021) | Hosted training that needs API keys or non-local scheduling conflicts with current surface |
| No secrets in Git or model context | Provider accounts, LoRA weights with leaked prompts, and raw dumps stay out |
| Phase discipline | Vector retrieval, rival analysis, computer-use execution remain deferred |

A Verifiers-style **environment** (dataset + harness + rubric) maps cleanly onto
the overlay layer. It does **not** map onto rules validation, scoring, or the
enumerative optimiser.

## Inventory of sealed rewards (already in-repo)

### Agent-eval golden cases

- `evals/golden-cases/agents/evidence-agent-v1.json` — valid claims + proposed
  adjustments with citation hashes and expiry.
- `evals/golden-cases/agents/challenger-v1.json` — independent review /
  escalation outcomes.
- `evals/golden-cases/agents/failure-cases.json` — expected failure categories:
  `invalid_output`, `tool_failure`, `policy_denial`, `budget_exhaustion`
  (stale/conflict/unknown player, rule mutation, injection, budget).
- Evidence fixtures under `evals/golden-cases/evidence/` (injection presser,
  conflict lineups, escalation blocks, structured tool boundary, hosted
  response failures).

### Validation and policy gates

- `src/agents/evidence_agent.py` / `challenger_agent.py` — closed JSON Schema
  validation (`prompts/*/output.schema.json`).
- `src/orchestration/agent_arm.py` — forbidden input walk, hosted response lint,
  repair request, deterministic fallback; model `gpt-5.6-sol` on subscription
  Codex only.
- `control/policies/scheduled-agent-overlay-v1.json` — T-48h / T-8h / T-2h /
  T-90m schedule and wall-clock budgets.

### Fork fixtures and traces

- Historical agent-fork runners (`scripts/run_gw*_agent_fork*.py`) plus
  `scripts/run_agent_fork.py` dispatcher (ticket 12 / ADR-0026 Option A).
- ADR-0010 JSONL traces via `src/orchestration/agent_trace.py`.

### GDR degrade contracts

- Forced-timeout hosted response and T-90m deterministic fallback in
  `src/orchestration/scheduled_agent_overlay.py`.
- `run_gameweek(..., agent_overlay=...)` attaches citations or degrade reasons;
  absence of overlay marks degraded data quality without blocking the
  deterministic plan.

### Sealed outcomes (use with care)

- Outcome golden cases under `evals/golden-cases/outcomes/` (autosub, chips)
  are rules/scoring fixtures — eligible only as **post-freeze** reward labels
  for overlay proposals that touched minutes/chips *after* the episode cutoff,
  never as live training targets before freeze
  (`live-shadow-candidate` prohibition:
  `must_not_train_on_live_outcomes_before_freeze`).

## Candidate environment sketch

One Verifiers-style env, built only from the inventory above:

1. **Dataset** — hash-bound hosted requests + approved passages from golden /
   fork fixtures (observed-only; no hidden-outcome partition).
2. **Harness** — invoke `run_agent_arm` or the scheduled overlay with
   injectable host responses; always exercise the forced-timeout path as a
   first-class episode.
3. **Rubric (proposal-only rewards)**
   - schema + role validity;
   - citation excerpt hash groundable to host-owned passages;
   - no forbidden fields / injection / rule mutation;
   - challenger escalation matches expected category when preregistered;
   - optional sealed post-GW delta: proposal vs control points **only** from
     frozen replay partitions.
4. **Episode terminal** — emit a graded record + ADR-0010 JSONL; never write
   to FPL accounts or mutate live solver selection.

Reward stays discontinuous and fail-closed: invalid → score 0 / degrade, not a
soft RL signal into the optimiser.

## Option comparison

| Option | Cost / secrets | Reproducibility | ADR impact | Fit now |
| --- | --- | --- | --- | --- |
| **A. Local graded eval only** (wrap golden + overlay contracts; no new package) | None | High — content-addressed fixtures | None | **Preferred next step when re-opened** |
| **B. Local Verifiers package** | Needs owner install sign-off; dependency age policy | Good if pinned | Docs only until training | Premature until A proves signal |
| **C. Hosted (Prime Intellect Lab / similar)** | Account, possible API keys, egress, training artefacts | Weaker unless every reward + prompt + weight is sealed back into Git-adjacent private store | **Must amend ADR-0021/0024** (and likely ADR-0016 budgets) | **No-go for now** |

Prime Intellect is a plausible **alpha for post-training the overlay proposer**
once the lab owns a large graded corpus. It is a poor fit while the live path
still needs first 2026/27 GDRs, and while ADR-0024 declines metered API arms.

## Phase risks

- Training on pre-freeze live outcomes contaminates the shadow protocol.
- A hosted loop that “improves” the overlay into selecting transfers/chips
  would violate the propose-only boundary.
- Package installs without session sign-off violate the global agent safety
  policy.
- Spending cycles on industrialised eval before ticket 19 (lineup trial) and
  early live Gameweeks crowds out the §17.6 live-first warning.

## Recommendation

**Defer** (explicit). Do not bind Prime Intellect, do not install Verifiers, do
not change `run_gameweek` or the deterministic core for this ticket.

When re-opened (suggested gate: ≥3 live 2026/27 GDRs with completed or
correctly degraded overlay traces, outside a deadline week):

1. Implement option A as a thin `evals/` graded suite over existing golden
   cases + forced-timeout overlay — still no new dependencies.
2. Only if A shows stable failure modes worth targeting, consider option B
   with an owner-approved pin.
3. Only if B needs distributed training/inference, draft an ADR amending
   ADR-0021/0024 for a named provider (Prime Intellect or other), with secret
   handling and hard caps — then the smallest hosted experiment is
   **offline LoRA on frozen graded traces**, never live enforcement.

## Out of scope (confirmed)

- No live path changes shipped with this review.
- No cloud account binding, API keys, or package installs.
- No scrape or invented FPL outcomes for rewards.
