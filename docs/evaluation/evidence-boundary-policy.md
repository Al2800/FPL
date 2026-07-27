# Availability ledger and decision-boundary evidence policy

The live evidence arm must remember what it already knows, but it must not turn silence into a claim. This policy defines how player availability evidence persists and how a bounded evidence pack is selected for an agent.

## Availability lifecycle

Every availability claim records the player, status, confidence, exact publication, observation, availability and expiry timestamps, and source provenance. The ledger is append-only and content-hashed. A decision-time view retains four distinct classes:

- **accepted** — known before the deadline, unexpired, above the evidence confidence threshold, not superseded, and not conflicted;
- **stale** — known but unusable at the deadline, including expired evidence;
- **superseded** — replaced by a later explicit claim;
- **future** — not yet available at the deadline and therefore prohibited from replay use.

An unexpired absence or doubt persists across gameweeks without being copied into each weekly prompt. At expiry, the engine abstains unless a newer claim exists. Missing news never means that a player is fit.

An availability claim permanently supersedes the claims it names once it was known. A recovery from an unresolved absence or doubt must supersede every such claim and state an observed recovery condition: declared fit, returned to training, or started a match. When the recovery claim later expires, the old absence remains superseded; the state becomes unknown rather than reverting to injured.

Different active statuses for the same player are an unresolved conflict. All claims stay visible, but none is accepted until a later claim explicitly supersedes the disagreement. The engine does not resolve a conflict by source recency or confidence alone.

## Decision-boundary retrieval

A decision boundary is a close choice produced by the deterministic engine. It names the decision type (transfer, lineup, captaincy, or chip), the incumbent and alternative, the current projected-points margin, affected players, and a conservative maximum points swing for relevant availability evidence.

For each accepted claim, retrieval estimates impact as:

    maximum boundary swing × claim confidence

A claim can plausibly flip a boundary when this estimate is at least the current margin. Ranking is deterministic:

1. claims that can flip at least one supplied boundary;
2. smaller best margin;
3. larger estimated impact;
4. higher confidence;
5. stable claim identifier.

The pack is capped by `max_evidence`. Accepted evidence not selected due to the cap remains named under omitted identifiers. Conflicts and abstentions are always included, so a bounded prompt cannot hide uncertainty.

This is attention routing, not an automatic projection adjustment. The deterministic engine supplies identical state, forecasts and boundaries to every agent arm. The agent assesses the selected unstructured evidence under the same policy, and all proposed changes still pass the shared completion and validation gates.

## Shadow attribution

Every evidence-versus-control comparison records separate fields for:

- evidence claims accepted at the deadline;
- whether the complete frozen plan changed;
- whether the transfer list changed and both transfer lists;
- realised score delta, or a pending marker before outcome reveal.

This separation prevents a later state-compounding gain from being described as a direct news gain. The frozen no-evidence shadow remains the counterfactual for determining whether evidence changed the current decision.

## Historical and live use

The Timber GW34–GW36 regression test demonstrates state mechanics with one long-lived absence claim across three real 2025–26 deadlines. It is a synthetic lifecycle fixture derived from the historical failure mode, not a rewrite of the archived source’s actual expiry. Historical bundles retain their original timestamps.

For 2026–27 live operation, claims must be captured immutably as they arrive. Expiry should be set conservatively from the source and situation. A subsequent press conference, training report, official squad update, or observed match start should append a new claim; prior history must never be edited.
