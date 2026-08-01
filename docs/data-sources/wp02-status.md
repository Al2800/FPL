# WP-02 Source governance — status

**Package:** WP-02  
**Registry:** `control/sources/source-registry.yaml` (`0.1.0`)

## Done-when checklist (Section 6.1 Tier 1)

| Criterion | Status |
|---|---|
| Every Section 6.1 source has a complete Section 6.2 field set | Met |
| Collector `enabled` follows licence/allowed_use | Met — only `fpl-official-endpoints` enabled |
| Disabled sources document an alternative or accepted gap | Met — see `notes` on each entry |

## Enabled collectors

- `fpl-official-endpoints` — private local snapshots per ADR-0001/0002 (`licence_status: restricted`, not prohibited).

## Explicitly disabled (with alternatives)

| Source | Alternative / gap |
|---|---|
| Official rules/news HTML | Manual citation into `control/rules/` (WP-01) |
| Authenticated manager state | Manual entry (ADR-0005); public entry endpoints for cross-check later |
| Club communications | Enabled for manual citation only (registry 0.6.3+; no HTML scrape) |
| Competition schedules | FPL fixtures endpoint + manual revision notes |

## Out of scope for this pass

Tier 2/3 sources (vaastav, FBref, odds, line-up services, etc.) are not yet registered. They remain disabled-by-default until individual terms reviews — do not enable collectors for them.

> **Status update — 28 July 2026:** This page records the original WP-02
> completion state. The source registry is now version `0.6.0` and is
> authoritative. It additionally enables the governed private/local uses of
> `vaastav-fpl`, `football-data-co-uk`, `the-odds-api` and
> `statsbomb-open`; it does not make their raw data redistributable. Consult
> each current registry entry, activation approval and allowed-use field before
> collection.

The paragraph above is historical. As of registry `0.6.0`, the specifically
named sources in the status update are registered and enabled within their
bounded allowed uses. Other Tier 2/3 sources remain disabled unless their
current registry entry says otherwise.
