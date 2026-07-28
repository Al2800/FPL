# 2026/27 evidence acquisition and candidate-boundary retrieval

## Outcome

The live engine should accumulate a large governed evidence ledger while each
agent receives only a small, reproducible packet about decisions that are
actually close. More evidence may improve an agent, but raw volume and model
context size are not the benchmark. The benchmark is whether admitted
point-in-time evidence changes a valid decision and improves its paired
no-evidence outcome.

## System boundary

The system has four separately measured planes:

1. **Raw acquisition** — immutable source attempts, snapshots, citations and
   failures.
2. **Active ledger** — deduplicated claims that were known before the
   checkpoint, unexpired, unsuperseded, unquarantined and unconflicted.
3. **Retrieved packet** — active claims selected for deterministic candidate
   boundaries under fixed claim and character budgets.
4. **Accepted adjustment** — schema-valid, cited agent proposals that pass the
   independent challenger and deterministic host validation.

Counts must never be collapsed across these planes. Ten thousand downloaded
characters are not ten thousand useful evidence characters, and twelve
retrieved claims are not twelve accepted forecast changes.

## Acquisition funnel

The source registry remains authoritative. Coverage configuration can require
or schedule a source family but cannot enable it.

- Official FPL endpoint snapshots are automated because their registry entry
  is enabled and rights-resolved for private local analysis.
- Official FPL news, club communications, press conferences, training reports
  and official lineup/minutes evidence use linked derived claims while their
  registry entries remain manual or disabled.
- An automated adapter for a disabled, unknown-rights or unregistered source
  is refused before its callback or network boundary runs.
- Specifically approved analyst material remains blocked until each exact
  source receives a registry entry and owner approval.
- Every failure or missing family is a visible gap. Silence means unknown, not
  fit, available or unchanged.

The configured checkpoints are daily preseason, T-48h, T-24h, T-8h, T-2h,
final pre-deadline and post-match. A coverage report evaluates only the source
families required at that checkpoint.

## Deterministic attention set

The candidate layer consumes the exact structured solver input and output used
by every arm. It does not rescore players from unstructured evidence.

The solver's evaluated candidates provide a legal universe because they have
already passed position, price, bank, club-limit, transfer and lineup rules.
The retrieval layer projects that universe into:

- an owned watchlist, including availability-risk players, weak starters or
  bench players, selected sales and players with a strong legal replacement;
- legal external candidates that occur in evaluated transfer plans, grouped by
  position, price, club and planning horizon;
- transfer boundaries measured by objective distance from the selected plan;
- the selected XI versus best-bench lineup boundary;
- captain versus vice-captain and other retained captain alternatives; and
- stable player, club and fixture entities attached to each boundary.

If the supplied engine bundle contains realised/outcome fields or does not bind
to the solver input fingerprint, retrieval fails closed.

## Claim retrieval

An active claim is relevant when either:

- it explicitly names a generated boundary; or
- one of its stable identity bindings matches a player, club or fixture entity
  expanded from that boundary.

Identity aliases are host-owned data. They may map an official FPL code to a
canonical player UID, but the agent cannot invent an alias.

Ranking is deterministic:

1. claims capable of flipping at least one boundary;
2. decision type priority and smaller objective/points margin;
3. larger confidence-weighted estimated impact;
4. fresher availability time within the source family window;
5. stronger registered source authority;
6. higher confidence; and
7. stable claim ID.

Only conflicts attached to an expanded boundary entity remain agent-visible,
and they are not converted into accepted claims. Future, expired, superseded
and quarantined claims remain counted under exclusions. Claims excluded as
irrelevant, stale, over the claim cap or over the character cap retain explicit
identifiers and reasons in host-owned audit metadata.

The packet carries an explicit context contract. Selected evidence,
boundary-relevant conflicts, boundaries, limits and binding hashes may enter
the agent prompt. Full omission identifiers and exclusion counts are host-audit
only and must never enter model context. This keeps the prompt bounded without
losing completeness in coverage and error-rate evaluation.

The packet is sealed and bound to the structured engine output and evidence
view hashes. Identical inputs yield identical bytes for every model arm.

## Coverage and evaluation

Each checkpoint reports:

- required source-family completion and automated success;
- expected club and player observation coverage;
- source freshness and stale families;
- raw documents, deduplicated claims and duplicate rate;
- active, future, expired, superseded, conflicted and quarantined claims;
- retrieved claims and omission rates by reason;
- golden relevant-claim recall and irrelevant-claim precision;
- packet construction latency against the configured local guardrail; and
- accepted adjustments, changed plans and realised paired score deltas when
  outcomes later exist.

Coverage failures degrade the evidence arm but do not block the shared
structured recommendation. Live reliance requires pre-registered thresholds
and repeated shadow evidence; a single historical path is exploratory.

## Agent orchestration

The same packet can be reviewed by multiple isolated evidence agents or by
shards divided by decision boundary. Their outputs are structured proposals,
not plan authority. Host-owned deterministic reduction deduplicates claim IDs,
preserves disagreements and sends a bounded combined proposal to the
challenger. The frozen no-evidence candidate remains unchanged beside the
evidence arm.

Model capability may be benchmarked later by allowing a stronger model to
process more *registered and point-in-time* evidence, but that is a distinct
information-budget arm. Equal-packet model comparisons and expanded-information
comparisons must not be conflated.
