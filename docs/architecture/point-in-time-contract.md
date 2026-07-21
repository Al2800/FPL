# Point-in-time contract

**Status:** Active  
**Package:** WP-03  
**Plan references:** Sections 7.2, 11.4, 21.3

## Purpose

Every temporal record used in a decision must be filterable so that a Gameweek Decision Record can be reconstructed using only information that was available at or before the relevant deadline.

## Required timestamps

Where applicable, records carry:

| Field | Meaning |
|---|---|
| `published_at` | When the source published the information |
| `observed_at` | When this system collected or recorded it |
| `effective_at` | When the underlying world state became true |
| `finalised_at` | When FPL locked or otherwise confirmed it |

Derived decision-plane rows additionally carry:

| Field | Meaning |
|---|---|
| `available_at` | Earliest instant at which this system may use the record in a decision (`available_at = observed_at` unless a later effective constraint applies) |

## Hard filter

```text
usable_in_decision(record, deadline) ⇔ record.available_at <= deadline
```

Outcome data, post-deadline `ep_this` revisions, and later fixture corrections must not appear in earlier decision snapshots (plan Section 11.4). Post-deadline captures of ephemeral fields such as `ep_next` / FDR must be labelled as leakage-risk and excluded from pre-deadline features.

## Provenance on derived records

Every derived record retains:

- source references (`source_id`, content hash or document id);
- transformation version;
- ruleset id / version;
- model version (if any);
- prompt / agent-run id (if any).

## Testing obligation

Historical replay (Section 21.3) and contract tests must fail closed if a feature with `available_at > deadline` enters a decision context.
