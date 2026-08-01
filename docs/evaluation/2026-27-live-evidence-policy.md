# 2026/27 live unstructured-evidence policy

The live evidence programme is an append-only decision ledger, not a web
scraper and not an invitation to place whole articles in model context.

## Source boundary

Automated snapshot admission is allowed only for a source that is registered,
enabled, has a resolved non-prohibited licence status and an explicit allowed
use. The initial automated source is the official FPL endpoint data already
approved for private local analysis.

Official club communications, official news pages and official lineup/minutes
evidence now have two controlled paths. A manual citation remains valid, and
the scheduled model-run path may visit one registered official URL at a time,
hash the response in memory, discard the body, and emit a derived claim
candidate. The host validates the candidate before appending it. Both paths
store the URL, document hash, publication/observation/availability times,
attribution and derived claim; neither retains a bulk article mirror. Where
registry rights remain unknown, verbatim excerpts and automated candidates are
rejected. Analyst/blog material is rejected until the exact source has a
registry entry and owner approval.

This policy does not enable any new collector.

## Claim contract

Every claim records:

- exact source, document, URL and source-content hash;
- `published_at`, `observed_at`, `available_at` and `expires_at`;
- stable identity bindings and match precision;
- claim type, structured value, confidence and claim precision;
- relevant decision-boundary IDs and estimated maximum point impact;
- source authority, licence precision, allowed use, retention and attribution;
- explicit supersession references;
- quarantine status for prompt-injection-like text.

Claims append in availability order. A later claim may supersede only an
earlier claim about the same stable subject and claim type. At a checkpoint,
future, expired, superseded and quarantined records remain visible but are
excluded. Conflicting unsuperseded values are excluded until an explicit later
claim supersedes them; the ledger never silently merges them.

## Model-run admission and bounded agent packet

The model run is deliberately not a ledger writer:

1. The engine model searches every catalogue club and builds a broad watchlist
   before the final 15 is chosen.
2. It emits structured candidates plus a concise decision trace (choice,
   rejected alternatives, opportunity cost, claims, confidence and falsifiers).
3. `scripts/ingest_model_evidence_run.py` checks the prompt hash, catalogue
   coverage, exact player IDs, registered official domains, source rights,
   timestamps, confidence and ephemeral source hashes.
4. Valid candidates append to a content-addressed availability ledger. Invalid
   candidates are rejected with reasons; incomplete club coverage marks the run
   degraded. The strategy briefing retains the model-run and audit hashes.

This makes Composer/Grok research useful without allowing model prose or
community citations to become governed evidence. It also gives the owner a
machine-readable explanation of what the model considered and why.

The deterministic engine first emits its decision boundaries and margins.
Only active evidence tied to those boundaries is ranked for the agent.
Confidence-weighted impact, ability to cross a margin, and confidence determine
the ordering. The packet has fixed claim-count and character budgets and lists
every omission.

The packet is content-addressed and bound to the shared engine output hash.
Agents cannot add claim IDs that were not in the packet.

## Frozen counterfactual and degradation

Before an evidence call, the host freezes the no-evidence candidate byte for
byte. An agent proposal must:

- complete with schema-valid structured output;
- bind the shared engine and evidence-packet hashes;
- cite only packet claim IDs;
- include a content-bound proposal and declared confidence.

A challenger must bind the same proposal and accept it. Missing evidence,
timeouts, malformed output, outside-packet claims, challenger failure or agent
abstention all return the frozen no-evidence candidate. The failure reason is
recorded; it is never converted into an invented evidence decision.

The evidence actual and frozen no-evidence plans remain side by side for later
same-state and longitudinal attribution. Both are advisory-only:
`browser_actions` and `account_writes` are always false.
