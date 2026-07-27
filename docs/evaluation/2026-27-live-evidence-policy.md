# 2026/27 live unstructured-evidence policy

The live evidence programme is an append-only decision ledger, not a web
scraper and not an invitation to place whole articles in model context.

## Source boundary

Automated snapshot admission is allowed only for a source that is registered,
enabled, has a resolved non-prohibited licence status and an explicit allowed
use. The initial automated source is the official FPL endpoint data already
approved for private local analysis.

Official club communications, official news pages and official lineup/minutes
evidence currently enter through manual citations only. A manual record stores
the URL, document hash, publication/observation/availability times, attribution
and a derived claim. It does not retain raw page content. Where registry rights
remain unknown, verbatim excerpts are rejected. Analyst/blog material is
rejected until the exact source has a registry entry and owner approval.

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

## Bounded agent packet

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
